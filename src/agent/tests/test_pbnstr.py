import unittest

from agent.card_stats import PlayerPosition
from agent.pbn import PBN

class TestCardSet(unittest.TestCase):
    def setUp(self) -> None:
        self.dealer = PlayerPosition.NORTH
        self.cardsets = [
            {32, 2, 3, 35, 8, 43, 44, 45, 14, 21, 22, 25, 29},
            {33, 34, 36, 6, 7, 41, 11, 16, 49, 18, 20, 26, 30},
            {1, 39, 9, 46, 47, 48, 17, 19, 51, 24, 27, 28, 31},
            {0, 4, 5, 37, 38, 40, 10, 42, 12, 13, 15, 50, 23}
        ]
        self.assertEqual(len(self.cardsets), 4)

    def test_pbn_str(self):
        pbn = PBN.from_cardsets(self.cardsets, self.dealer)
        self.assertEqual(pbn.pbn_str, "N:QJ6.K652.J85.T98 873.J97.AT764.Q4 K5.T83.KQ9.A7652 AT942.AQ4.32.KJ3")

if __name__ == '__main__':
    unittest.main()
