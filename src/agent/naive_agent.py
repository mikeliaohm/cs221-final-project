import enum
from typing import List, Dict, Tuple

import numpy as np

from agent.assigners.random_assigner import RandomAssigner
from objects import Card, CardResp
from agent.card_stats import CardSuit, PlayerPosition, PlayerTurn, highest_card, lowest_card, lowest_card_in_any_suit
from agent.generic_agent import GenericAgent
from agent.card_utils import CARD_INDEX_MAP, CardSet, index_to_card

class NaiveAgent(GenericAgent):
    def __str__(self) -> str:
        return "Baseline"

    def choose_card(self, lead_pos: PlayerPosition = None, current_trick52: List[int] = None, playing_dummy = False) -> int:
        self.assign_cards()
        if current_trick52 is None or len(current_trick52) == 0:
            card_idx = self.choose_lead(playing_dummy)
        else:
            card_idx = self.follow_suit(lead_pos, current_trick52, playing_dummy)
        
        seat = self.dummy_position if playing_dummy else self.__position__
        if card_idx < 0:
            card_idx = self.fallback(lead_pos, current_trick52)

        # Sanity check to make sure the card follows the suit
        elif not playing_dummy and not self.validate_follow_suit(card_idx, current_trick52):
            print("\nxxxx  error following the suit, card chosen: ", index_to_card(card_idx), "  xxxx\n")
            self.print_cards()
            self.print_debug(lead_pos, current_trick52)
            assert False

        # Sanity check to make sure the card chosen is in the hand
        elif not card_idx in self.__cardsets__[seat.value]:
            print("\nxxxx  error playing a card not in hand: ", index_to_card(card_idx), "  xxxx\n")
            self.print_cards()
            self.print_debug(lead_pos, current_trick52)
            assert False
        
        return card_idx

    # Choose a card from the hand when the playing strategy fails to select a card
    def fallback(self, lead_pos: PlayerPosition = None, current_trick52: List[int] = None, playing_dummy = False) -> int:
        self.assign_cards()
        cardset = self.__cards__ if not playing_dummy else self.__dummy__
        if current_trick52 is None or len(current_trick52) == 0:
            card_idx = min(cardset)
        else:
            suit = current_trick52[0] // 13
            if not any(card // 13 == suit for card in cardset):
                card_idx = min(cardset)
            else:
                card_idx = max(card for card in cardset if card // 13 == suit)
        return card_idx
        
    async def opening_lead(self, contract: str) -> CardResp:
        declarer = PlayerPosition((self.__position__.value + 4 - 1) % 4)
        self.set_contract(contract, declarer)
        card_idx = self.choose_card()
        return CardResp(card=Card.from_code(card_idx), candidates=[], samples=[], shape=-1, hcp=-1, quality=None, who=None)
    
    async def async_play_card(self, trick_i: int, leader_i: int, 
        current_trick52: List[int], players_states: List[any], 
        bidding_scores: List[any], quality: any, 
        probability_of_occurence: List[float], shown_out_suits: List[Dict], 
        play_status: str) -> CardResp:
        seat = ((self.__contract__.declarer.value + 1) % 4 + leader_i) % 4
        card_idx = self.choose_card(PlayerPosition(seat), current_trick52)
        return CardResp(card=Card.from_code(card_idx), candidates=[], samples=[], shape=-1, hcp=-1, quality=None, who=None)
    
    async def play_dummy_hand(self, current_trick52: List[int], leader_seqno: int) -> CardResp:
        seat = ((self.__contract__.declarer.value + 1) % 4 + leader_seqno) % 4
        card_idx = self.choose_card(PlayerPosition(seat), current_trick52, True)
        if self.__verbose__:
            print(f"Play on dummy card: {Card.from_code(card_idx)}")
        return CardResp(card=Card.from_code(card_idx), candidates=[], samples=[], shape=-1, hcp=-1, quality=None, who=None)
    
    def set_real_card_played(self, card_played: int, player_i: int) -> None:
        seat = ((self.__contract__.declarer.value + 1) % 4 + player_i) % 4
        # The NaiveAgent only knows its own hand
        known_hands = [self.__position__.value, self.dummy_position.value]
        if seat in known_hands:
            try:
                self.__cardsets__[seat].remove(card_played)
            except KeyError:
                print(f"Card played: {index_to_card(card_played)}")
                print(f"Player: {seat}")
                print(f"Known hands: {known_hands}")
                print(f"Cardsets: {self.print_cards()}")
                assert False
        super().set_real_card_played(card_played, player_i)
        
    """
    =================================================================================
    The section below defines methods used to deal with the unseen cards.
    =================================================================================
    """
    def get_hidden_players(self) -> List[PlayerPosition]:
        if self.is_declarer:
            hidden_players = [PlayerPosition.EAST, PlayerPosition.WEST]
        elif self.__contract__.declarer == PlayerPosition.WEST:
            hidden_players = [PlayerPosition.NORTH, PlayerPosition.WEST]
        elif self.__contract__.declarer == PlayerPosition.EAST:
            hidden_players = [PlayerPosition.NORTH, PlayerPosition.EAST]
        else:
            raise ValueError("Shouldn't have reached here since the agent is never playing when NORTH is the declarer.")
        
        return hidden_players
    
    def get_unseen_cards(self) -> CardSet:
        unseen_cards = set(range(52))
        for player in [self.__position__.value, self.dummy_position.value]:
            unseen_cards -= self.__cardsets__[player]
        num_complete_tricks = sum(1 for trick in self.__played__ if len(trick) == 4)
        hidden_players = self.get_hidden_players()
        unseen_counts = {player: 13 - num_complete_tricks for player in hidden_players}
        if len(self.__played__) == 0:
            return unseen_cards, unseen_counts
        
        for player, card_idx in self.__played__[-1]:
            if player in hidden_players:
                unseen_counts[player] -= 1
            unseen_cards.remove(card_idx)
        
        return unseen_cards, unseen_counts
    
    def assign_cards(self) -> None:
        unseen_cards, unseen_counts = self.get_unseen_cards()
        assigned_hands = RandomAssigner.assign(unseen_cards, unseen_counts)
        hidden_players = self.get_hidden_players()
        for player in hidden_players:
            self.__cardsets__[player.value] = assigned_hands[player]
            
    """
    =================================================================================
    The section below defines the rule based playing strategy for the NaiveAgent.
    =================================================================================
    """
    def prepare_candidates(self, suits: List[CardSuit], opp_cardsets: CardSet = None, 
                           team_cardsets: CardSet = None) -> Tuple[List[int], List[int]]:
        winning_candidates = list()
        defensive_candidates = list()
        if opp_cardsets is None:
            opp_cardsets = self.__cardsets__[PlayerPosition.EAST.value] | self.__cardsets__[PlayerPosition.WEST.value]
        if team_cardsets is None:
            team_cardsets = self.__cardsets__[PlayerPosition.NORTH.value] | self.__cardsets__[PlayerPosition.SOUTH.value]
        for suit in suits:
            opp_card = highest_card(opp_cardsets, suit)
            team_card = highest_card(team_cardsets, suit)
            
            # Attach a winning card, assuming the opponents have no trump cards
            if team_card >= 0 and team_card < opp_card:
                winning_candidates.append(team_card)
        
            if team_card > opp_card:
                team_low_card = lowest_card(team_cardsets, suit)
                defensive_candidates.append(team_low_card)
                
        trump_candidate = None
        opp_trump_card = highest_card(opp_cardsets, self.__contract__.trump_suit)
        team_trump_card = highest_card(team_cardsets, self.__contract__.trump_suit)
        if team_trump_card >= 0 and team_trump_card < opp_trump_card:
            trump_candidate = team_trump_card

        return winning_candidates, defensive_candidates, trump_candidate
    
    def pick_among_candidates(self, winning_candidates: List[int], defensive_candidates: List[int], 
                              trump_candidate: int, playing_dummy: bool, following_suit: CardSuit = None) -> int:
        
        if playing_dummy:
            partner_cards = self.__cardsets__[PlayerPosition.SOUTH.value]
            agent_cards = self.__cardsets__[PlayerPosition.NORTH.value]
        else:
            partner_cards = self.__cardsets__[PlayerPosition.NORTH.value]
            agent_cards = self.__cardsets__[PlayerPosition.SOUTH.value]
            
        if len(winning_candidates) > 0:
            for winning_card in winning_candidates:
                if winning_card not in partner_cards and winning_card in agent_cards:
                    return winning_card
        
                card_suit = CardSuit.from_card_idx(winning_card)
                low_card_in_same_suit = lowest_card(agent_cards, card_suit)
                if low_card_in_same_suit >= 0:
                    return low_card_in_same_suit
                else:
                    low_cards_in_other_suit = set() # excludes the trump suit since our partner has a winning card
                    for suit in CardSuit.all_suits():
                        if suit == self.__contract__.trump_suit:
                            continue
                        low_card = lowest_card(agent_cards, suit)
                        if low_card >= 0:
                            low_cards_in_other_suit.add(low_card)
                    return lowest_card_in_any_suit(low_cards_in_other_suit)
        else:
            for defensive_card in defensive_candidates:
                if defensive_card not in partner_cards and defensive_card in agent_cards:
                    return defensive_card
                if following_suit:
                    low_card_in_same_suit = lowest_card(agent_cards, following_suit)
                    if low_card_in_same_suit >= 0:
                        return low_card_in_same_suit
            
            if trump_candidate is not None and trump_candidate not in partner_cards:
                return trump_candidate
            
            return lowest_card_in_any_suit(agent_cards)
    
    def choose_lead(self, playing_dummy = False) -> int:
        """
        Choose the card that can mostly likely win the trick by giving 
        priority to the high cards in the suit. If winning is not possible,
        play defensively by leading a low card.
        """
        winning_candidates, defensive_candidates, trump_candidate = self.prepare_candidates(CardSuit.all_suits())
        # Decide whether the candidate cards are held by the partner or the agent
        
        return self.pick_among_candidates(winning_candidates, defensive_candidates, trump_candidate, playing_dummy)
    
    def follow_suit(self, lead_pos: PlayerPosition, current_trick: List[int], playing_dummy = False) -> int:
        player_turn = PlayerTurn(lead_pos)
        opp_cardsets = set()
        team_cardsets = set()
        current_suit = CardSuit.from_card_idx(current_trick[0])
        for idx in range(4):
            if idx < len(current_trick):
                if player_turn.position() in [PlayerPosition.NORTH, PlayerPosition.SOUTH]:
                    team_cardsets.add(current_trick[idx])
                else:
                    opp_cardsets.add(current_trick[idx])
            else:
                remaining_cards = self.__cardsets__[player_turn.position().value]
                playable_cards = set([card for card in remaining_cards if CardSuit.from_card_idx(card) == current_suit])
                if player_turn.position() in [PlayerPosition.NORTH, PlayerPosition.SOUTH]:
                    if len(playable_cards) == 0:
                        team_cardsets |= remaining_cards
                    else:
                        team_cardsets |= playable_cards
                else:
                    if len(playable_cards) == 0:
                        opp_cardsets |= remaining_cards
                    else:
                        opp_cardsets |= playable_cards
                    
            player_turn = player_turn.next()
            
        winning_candidates, defensive_candidates, trump_candidate = self.prepare_candidates([current_suit], opp_cardsets, team_cardsets)
        return self.pick_among_candidates(winning_candidates, defensive_candidates, trump_candidate, playing_dummy, current_suit)
    
    # This is used to validate the consistency of internal state
    def print_debug(self, lead_pos: PlayerPosition, current_trick: List[int] = None, playing_dummy = False):
        player_turn = PlayerTurn(lead_pos)
        opp_cardsets = set()
        team_cardsets = set()
        if current_trick is None or len(current_trick) == 0:
            winning_candidates, defensive_candidates, trump_candidate = self.prepare_candidates(CardSuit.all_suits())

        else:
            current_suit = CardSuit.from_card_idx(current_trick[0])

            for idx in range(4):
                if idx < len(current_trick):
                    if player_turn.position() in [PlayerPosition.NORTH, PlayerPosition.SOUTH]:
                        team_cardsets.add(current_trick[idx])
                    else:
                        opp_cardsets.add(current_trick[idx])
                else:
                    remaining_cards = self.__cardsets__[player_turn.position().value]
                    playable_cards = set(card for card in remaining_cards if CardSuit.from_card_idx(card) == current_suit)
                    if player_turn.position() in [PlayerPosition.NORTH, PlayerPosition.SOUTH]:
                        if len(playable_cards) == 0:
                            team_cardsets |= remaining_cards
                        else:
                            team_cardsets |= playable_cards
                    else:
                        if len(playable_cards) == 0:
                            opp_cardsets |= remaining_cards
                        else:
                            opp_cardsets |= playable_cards
                        
                player_turn = player_turn.next()
            
            winning_candidates, defensive_candidates, trump_candidate = self.prepare_candidates([current_suit], opp_cardsets, team_cardsets)
        print(f"Contract {self.__contract__}")
        print(f"Winning candidates: {winning_candidates}")
        print(f"Defensive candidates: {defensive_candidates}")
        print(f"Trump candidate: {trump_candidate}")

        card_idx = self.pick_among_candidates(winning_candidates, defensive_candidates, trump_candidate, playing_dummy, current_suit[0])
        print(f"Card Chosen to play: {index_to_card(card_idx)}")
