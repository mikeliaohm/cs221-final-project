"""
test_dummy.py
-------------

Test the generic agent class where the agent plays the declarer 
and dummy hands. This mainly tests the consistency of the agent's
internal state related to the dummy cards.

The test cases are reproduced from AlsReg6-Final.pbn.
"""

import unittest

from agent.generic_agent import GenericAgent
from agent.card_stats import CardSuit, PlayerPosition
from agent.card_utils import card_to_index

"""

[Deal "N:AJ4.T7.AT652.KJ2 K73.A985432.Q9.7 985..KJ84.AQT654 QT62.KQJ6.73.983"]
[Declarer "S"]
[Contract "6C"]
[Result "12"]
[Score "NS 920"]
[Auction "N"]
1D      2H      3C      3H
X       Pass    5D      Pass
6C      Pass    Pass    Pass
"""
class TestDummyPlays(unittest.TestCase):
    def setUp(self) -> None:
        deal_str = "AJ4.T7.AT652.KJ2 K73.A985432.Q9.7 985..KJ84.AQT654 QT62.KQJ6.73.983"
        self.hands = deal_str.split()
        self.seat = PlayerPosition.SOUTH
        self.dummy_seat = PlayerPosition.NORTH
        self.agent = GenericAgent(self.hands[self.seat.value], self.seat.value)
        self.agent.set_init_x_play(self.hands[self.dummy_seat.value], "6C", self.seat.value)

    def test_cardset(self):
        agent_cardset = card_to_index(self.hands[self.seat.value])
        dummy_cardset = card_to_index(self.hands[self.dummy_seat.value])
        self.assertEqual(agent_cardset, self.agent.__cards__)
        self.assertEqual(dummy_cardset, self.agent.__dummy__)

    def test_the_agent_is_controlling_dummy(self):
        self.assertTrue(self.agent.control_dummy)

    def test_player_seqno(self):
        self.assertEqual(3, self.agent.player_seqno)

    # If current_trick contains more than two cards, we should be able
    # to determine whether the agent is playing the dummy hand when 
    # async_play_card is called

class TestPlayerSequence(unittest.TestCase):
    def test_opening_lead_sequence(self):
        """
        Test case where agent is the opening lead with EAST as declarer
        """
        deal_str = "643.QT432.532.T9 Q85.K5.AK97.AK54 KT7.J87.QT86.Q73 AJ92.A96.J4.J862"
        hands = deal_str.split()
        seat = PlayerPosition.SOUTH
        declarer = PlayerPosition.EAST
        dummy_seat = PlayerPosition.WEST
        agent = GenericAgent(hands[seat.value], seat.value)
        agent.set_init_x_play(hands[dummy_seat.value], "3NT", declarer.value)
        self.assertEqual(0, agent.player_seqno)
        self.assertEqual(CardSuit.NT, agent.__contract__.trump_suit)
        self.assertEqual(3, agent.__contract__.level)
        self.assertEqual(declarer, agent.__contract__.declarer)

    def test_declarer_seqno(self):
        """
        Test case where agent is the declarer (SOUTH)
        """
        deal_str = "AJ4.T7.AT652.KJ2 K73.A985432.Q9.7 985..KJ84.AQT654 QT62.KQJ6.73.983"
        hands = deal_str.split()
        seat = PlayerPosition.SOUTH
        declarer = PlayerPosition.SOUTH
        dummy_seat = PlayerPosition.NORTH
        agent = GenericAgent(hands[seat.value], seat.value)
        agent.set_init_x_play(hands[dummy_seat.value], "5C", declarer.value)
        self.assertEqual(3, agent.player_seqno)
        self.assertEqual(CardSuit.CLUBS, agent.__contract__.trump_suit)
        self.assertEqual(5, agent.__contract__.level)
        self.assertEqual(declarer, agent.__contract__.declarer)

    def test_righty_seqno(self):
        """
        Test case where agent is the right hand player of the declarer (WEST)
        """
        deal_str = "J9.AQ962.8752.K8 Q43.K85.KQT.QJT5 KT765.J4.J43.742 A82.T73.A96.A963"
        hands = deal_str.split()
        seat = PlayerPosition.SOUTH
        declarer = PlayerPosition.WEST
        dummy_seat = PlayerPosition.EAST
        agent = GenericAgent(hands[seat.value], seat.value)
        agent.set_init_x_play(hands[dummy_seat.value], "4H", declarer.value)
        self.assertEqual(2, agent.player_seqno)
        self.assertEqual(CardSuit.HEARTS, agent.__contract__.trump_suit)
        self.assertEqual(4, agent.__contract__.level)
        self.assertEqual(declarer, agent.__contract__.declarer)

    def test_dummy_seqno(self):
        """
        Test case where agent is the dummy hand with NORTH as declarer
        """
        deal_str = "AQJ86.92.K9.J853 T73.743.J53.AKT2 K952.T5.Q87642.9 4.AKQJ86.AT.Q764"
        hands = deal_str.split()
        seat = PlayerPosition.SOUTH
        declarer = PlayerPosition.NORTH
        dummy_seat = PlayerPosition.SOUTH
        agent = GenericAgent(hands[seat.value], seat.value)
        agent.set_init_x_play(hands[dummy_seat.value], "4SX", declarer.value)
        self.assertEqual(1, agent.player_seqno)
        self.assertEqual(CardSuit.SPADES, agent.__contract__.trump_suit)
        self.assertEqual(4, agent.__contract__.level)
        self.assertEqual(declarer, agent.__contract__.declarer)

if __name__ == "__main__":
    unittest.main()