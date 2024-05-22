from typing import Set

CardSet = Set[int]

# Define suit and rank orders based on the deck configuration
SUITS = 'SHDC'  # Spades, Hearts, Diamonds, Clubs
RANKS = 'AKQJT98765432'

# Create a mapping of each card to its index
CARD_INDEX_MAP = {f"{suit}{rank}": suit_idx * 13 + rank_idx
                  for suit_idx, suit in enumerate(SUITS)
                  for rank_idx, rank in enumerate(RANKS)}

def index_to_card(index: int) -> str:
    """Convert a card index into a string representation of the card.

    Args:
        index (int): An index representing a card in a sorted 52-card deck.

    Returns:
        str: A string representation of the card, e.g., "K" or "S"
    """
    if index < 0 or index >= 52:
        raise ValueError(f"Invalid index: {index}")

    # Determine the suit and rank based on the index
    rank = RANKS[index % 13]
    suit = SUITS[index // 13]

    # Return the card string
    return f"{suit}{rank}"

def card_to_index(card_str: str) -> CardSet:
    """Convert a hand of cards from string format to a set of indices.

    Args:
        card_str (str): A string representation of the hand, e.g., "KJT83.86.632.Q62"

    Returns:
        set: A set of indices representing the card positions in a sorted 52-card deck.
    """

    # Split the hand into SUITS
    hand_by_suits = card_str.split('.')

    # Set to hold all card indices
    indices = set()

    # Process each suit group
    for suit_idx, suit_group in enumerate(hand_by_suits):
        suit = SUITS[suit_idx]  # Determine the suit based on order
        for card in suit_group:
            # Build the card string and find its index
            card_name = f"{suit}{card}"
            if card_name in CARD_INDEX_MAP:
                indices.add(CARD_INDEX_MAP[card_name])

    # Return the set of indices
    return indices

def cardset_to_hand(indices_set: CardSet) -> str:
    """Convert a set of card indices into a string representation of the hand.

    Args:
        indices_set (set): A set of card indices in a 52-card deck.

    Returns:
        str: A string representation of the hand, e.g., "KJT83.86.632.Q62"
    """

    # Initialize hand structure
    hand_structure = {suit: [] for suit in SUITS}

    # Fill the hand structure with the corresponding card ranks
    for index in sorted(indices_set):  # Sort the set to maintain order
        suit = SUITS[index // 13]
        rank = RANKS[index % 13]
        hand_structure[suit].append(rank)

    # Create the hand string by joining each suit's cards
    hand_str = '.'.join(''.join(hand_structure[suit]) for suit in SUITS)

    return hand_str

def complementary_cardset(cardset: CardSet) -> CardSet:
    """Return the set of cards not in the parameter.

    Args:
        cardset (set): A set of card indices in a 52-card deck.

    Returns:
        set: A set of card indices representing the complementary cards.
    """
    all_cards = set(range(52))
    complementary_cards = all_cards - cardset
    return complementary_cards

if __name__ == "__main__":
    # Example usage
    print("Card Utils, converting between card strings and indices")
    print("-----------------------------------------------------")
    hand_str = "AQ54.AQ752..Q984"
    print(f"Example 1: {hand_str}")
    indices = card_to_index(hand_str)
    print("Card Indices:", indices)

    convert_back = cardset_to_hand(indices)
    print("Converted Back:", convert_back)
    
    j = 1
    msg = ""
    for card, idx in CARD_INDEX_MAP.items():
        msg += f"{idx}: {card}\t"
        if j % 13 == 0:
            msg += "\n"
        j += 1
    print(msg)