"""
Minimax agent
-------------

Agent that uses the minimax algorithm to choose the best card to play.
"""

import copy
from typing import Dict, List
from agent.card_stats import CardTrick, PlayerPosition, PlayerTurn, Card
from agent.card_utils import card_to_index, index_to_card
from agent.game_env import GameEnv, GameState
from objects import CardResp
from agent.generic_agent import GenericAgent
from agent.assigners.random_assigner import RandomAssigner

class MinimaxAgent(GenericAgent):
    def __str__(self) -> str:
        return "Minimax"

    def choose_card(self, lead_pos: PlayerPosition = None, current_trick: List[int] = None, playing_dummy = False) -> int:
        self.assign_cards()

        current_trick = None
        if self.__played__ is not None and len(self.__played__) > 0:
            if len(self.__played__[-1]) < 4:
                current_trick = copy.deepcopy(self.__played__[-1])

        cur_turn = PlayerTurn(PlayerPosition.NORTH) if playing_dummy else PlayerTurn(self.__position__) 
        cur_states = GameState(cardsets=copy.deepcopy(self.__cardsets__), 
                               cur_turn=cur_turn, 
                               partial_trick=copy.deepcopy(current_trick))
        card_idx = self.get_optimal_card(cur_states)
        return card_idx
    
    def fallback(self, lead_pos: PlayerPosition = None, current_trick52: List[int] = None, playing_dummy = False) -> int:
        cardset = self.__cards__ if not playing_dummy else self.__dummy__
        if current_trick52 is None or len(current_trick52) == 0:
            card_idx = min(cardset)
        else:
            suit = current_trick52[0] // 13
            if not any(card // 13 == suit for card in cardset):
                card_idx = min(cardset)
            else:
                card_idx = max(card for card in cardset if card // 13 == suit)
        return card_idx

    async def opening_lead(self, contract: str, dummy_hand_str: str) -> CardResp:
        declarer = PlayerPosition((self.__position__.value + 4 - 1) % 4)
        self.set_contract(contract, declarer)
        self.__cardsets__[self.dummy_position.value] = card_to_index(dummy_hand_str)
        card_idx = self.choose_card()
        return CardResp(card=Card.from_code(card_idx), candidates=[], samples=[], shape=-1, hcp=-1, quality=None, who=None)
    
    async def async_play_card(self, trick_i: int, leader_i: int, 
        current_trick52: List[int], players_states: List[any], 
        bidding_scores: List[any], quality: any, 
        probability_of_occurence: List[float], shown_out_suits: List[Dict], 
        play_status: str) -> CardResp:
        seat = ((self.__contract__.declarer.value + 1) % 4 + leader_i) % 4
        card_idx = self.choose_card(PlayerPosition(seat), current_trick52)
        return CardResp(card=Card.from_code(card_idx), candidates=[], samples=[], shape=-1, hcp=-1, quality=None, who=None)
    
    async def play_dummy_hand(self, current_trick52: List[int], leader_seqno: int) -> CardResp:
        seat = ((self.__contract__.declarer.value + 1) % 4 + leader_seqno) % 4
        card_idx = self.choose_card(PlayerPosition(seat), current_trick52, True)
        if self.__verbose__:
            print(f"Play on dummy card: {Card.from_code(card_idx)}")
        return CardResp(card=Card.from_code(card_idx), candidates=[], samples=[], shape=-1, hcp=-1, quality=None, who=None)
    
    def set_real_card_played(self, card_played: int, player_i: int) -> None:
        seat = ((self.__contract__.declarer.value + 1) % 4 + player_i) % 4
        # The NaiveAgent only knows its own hand
        known_hands = [self.__position__.value, self.dummy_position.value]
        if seat in known_hands:
            try:
                self.__cardsets__[seat].remove(card_played)
            except KeyError:
                print(f"Card played: {index_to_card(card_played)}")
                print(f"Player: {seat}")
                print(f"Known hands: {known_hands}")
                print(f"Cardsets: {self.print_cards()}")
                assert False
        super().set_real_card_played(card_played, player_i)

    """
    =================================================================================
    The section below defines methods used to deal with the unseen cards.
    =================================================================================
    """
    
    def assign_cards(self) -> None:
        unseen_cards, unseen_counts = self.get_unseen_cards()
        assigned_hands = RandomAssigner.assign(unseen_cards, unseen_counts)
        hidden_players = self.get_hidden_players()
        for player in hidden_players:
            self.__cardsets__[player.value] = assigned_hands[player]

    """
    =================================================================================
    The section below defines methods for the game tree.
    =================================================================================
    """

    def get_optimal_card(self, cur_states: GameState) -> int:
        """
        Get the optimal card to play using the minimax strategy.
        """
        game_env = GameEnv(self.__contract__)
        team = [PlayerPosition.NORTH, PlayerPosition.SOUTH]

        def recurse(game_state: GameState, depth: int, root_card: int) -> int:
            if game_env.is_end(game_state):
                return (game_env.get_scores(), root_card)
            if depth == 0:
                return (game_env.evaluation(game_state), root_card)
            
            actions = game_env.get_legal_actions(game_state)
            depth = depth - 1 if game_env.last_card_to_play(game_state) else depth
            if game_env.get_current_player(game_state).position() in team:
                best_val = (float('-inf'), None)
                for action in actions:
                    new_state = game_env.move_to_next_player(game_state, action)
                    new_root_card = action if root_card is None else root_card
                    val = recurse(new_state, depth, new_root_card)
                    best_val = max(best_val, val, key=lambda x: x[0])
                return best_val
            else:
                best_val = (float('inf'), None)
                for action in actions:
                    new_state = game_env.move_to_next_player(game_state, action)
                    new_root_card = action if root_card is None else root_card
                    val = recurse(new_state, depth, new_root_card)
                    best_val = min(best_val, val, key=lambda x: x[0])
                return best_val

        optimal = recurse(cur_states, 1, None)
        return optimal[1]