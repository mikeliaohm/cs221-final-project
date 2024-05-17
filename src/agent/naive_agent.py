import enum
from typing import List, Dict

import numpy as np

from objects import Card, CardResp
from .generic_agent import GenericAgent
from .card_utils import CARD_INDEX_MAP, index_to_card

class NaiveAgent(GenericAgent):
    def choose_card(self, current_trick52: List[int] = None) -> int:
        if current_trick52 is None or len(current_trick52) == 0:
            card_idx = min(self.__cards__)
        else:
            suit = current_trick52[0] // 13
            if not any(card // 13 == suit for card in self.__cards__):
                card_idx = min(self.__cards__)
            else:
                card_idx = max(card for card in self.__cards__ if card // 13 == suit)
        self.play_card(card_idx)
        
        if not self.validate_follow_suit(card_idx, current_trick52):
            print("You have a card in the suit. Please play a card in the suit.")
            return self.choose_card(current_trick52)
        return card_idx
        
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