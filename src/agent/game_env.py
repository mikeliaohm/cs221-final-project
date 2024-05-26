"""
game_env.py
-----------

Contains the class that keeps the tracks of the game state and environment.
The GameEnv class provides interfaces to simulate the progress of the game.
"""

import copy

from typing import List
from agent.card_stats import Card, CardSuit, CardTrick, PlayerPosition, PlayerTurn
from agent.card_utils import CardSet
from agent.dds_eval import DDSEvaluator
from agent.generic_agent import Contract
from agent.pbn import PBN

class GameState:
    """
    Game State stores the cardsets held by players, the tricks won
    """
    def __init__(self, cardsets: List[CardSet], tricks_won: int = 0, 
                 cur_turn: PlayerTurn = None, partial_trick: CardTrick = None) -> None:
        self._tricks_won = tricks_won
        self._cardsets = cardsets

        if cur_turn is None and partial_trick is None:
            raise ValueError("Game State requires a partial trick and the player to lead the game.")
        if cur_turn is not None:
            self._cur_turn = cur_turn
        else:
            self._cur_turn = self.last_player().next()

        self._partial_trick = partial_trick

    def prev_player(self) -> PlayerTurn:
        """
        Get the last player who played the card.
        """
        if self._partial_trick is None:
            return None
        else:
            return PlayerTurn(self._partial_trick[-1][0])

    def cur_player(self) -> PlayerTurn:
        """
        Get the current player.
        """
        return self._cur_turn
    
    def next_player(self) -> PlayerTurn:
        """
        Get the next player.
        """
        return self._cur_turn.next()

DEDUCTION = 0.5 # Deduct 0.5 due to an error in the trick

class GameEnv:
    def __init__(self, contract: Contract) -> None:
        """
        Initialize the game environment the remaining card sets, contract, and the partial trick.
        """
        self._contract = contract

    def is_end(self, game_state: GameState) -> bool:
        """
        Check if the game has ended.
        """
        for cardset in game_state._cardsets:
            if len(cardset) != 0:
                return False
        return True

    def get_current_player(self, cur_state: GameState) -> PlayerTurn:
        """
        Get the current player.
        """
        return cur_state.cur_player()

    def get_legal_actions(self, cur_state: GameState) -> CardSet:
        """
        Get the legal actions for the current player.
        """
        cur_trick = cur_state._partial_trick
        cur_player = self.get_current_player(cur_state)
        if cur_trick is None:
            return cur_state._cardsets[cur_player.position().value]
        else:
            cur_suit = CardSuit.from_card_idx(cur_trick[0][1])
            cur_player = self.get_current_player(cur_state)
            legal_actions = []
            for card in cur_state._cardsets[cur_player.position().value]:
                if Card.from_code(card).suit == cur_suit:
                    legal_actions.append(card)

            if len(legal_actions) == 0:
                return cur_state._cardsets[cur_player.position().value]
            else:
                return legal_actions

    def move_to_next_player(self, cur_state: GameState, play_card: Card) -> GameState:
        """
        Generate the successor state by applying the action.
        """
        cur_player = self.get_current_player(cur_state)
        new_cardsets = copy.deepcopy(cur_state._cardsets)
        new_cardsets[cur_player.position().value].remove(play_card)
        new_trick = copy.deepcopy(cur_state._partial_trick) if cur_state._partial_trick is not None else []
        tricks_won = cur_state._tricks_won
        next_player = cur_player.next()

        # Eval the trick and return Game State for the next player
        new_trick.append((cur_player.position(), play_card))
        if len(new_trick) == 4:

            winner = self.win_trick(new_trick)
            if winner in [PlayerPosition.NORTH, PlayerPosition.SOUTH]:
                tricks_won += 1
            else:
                for card in new_trick:
                    if card[0] in [PlayerPosition.NORTH, PlayerPosition.SOUTH]:
                        if card[1] % 13 <= 4:
                            tricks_won -= DEDUCTION
            new_trick = None
            next_player = PlayerTurn(winner)

        return GameState(new_cardsets, tricks_won, next_player, new_trick)

    def get_tricks_won(self, game_state: GameState) -> int:
        """
        Get the number of tricks won by the NORTH-SOUTH team.
        """
        return game_state._tricks_won

    def get_scores(self, game_state: GameState) -> int:
        """
        Get the scores of the game. Scores are assigned only at the end of the game.
        """
        return game_state._tricks_won

    def evaluation(self, game_state: GameState) -> int:
        remaining_tricks = len(game_state._cardsets[0])

        # Sanity check that all cardsets have the same number of cards
        for cardset in game_state._cardsets:
            assert len(cardset) == remaining_tricks

        pbn_str = PBN.from_cardsets(game_state._cardsets, PlayerPosition.NORTH)
        lead_pos = self.get_current_player(game_state).position()
        if game_state._partial_trick is not None:
            lead_pos = game_state._partial_trick[0][0]
        cards = [] if game_state._partial_trick is None \
            else [Card.from_code(idx) for (pos, idx) in game_state._partial_trick]
        scores = DDSEvaluator(self._contract.trump_suit, lead_pos, cards, pbn_str)
        
        if lead_pos in [PlayerPosition.NORTH, PlayerPosition.SOUTH]:
            highest_score = scores.get_highest_scores()
        else:
            highest_score = remaining_tricks - scores.get_highest_scores()

        return self.get_tricks_won(game_state) + highest_score

    def win_trick(self, trick: CardTrick) -> PlayerPosition:
        """
        Evaluate the trick and return the winner of the trick.
        """
        current_suit = CardSuit.from_card_idx(trick[0][1])
        # keep track of the highest card played, initialize to the first card
        max = (trick[0][0], Card.from_code(trick[0][1]))
        for i in range(1, 4):
            player, card_idx = trick[i]
            other_card = Card.from_code(card_idx)
            if other_card.suit != current_suit and other_card.suit != self._contract.trump_suit:
                continue
                
            if other_card.larger_than(max[1], self._contract.trump_suit):
                max = (player, other_card)

        return max[0]
    
    def last_card_to_play(self, game_state: GameState) -> Card:
        """
        Get the last card played in the partial trick.
        """
        return game_state._partial_trick is not None and len(game_state._partial_trick) == 3