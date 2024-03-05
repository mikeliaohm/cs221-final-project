import asyncio
import clr
import ctypes
import sys
import os
import math 
from objects import BidResp, CandidateBid, Card, CardResp, CandidateCard
import time
from binary import get_hcp
import scoring

from bidding import bidding
sys.path.append("..")

BEN_HOME = os.getenv('BEN_HOME') or '..'
BIN_FOLDER = os.path.join(BEN_HOME, 'bin')
if sys.platform == 'win32':
    BGADLL_LIB = 'BGADLL'
elif sys.platform == 'darwin':
    BGADLL_LIB = 'N/A'
else:
    BGADLL_LIB = 'N/A'

BGADLL_PATH = os.path.join(BIN_FOLDER, BGADLL_LIB)

from enum import Enum
from typing import List, Iterable

class BGADLL: 

    def __init__(self, wait, tophand, bottomhand, contract, player_i, is_decl_vuln, verbose):
        try:
           # Load the .NET assembly and import the types and classes from the assembly
            clr.AddReference(BGADLL_PATH)
            from BGADLL import PIMC, Hand, Details, Macros, Extensions

        except Exception as ex:
            # Provide a message to the user if the assembly is not found
            print("Error: Unable to load BGAIDLL.dll. Make sure the DLL is in the ./bin directory")
            print("Make sure the dll is not blocked by OS (Select properties and click unblock)")
            print('Error:', ex)
        
        self.wait = wait
        self.pimc = PIMC()
        self.pimc.Clear()
        self.full_deck = Extensions.Parse("AKQJT98765432.AKQJT98765432.AKQJT98765432.AKQJT98765432")
        self.tophand = Extensions.Parse(tophand)
        self.bottomhand = Extensions.Parse(bottomhand)
        self.opposHand = self.full_deck.Except(self.tophand.Union(self.bottomhand))
        self.playedHand = Hand()
        # Constraint are Clubs, Diamonds ending with hcp
        self.righty_constraints = Details(0,13,0,13,0,13,0,13,0,37)
        self.lefty_constraints = Details(0,13,0,13,0,13,0,13,0,37)
        self.suit = bidding.get_strain_i(contract)
        self.mintricks = int(contract[0]) + 6
        self.contract = contract
        self.tricks_taken = 0
        self.player_i = player_i
        self.score_by_tricks_taken = [scoring.score(self.contract, is_decl_vuln, n_tricks) for n_tricks in range(14)]
        self.verbose = verbose

    def calculate_hcp(self, rank):
        hcp_values = {
            0: 4,
            1: 3,
            2: 2,
            3: 1,
        }
        return hcp_values.get(rank, 0)

    def reset_trick(self):
        from BGADLL import Hand
        self.playedHand = Hand()

    def update_trick_needed(self):
        self.mintricks += -1
        self.tricks_taken += 1

    def update_constraints(self, min1,max1, min2, max2):
        self.lefty_constraints.MinHCP = max(min1,0)
        self.lefty_constraints.MaxHCP = min(max1,37)
        self.righty_constraints.MinHCP = max(min2,0)
        self.righty_constraints.MaxHCP = min(max2,37)
        print(self.lefty_constraints.ToString())
        print(self.righty_constraints.ToString())
        

    def set_card_played(self, card52, playedBy):
        real_card = Card.from_code(card52)
        card = real_card.symbol_reversed()
        from BGADLL import Card as PIMCCard
        self.playedHand.Add(PIMCCard(card))
        self.opposHand.Remove(PIMCCard(card))
        hcp = self.calculate_hcp(real_card.rank)
        suit = real_card.suit
        if self.player_i == 1:
            # We are dummy - our board is rotated
            if (playedBy == 1):
                self.tophand.Remove(PIMCCard(card))
            if (playedBy == 3):
                self.bottomhand.Remove(PIMCCard(card))
            if (playedBy == 2):
                # Lefty
                if suit == 0:
                    self.lefty_constraints.MinSpades = max(0,self.lefty_constraints.MinSpades - 1)    
                    self.lefty_constraints.MaxSpades = max(0,self.lefty_constraints.MaxSpades - 1)    
                if suit == 1:
                    self.lefty_constraints.MinHearts = max(0,self.lefty_constraints.MinHearts - 1)    
                    self.lefty_constraints.MaxHearts = max(0,self.lefty_constraints.MaxHearts - 1)    
                if suit == 2:
                    self.lefty_constraints.MinDiamonds = max(0,self.lefty_constraints.MinDiamonds - 1)    
                    self.lefty_constraints.MaxDiamonds = max(0,self.lefty_constraints.MaxDiamonds - 1)    
                if suit == 3:
                    self.lefty_constraints.MinClubs = max(0,self.lefty_constraints.MinClubs - 1)    
                    self.lefty_constraints.MaxClubs = max(0,self.lefty_constraints.MaxClubs - 1)    
                self.lefty_constraints.MinHCP = max(0,self.lefty_constraints.MinHCP - hcp)
                self.lefty_constraints.MaxHCP = max(0,self.lefty_constraints.MaxHCP - hcp)
            if (playedBy == 0):
                # Righty
                if suit == 0:
                    self.righty_constraints.MinSpades = max(0,self.righty_constraints.MinSpades - 1)    
                    self.righty_constraints.MaxSpades = max(0,self.righty_constraints.MaxSpades - 1)    
                if suit == 1:
                    self.righty_constraints.MinHearts = max(0,self.righty_constraints.MinHearts - 1)    
                    self.righty_constraints.MaxHearts = max(0,self.righty_constraints.MaxHearts - 1)    
                if suit == 2:
                    self.righty_constraints.MinDiamonds = max(0,self.righty_constraints.MinDiamonds - 1)    
                    self.righty_constraints.MaxDiamonds = max(0,self.righty_constraints.MaxDiamonds - 1)    
                if suit == 3:
                    self.righty_constraints.MinClubs = max(0,self.lefty_constraints.MinClubs - 1)    
                    self.righty_constraints.MaxClubs = max(0,self.lefty_constraints.MaxClubs - 1)    
                self.righty_constraints.MinHCP = max(0,self.righty_constraints.MinHCP - hcp)
                self.righty_constraints.MaxHCP = max(0,self.righty_constraints.MaxHCP - hcp)
        else:
            if (playedBy == 3):
                self.tophand.Remove(PIMCCard(card))
            if (playedBy == 1):
                self.bottomhand.Remove(PIMCCard(card))
            if (playedBy == 0):
                # Lefty
                if suit == 0:
                    self.lefty_constraints.MinSpades = max(0,self.lefty_constraints.MinSpades - 1)    
                    self.lefty_constraints.MaxSpades = max(0,self.lefty_constraints.MaxSpades - 1)    
                if suit == 1:
                    self.lefty_constraints.MinHearts = max(0,self.lefty_constraints.MinHearts - 1)    
                    self.lefty_constraints.MaxHearts = max(0,self.lefty_constraints.MaxHearts - 1)    
                if suit == 2:
                    self.lefty_constraints.MinDiamonds = max(0,self.lefty_constraints.MinDiamonds - 1)    
                    self.lefty_constraints.MaxDiamonds = max(0,self.lefty_constraints.MaxDiamonds - 1)    
                if suit == 3:
                    self.lefty_constraints.MinClubs = max(0,self.lefty_constraints.MinClubs - 1)    
                    self.lefty_constraints.MaxClubs = max(0,self.lefty_constraints.MaxClubs - 1)    
                self.lefty_constraints.MinHCP = max(0,self.lefty_constraints.MinHCP - hcp)
                self.lefty_constraints.MaxHCP = max(0,self.lefty_constraints.MaxHCP - hcp)
            if (playedBy == 2):
                # Righty
                if suit == 0:
                    self.righty_constraints.MinSpades = max(0,self.righty_constraints.MinSpades - 1)    
                    self.righty_constraints.MaxSpades = max(0,self.righty_constraints.MaxSpades - 1)    
                if suit == 1:
                    self.righty_constraints.MinHearts = max(0,self.righty_constraints.MinHearts - 1)    
                    self.righty_constraints.MaxHearts = max(0,self.righty_constraints.MaxHearts - 1)    
                if suit == 2:
                    self.righty_constraints.MinDiamonds = max(0,self.righty_constraints.MinDiamonds - 1)    
                    self.righty_constraints.MaxDiamonds = max(0,self.righty_constraints.MaxDiamonds - 1)    
                if suit == 3:
                    self.righty_constraints.MinClubs = max(0,self.lefty_constraints.MinClubs - 1)    
                    self.righty_constraints.MaxClubs = max(0,self.lefty_constraints.MaxClubs - 1)    
                self.righty_constraints.MinHCP = max(0,self.righty_constraints.MinHCP - hcp)
                self.righty_constraints.MaxHCP = max(0,self.righty_constraints.MaxHCP - hcp)

    async def check_threads_finished(self):
        start_time = time.time()
        while time.time() - start_time < self.wait:  
            await asyncio.sleep(0.05)
            if self.pimc.Evaluating == False:  
                print(f"Threads are finished after {time.time() - start_time:.2f}.")
                print(f"Playouts: {self.pimc.Playouts}")    
                return
        print(f"Playouts: {self.pimc.Playouts}")    
        print(f"Threads are still running after {self.wait} second.")

    def find_trump(self, value):
        from BGADLL import Macros
        if value == 4:
            return Macros.Trump.Club
        elif value == 3:
            return Macros.Trump.Diamond
        elif value == 2:
            return Macros.Trump.Heart
        elif value == 1:
            return Macros.Trump.Spade
        elif value == 0:
            return Macros.Trump.No
        else:
            # Handle the case where value doesn't match any of the specified cases
            # This could be raising an exception, returning a default value, or any other appropriate action
            # For now, let's return None
            return None

    # Define a Python function to find a bid
    async def nextplay(self, shown_out_suits):

        from BGADLL import PIMC, Hand, Details, Macros, Extensions, Card as PIMCCard

        self.pimc.Clear()
        if self.verbose:
            print("self.player_i", self.player_i)
            print(self.tophand.ToString(),self.bottomhand.ToString())
            print(self.opposHand.ToString(),self.playedHand.ToString())
            print(shown_out_suits)

        if self.player_i == 1:
            idx = 0
            idx1 = 2
        else: 
            idx = 2
            idx1 = 0
        if 0 in shown_out_suits[idx]:
            self.lefty_constraints.MaxSpades = 0
        if 1 in shown_out_suits[idx]:
            self.lefty_constraints.MaxHearts = 0
        if 2 in shown_out_suits[idx]:
            self.lefty_constraints.MaxDiamonds = 0
        if 3 in shown_out_suits[idx]:
            self.lefty_constraints.MaxClubs = 0
        if 0 in shown_out_suits[idx1]:
            self.righty_constraints.MaxSpades = 0
        if 1 in shown_out_suits[idx1]:
            self.righty_constraints.MaxHearts = 0
        if 2 in shown_out_suits[idx1]:
            self.righty_constraints.MaxDiamonds = 0
        if 3 in shown_out_suits[idx1]:
            self.righty_constraints.MaxClubs = 0

        if self.verbose:
            print(self.lefty_constraints.ToString())
            print(self.righty_constraints.ToString())

        # The deal is rotated so it is always North to play
        # Constraints are for righty first
        self.pimc.SetupEvaluation([self.tophand,self.bottomhand], self.opposHand, self.playedHand, [self.righty_constraints, self.lefty_constraints], Macros.Player.North)      
        
        trump = self.find_trump(self.suit)
        if self.verbose:
            print(trump)
        self.pimc.BeginEvaluate(trump)

        candidate_cards = []

        await self.check_threads_finished()
        self.pimc.EndEvaluate()
        legalMoves = self.pimc.LegalMoves
        candidate_cards = {}
        for card in legalMoves:
            # Calculate win probability
            output = self.pimc.Output[card]
            count = float(len(output))
            makable = sum(1 for t in output if t >= self.mintricks)
            probability = makable / count if count > 0 else 0
            if math.isnan(probability):
                probability = 0
            tricks = sum(t for t in output)/ count if count > 0 else 0

            # Second element is the score. We need to calculate it
            score = sum(self.score_by_tricks_taken[t + self.tricks_taken] for t in output) / count if count > 0 else 0

            candidate_cards[Card.from_symbol(str(card)[::-1])] = (tricks, score, probability)

        if self.verbose:
            for card, (tricks, score, probability) in candidate_cards.items():
                print(card, f"{tricks:.2f}", f"{score:.0f}", f"{probability:.2f}")


        self.pimc.EndEvaluate()
        return candidate_cards

