"""
random_assigner.py
-------------------

Assign the unseen cards to the players with hidden hands randomly.
"""

from typing import Dict, List
import random

from agent.card_stats import PlayerPosition
from agent.card_utils import CardSet, card_to_index

class RandomAssigner:
    @staticmethod
    def assign(unseen_cards: CardSet, unseen_counts: Dict[PlayerPosition, int], rand_seed: int = None) -> Dict[PlayerPosition, CardSet]:
        """
        Assign the unseen cards to the players with hidden hands randomly.
        """
        if rand_seed is not None:
            random.seed(rand_seed)
        unseen_cards = list(unseen_cards)
        random.shuffle(unseen_cards)
        player_hands = {player: set() for player in unseen_counts.keys()}
        for player, num_cards in unseen_counts.items():
            for i in range(num_cards):
                player_hands[player].add(unseen_cards.pop())
                
        return player_hands
    
    
if __name__ == "__main__":
    # South is the declarer
    RAND_SEED = 3
    random.seed(RAND_SEED)
    deal_str = "AJ4.T7.AT652.KJ2 K73.A985432.Q9.7 985..KJ84.AQT654 QT62.KQJ6.73.983"
    deals = deal_str.split()
    cardsets = [card_to_index(deal) for deal in deals]
    unseen_cards = set(list(cardsets[1]) + list(cardsets[3]))
    unseen_counts = {PlayerPosition.WEST: 13, PlayerPosition.EAST: 13}
    assigned_hands = RandomAssigner.assign(unseen_cards, unseen_counts)
    print(assigned_hands)