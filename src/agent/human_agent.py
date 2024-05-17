import enum
from typing import List, Dict

import numpy as np

from objects import Card, CardResp
from .generic_agent import GenericAgent
from .card_utils import CARD_INDEX_MAP, index_to_card

class Command(enum.Enum):
    SHOW_HAND = 'show'

class HumanAgent(GenericAgent):
    def choose_card(self, current_trick52: List[int] = None) -> int:
        while True:
            card = input("Enter the card to play: ")
            if card == Command.SHOW_HAND.value:
                print(f"{self.__position__} hand: {self.current_hand()}")
                continue
            # Process the card input and perform the desired actions
            if self.validate_card(card):
                card_idx = CARD_INDEX_MAP[card]
                if not self.validate_follow_suit(card_idx, current_trick52):
                    print("You have a card in the suit. Please play a card in the suit.")
                    continue
                self.play_card(card_idx)
                return card_idx
            else:
                print("Invalid card. Please enter a valid card.")
        
    async def opening_lead(self, auction: List[str]) -> CardResp:
        card_idx = self.choose_card()
        return CardResp(card=Card.from_code(card_idx), candidates=[], samples=[], shape=-1, hcp=-1, quality=None, who=None)
    
    async def async_play_card(self, trick_i: int, leader_i: int, 
        current_trick52: List[int], players_states: List[any], 
        bidding_scores: List[any], quality: any, 
        probability_of_occurence: List[float], shown_out_suits: List[Dict], 
        play_status: str) -> CardResp:
        card_idx = self.choose_card(current_trick52)
        return CardResp(card=Card.from_code(card_idx), candidates=[], samples=[], shape=-1, hcp=-1, quality=None, who=None)
    
    async def get_card_input(self) -> int:
        return self.choose_card()