import unittest
import ctypes

from agent.dds_eval import solve_board_pbn
from agent.pbn import PBN
from agent.card_stats import PlayerPosition, CardSuit, CardRank, Card
from agent.python_dds.examples import functions

# This is required for loading the DDS shared library
from ddsolver import dds
dds.SetMaxThreads(0)

"""
Sample output from SolveBoard
SolveBoard, hand 1: solutions 3 OK, solutions 2 ERROR
-----------------------------------------------------                           
            QJ6                                                                 
            K652                                                                
            J85                                                                 
            T98                                                                
AT942                   873                                                     
AQ4                     J97                                                     
32                      AT764                                                   
KJ3                     Q4                                                     
            K5                                                                  
            T83                                                                 
            KQ9                                                                 
            A7652                                                              


solutions == 3

card   suit   rank   equals score 
     0 D      5             5     
     1 D      8             5     
     2 D      J             5     
     3 C      T      98     5     
     4 S      6             5     
     5 S      Q      J      5     
     6 H      2             4     
     7 H      6      5      4     
     8 H      K             4 
"""
class TestDDSEvalModule(unittest.TestCase):
    def setUp(self) -> None:
        self.dealer = PlayerPosition.NORTH
        self.cardsets = [
            {32, 2, 3, 35, 8, 43, 44, 45, 14, 21, 22, 25, 29},
            {33, 34, 36, 6, 7, 41, 11, 16, 49, 18, 20, 26, 30},
            {1, 39, 9, 46, 47, 48, 17, 19, 51, 24, 27, 28, 31},
            {0, 4, 5, 37, 38, 40, 10, 42, 12, 13, 15, 50, 23}
        ]
        self.trump_suit = CardSuit.SPADES
        self.assertEqual(len(self.cardsets), 4)

    def test_solve_board_pbn_stats(self):
        scores = solve_board_pbn(self.trump_suit, self.dealer, [], PBN.from_cardsets(self.cardsets, self.dealer))
        self.assertTrue(hasattr(scores, 'suit'))
        self.assertTrue(hasattr(scores, 'rank'))
        self.assertTrue(hasattr(scores, 'score'))
        self.assertEqual(len(scores.rank), len(scores.suit))
        self.assertEqual(len(scores.rank), len(scores.score))
        self.assertEqual(len(scores.rank), 13)


    def test_solve_board_pbn_score(self):
        scores = solve_board_pbn(self.trump_suit, self.dealer, [], PBN.from_cardsets(self.cardsets, self.dealer))
        solution = [
            (Card(CardSuit.DIAMONDS, CardRank.FIVE), 5),
            (Card(CardSuit.DIAMONDS, CardRank.EIGHT), 5),
            (Card(CardSuit.DIAMONDS, CardRank.JACK), 5),
            (Card(CardSuit.CLUBS, CardRank.TEN), 5),
            (Card(CardSuit.SPADES, CardRank.SIX), 5),
            (Card(CardSuit.SPADES, CardRank.QUEEN), 5),
            (Card(CardSuit.HEARTS, CardRank.TWO), 4),
            (Card(CardSuit.HEARTS, CardRank.SIX), 4),
            (Card(CardSuit.HEARTS, CardRank.KING), 4),
        ]

        equals = [
            (Card(CardSuit.CLUBS, CardRank.NINE), 5),
            (Card(CardSuit.CLUBS, CardRank.EIGHT), 5),
            (Card(CardSuit.SPADES, CardRank.JACK), 5),
            (Card(CardSuit.HEARTS, CardRank.FIVE), 4),
        ]

        for idx in range(scores.cards):
            self.assertEqual(scores.score[idx], solution[idx][1])
            self.assertTrue(Card(CardSuit(scores.suit[idx]), CardRank(scores.rank[idx])) == solution[idx][0])

        eq_idx = [3, 5, 7]
        eq_cards = []
        for idx in eq_idx:
            res = ctypes.create_string_buffer(15)
            functions.equals_to_string(scores.equals[idx], res)
            eq_ranks = res.value.decode("utf-8")
            for rank in eq_ranks:
                eq_card = Card(CardSuit(scores.suit[idx]), CardRank.from_str(rank))
                eq_cards.append((eq_card, scores.score[idx]))

        for idx, equal in enumerate(equals):
            self.assertTrue(eq_cards[idx] == equal)

"""
            QJ6                                                                 
            K65                                                                 
            J85                                                                 
            T98                                                                
AT942                   873                                                     
AQ4                     J97                                                     
32                      AT764                                                   
KJ3                     Q4                                                     
            K5                                                                  
            T83                                                                 
            KQ9                                                                 
            A7652                                                              


solutions == 3

card   suit   rank   equals score 
     0 H      7             9     
     1 H      9             9     
     2 H      J             9     
"""
class TestDDSEvalCurrentTrick(unittest.TestCase):
    def setUp(self) -> None:
        self.dealer = PlayerPosition.NORTH
        self.remains = [
            "QJ6.K65.J85.T98",
            "873.J97.AT764.Q4",
            "K5.T83.KQ9.A7652",
            "AT942.AQ4.32.KJ3"
        ]
        self.trump_suit = CardSuit.SPADES
        self.current_trick = [Card(CardSuit.HEARTS, CardRank.TWO)]
        self.assertEqual(len(self.remains), 4)

    def test_solve_board_pbn_current_trick(self):
        scores = solve_board_pbn(self.trump_suit, self.dealer, self.current_trick, PBN.from_hands(self.remains, self.dealer))
        solution = [
            (Card(CardSuit.HEARTS, CardRank.SEVEN), 9),
            (Card(CardSuit.HEARTS, CardRank.NINE), 9),
            (Card(CardSuit.HEARTS, CardRank.JACK), 9),
        ]
        for idx in range(scores.cards):
            self.assertEqual(scores.score[idx], solution[idx][1])
            self.assertTrue(Card(CardSuit(scores.suit[idx]), CardRank(scores.rank[idx])) == solution[idx][0])

if __name__ == '__main__':
    unittest.main()