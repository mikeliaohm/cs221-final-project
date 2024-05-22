from typing import List, Dict

from objects import CardResp
from .generic_agent import GenericAgent
from .dds_eval import DDSEvaluator
from .pbn import PBN
from .card_stats import Card, PlayerPosition
from .card_utils import CardSet, card_to_index, index_to_card

class TheOracle(GenericAgent):
    def __init__(self, deal_str: str, position: int, verbose: bool) -> None:
        # The Oracle gets to see all hands
        deals = deal_str.split()
        hand_str = deals[position]
        super().__init__(hand_str, position, verbose)
        self.__cardsets__: List[CardSet] = []
        for seat in range(4):
            self.__cardsets__.append(card_to_index(deals[seat]))

    def __str__(self) -> str:
        return "Oracle"

    def choose_card(self, lead_pos: PlayerPosition = None, current_trick52: List[int] = None, playing_dummy = False) -> int:
        pbn_str = PBN.from_cardsets(self.__cardsets__, PlayerPosition.NORTH)
        lead_pos = self.__position__ if lead_pos is None else lead_pos
        cards = [] if current_trick52 is None \
            else [Card.from_code(idx) for idx in current_trick52]
        scores = DDSEvaluator(self.__contract__.trump_suit, lead_pos, cards, pbn_str)
        card_idx = scores.get_best_card()
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
        card_idx = self.choose_card(PlayerPosition(seat), current_trick52, playing_dummy=True)
        if self.__verbose__:
            print(f"Play on dummy card: {Card.from_code(card_idx)}")
        return CardResp(card=Card.from_code(card_idx), candidates=[], samples=[], shape=-1, hcp=-1, quality=None, who=None)
    
    # Override the set_real_card_played() method to remove the played card from the other players' hands
    def set_real_card_played(self, opening_lead52: int, player_i: int) -> None:
        seat = ((self.__contract__.declarer.value + 1) % 4 + player_i) % 4
        self.__cardsets__[seat].remove(opening_lead52)
        super().set_real_card_played(opening_lead52, player_i)

    def print_all_hands(self) -> None:
        pbn = PBN.from_cardsets(self.__cardsets__, PlayerPosition.NORTH)
        print(pbn.pbn_str)