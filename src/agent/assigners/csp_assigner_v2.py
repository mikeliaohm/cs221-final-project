"""
csp_assigner_v2.py
-------------------

Contains a solver that interfaces with CSP to assign the unseen cards
to the players who don't reveal their hands.

This version of the CSPAssigner class redefines the variables so that
we lump the lower value cards of the same suits into a single variable.
This is done to reduce the number of variables in the CSP problem and 
make the problem solvable.
"""

import copy
import random
from typing import Dict, List, Set, DefaultDict, Tuple
import math

from agent.assigners.random_assigner import RandomAssigner
from agent.card_stats import CardRank, CardSuit, PlayerPosition, Card
from agent.card_utils import CardSet, card_to_index, CARD_INDEX_MAP
from agent.csp.backtrack import BacktrackingSearch, BeamSearch, create_sum_variable
from agent.csp.util import CSP

class CSPAssignerV2:
    def __init__(self, unseen_cards: CardSet, player_stats: Dict[PlayerPosition, Tuple[int, CardSuit]],
                 show_out_suits: Dict[PlayerPosition, Set[CardSuit]]) -> None:
        """
        @param unseen_cards: The set of unseen cards in hidden hands
        @param player_stats: Key: the player with a hidden hand, value is a tuple of the number of cards
                                  and the suit that the player bided for in the auction.
        """
        self._csp = CSP()
        self._unseen_cards: Set[Card] = {Card.from_code(idx) for idx in unseen_cards}
        self._player_stats = player_stats
        self._num_cards_in_suit, self._honor_cards_in_suit = self.compute_num_cards_in_suit()
        self._shown_out = show_out_suits

    def compute_num_cards_in_suit(self) -> None:
        num_cards_in_suit: Dict[CardSuit, int] = {}
        honor_cards_in_suit: Dict[CardSuit, int] = {}
        for card in self._unseen_cards:
            suit = card.suit
            if suit in num_cards_in_suit:
                num_cards_in_suit[suit] += 1
            else:
                num_cards_in_suit[suit] = 1

            if card.rank in [CardRank.ACE, CardRank.KING, CardRank.QUEEN, CardRank.JACK]:
                if suit in honor_cards_in_suit:
                    honor_cards_in_suit[suit] += 1
                else:
                    honor_cards_in_suit[suit] = 1
        
        return num_cards_in_suit, honor_cards_in_suit
    
    """
    ============================================================================
    There are three types of variables, C, H, and B, where C is the number of
    cards in a suit, H is the number of honor cards in a suit, and B is
    the number of cards and honor cards assigned to a player.

    The naming of the variables is as follows:
    N_D: type C variable, number of cards in the suit of Diamonds for NORTH.
    N_D_H: type H variable, number of honor cards in the suit of Diamonds for NORTH.
    N_D_B: type B variable, number of cards and honor cards in the suit of Diamonds for NORTH.
    ============================================================================
    """
    def add_constraints(self) -> None:
        """
        Add the constraints to the CSP problem.
        """
        self.add_prob_C()
        self.add_prob_H_given_C()
        self.add_evidence()
        self.add_shown_out()

    def add_prob_C(self) -> None:
        """
        Add factors of weights of assigning num_cards of suit to the Players.
        These are unary factors.
        """
        for player, (num_cards_to_assign, suit) in self._player_stats.items():
            if suit is None:
                continue
            max_num_cards = self._num_cards_in_suit[suit]
            self._csp.add_variable(f"{player}_{suit}", [i for i in range(max_num_cards + 1)])

            def prob_C(num_cards: int) -> float:
                total_num_cards = len(self._unseen_cards)
                denominator = math.comb(total_num_cards, num_cards_to_assign)
                numerator = math.comb(max_num_cards, num_cards) \
                    * math.comb(total_num_cards - max_num_cards, num_cards_to_assign - num_cards)
                return numerator / denominator

            self._csp.add_unary_factor(f"{player}_{suit}", prob_C)

    def add_prob_H_given_C(self) -> None:
        """
        Add factors of weights of assigning honor cards to the Players given num_cards of suit.
        These are binary factors.
        """
        for player, (num_cards_to_assign, suit) in self._player_stats.items():
            if suit is None:
                continue
            max_honor_cards = self._honor_cards_in_suit[suit]
            num_cards_in_suit = self._num_cards_in_suit[suit]
            self._csp.add_variable(f"{player}_{suit}_Hon", [i for i in range(max_honor_cards + 1)])

            def prob_H_given_C(num_honor: int, num_cards: int) -> float:
                if num_honor > num_cards:
                    return 0
                try:
                    numerator = math.comb(max_honor_cards, num_honor) \
                        * math.comb(num_cards_in_suit - max_honor_cards, num_cards - num_honor)
                    denominator = math.comb(num_cards_in_suit, num_cards)
                except ValueError:
                    return 0
                return numerator / denominator
            
            self._csp.add_binary_factor(f"{player}_{suit}_Hon", f"{player}_{suit}", prob_H_given_C)

    def add_evidence(self) -> None:
        """        
        Some magic numbers for the weights of the factors based on the 
        compiled results from dataset in agent/boards/bids
        The script used to parse the data in bids: assigners/parse_bid.py
        """
        HONOR_CARDS_COUNT = {
            0: 36,
            1: 114, 
            2: 80, 
            3: 44,
            4: 3
        }

        NUM_CARDS_COUNT = {
            1: 9,
            2: 21,
            3: 32,
            4: 55,
            5: 92, 
            6: 57,
            7: 11
        }

        for player, (_, suit) in self._player_stats.items():
            if suit is None:
                continue
            self._csp.add_variable(f"{player}_{suit}_BIDDING", [0, 1])
            self._csp.add_binary_factor(f"{player}_{suit}_BIDDING", 
                                        f"{player}_{suit}_Hon",
                                        lambda x, y: x * (HONOR_CARDS_COUNT.get(y, 0) + 1))
            self._csp.add_binary_factor(f"{player}_{suit}_BIDDING", 
                                        f"{player}_{suit}",
                                        lambda x, y: x * (NUM_CARDS_COUNT.get(y, 0) + 1))

    def add_shown_out(self) -> None:
        for player, suits in self._shown_out.items():
            for suit in suits:
                var_name = f"{player}_{suit}"
                if var_name not in self._csp.variables:
                    self._csp.add_variable(var_name, [0])
                self._csp.add_variable(f"{var_name}_SHOWN", [0])
                self._csp.add_binary_factor(f"{var_name}_SHOWN", var_name, lambda x, y: y == 0)

    def assign_cards(self, verbose: bool = False) -> Dict[PlayerPosition, int]:
        """
        Solve the CSP problem to get the max weights assignment of bided suits.
        Then, assign the unseen cards to the players based on the max weights
        of the bided suits. For the rest of the cards, assign them randomly.
        """
        solver = BacktrackingSearch()
        self.add_constraints()
        solver.solve(self._csp, mcv=True, ac3=True)

        unseen_cards = set([card.code() for card in self._unseen_cards])
        # Fallback to random assignment if no solution found
        if len(solver.optimalAssignment) == 0:
            player_stats = {player: num_cards for player, (num_cards, _) in self._player_stats.items()}
            return RandomAssigner.assign(unseen_cards, player_stats)
        
        previous_player_stats = copy.deepcopy(self._player_stats)

        plain_cards_suited = {}
        honor_cards_suited = {}
        for card in self._unseen_cards:
            suit = card.suit
            if suit not in plain_cards_suited:
                plain_cards_suited[suit] = []
                honor_cards_suited[suit] = []
            if card.rank in [CardRank.ACE, CardRank.KING, CardRank.QUEEN, CardRank.JACK]:
                honor_cards_suited[suit].append(card)
            else:
                plain_cards_suited[suit].append(card)
        
        if verbose:
            for var in solver.optimalAssignment:
                print(f"{var}: {solver.optimalAssignment[var]}")
        assignment = {player: [] for player in self._player_stats.keys()}
        players = list(self._player_stats.keys())
        for player, (num_cards_to_assign, suit) in self._player_stats.items():
            if suit is None:
                continue
            another_player = players[players.index(player) - 1]
            num_cards_assigned = solver.optimalAssignment[f"{player}_{suit}"]
            num_honor_assigned = solver.optimalAssignment[f"{player}_{suit}_Hon"]
            random.shuffle(plain_cards_suited[suit])
            random.shuffle(honor_cards_suited[suit])
            assignment[player] += honor_cards_suited[suit][:num_honor_assigned]
            assignment[player] += plain_cards_suited[suit][:num_cards_assigned - num_honor_assigned]
            assignment[another_player] += honor_cards_suited[suit][num_honor_assigned:]
            assignment[another_player] += plain_cards_suited[suit][num_cards_assigned - num_honor_assigned:]
        
        if verbose:
            for player, cards in assignment.items():
                print(f"{player}: {cards}")
        
        player_stat = {}
        for player in players:
            cardset = set([card.code() for card in assignment[player]])
            unseen_cards -= cardset
            assignment[player] = cardset
            len_assigned = len(cardset)
            player_stat[player] = previous_player_stats[player][0] - len_assigned
        
        random_assignments = RandomAssigner.assign(unseen_cards, player_stat)
        for player, cards in random_assignments.items():
            assignment[player] |= cards

        return assignment

if __name__ == "__main__":
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

    print("\nAssignment 1: EAST and NORTH\n")
    deal_str = "52.J76.KQJ874.T9 AK3.T9854.T.K832 Q976.Q.9632.QJ74 JT84.AK32.A5.A65"
    deals = deal_str.split()
    cardsets = [card_to_index(deal) for deal in deals]
    unseen_cards = set(list(cardsets[NORTH]) + list(cardsets[EAST]))
    player_stats = {PlayerPosition.EAST: (13, CardSuit.HEARTS),
                    PlayerPosition.NORTH: (13, CardSuit.DIAMONDS)}
    assigner = CSPAssignerV2(unseen_cards, player_stats)
    assignment = assigner.assign_cards(True)
    
    print("\nAssignment 2: SOUTH and WEST\n")
    unseen_cards = set(list(cardsets[SOUTH]) + list(cardsets[WEST]))
    player_stats = {PlayerPosition.SOUTH: (13, CardSuit.SPADES),
                    PlayerPosition.WEST: (13, None)}
    assigner = CSPAssignerV2(unseen_cards, player_stats)
    assignment = assigner.assign_cards(True)

    print("\nAssignment 3: EAST and NORTH (uneven)\n")
    deal_str = "52.J76.KQJ4.T AK3.T954.T.832 Q976.Q.632.QJ4 JT84.A32.A5.A5"
    deals = deal_str.split()
    cardsets = [card_to_index(deal) for deal in deals]
    unseen_cards = set(list(cardsets[NORTH]) + list(cardsets[EAST]))
    player_stats = {PlayerPosition.EAST: (10, CardSuit.HEARTS),
                    PlayerPosition.NORTH: (11, CardSuit.DIAMONDS)}
    assigner = CSPAssignerV2(unseen_cards, player_stats)
    assignment = assigner.assign_cards(True)
    assert len(assignment[PlayerPosition.NORTH]) == 11
    assert len(assignment[PlayerPosition.EAST]) == 10