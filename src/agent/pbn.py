from typing import List    

try:
    from .card_stats import PlayerPosition
    from .card_utils import cardset_to_hand, CardSet
except ImportError:
    from card_stats import PlayerPosition
    from card_utils import cardset_to_hand, CardSet

class PBN:
    def __init__(self, pbn_str: str) -> None:
        self.pbn_str = pbn_str

    def to_bytes(self) -> bytes:
        return self.pbn_str.encode('utf-8')

    @staticmethod
    def from_pbn(pbn_str: str) -> "PBN":
        return PBN(pbn_str)

    @staticmethod
    def from_hands(hands: List[str], dealer: PlayerPosition) -> "PBN":
        pbn_str = f"{dealer}:{hands[0]} {hands[1]} {hands[2]} {hands[3]}"
        return PBN(pbn_str)
    
    @staticmethod
    def from_cardsets(hands: List[CardSet], dealer: PlayerPosition) -> "PBN":
        hands_str = f"{dealer}:"
        for hand in hands:
            str1 = cardset_to_hand(hand)
            hands_str += f"{str1} "
        hands_str = hands_str.rstrip()
        return PBN(hands_str)

if __name__ == "__main__":
    pbn = PBN.from_hands(["QJ6.K652.J85.T98", "873.J97.AT764.Q4", "K5.T83.KQ9.A7652", "AT942.AQ4.32.KJ3"], PlayerPosition.NORTH)
    print(pbn.pbn_str)
    pbn2 = PBN.from_cardsets([[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], [13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25], [26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38], [39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51]], PlayerPosition.NORTH)
    print(pbn2.pbn_str)