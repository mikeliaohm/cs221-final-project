"""
csp_assigner.py
---------------

Contains a solver that interfaces with CSP to assign the unseen cards
to the players who don't reveal their hands.
"""

from typing import Dict, List, Set, DefaultDict

from agent.card_stats import CardRank, CardSuit, PlayerPosition, Card
from agent.card_utils import CardSet, card_to_index, CARD_INDEX_MAP
from agent.csp.backtrack import BacktrackingSearch, BeamSearch, create_sum_variable
from agent.csp.util import CSP

class CSPAssigner:
    def __init__(self, unseen_cards: CardSet, players: List[PlayerPosition], 
                 high_card_prob: Dict[Card, float], suit_count_prob: Dict[CardSuit, DefaultDict[int, float]]) -> None:
        self._csp = CSP()
        self._unseen_cards: Set[Card] = {Card.from_code(idx) for idx in unseen_cards}

        """
        Associate variable domains {0, 1} with player positions where
        0 means Player 1 and 1 means Player 2. 
        e.g. in the case where South is the declarer, Player 1 (idx 0) is
        WEST and Player 2 (idx 1) is EAST.
        """
        self._players: Dict[int, PlayerPosition] = {}
        if PlayerPosition.NORTH in players:
            self._players[0] = PlayerPosition.NORTH
            players.remove(PlayerPosition.NORTH)
            self._players[1] = players[0]
        else:
            self._players[0] = PlayerPosition.WEST
            self._players[1] = PlayerPosition.EAST

        # Add the unseen cards as variables to the CSP, each card 
        # can be assigned to either player 1 or player 2.
        for card in self._unseen_cards:
            self._csp.add_variable(f"{card}", [0, 1])
        
        # Add the unary factors that specify weights (probability) with 
        # which the high cards (A, K, Q, J, T) are assigned to Player 1.
        for card, prob in high_card_prob.items():
            self._csp.add_unary_factor(f"{card}", lambda x: prob if x == 1 else 1 - prob)

        # self.process_aggregate_suit_variables(suit_count_prob)

        # Add the constraint that the sum of cards assigned to either
        # player must be 13.
        all_cards = [f"{card}" for card in self._unseen_cards]
        card_sum_var = create_sum_variable(self._csp, "all_cards", all_cards, len(all_cards) // 2)
        self._csp.add_unary_factor(card_sum_var, lambda x: x == len(all_cards) // 2)

    def process_aggregate_suit_variables(self, suit_count_prob: Dict[CardSuit, DefaultDict[int, float]]) -> None:
        """
        Add the unary factors that specify weights (probability) with 
        which the suit counts are assigned to Player 1. suit_count_prob
        is in the format of { SPADES: {0: 0.1, 1: 0.2, 2: 0.3, 3: 0.4}, ... }.
        """
        for suit, weights_map in suit_count_prob.items():
            # Aggregate the suit variables
            suit_cards = [f"{card}" for card in self._unseen_cards if card.suit == suit]
            suit_var = create_sum_variable(self._csp, f"{suit}", suit_cards, len(suit_cards))
            acc_prob = 0
            for _, prob in weights_map.items():
                acc_prob += prob
            remaining_prob = 1 - acc_prob
            remaining_count = len(suit_cards) - len(weights_map)
            self._csp.add_unary_factor(suit_var, lambda x: weights_map.get(x, remaining_prob / remaining_count))

if __name__ == "__main__":
    # South is the declarer
    # deal_str = "AJ4.T7.AT652.KJ2 K73.A985432.Q9.7 985..KJ84.AQT654 QT62.KQJ6.73.983"
    # deals = deal_str.split()
    # cardsets = [card_to_index(deal) for deal in deals]
    # unseen_cards = set(list(cardsets[1]) + list(cardsets[3]))
    # players = [PlayerPosition.WEST, PlayerPosition.EAST]
    # high_card_prob = {Card(CardSuit.SPADES, CardRank.KING): 0.6,
    #                   Card(CardSuit.SPADES, CardRank.QUEEN): 0.3,
    #                   Card(CardSuit.HEARTS, CardRank.ACE): 0.5,
    #                   Card(CardSuit.DIAMONDS, CardRank.QUEEN): 0.9,}
    # suit_count_prob = {CardSuit.SPADES: {0: 0.1, 1: 0.2, 2: 0.3, 3: 0.4},
    #                   CardSuit.HEARTS: {0: 0, 1: 0.05, 5: 0.3, 6: 0.2},
    #                   CardSuit.DIAMONDS: {0: 0.1}}
    # assigner = CSPAssigner(unseen_cards, players, high_card_prob, suit_count_prob)
    # solver = BeamSearch(1)
    # # This problem does not seem to be solvable, there are 78 variables to assign
    # solver.solve(assigner._csp, mcv=True, ac3=True)
    # for var in solver.optimalAssignment:
    #     if CARD_INDEX_MAP.get(var, -1) in unseen_cards:
    #         print(f"{var}: {solver.optimalAssignment[var]}")

    deal_str = "AJ4.T7.AT652.KJ2"
    cardset = card_to_index(deal_str)
    unseen_cards = cardset
    # The unseen cards are the cards in the WEST and EAST hands
    players = [PlayerPosition.WEST, PlayerPosition.EAST]
    high_card_prob = {Card(CardSuit.SPADES, CardRank.ACE): 0.6,
                      Card(CardSuit.SPADES, CardRank.JACK): 0.3,
                      Card(CardSuit.DIAMONDS, CardRank.ACE): 0.9,}
    suit_count_prob = {CardSuit.SPADES: {0: 0.1},
                      CardSuit.DIAMONDS: {0: 0.1, 2: 0.5}}
    assigner = CSPAssigner(unseen_cards, players, high_card_prob, suit_count_prob)
    solver = BacktrackingSearch()
    # This problem does not seem to be solvable, there are 78 variables to assign
    solver.solve(assigner._csp, mcv=True, ac3=True)

    for var in solver.optimalAssignment:
        if CARD_INDEX_MAP.get(var, -1) in unseen_cards:
            print(f"{var}: {solver.optimalAssignment[var]}")