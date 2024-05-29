import math
import unittest

from agent.card_utils import card_to_index
from agent.card_stats import PlayerPosition, Card, CardSuit, CardRank
from agent.assigners.csp_assigner_v2 import CSPAssignerV2

NORTH = 0
EAST = 1
SOUTH = 2
WEST = 3

class TestCSPAssignerV2ContractEast(unittest.TestCase):
    def setUp(self) -> None:
        """
        [Deal "N:52.J76.KQJ874.T9 AK3.T9854.T.K832 Q976.Q.9632.QJ74 JT84.AK32.A5.A65"]
        [Declarer "E"]
        [Contract "4H"]
        [Auction "N"]
        3D Pass 4D X
        Pass 4H Pass Pass
        Pass
        """
        deal_str = "52.J76.KQJ874.T9 AK3.T9854.T.K832 Q976.Q.9632.QJ74 JT84.AK32.A5.A65"
        deals = deal_str.split()
        cardsets = [card_to_index(deal) for deal in deals]
        unseen_cards = set(list(cardsets[NORTH]) + list(cardsets[EAST]))
        player_stats = {PlayerPosition.EAST: (13, CardSuit.HEARTS),
                        PlayerPosition.NORTH: (13, CardSuit.DIAMONDS)}
        self.assigner = CSPAssignerV2(unseen_cards, player_stats, {})

        return super().setUp()
    
    def test_num_cards_in_suit_factors(self):
        self.assigner.add_prob_C()
        num_cards_in_suit = {CardSuit.SPADES: 5, CardSuit.HEARTS: 8, 
                             CardSuit.DIAMONDS: 7, CardSuit.CLUBS: 6}
        self.assertEqual(self.assigner._num_cards_in_suit, num_cards_in_suit, {})
        
        # Check variables existed
        self.assigner._csp.variables.sort()
        self.assertEqual(self.assigner._csp.variables, ['E_H', 'N_D'])

        # Check variable domains
        domains = {'E_H': [i for i in range(9)], 'N_D': [i for i in range(8)]}
        self.assertEqual(self.assigner._csp.values['E_H'], [i for i in range(9)])
        self.assertEqual(self.assigner._csp.values['N_D'], [i for i in range(8)])
        
        # Check unary factors (Probabilities for num cards in a suit)
        for var, probs_map in self.assigner._csp.unaryFactors.items():
            accm_prob = 0
            for val, prob in probs_map.items():
                self.assertGreaterEqual(prob, 0)
                self.assertLessEqual(prob, 1)
                accm_prob += prob

            self.assertAlmostEqual(accm_prob, 1)

        self.assertEqual(self.assigner._csp.unaryFactors['E_H'][0], 
                         math.comb(26 - 8, 13) / math.comb(26, 13))
        self.assertEqual(self.assigner._csp.unaryFactors['E_H'][1], 
                         math.comb(8, 1) * math.comb(26 - 8, 13 - 1) / math.comb(26, 13))

    def test_honor_cards_in_suit_factors(self):
        self.assigner.add_prob_C()
        self.assigner.add_prob_H_given_C()
        num_honor_cards_in_suit = {CardSuit.SPADES: 2, CardSuit.HEARTS: 1, 
                                   CardSuit.DIAMONDS: 3, CardSuit.CLUBS: 1}
        for suit, num_cards in self.assigner._honor_cards_in_suit.items():
            self.assertEqual(num_honor_cards_in_suit[suit], num_cards)

        for var, dict in self.assigner._csp.binaryFactors.items():
            if 'Hon' in var:
                continue
            for var_prime, probs_map in dict.items():
                for val, prob in probs_map.items():
                    accm_prob = 0
                    for val_prime, prob_prime in prob.items():
                        self.assertGreaterEqual(prob_prime, 0)
                        self.assertLessEqual(prob_prime, 1)
                        accm_prob += prob_prime
                    self.assertAlmostEqual(accm_prob, 1)

    def test_inference(self):
        self.assigner.add_constraints()
        self.assertEqual(self.assigner._csp.binaryFactors['E_H_BIDDING']['E_H_Hon'][1][0], 36 + 1)
        self.assertEqual(self.assigner._csp.binaryFactors['E_H_BIDDING']['E_H'][1][1], 9 + 1)

if __name__ == '__main__':
    unittest.main()