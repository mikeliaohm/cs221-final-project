import ctypes
from queue import PriorityQueue
from typing import List

from ddsolver import dds, functions
try:
    from .card_stats import CardSuit, CardRank, PlayerPosition, Card
    from .card_utils import CARD_INDEX_MAP
    from .pbn import PBN
except ImportError:
    from card_stats import CardSuit, CardRank, PlayerPosition, Card
    from card_utils import CARD_INDEX_MAP
    from pbn import PBN

VERBOSE = False

def solve_board_pbn(trump_suit: CardSuit, lead_idx: PlayerPosition, 
                    current_trick: List[Card], remaining_cards: PBN) -> dds.futureTricks:
    dlPBN = dds.dealPBN()
    fut3 = dds.futureTricks()
    dlPBN.trump = trump_suit.value
    dlPBN.first = lead_idx.value
    
    for idx, card in enumerate(current_trick):
        dlPBN.currentTrickSuit[idx] = card.suit.value
        dlPBN.currentTrickRank[idx] = card.rank.value

    dlPBN.remainCards = remaining_cards.to_bytes()
    target = -1
    solutions = 3
    mode = 0
    res = dds.SolveBoardPBN(
        dlPBN,
        target,
        solutions,
        mode,
        ctypes.pointer(fut3),
        0)

    if res != dds.RETURN_NO_FAULT:
        line = ctypes.create_string_buffer(80)
        dds.ErrorMessage(res, line)
        raise Exception("DDS error {}".format(line.value.decode("utf-8")))

    if VERBOSE:
        line = "Cards"
        functions.PrintPBNHand(line, dlPBN.remainCards)

    return fut3

class DDSEvaluator:
    def __init__(self, trump_suit: CardSuit, lead_idx: PlayerPosition, 
                 current_trick: List[Card], remaining_cards: PBN):
        self.scores = solve_board_pbn(trump_suit, lead_idx, current_trick, remaining_cards)
    
    def print_scores(self):
        functions.PrintFut("scores: ", ctypes.pointer(self.scores))

    def get_best_card(self) -> int:
        card = Card(CardSuit(self.scores.suit[0]), CardRank(self.scores.rank[0]))
        return CARD_INDEX_MAP[f"{card}"]

if __name__ == "__main__":
    """
    run this as a module with the following command:
    python -m agent.dds_eval
    """
    dds.SetMaxThreads(0)
    # Past deal
    cards: str = "S:Q9652.754.T4.862 J.KQJ96.AKQ5.J94 AK8.A2.962.KQT73 T743.T83.J873.A5"
    VERBOSE = True
    scores = solve_board_pbn(CardSuit.SPADES, PlayerPosition.WEST, [], PBN.from_pbn(cards))
    functions.PrintFut("scores: ", ctypes.pointer(scores))
    
    # Balanced hand
    cards: str = "N:AT62.J73.Q84.K95 K95.AT62.J73.Q84 Q84.K95.T652.J73 J73.Q84.AK9.AT62"
    VERBOSE = True
    scores = solve_board_pbn(CardSuit.NT, PlayerPosition.NORTH, [], PBN.from_pbn(cards))
    functions.PrintFut("scores: ", ctypes.pointer(scores))
    
    # Balanced hand
    cards: str = "N:AK32.AK2.QJT.QJT QJT.QJT.AK32.AK2 987.987.654.6543 654.6543.987.987"
    VERBOSE = True
    scores = solve_board_pbn(CardSuit.NT, PlayerPosition.NORTH, [], PBN.from_pbn(cards))
    functions.PrintFut("scores: ", ctypes.pointer(scores))

    # Testing partial trick
    cards = "N:643.T432.532.T9 Q8.5.AK97.AK54 KT7.J7.QT86.Q73 AJ92.A6.J4.J862"
    VERBOSE = True
    current_trick = [Card(CardSuit.SPADES, CardRank.FIVE)]
    scores = solve_board_pbn(CardSuit.NT, PlayerPosition.EAST, current_trick, PBN.from_pbn(cards))
    functions.PrintFut("scores: ", ctypes.pointer(scores))
