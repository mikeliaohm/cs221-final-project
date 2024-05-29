"""
generic_agent.py
----------------
by Mike Liao

Create a generic agent class that defines a common set of interfaces.
"""

from collections import deque
from typing import List, Dict, Set

import numpy as np

from agent.pbn import PBN
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

    def __str__(self) -> str:
        return f"{self.level}{self.trump_suit} Declarer: {self.declarer}"
    
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Contract):
            return NotImplemented
        return self.level == value.level and self.trump_suit == value.trump_suit and self.declarer == value.declarer

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
    def __init__(self, hand_str: str, position: int, verbose: bool = False) -> None:
        self.__cardsets__: List[CardSet] = [set() for _ in range(4)]
        self.__cardsets__[position] = card_to_index(hand_str)
        self.__played__: CardPlayed = deque()
        self.__position__: PlayerPosition = PlayerPosition(position)
        self.x_play = None
        self.__contract__ = None
        self.n_tricks_taken: int = 0
        self.__verbose__ = verbose
        self._shown_out_suits: Dict[PlayerPosition, Set[CardSuit]] = {
            PlayerPosition.NORTH: set(), PlayerPosition.EAST: set(), 
            PlayerPosition.SOUTH: set(), PlayerPosition.WEST: set()}

    @property
    def __cards__(self) -> CardSet:
        return self.__cardsets__[self.__position__.value]
    
    @property
    def dummy_position(self) -> PlayerPosition:
        return PlayerPosition((self.__contract__.declarer.value + 2) % 4)

    @property
    def __dummy__(self) -> CardSet:
        return self.__cardsets__[self.dummy_position.value]

    def current_hand(self) -> str:
        """
        Return the agent's current hand as a string.
        """
        return cardset_to_hand(self.__cards__)

    def print_deque(self, tricks_result: List[PlayerPosition] = None) -> None:
        """
        Print the contents of the agent's played cards.
        """
        print_deque(self.__played__, tricks_result)

    def print_cards(self) -> None:
        """
        Print all four hands.
        """
        print(PBN.from_cardsets(self.__cardsets__, PlayerPosition.NORTH).pbn_str)

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
    def is_declarer(self) -> PlayerPosition:
        return self.control_dummy

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
        from agent.dummy_agent import DummyAgent
        if self.__contract__ is None:
            self.set_contract(contract, declarer)
        if isinstance(self, DummyAgent):
            self.__cardsets__[declarer] = card_to_index(public_hand_str)
        else:
            self.__cardsets__[self.dummy_position.value] = card_to_index(public_hand_str)
        level = int(contract[0])
        strain_i = bidding.get_strain_i(contract)
        self.x_play = np.zeros((1, 13, 298))
        BinaryInput(self.x_play[:,0,:]).set_player_hand(self.hand32)
        BinaryInput(self.x_play[:,0,:]).set_public_hand(parse_hand_f(32)(public_hand_str))
        self.x_play[:,0,292] = level
        self.x_play[:,0,293+strain_i] = 1

    # Invoked when the agent is to deal a hand for the initial trick.
    async def opening_lead(self, contract: str, dummy_hand_str: str) -> CardResp:
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
        deque_count = len(self.__played__)
        # Play the last trick
        if deque_count == 13 or (deque_count == 12 and len(self.__played__[-1]) == 4):
            assert len(self.__cards__) == 1
            card_idx = min(self.__cards__)
        else:
            card_idx = self.choose_card()
        return card_idx
    
    def set_real_card_played(self, opening_lead52: int, player_i: int) -> None:
        seat = ((self.__contract__.declarer.value + 1) % 4 + player_i) % 4
        position = PlayerPosition(seat)
        if len(self.__played__) > 0 and len(self.__played__[-1]) < 4:
            lead_suit = CardSuit.from_card_idx(self.__played__[-1][0][1])
            played_suit = CardSuit.from_card_idx(opening_lead52)
            if played_suit != lead_suit:
                self._shown_out_suits[position].add(lead_suit)

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
        # when in set_real_card_played()
        return
        try:
            self.__cardsets__[self.dummy_position.value].remove(card52)
        except KeyError:
            raise ValueError(f"Card {index_to_card(card52)} not in dummy.")
        
    def set_contract(self, contract: str, declarer: int) -> None:
        self.__contract__ = Contract.from_str(contract, PlayerPosition(declarer))

    def set_auction(self, bided_suit: List[CardSuit]) -> None:
        self.__bided_suit__ = bided_suit

    """
    =================================================================================
    The section below defines methods used collect the unseen cards.
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
        hidden_players = self.get_hidden_players()
        unseen_counts = {player: 13 for player in hidden_players}
        
        for trick in self.__played__:
            for player, card_idx in trick:
                if player in hidden_players:
                    unseen_counts[player] -= 1
                unseen_cards.remove(card_idx)

        return unseen_cards, unseen_counts