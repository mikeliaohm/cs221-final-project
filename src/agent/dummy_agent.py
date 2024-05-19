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
        self.play_card(card_resp.card.code())
        return card_resp
    
    async def get_card_input(self) -> int:
        assert len(self.__cards__) == 1
        card_idx = self.__cards__.pop()
        return card_idx