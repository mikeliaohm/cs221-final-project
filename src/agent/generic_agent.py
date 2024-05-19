"""
generic_agent.py
----------------
by Mike Liao

Create a generic agent class that defines a common set of interfaces.
"""

from collections import deque
from typing import List, Dict, Set

import numpy as np

from objects import CardResp
from bidding import binary, bidding
from binary import BinaryInput, parse_hand_f
from .card_utils import (CardSet, card_to_index, cardset_to_hand, 
                        CARD_INDEX_MAP, index_to_card, complementary_cardset)
from .card_stats import PlayerPosition, CardSuit, CardTrick, CardPlayed, CardDist, append_trick, print_deque

class Contract:
    def __init__(self, level: int, trump_suit: CardSuit, declarer: PlayerPosition) -> None:
        self.level = level
        self.trump_suit = trump_suit
        self.declarer = declarer

    @staticmethod
    def validate_contract(contract: str) -> bool:
        if len(contract) < 2:
            return False
        if not contract[0].isdigit():
            return False
        if contract[1] not in "CDHSN":
            return False
        return True
    
    @staticmethod
    def from_str(contract: str, declarer: PlayerPosition) -> "Contract":
        if not Contract.validate_contract(contract):
            raise ValueError(f"Invalid contract {contract}")

        level = int(contract[0])
        last_char = contract[-1]
        contract_suit = None
        if last_char in "X":
            contract_suit = CardSuit.from_str(contract[1:-1])
        else:
            contract_suit = CardSuit.from_str(contract[1:])

        return Contract(level, contract_suit, declarer)

class GenericAgent:
    def __init__(self, hand_str: str, position: int) -> None:
        self.__cards__: CardSet = card_to_index(hand_str)
        self.__played__: CardPlayed = deque()
        self.__position__: PlayerPosition = PlayerPosition(position)
        self.__dummy__ : CardSet = None
        self.x_play = None
        self.__contract__ = None
        self.n_tricks_taken: int = 0

    def current_hand(self) -> str:
        """
        Return the agent's current hand as a string.
        """
        return cardset_to_hand(self.__cards__)

    def print_deque(self) -> None:
        """
        Print the contents of the agent's played cards.
        """
        print_deque(self.__played__)

    def validate_card(self, card_str: str, current_trick52: List[int] = None) -> bool:
        """
        Validate whether a card is in the agent's hand.
        """
        if card_str not in CARD_INDEX_MAP:
            return False
        return CARD_INDEX_MAP[card_str] in self.__cards__
    
    def validate_follow_suit(self, card_idx: int, current_trick52: List[int]) -> bool:
        """
        Validate whether a card follows the suit of the current trick.
        """
        if current_trick52 is None or len(current_trick52) == 0:
            return True
        suit = current_trick52[0] // 13
        return card_idx // 13 == suit or not any(card // 13 == suit for card in self.__cards__)
    
    def choose_card(self, current_trick52: List[int] = None) -> int:
        raise NotImplementedError
    
    def play_card(self, card_idx: int) -> None:
        """
        Remove a card from the agent's hand. This function can 
        throw an error if the card is not in the agent's hand.
        """
        try:
            self.__cards__.remove(card_idx)
        except KeyError:
            raise ValueError(f"Card {index_to_card(card_idx)} not in hand.")
        append_trick(self.__played__, self.__position__, card_idx)

    def play_dummy_card(self, card_idx: int) -> None:
        """
        Remove a card from the dummy's hand. This function can 
        throw an error if the card is not in the agent's hand.
        """
        try:
            self.__dummy__.remove(card_idx)
        except KeyError:
            raise ValueError(f"Card {index_to_card(card_idx)} not in dummy.")

    @staticmethod
    def convert_cardset(num_cards: int, cardset: CardSet) -> np.ndarray[any, np.dtype[np.float64]]:
        hand_str = cardset_to_hand(cardset)
        return binary.parse_hand_f(num_cards)(hand_str).reshape(num_cards)

    @property
    def hand32(self) -> np.ndarray[any, np.dtype[np.float64]]:
        return self.convert_cardset(32, self.__cards__)
        # hand_str = cardset_to_hand(self.__cards__)
        # return binary.parse_hand_f(32)(hand_str).reshape(32)

    @property
    def hand52(self) -> np.ndarray[any, np.dtype[np.float64]]:
        return self.convert_cardset(52, self.__cards__)
        # hand_str = cardset_to_hand(self.__cards__)
        # return binary.parse_hand_f(52)(hand_str).reshape(52)

    @property
    def public52(self) -> np.ndarray[any, np.dtype[np.float64]]:
        dummy_str = cardset_to_hand(self.__dummy__)
        return binary.parse_hand_f(52)(dummy_str).reshape(52)

    @property
    def control_dummy(self) -> bool:
        return self.__position__ == self.__contract__.declarer

    @property
    def player_seqno(self) -> int:
        return (self.__position__.value - (self.__contract__.declarer.value + 1) + 4) %4
    
    def playing_dummy(self, leader_seqno: int, num_cards_in_trick: int) -> bool:
        if not self.control_dummy:
            return False
        # Check if the agent is playing after the dummy has played
        after_dummy = leader_seqno - self.player_seqno < 0
        if after_dummy:
            return num_cards_in_trick < 2
        else:
            return num_cards_in_trick >= 2

    def is_dummy_seqno(self, card_player_seqno: int) -> bool:
        if self.control_dummy:
            player_seqno = self.player_seqno
            return card_player_seqno == (player_seqno + 2) % 4
        return False

    def set_init_x_play(self, public_hand_str: str, contract: str, declarer: int) -> None:
        """
        This function is ported from HumanCardPlayer.init_x_play()
        """
        if self.__contract__ is None:
            self.set_contract(contract, declarer)
        self.__dummy__ : CardSet = card_to_index(public_hand_str)
        level = int(contract[0])
        strain_i = bidding.get_strain_i(contract)
        self.x_play = np.zeros((1, 13, 298))
        BinaryInput(self.x_play[:,0,:]).set_player_hand(self.hand32)
        BinaryInput(self.x_play[:,0,:]).set_public_hand(parse_hand_f(32)(public_hand_str))
        self.x_play[:,0,292] = level
        self.x_play[:,0,293+strain_i] = 1

    # Invoked when the agent is to deal a hand for the initial trick.
    async def opening_lead(self, contract: str) -> CardResp:
        raise NotImplementedError

    async def play_dummy_hand(self, current_trick52: List[int], leader_seqno: int) -> CardResp:
        """
        Play a card from the dummy's hand.
        """
        raise NotImplementedError

    async def async_play_card(self, trick_i: int, leader_i: int, 
        current_trick52: List[int], players_states: List[any], 
        bidding_scores: List[any], quality: any, 
        probability_of_occurence: List[float], shown_out_suits: List[Dict], 
        play_status: str) -> CardResp:
        """
        @param leader_i: the index card_players who led the trick
        """
        raise NotImplementedError
    
    async def get_card_input(self) -> int:
        raise NotImplementedError
    
    def set_real_card_played(self, opening_lead52: int, player_i: int) -> None:
        seat = ((self.__contract__.declarer.value + 1) % 4 + player_i) % 4
        position = PlayerPosition(seat)
        # No op since a card play is already recorded in play_card()
        if seat == self.__position__.value: 
            return
        append_trick(self.__played__, position, opening_lead52)
    
    def set_card_played(self, trick_i: int, leader_i: int, i: int, card: int) -> None:
        # TODO: don't know the difference from this and set_real_card_played()
        player_i = self.__position__.value - ((self.__contract__.declarer.value + 1) % 4)
        if player_i < 0:
            player_i += 4
        played_to_the_trick_already = (i - leader_i) % 4 > (player_i - leader_i) % 4

        if played_to_the_trick_already:
            return

        if player_i == i:
            return
        # TODO: check if this is needed? check the declarer's position
        # if player_i == i and (trick_i == 0 and self.__position__.value != (self.__declarer__.value + 1) % 4):
        #     return

        # update the public hand when the public hand played
        if player_i in (0, 2, 3) and i == 1 or player_i == 1 and i == 3:
            self.x_play[:, trick_i, 32 + card] -= 1

        # update the current trick
        offset = (player_i - i) % 4   # 1 = rho, 2 = partner, 3 = lho
        try:
            self.x_play[:, trick_i, 192 + (3 - offset) * 32 + card] = 1
        except:
            print(f"Player {player_i} / Card {index_to_card(card)}")

    
    def set_own_card_played52(self, card52: int) -> None:
        # TODO: when card is played, it's popped off already
        pass
    
    def set_public_card_played52(self, card52: int) -> None:
        """
        Card has been set in set_real_card_played() without the need for another function
        """
        # There is no need to remove the card since it has been done
        # when the agent played the dummy's hand
        if self.control_dummy:
            return
        try:
            self.__dummy__.remove(card52)
        except KeyError:
            raise ValueError(f"Card {index_to_card(card52)} not in dummy.")
        
    def set_contract(self, contract: str, declarer: int) -> None:
        self.__contract__ = Contract.from_str(contract, PlayerPosition(declarer))