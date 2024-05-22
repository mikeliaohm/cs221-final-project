import unittest

from agent.card_stats import Card, CardRank, CardSuit, PlayerPosition
from agent.card_utils import CARD_INDEX_MAP, card_to_index, index_to_card
from agent.naive_agent import NaiveAgent

NORTH = 0
EAST = 1
SOUTH = 2
WEST = 3

class TestLeadCard(unittest.TestCase):
    def prepare_agent(self, deal_str: str, contract: str, declarer: str) -> NaiveAgent:
        hands = deal_str.split()
        agent = NaiveAgent(hands[SOUTH], SOUTH)
        agent.set_contract(contract, declarer)
        # Assign all the cards to players
        agent.__cardsets__[NORTH] = card_to_index(hands[NORTH])
        agent.__cardsets__[EAST] = card_to_index(hands[EAST])
        agent.__cardsets__[WEST] = card_to_index(hands[WEST])
        return agent
    
    def test_lead_defensive_card(self) -> None:
        """
        Test case: from declarer.pbn
        N: 643.QT432.532.T9 
        E: Q85.K5.AK97.AK54 
        S: KT7.J87.QT86.Q73 
        W: AJ92.A96.J4.J862
        
        [Declarer "E"]
        [Contract "3NT"]
        """
        
        deal_str = "643.QT432.532.T9 Q85.K5.AK97.AK54 KT7.J87.QT86.Q73 AJ92.A96.J4.J862"
        agent = self.prepare_agent(deal_str, "3NT", EAST)
        winning_candidates, defensive_candidates, trump_candidate = agent.prepare_candidates(CardSuit.all_suits())
        winning_cards = [index_to_card(candidate) for candidate in winning_candidates]
        defensive_cards = [index_to_card(candidate) for candidate in defensive_candidates]
        self.assertEqual(winning_cards, [])
        self.assertEqual(defensive_cards, ["S3", "H2", "D2", "C3"])
        self.assertEqual(trump_candidate, None)
        card_idx = agent.choose_lead()
        self.assertEqual(Card.from_code(card_idx), Card(CardSuit.CLUBS, CardRank.THREE))

    def test_lead_low_card_for_partner(self) -> None:
        """
        Test case: from declarer.pbn

        N: AJ4.T7.AT652.KJ2 
        E: K73.A985432.Q9.7 
        S: 985..KJ84.AQT654 
        W: QT62.KQJ6.73.983

        [Declarer "E"]
        [Contract "5H"]
        """
        deal_str = "AJ4.T7.AT652.KJ2 K73.A985432.Q9.7 985..KJ84.AQT654 QT62.KQJ6.73.983"
        agent = self.prepare_agent(deal_str, "5H", EAST)
        winning_candidates, defensive_candidates, trump_candidate = agent.prepare_candidates(CardSuit.all_suits())
        winning_cards = [index_to_card(candidate) for candidate in winning_candidates]
        defensive_cards = [index_to_card(candidate) for candidate in defensive_candidates]
        self.assertEqual(winning_cards, ['SA', 'DA', 'CA'])
        self.assertEqual(defensive_cards, ['H7'])
        self.assertEqual(trump_candidate, None)
        
        card_idx = agent.choose_lead()
        self.assertEqual(Card.from_code(card_idx), Card(CardSuit.SPADES, CardRank.FIVE))
    
    def test_lead_high_card(self) -> None:
        """
        Test case: from declarer.pbn

        N: ...KJ2
        E: ...7 
        S: ...AQT654 
        W: ...983
        
        """
        deal_str = "...KJ2 ...7 ...AQT654 ...983"
        agent = self.prepare_agent(deal_str, "5H", EAST)
        winning_candidates, defensive_candidates, trump_candidate = agent.prepare_candidates(CardSuit.all_suits())
        winning_cards = [index_to_card(candidate) for candidate in winning_candidates]
        defensive_cards = [index_to_card(candidate) for candidate in defensive_candidates]
        self.assertEqual(winning_cards, ['CA'])
        self.assertEqual(defensive_cards, [])
        self.assertEqual(trump_candidate, None)
        
        card_idx = agent.choose_lead()
        self.assertEqual(Card.from_code(card_idx), Card(CardSuit.CLUBS, CardRank.ACE))
        
class TestFollowSuit(unittest.TestCase):
    def prepare_agent(self, deal_str: str, contract: str, declarer: str) -> NaiveAgent:
        hands = deal_str.split()
        agent = NaiveAgent(hands[SOUTH], SOUTH)
        agent.set_contract(contract, declarer)
        # Assign all the cards to players
        agent.__cardsets__[NORTH] = card_to_index(hands[NORTH])
        agent.__cardsets__[EAST] = card_to_index(hands[EAST])
        agent.__cardsets__[WEST] = card_to_index(hands[WEST])
        return agent
    
    def test_lead_defensive_card(self) -> None:
        """
        Test case: from declarer.pbn
        A2.4.86432.A9654 
        T95.K52.T95.KQJ3 
        KQ73.T63.AJ7.T82 
        J864.AQJ987.KQ.7
        
        [Declarer "W"]
        [Contract "4HX"]
        """
        
        deal_str = ".4.86432.A9654 T.K52.T95.QJ3 KQ.T63.AJ7.T82 J8.AQJ987.KQ.7"
        agent = self.prepare_agent(deal_str, "4HX", WEST)
        agent.assign_cards()
        card_idx = agent.choose_card(PlayerPosition.EAST, [CARD_INDEX_MAP["CK"]])
        self.assertEqual(Card.from_code(card_idx), Card.from_str('C2'))


if __name__ == "__main__":
    unittest.main()