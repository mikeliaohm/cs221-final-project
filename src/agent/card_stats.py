import enum
from typing import Dict, List, Tuple
from collections import deque

from agent.card_utils import CardSet, index_to_card, CARD_INDEX_MAP

class CardSuit(enum.Enum):
    SPADES = 0
    HEARTS = 1
    DIAMONDS = 2
    CLUBS = 3
    NT = 4  # No Trump (for auction)

    def __str__(self) -> str:
        if self == CardSuit.SPADES:
            return "S"
        elif self == CardSuit.HEARTS:
            return "H"
        elif self == CardSuit.DIAMONDS:
            return "D"
        elif self == CardSuit.CLUBS:
            return "C"
        elif self == CardSuit.NT:
            return "NT"
        
    @staticmethod
    def from_str(suit: str) -> "CardSuit":
        if suit == "S":
            return CardSuit.SPADES
        elif suit == "H":
            return CardSuit.HEARTS
        elif suit == "D":
            return CardSuit.DIAMONDS
        elif suit == "C":
            return CardSuit.CLUBS
        elif suit == "NT" or suit == "N":
            return CardSuit.NT
        else:
            raise ValueError(f"Invalid suit: {suit}")
    
    @staticmethod
    def from_card_idx(card_idx: int) -> "CardSuit":
        return CardSuit(card_idx // 13)
    
    @staticmethod
    def all_suits() -> List["CardSuit"]:
        return [CardSuit.SPADES, CardSuit.HEARTS, CardSuit.DIAMONDS, CardSuit.CLUBS]

class CardRank(enum.Enum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

    def __str__(self) -> str:
        if self == CardRank.TWO:
            return "2"
        elif self == CardRank.THREE:
            return "3"
        elif self == CardRank.FOUR:
            return "4"
        elif self == CardRank.FIVE:
            return "5"
        elif self == CardRank.SIX:
            return "6"
        elif self == CardRank.SEVEN:
            return "7"
        elif self == CardRank.EIGHT:
            return "8"
        elif self == CardRank.NINE:
            return "9"
        elif self == CardRank.TEN:
            return "T"
        elif self == CardRank.JACK:
            return "J"
        elif self == CardRank.QUEEN:
            return "Q"
        elif self == CardRank.KING:
            return "K"
        elif self == CardRank.ACE:
            return "A"
        else:
            raise ValueError(f"Invalid rank: {self}")
        
    @staticmethod
    def from_str(rank: str) -> "CardRank":
        if rank == "2":
            return CardRank.TWO
        elif rank == "3":
            return CardRank.THREE
        elif rank == "4":
            return CardRank.FOUR
        elif rank == "5":
            return CardRank.FIVE
        elif rank == "6":
            return CardRank.SIX
        elif rank == "7":
            return CardRank.SEVEN
        elif rank == "8":
            return CardRank.EIGHT
        elif rank == "9":
            return CardRank.NINE
        elif rank == "T":
            return CardRank.TEN
        elif rank == "J":
            return CardRank.JACK
        elif rank == "Q":
            return CardRank.QUEEN
        elif rank == "K":
            return CardRank.KING
        elif rank == "A":
            return CardRank.ACE
        else:
            raise ValueError(f"Invalid rank: {rank}")


class Card():
    def __init__(self, suit: CardSuit, rank: CardRank) -> None:
        self.suit = suit
        self.rank = rank

    def __str__(self) -> str:
        return f"{self.suit}{self.rank}"

    def __repr__(self) -> str:
        return self.__str__()

    @staticmethod
    def from_code(code: int) -> "Card":
        card_str = index_to_card(code)
        suit = CardSuit.from_str(card_str[0])
        rank = CardRank.from_str(card_str[1])
        return Card(suit, rank)
    
    @staticmethod
    def from_str(card_str: str) -> "Card":
        suit = CardSuit.from_str(card_str[0])
        rank = CardRank.from_str(card_str[1])
        return Card(suit, rank)

    def symbol(self):
        return self.__str__()

    def code(self) -> int:
        return CARD_INDEX_MAP[f"{self}"]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self.suit == other.suit and self.rank == other.rank

    def __hash__(self) -> int:
        return hash((self.suit, self.rank))

class PlayerPosition(enum.Enum):
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

    def __str__(self) -> str:
        if self == PlayerPosition.NORTH:
            return "N"
        elif self == PlayerPosition.EAST:
            return "E"
        elif self == PlayerPosition.SOUTH:
            return "S"
        else:
            return "W"

class PlayerTurn():
    def __init__(self, cur_player: PlayerPosition) -> None:
        self._cur_player = cur_player
        
    def __str__(self) -> str:
        return f"{self._cur_player}"
        
    def position(self) -> PlayerPosition:
        return self._cur_player
        
    def next(self) -> "PlayerTurn":
        return self.next_k(1)
    
    def prev(self) -> "PlayerTurn":
        return PlayerTurn(PlayerPosition((self._cur_player.value + 3) % 4))
    
    def next_k(self, k: int) -> "PlayerTurn":
        return PlayerTurn(PlayerPosition((self._cur_player.value + k) % 4))

# Store a card trick
CardTrick = List[Tuple[PlayerPosition, int]]
CardPlayed = deque[CardTrick]

# Store the probability distribution of each card
CardDist = Dict[int, Tuple[PlayerPosition, float]]

def append_trick(tricks: CardPlayed, position: PlayerPosition, card: int) -> None:
    """
    Append a card to the current trick.
    """
    # new trick
    if len(tricks) == 0 or len(tricks[-1]) == 4:
        tricks.append([(position, card)])
    # existing trick
    else:
        tricks[-1].append((position, card))

def print_deque(deque: CardPlayed, tricks_result: List[PlayerPosition]) -> None:
    """
    Print the contents of a deque.
    """
    for idx, plays in enumerate(deque):
        msg = ", ".join([f"\'{index_to_card(play[1])}\'" for play in plays])
        msg += "\t"
        msg += " ".join([f"{play[0]}" for play in plays])
        if tricks_result is not None:
            msg += f"\twon by {tricks_result[idx]}"
        print(f"Trick {idx + 1:02}\t: {msg}")

def highest_card(cardset: CardSet, suit: CardSuit) -> int:
    """
    Return the highest card in the given suit. If the suit is NT, 
    return -1 (meaning no trump card).
    """
    suit_cards = [card for card in cardset if card // 13 == suit.value]
    return min(suit_cards) if len(suit_cards) > 0 else -1

def lowest_card(cardset: CardSet, suit: CardSuit) -> int:
    """
    Return the lowest card in the given suit. If the suit is NT, 
    return -1 (meaning no trump card).
    """
    suit_cards = [card for card in cardset if card // 13 == suit.value]
    return max(suit_cards) if len(suit_cards) > 0 else -1

def lowest_card_in_any_suit(cardset: CardSet) -> int:
    """
    Return the lowest card in any suit.
    """
    max = -1
    for card in cardset:
        card = Card.from_code(card)
        if card.rank.value > max:
            max = card.code()
    return max

if __name__ == "__main__":
    print(Card(CardSuit.SPADES, CardRank.ACE))