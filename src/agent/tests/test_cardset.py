import unittest

from agent.card_utils import card_to_index
from agent.card_stats import PlayerPosition

# N:QJ6.K652.J85.T98 873.J97.AT764.Q4 K5.T83.KQ9.A7652 AT942.AQ4.32.KJ3
class TestCardSet(unittest.TestCase):
    def setUp(self) -> None:
        self.deal_str = "QJ6.K652.J85.T98 873.J97.AT764.Q4 K5.T83.KQ9.A7652 AT942.AQ4.32.KJ3"
        self.deals = self.deal_str.split()
        self.assertEqual(len(self.deals), 4)

    def test_north_cardset(self):
        hand_str = self.deals[PlayerPosition.NORTH.value]
        cardset = card_to_index(hand_str)
        expected_result = {32, 2, 3, 35, 8, 43, 44, 45, 14, 21, 22, 25, 29}
        self.assertEqual(len(cardset), 13)
        self.assertEqual(cardset, expected_result)

    def test_east_cardset(self):
        hand_str = self.deals[PlayerPosition.EAST.value]
        cardset = card_to_index(hand_str)
        expected_result = {33, 34, 36, 6, 7, 41, 11, 16, 49, 18, 20, 26, 30}
        self.assertEqual(len(cardset), 13)
        self.assertEqual(cardset, expected_result)

    def test_south_cardset(self):
        hand_str = self.deals[PlayerPosition.SOUTH.value]
        cardset = card_to_index(hand_str)
        expected_result = {1, 39, 9, 46, 47, 48, 17, 19, 51, 24, 27, 28, 31}
        self.assertEqual(len(cardset), 13)
        self.assertEqual(cardset, expected_result)

    def test_west_cardset(self):
        hand_str = self.deals[PlayerPosition.WEST.value]
        cardset = card_to_index(hand_str)
        expected_result = {0, 4, 5, 37, 38, 40, 10, 42, 12, 13, 15, 50, 23}
        self.assertEqual(len(cardset), 13)
        self.assertEqual(cardset, expected_result)

    def test_full_cardset(self):
        full_cardset = set()
        for deal in self.deals:
            cardset = card_to_index(deal)
            full_cardset.update(cardset)
        self.assertEqual(full_cardset, set(range(52)))

if __name__ == '__main__':
    unittest.main()