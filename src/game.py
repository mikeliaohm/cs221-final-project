import os
import sys
import asyncio
import logging

from typing import List, Tuple

from agent.card_stats import CardSuit
import agent.conf
from agent.evaluator import AgentEvaluator
from agent.minimax_agent import MinimaxAgent
from agent.minimax_bayes_agent import MinimaxBayesAgent
from agent.minimax_opt_agent import MinimaxOptAgent

# Set logging level to suppress warnings
logging.getLogger().setLevel(logging.ERROR)
# Just disables the warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# This import is only to help PyInstaller when generating the executables
import tensorflow as tf

import pprint
import time
import datetime
import json
import asyncio
import uuid
import shelve
import re
import argparse
import numpy as np

import human
import bots
import conf

from sample import Sample
from bidding import bidding
from deck52 import board_dealer_vuln, decode_card, card52to32, get_trick_winner_i, random_deal
from bidding.binary import DealData
from objects import CardResp, Card, BidResp
from claim import Claimer
from pbn2ben import load
from util import calculate_seed, get_play_status
# This helps resolve the dependency issue of pythonnet (which needs .NET runtime)
try:
    from pimc.PIMC import BGADLL
    from pimc.PIMCDef import BGADefDLL
except:
    print("Cannot import PIMC, which is dependent on pythonnet, which needs .NET runtime.")

# Bridge Agent
import agent
from agent.human_agent import HumanAgent
from agent.oracle import TheOracle
from agent.naive_agent import NaiveAgent
from agent.dummy_agent import DummyAgent

agent_type = agent.conf.AGENT_TYPE
NORTH = 0
EAST = 1
SOUTH = 2
WEST = 3

def get_execution_path():
    # Get the directory where the program is started from either PyInstaller executable or the script
    return os.getcwd()


def random_deal_board(number=None):
    deal_str = random_deal()
    if number == None:
        number = np.random.randint(1, 17)
    auction_str = board_dealer_vuln(number)

    return deal_str, auction_str


class AsyncBotBid(bots.BotBid):
    async def async_bid(self, auction):
        return self.bid(auction)

class AsyncBotLead(bots.BotLead):
    async def async_opening_lead(self, auction):
        return self.find_opening_lead(auction)

class AsyncCardPlayer(bots.CardPlayer):
    async def async_play_card(self, trick_i, leader_i, current_trick52, players_states, bidding_scores, quality, probability_of_occurence, shown_out_suits, play_status):
        return await self.play_card(trick_i, leader_i, current_trick52, players_states, bidding_scores, quality, probability_of_occurence, shown_out_suits, play_status)
    
    
class Driver:

    def __init__(self, models, factory, sampler, seed, verbose, log, log_file_name=None):
        self.models = models
        self.sampler = sampler
        self.factory = factory
        self.confirmer = factory.create_confirmer()
        self.channel = factory.create_channel()

        if seed is not None:
            print(f"Setting seed={seed}")
            np.random.seed(seed)

        #Default is a Human South
        self.human = [False, False, True, False]
        self.human_declare = False
        self.rotate = False
        self.name = models.name
        self.ns = models.ns
        self.ew = models.ew
        self.verbose = verbose
        self.play_only = False
        self.claim = models.claim
        self.claimed = None
        self.claimedbydeclarer = None
        self.conceed = None
        self.decl_i = None
        self.strain_i = None
        self.log = log # bool to indicate if agent should log the messages to the console
        self.log_file_name = "temp" if log_file_name is None else log_file_name # the file to log the result of a single deal

    def set_deal(self, board_number, deal_str, auction_str, play_only = None, bidding_only=False, contract=None, declarer_i=None):
        self.play_only = play_only
        self.bidding_only = bidding_only
        self.board_number = board_number
        self.deal_str = deal_str
        self.hands = deal_str.split()
        self.deal_data = DealData.from_deal_auction_string(self.deal_str, auction_str, "", self.ns, self.ew,  32)
        self.agent: agent.conf.AGENT_TYPES = None   # Reset the agents
        self.contract = contract
        self.decl_i = declarer_i

        auction_part = auction_str.split(' ')
        if play_only == None and len(auction_part) > 2: play_only = True
        if play_only:
            self.auction = self.deal_data.auction
            self.play_only = play_only
        self.bidding_only = bidding_only
        if self.rotate:
            self.dealer_i = (self.deal_data.dealer + 1) % 4
            self.vuln_ns = self.deal_data.vuln_ew
            self.vuln_ew = self.deal_data.vuln_ns
            self.hands.insert(0, self.hands.pop())
            self.deal_str = " ".join(self.hands)
            print("Rotated deal: "+self.deal_str)
        else:
            self.dealer_i = self.deal_data.dealer
            self.vuln_ns = self.deal_data.vuln_ns
            self.vuln_ew = self.deal_data.vuln_ew
        self.trick_winners = []

        # Set up the agent player (South Seat)
        if agent_type == TheOracle:
            # The Oracle gets to see all hands
            self.agent = agent_type(self.deal_str, SOUTH, self.log)
        else:
            self.agent = agent_type(self.hands[SOUTH], SOUTH, self.log)

        # Now you can use hash_integer as a seed
        hash_integer = calculate_seed(deal_str)
        if self.verbose:
            print("Setting seed (Full deal)=",hash_integer)
        np.random.seed(hash_integer)


    async def run(self):
        result_list = self.hands.copy()

        # If human involved hide the unseen hands
        if np.any(np.array(self.human)):
            for i in range(len(self.human)):
                if not self.human[i]:
                    result_list[i] = ""

        await self.channel.send(json.dumps({
            'message': 'deal_start',
            'dealer': self.dealer_i,
            'vuln': [self.vuln_ns, self.vuln_ew],
            'hand': result_list,
            'name': self.name,
            'board_no' : self.board_number,
            'agent': f"{agent_type.__name__}",
            "filename": self.log_file_name,
        }))

        self.bid_responses = []
        self.card_responses = []

        if self.play_only:
            auction = self.auction
            for bid in auction:
                if bidding.BID2ID[bid] > 1:
                    self.bid_responses.append(BidResp(bid=bid, candidates=[], samples=[], shape=-1, hcp=-1, who="PlayOnly", quality=None))
        else:
            auction = await self.bidding()

        if self.contract is None:
            contract = bidding.get_contract(auction)
            self.contract = contract[:-1]
            self.decl_i = bidding.get_decl_i(contract)
            await self.channel.send(json.dumps({
                'message': 'deal_end',
                'pbn': self.deal_str,
                'dict': self.to_dict() 
            }))
            if self.bidding_only:
                return

        self.strain_i = bidding.get_strain_i(self.contract)
        if self.decl_i is None:
            self.decl_i = bidding.get_decl_i(self.contract)
        
        await self.channel.send(json.dumps({
            'message': 'auction_end',
            'declarer': self.decl_i,
            'auction': auction,
            'strain': self.strain_i
        }))

        if self.bidding_only:
            return
        
        print("trick 1")

        opening_lead52 = (await self.opening_lead(auction))

        if str(opening_lead52.card).startswith("Conceed"):

            self.conceed = True
            self.claimed = 0
            self.claimedbydeclarer = False
            await self.channel.send(json.dumps({
                'message': 'deal_end',
                'pbn': self.deal_str,
                'dict': self.to_dict() 
            }))
            return
        
        self.card_responses.append(opening_lead52)

        opening_lead52 = opening_lead52.card.code()
        await self.channel.send(json.dumps({
            'message': 'card_played',
            'player': (self.decl_i + 1) % 4,
            'card': decode_card(opening_lead52)
        }))

        # If human is dummy display declarers hand unless declarer also is human
        if self.human[(self.decl_i + 2) % 4] and not self.human[self.decl_i]:
            hand = self.deal_str.split()[self.decl_i]
            await self.channel.send(json.dumps({
                'message': 'show_dummy',
                'player': self.decl_i,
                'dummy': hand
            }))
        else:
            # dummys hand
            hand = self.deal_str.split()[(self.decl_i + 2) % 4]
            await self.channel.send(json.dumps({
                'message': 'show_dummy',
                'player': (self.decl_i + 2) % 4,
                'dummy': hand
            }))

        if self.verbose: 
            for card_resp in self.card_responses:
                pprint.pprint(card_resp.to_dict(), width=200)

        
        await self.play(self.contract, self.strain_i, self.decl_i, auction, opening_lead52)

        await self.channel.send(json.dumps({
            'message': 'deal_end',
            'pbn': self.deal_str,
            'dict': self.to_dict()
        }))

    def to_dict(self):
        result = {
            'timestamp': time.time(),
            'dealer': self.dealer_i,
            'vuln_ns': self.vuln_ns,
            'vuln_ew': self.vuln_ew,
            'hands': self.deal_str,
            'bids': [b.to_dict() for b in self.bid_responses],
            'contract': self.contract,
            'play': [c.to_dict() for c in self.card_responses],
            'trick_winners': self.trick_winners,
            'board_number' : self.board_number,
            'player': self.name,
            'rotated': self.rotate,
            'play_only': self.play_only,
            'bidding_only': self.bidding_only,
            'human': self.human
        }
        if self.decl_i is not None:
            result['declarer'] = self.decl_i
        if self.strain_i is not None:
            result['strain'] = self.strain_i
        if self.claimed is not None:
            result['claimed'] = self.claimed
        if self.claimedbydeclarer is not None:
            result['claimedbydeclarer'] = self.claimedbydeclarer
        if self.conceed is not None:
            result['conceed'] = self.conceed
        return result

# trick_i : 
# 	the number of the trick (0-12)
# player_i : 
# 	the number of the player (0-3)
# card_players : 
# 	a list of bots.CardPlayer(left,dummy,right,declarer). Updated trough time
# 	init :
#         card_players = [
#                     bots.CardPlayer(self.models.player_models, 0, lefty_hand, dummy_hand, contract, is_decl_vuln),
#                     bots.CardPlayer(self.models.player_models, 1, dummy_hand, decl_hand, contract, is_decl_vuln),
#                     bots.CardPlayer(self.models.player_models, 2, righty_hand, dummy_hand, contract, is_decl_vuln),
#                     bots.CardPlayer(self.models.player_models, 3, decl_hand, dummy_hand, contract, is_decl_vuln)
#                 ] 
#         Note : for some reason the declarer hand is set up as the public hand for the dummy.
#         self.x_play contains the cards played as 13 list of binaries repr, one for each card played
#         self.hand52 contains the hand of the player as a list of binaries (except for dummy)
#         self.public52 contains the dummy hand as a list of binaries (except for dummy)
#     each card played :
#         card_player[player_i].set_own_card_played52(card52)
#         if player_i==1 : (dummy)
#             card_player.set_public_card_played52(card52) for all cards players except dummy
#         if player_i==3 : (declarer)
#             dummy.set_public_card_played52(card52) # Why this ? Because of the curious point mentionned before
# shown_out_suit :
#     A list of set, each set containing the shown_out suit as a number(spades=0,clubs=3)
#     Updated for each card play     
# players_cards played:
# 	a list of 4 list(left,dummy,right,declarer). 32 repr
# 	Updated only when the trick is finished
# current_trick : 
# 	the current trick, is the order the card have been played. 32 repr
# self.padded_auction : 
# 	The auction, with the pad at the begining
# card_players[player_i].hand.reshape((-1, 32)) :
# 	The 13 cards of a player, reshaped into a list. Not updated trough tricks. 32 repr 
# self.vuln :
# 	The vuls, as a list of two bools

# After each trick is done :
#     for each card played, init the x_play slice of the next trick. Pain in the ass

    async def play(self, contract, strain_i, decl_i, auction, opening_lead52):
        
        level = int(contract[0])
        is_decl_vuln = [self.vuln_ns, self.vuln_ew, self.vuln_ns, self.vuln_ew][decl_i]

        lefty_hand = self.hands[(decl_i + 1) % 4]
        dummy_hand = self.hands[(decl_i + 2) % 4]
        righty_hand = self.hands[(decl_i + 3) % 4]
        decl_hand = self.hands[decl_i]

        pimc = [None, None, None, None]

        if self.models.pimc_use_declaring: 
            # No PIMC for dummy, we want declarer to play both hands
            declarer = BGADLL(self.models, dummy_hand, decl_hand, contract, is_decl_vuln, self.verbose)
            pimc[1] = declarer
            pimc[3] = declarer
            if self.verbose:
                print("PIMC",dummy_hand, decl_hand, contract)
        else:
            pimc[1] = None
            pimc[3] = None
        if self.models.pimc_use_defending:
            pimc[0] = BGADefDLL(self.models, dummy_hand, lefty_hand, contract, is_decl_vuln, 0, self.verbose)
            pimc[2] = BGADefDLL(self.models, dummy_hand, righty_hand, contract, is_decl_vuln, 2, self.verbose)
            if self.verbose:
                print("PIMC",dummy_hand, lefty_hand, righty_hand, contract)
        else:
            pimc[0] = None
            pimc[2] = None

        # Set the card player models here
        card_players = [
            AsyncCardPlayer(self.models, 0, lefty_hand, dummy_hand, contract, is_decl_vuln, self.sampler, pimc[0], self.verbose),
            AsyncCardPlayer(self.models, 1, dummy_hand, decl_hand, contract, is_decl_vuln, self.sampler, pimc[1], self.verbose),
            AsyncCardPlayer(self.models, 2, righty_hand, dummy_hand, contract, is_decl_vuln, self.sampler, pimc[2], self.verbose),
            AsyncCardPlayer(self.models, 3, decl_hand, dummy_hand, contract, is_decl_vuln, self.sampler, pimc[3], self.verbose)
        ]
        self.agent.set_init_x_play(dummy_hand, contract, decl_i)
        agent_no = None

        # check if user is playing and update card players accordingly
        # the card players are allways positioned relative to declarer (lefty = 0, dummy = 1 ...)
        for i in range(4): 
            if self.human[i]:
                # We are declarer or human declare and dummy
                if decl_i == i or self.human_declare and decl_i == (i + 2) % 4:
                    # keep the old setup
                    # card_players[3] = self.factory.create_human_cardplayer(self.models, 3, decl_hand, dummy_hand, contract, is_decl_vuln)
                    # card_players[1] = self.factory.create_human_cardplayer(self.models, 1, dummy_hand, decl_hand, contract, is_decl_vuln)
                    card_players[1] = DummyAgent(self.hands[NORTH], NORTH, self.log, self.agent)
                    card_players[1].set_init_x_play(decl_hand, contract, decl_i)
                    card_players[3] = self.agent
                    self.agent.set_auction(self.get_initial_bided_suit(auction))
                    agent_no = 3

                # We are lefty
                if i == (decl_i + 1) % 4:
                    # card_players[0] = self.factory.create_human_cardplayer(self.models, 0, lefty_hand, dummy_hand, contract, is_decl_vuln)
                    card_players[0] = self.agent
                    self.agent.set_auction(self.get_initial_bided_suit(auction))
                    agent_no = 0
                # We are righty
                if i == (decl_i + 3) % 4:
                    # card_players[2] = self.factory.create_human_cardplayer(self.models, 2, righty_hand, dummy_hand, contract, is_decl_vuln)
                    card_players[2] = self.agent
                    self.agent.set_auction(self.get_initial_bided_suit(auction))
                    agent_no = 2

        claimer = Claimer(self.verbose)

        player_cards_played = [[] for _ in range(4)]
        shown_out_suits = [set() for _ in range(4)]

        leader_i = 0

        tricks = []
        tricks52 = []
        trick_won_by = []

        opening_lead = card52to32(opening_lead52)

        current_trick = [opening_lead]
        current_trick52 = [opening_lead52]

        card_players[0].hand52[opening_lead52] -= 1

        for trick_i in range(12):
            if trick_i != 0:
                print(f"trick {trick_i+1} lead:{leader_i}")

            for player_i in map(lambda x: x % 4, range(leader_i, leader_i + 4)):
                if self.verbose:
                    print('player {}'.format(player_i))
                
                if trick_i == 0 and player_i == 0:
                    # To get the state right we ask for the play when using Tf.2X
                    if self.verbose:
                        print('skipping opening lead for ',player_i)
                    for i, card_player in enumerate(card_players):
                        card_player.set_real_card_played(opening_lead52, player_i)
                        card_player.set_card_played(trick_i=trick_i, leader_i=leader_i, i=0, card=opening_lead)
                    continue
                
                play_status = get_play_status(card_players[player_i].hand52,current_trick52)

                if isinstance(card_players[player_i], bots.CardPlayer):
                    rollout_states, bidding_scores, c_hcp, c_shp, good_quality, probability_of_occurence = self.sampler.init_rollout_states(trick_i, player_i, card_players, player_cards_played, shown_out_suits, current_trick, self.dealer_i, auction, card_players[player_i].hand_str, [self.vuln_ns, self.vuln_ew], self.models, card_players[player_i].rng)
                    assert rollout_states[0].shape[0] > 0, "No samples for DDSolver"
                    card_players[player_i].check_pimc_constraints(trick_i, rollout_states, good_quality)
                else: 
                    rollout_states = []
                    bidding_scores = []
                    c_hcp = -1
                    c_shp = -1
                    good_quality = None
                    probability_of_occurence = []
                    
                await asyncio.sleep(0.01)

                card_resp = None
                while card_resp is None:
                    # TODO(check): this seems to be a good place to use DDS to find optimal play
                    # by the agent
                    # AgentEvaluator()
                    card_resp = await card_players[player_i].async_play_card(trick_i, leader_i, current_trick52, rollout_states, bidding_scores, good_quality, probability_of_occurence, shown_out_suits, play_status)
                    # TODO(check): this seems to be a good place to evaluate the play
                    # made by the agent

                    if (str(card_resp.card).startswith("Conceed")) :
                            self.claimedbydeclarer = False
                            self.claimed = 0
                            self.conceed = True
                            self.trick_winners = trick_won_by
                            print(f"Contract: {self.contract} Accepted conceed")
                            return

                    if (str(card_resp.card).startswith("Claim")) :
                        tricks_claimed = int(re.search(r'\d+', card_resp.card).group()) if re.search(r'\d+', card_resp.card) else None
                        
                        self.canclaim = claimer.claim(
                            strain_i=strain_i,
                            player_i=player_i,
                            hands52=[card_player.hand52 for card_player in card_players],
                            n_samples=50
                        )
                        if (tricks_claimed <= self.canclaim):
                            # player_i is relative to declarer
                            print(f"Claimed {tricks_claimed} can claim {self.canclaim} {player_i} {decl_i}")
                            self.claimedbydeclarer = (player_i == 3) or (player_i == 1)
                            self.claimed = tricks_claimed

                            # Trick winners until claim is saved
                            self.trick_winners = trick_won_by
                            # Print contract and result
                            if self.claimedbydeclarer:
                                print(f"Contract: {self.contract} Accepted declarers claim of {tricks_claimed} tricks")
                            else:
                                print(f"Contract: {self.contract} Accepted opponents claim of {tricks_claimed} tricks")
                            return
                        else:
                            if self.claimedbydeclarer:
                                print(f"Declarer claimed {tricks_claimed} tricks - rejected {self.canclaim}")
                            else:
                                print(f"Opponents claimed {tricks_claimed} tricks - rejected {self.canclaim}")
                            await self.channel.send(json.dumps({
                                'message': 'claim_rejected',
                            }))
                            card_resp = None


                card_resp.hcp = c_hcp
                card_resp.shape = c_shp
                if self.verbose:
                    pprint.pprint(card_resp.to_dict(), width=200)
                
                await asyncio.sleep(0.01)

                self.card_responses.append(card_resp)

                card52 = card_resp.card.code()

                await self.channel.send(json.dumps({
                    'message': 'card_played',
                    'seat': ((decl_i + 1) % 4 + player_i) % 4,
                    'card': card_resp.card.symbol()
                }))

                card32 = card52to32(card52)

                for card_player in card_players:
                    card_player.set_real_card_played(card52, player_i)
                    card_player.set_card_played(trick_i=trick_i, leader_i=leader_i, i=player_i, card=card32)

                # The current trick has been updated with new card played
                current_trick.append(card32)
                current_trick52.append(card52)

                # Decrement the card just played, only used by bots.CardPlayer
                card_players[player_i].set_own_card_played52(card52)
                if player_i == 1:
                    for i in [0, 2, 3]:
                        card_players[i].set_public_card_played52(card52)
                if player_i == 3:
                    card_players[1].set_public_card_played52(card52)

                # TODO(check): seems to a good place to use DDS to solve board, 
                # this is where card played has been updated in Ben.

                # update shown out state
                if card32 // 8 != current_trick[0] // 8:  # card is different suit than lead card
                    shown_out_suits[player_i].add(current_trick[0] // 8)

            # sanity checks after trick completed
            assert len(current_trick) == 4

            for i, card_player in enumerate(card_players):
                assert np.min(card_player.hand52) == 0
                assert np.min(card_player.public52) == 0
                assert np.sum(card_player.hand52) == 13 - trick_i - 1
                assert np.sum(card_player.public52) == 13 - trick_i - 1

            tricks.append(current_trick)
            tricks52.append(current_trick52)

            if self.models.pimc_use_declaring or self.models.pimc_use_defending:
                for card_player in card_players:
                    if isinstance(card_player, bots.CardPlayer) and card_player.pimc:
                        card_player.pimc.reset_trick()

            # initializing for the next trick
            # initialize hands
            for i, card32 in enumerate(current_trick):
                card_players[(leader_i + i) % 4].x_play[:, trick_i + 1, 0:32] = card_players[(leader_i + i) % 4].x_play[:, trick_i, 0:32]
                card_players[(leader_i + i) % 4].x_play[:, trick_i + 1, 0 + card32] -= 1

            # initialize public hands
            for i in (0, 2, 3):
                card_players[i].x_play[:, trick_i + 1, 32:64] = card_players[1].x_play[:, trick_i + 1, 0:32]
            card_players[1].x_play[:, trick_i + 1, 32:64] = card_players[3].x_play[:, trick_i + 1, 0:32]

            for card_player in card_players:
                # initialize last trick
                if self.verbose:
                    print("Initialize last trick")
                for i, card32 in enumerate(current_trick):
                    card_player.x_play[:, trick_i + 1, 64 + i * 32 + card32] = 1
                    
                # initialize last trick leader
                card_player.x_play[:, trick_i + 1, 288 + leader_i] = 1

                # initialize level
                card_player.x_play[:, trick_i + 1, 292] = level

                # initialize strain
                card_player.x_play[:, trick_i + 1, 293 + strain_i] = 1

            # sanity checks for next trick
            for i, card_player in enumerate(card_players):
                # TODO: there are inconsistencies in the x_play states 
                # if the opening lead is the agent
                try:
                    assert np.min(card_player.x_play[:, trick_i + 1, 0:32]) == 0
                    assert np.min(card_player.x_play[:, trick_i + 1, 32:64]) == 0
                    assert np.sum(card_player.x_play[:, trick_i + 1, 0:32], axis=1) == 13 - trick_i - 1
                    assert np.sum(card_player.x_play[:, trick_i + 1, 32:64], axis=1) == 13 - trick_i - 1
                except AssertionError as e:
                    print(f"Assertion error for player {i} in trick {trick_i}: {e}")

            trick_winner = (leader_i + get_trick_winner_i(current_trick52, (strain_i - 1) % 5)) % 4
            trick_won_by.append(trick_winner)

            if trick_winner % 2 == 0:
                card_players[0].n_tricks_taken += 1
                card_players[2].n_tricks_taken += 1
                if self.models.pimc_use_defending:
                    if isinstance(card_players[0], bots.CardPlayer) and card_players[0].pimc:
                        card_players[0].pimc.update_trick_needed()
                    if isinstance(card_players[2], bots.CardPlayer) and card_players[2].pimc:
                        card_players[2].pimc.update_trick_needed()
            else:
                card_players[1].n_tricks_taken += 1
                card_players[3].n_tricks_taken += 1
                if self.models.pimc_use_declaring:
                    if isinstance(card_players[3], bots.CardPlayer) and card_players[3].pimc :
                        card_players[3].pimc.update_trick_needed()

            if self.verbose:
                print('trick52 {} cards={}. won by {}'.format(trick_i+1, list(map(decode_card, current_trick52)), trick_winner))

            # update cards shown
            for i, card32 in enumerate(current_trick):
                player_cards_played[(leader_i + i) % 4].append(card32)
            
            leader_i = trick_winner
            current_trick = []
            current_trick52 = []

            if np.any(np.array(self.human)):
                key = await self.confirmer.confirm()
                if key == 'q':
                    print(self.deal_str)
                    return
            else:
                await self.confirmer.confirm()

        # play last trick
        print("trick 13")
        for player_i in map(lambda x: x % 4, range(leader_i, leader_i + 4)):
            
            if not isinstance(card_players[player_i], bots.CardPlayer):
                card52 = await card_players[player_i].get_card_input()
                who = "Human"
            else:
                # dump the remaining card for the last trick
                card52 = np.nonzero(card_players[player_i].hand52)[0][0]
                who = "NN"

            card32 = card52to32(card52)

            card_resp = CardResp(card=Card.from_code(card52), candidates=[], samples=[], shape=-1, hcp=-1, quality=None, who=who)

            await self.channel.send(json.dumps({
                'message': 'card_played',
                'seat': ((decl_i + 1) % 4 + player_i) % 4,
                'card': card_resp.card.symbol()
            }))

            self.card_responses.append(card_resp)
            
            current_trick.append(card32)
            current_trick52.append(card52)
            if agent_no is not None:
                card_players[agent_no].set_real_card_played(card52, player_i)
                card_players[agent_no].set_card_played(trick_i=trick_i, leader_i=leader_i, i=player_i, card=card32)

        await self.confirmer.confirm()

        tricks.append(current_trick)
        tricks52.append(current_trick52)
        
        trick_winner = (leader_i + get_trick_winner_i(current_trick52, (strain_i - 1) % 5)) % 4
        if trick_winner % 2 == 0:
            card_players[0].n_tricks_taken += 1
            card_players[2].n_tricks_taken += 1
        else:
            card_players[1].n_tricks_taken += 1
            card_players[3].n_tricks_taken += 1


        trick_won_by.append(trick_winner)
        if self.verbose:
            print('trick52 {} cards={}. won by {}'.format(trick_i+1, list(map(decode_card, current_trick52)), trick_winner))

        # Decode each element of tricks52
        decoded_tricks52 = [[decode_card(item) for item in inner] for inner in tricks52]
        pprint.pprint(list(zip(decoded_tricks52, trick_won_by)))

        self.trick_winners = trick_won_by

        # Print contract and result
        if agent_no is not None:
            card_players[agent_no].print_deque()
        print("Contract: ",self.contract, card_players[3].n_tricks_taken, "tricks, Declarer: ", "NESW"[decl_i])
        if agent_no is not None:
            evaluator = AgentEvaluator(self.log_file_name, self.board_number, self.deal_str, 
                                       card_players[agent_no], trick_won_by)
            if self.log:
                evaluator.log_result()

        # TODO: log the result a file
    
    # Get the initial bided suit of each of the players
    def get_initial_bided_suit(self, auction):
        bided_suit = [None, None, None, None]
        for idx, bid in enumerate(auction):
            if bided_suit[idx % 4] is not None:
                continue
            if len(bid) >=2 and bid[1] in "CDHS":
                bided_suit[idx % 4] = CardSuit.from_str(bid[1])
        return bided_suit

    async def opening_lead(self, auction):

        contract = bidding.get_contract(auction)
        decl_i = bidding.get_decl_i(contract)
        bided_suit = self.get_initial_bided_suit(auction)

        hands_str = self.deal_str.split()


        await asyncio.sleep(0.01)

        # Install the agent to open the lead
        if agent.conf.INSTALL_AGENT and (decl_i + 1) % 4 == 2:
            dummy_hand = hands_str[(decl_i + 2) % 4]
            self.agent.set_auction(bided_suit)
            card_resp = await self.agent.opening_lead(self.contract, dummy_hand)
        # overwrite the default behavior of ben, agent will take care of the game 
        # if there is any.
        elif not agent.conf.INSTALL_AGENT and self.human[(decl_i + 1) % 4]:
            card_resp = await self.factory.create_human_leader().async_lead()
        else:
            bot_lead = AsyncBotLead(
                [self.vuln_ns, self.vuln_ew], 
                hands_str[(decl_i + 1) % 4], 
                self.models,
                self.sampler,
                (decl_i + 1) % 4,
                self.dealer_i,
                self.verbose
            )
            card_resp = await bot_lead.async_opening_lead(auction)

        await asyncio.sleep(0.01)

        return card_resp

    async def bidding(self):
        hands_str = self.deal_str.split()
        
        vuln = [self.vuln_ns, self.vuln_ew]

        players = []
        hint_bots = [None, None, None, None]
        # Use bots to perform for auction
        all_bots = [False] * 4

        for i, level in enumerate(all_bots):
            if self.models.use_bba:
                from bba.BBA import BBABotBid
                players.append(BBABotBid(self.models.bba_ns, self.models.bba_ew, i, hands_str[i], vuln, self.dealer_i))
            elif level == 1:
                players.append(self.factory.create_human_bidder(vuln, hands_str[i], self.name))
                hint_bots[i] = AsyncBotBid(vuln, hands_str[i], self.models, self.sampler, i, self.dealer_i, self.verbose)
            else:
                bot = AsyncBotBid(vuln, hands_str[i], self.models, self.sampler, i, self.dealer_i, self.verbose)
                players.append(bot)

        auction = ['PAD_START'] * self.dealer_i

        player_i = self.dealer_i

        while not bidding.auction_over(auction):
            bid_resp = await players[player_i].async_bid(auction)
            if bid_resp.bid == "Hint":
                bid_resp = await hint_bots[player_i].async_bid(auction)
                await self.channel.send(json.dumps({
                    'message': 'hint',
                    'bids': bid_resp.to_dict()
                }))

                await asyncio.sleep(0.1)
            else :
                self.bid_responses.append(bid_resp)

                auction.append(bid_resp.bid)

                await self.channel.send(json.dumps({
                    'message': 'bid_made',
                    'auction': auction
                }))

                player_i = (player_i + 1) % 4
                # give time to client to redraw
                await asyncio.sleep(0.1)
            
        return auction

def random_deal_source():
    while True:
        yield random_deal_board()

async def simulate(random: bool, base_path: str, board_file: str, boardno: int, 
                   configfile: str, verbose: bool, seed: int, log: bool, auto: bool, 
                   playonly: bool, biddingonly: bool, board_dir: str = None):
    board_no = 0
    boards = []
    if random:
        log_file_name = "random"
    else:
        log_file_name = board_file.split("/")[-1].split(".")[0]
        if board_dir:
            sub_dir = board_dir.split("/")[-1]
            log_file_name = f"{sub_dir}/{log_file_name}"
        file_extension = os.path.splitext(board_file)[1].lower()  
        if file_extension == '.ben':
            with open(board_file, "r") as file:
                lines = file.readlines()  # 
                # Loop through the lines, grouping them into objects
                for i in range(0, len(lines), 2):
                    board = {
                        'deal': lines[i].strip(),      
                        'auction': lines[i+1].strip().replace('NT','N')
                    }
                    boards.append(board)            
            print(f"{len(boards)} boards loaded from {board_file}")
        if file_extension == '.pbn':
            with open(board_file, "r") as file:
                lines = file.readlines()
                boards = load(lines)
                print(f"{len(boards)} boards loaded from {board_file}")

    if boardno:
        print(f"Starting from {boardno}")
        board_no -= 1
        boardno = boardno

    np.set_printoptions(precision=1, suppress=True, linewidth=200)

    configuration = conf.load(configfile)
        
    try:
        if (configuration["models"]['tf_version'] == "2"):
            print("Loading version 2")
            from nn.models_tf2 import Models
        else: 
            # Default to version 1. of Tensorflow
            from nn.models import Models
    except KeyError:
            # Default to version 1. of Tensorflow
            from nn.models import Models

    models = Models.from_conf(configuration, base_path.replace(os.path.sep + "src",""))

    driver = Driver(models, human.ConsoleFactory(), Sample.from_conf(configuration, verbose), 
                    seed, verbose, log, log_file_name)

    while True:
        if random: 
            print("Playing random deals or deals from the client")
            if boardno:
                np.random.seed(boardno)

            #Just take a random"
            rdeal = random_deal_board(boardno)
            # example of to use a fixed deal
            # rdeal = ('973.KT652.A42.65 8.QJ98.KQ8765.K3 AKQ4.A74.T3.QJT2 JT652.3.J9.A9874', 'N N-S')

            print(f"Playing Board: {rdeal}")
            driver.set_deal(None, *rdeal, False, bidding_only=biddingonly)
        else:
            if board_no >= len(boards):
                break
            rdeal = boards[board_no]['deal']
            auction = boards[board_no]['auction']
            print("\n===============================")
            print(f"Board: {board_no + 1} {rdeal}")
            print(f"Agent: {agent_type.__name__}\nfilename: {board_file}")
            print("===============================\n")
            contract = boards[board_no].get('contract', None)
            declarer = boards[board_no].get('declarer', None)
            if declarer is not None:
                declarer = bidding.get_decl_i(declarer)
                # There is no need to simulate the game since the agent (the dummy hand) is not playing
                if declarer == NORTH:
                    print(f"Skipping board {board_no} since declarer is North")
                    board_no += 1
                    continue
            driver.set_deal(board_no + 1, rdeal, auction, play_only=playonly, 
                            bidding_only=biddingonly, contract=contract, declarer_i= declarer)

        # Agent is playing the South Seat while BEN is handling the other 3 hands
        driver.human = [False, False, True, False]
        t_start = time.time()
        await driver.run()
        board_no += 1

        # Check if any agent is playing
        if not biddingonly:
            with shelve.open(f"{base_path}/gamedb") as db:
                deal = driver.to_dict()
                print(f"Saving Board {board_no}: {driver.hands} in {base_path}/gamedb")
                print('{1} Board played in {0:0.1f} seconds.'.format(time.time() - t_start, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                db[uuid.uuid4().hex] = deal

        if not auto:
            user_input = input("\n Q to quit or any other key for next deal ")
            if user_input.lower() == "q":
                break

async def main():
    random = True
    #For some strange reason parameters parsed to the handler must be an array
    boardno = None

    # Get the path to the config file
    config_path = get_execution_path()
    
    base_path = os.getenv('BEN_HOME') or config_path

    parser = argparse.ArgumentParser(description="Game server")
    parser.add_argument("--auto", type=bool, default=False, help="Continue without user confirmation. If a file is provided it will stop at end of file")
    parser.add_argument("--boardno", default=0, type=int, help="Board number to start from")
    parser.add_argument("--config", default=f"{base_path}/config/default.conf", help="Filename for configuration")
    parser.add_argument("--playonly", type=bool, default=False, help="Just play, no bidding")
    parser.add_argument("--biddingonly", type=bool, default=False, help="Just bidding, no play")
    parser.add_argument("--verbose", type=bool, default=False, help="Output samples and other information during play")
    parser.add_argument("--seed", type=int, help="Seed for random")
    parser.add_argument("--agent", type=str, default=None, help="Agent to use")
    parser.add_argument("--log", type=bool, default=False, help="Log the game")
    parser.add_argument("--boardfile", default=None, help="Load the boards contained in a single file")
    parser.add_argument("--boarddir", type=str, default=None, help="Directory for boards")

    args = parser.parse_args()

    configfile = args.config
    verbose = args.verbose
    log = args.log
    auto = args.auto
    playonly = args.playonly
    biddingonly = args.biddingonly
    seed = args.seed
    global agent_type
    if args.agent == "oracle":
        agent_type = TheOracle
    elif args.agent == "baseline":
        agent_type = NaiveAgent
    elif args.agent == "human":
        agent_type = HumanAgent
    elif args.agent == "minimax":
        agent_type = MinimaxAgent
    elif args.agent == "minimaxbayes":
        agent_type = MinimaxBayesAgent
    elif args.agent == "minimaxopt":
        agent.type = MinimaxOptAgent
    elif args.agent is not None:
        raise ValueError(f"Unknown agent type {args.agent}")
    else:
        agent_type = agent.conf.AGENT_TYPE

    board_files = []
    boarddir = args.boarddir
    boardfile = args.boardfile
    random = False
    if boarddir is not None and boardfile is not None:
        raise ValueError("Cannot specify both board directory and board file")

    if boarddir is not None:
        print(f"Loading boards from {boarddir}")
        for filename in os.listdir(boarddir):
            board_files.append(os.path.join(boarddir, filename))
    elif boardfile is not None:
        board_files.append(boardfile)
    else:
        random = True

    if random:
        await simulate(random, base_path, None, boardno, configfile, verbose, 
                       seed, log, auto, playonly, biddingonly)
    else:
        for board_file in board_files:
            await simulate(random, base_path, board_file, boardno, configfile, 
                           verbose, seed, log, auto, playonly, biddingonly, board_dir=boarddir)

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
