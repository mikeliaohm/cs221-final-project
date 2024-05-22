from typing import List, Dict, Union

from objects import Card, CardResp
from agent.generic_agent import GenericAgent
from agent.card_utils import CARD_INDEX_MAP, index_to_card
from agent.conf import AGENT_TYPES

class DummyAgent(GenericAgent):
    def __init__(self, hand_str: str, position: int, verbose: bool, agent: AGENT_TYPES) -> None:
        self.__agent__ = agent
        super().__init__(hand_str, position, verbose)
    
    async def async_play_card(self, trick_i: int, leader_i: int, 
        current_trick52: List[int], players_states: List[any], 
        bidding_scores: List[any], quality: any, 
        probability_of_occurence: List[float], shown_out_suits: List[Dict], 
        play_status: str) -> CardResp:
        card_resp = await self.__agent__.play_dummy_hand(current_trick52, leader_i)
        return card_resp
    
    def set_real_card_played(self, opening_lead52: int, player_i: int) -> None:
        seat = ((self.__contract__.declarer.value + 1) % 4 + player_i) % 4
        # Dummy only tracks its own hand
        if seat == self.__position__.value:
            self.__cardsets__[seat].remove(opening_lead52)
        super().set_real_card_played(opening_lead52, player_i)

    async def get_card_input(self) -> int:
        assert len(self.__cards__) == 1
        card_idx = min(self.__cards__)
        return card_idx