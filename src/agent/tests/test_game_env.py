import unittest
import copy

from agent.card_stats import Card, CardSuit, PlayerPosition, PlayerTurn
from agent.card_utils import card_to_index
from agent.game_env import GameEnv, GameState
from agent.generic_agent import Contract

NORTH = 0
EAST = 1
SOUTH = 2
WEST = 3

class TestPlayATrick(unittest.TestCase):
    def setUp(self) -> None:
        """
        Test case: from declarer.pbn

        N: AJ4.T7.AT652.KJ2 
        E: K73.A985432.Q9.7 
        S: 985..KJ84.AQT654 
        W: QT62.KQJ6.73.983

        [Declarer "E"]
        [Contract "3NT"]
        """
        deal_str = "AJ4.T7.AT652.KJ2 K73.A985432.Q9.7 985..KJ84.AQT654 QT62.KQJ6.73.983"
        deals = deal_str.split()
        self.cardsets = [card_to_index(deal) for deal in deals]
        self.cur_states = GameState(copy.deepcopy(self.cardsets), cur_turn=PlayerTurn(PlayerPosition.SOUTH))
        self.game_env = GameEnv(Contract(3, "NT", PlayerPosition.EAST))

        return super().setUp()

    def test_player_turns_and_contract(self) -> None:

        self.assertEqual(self.cur_states.cur_player(), PlayerTurn(PlayerPosition.SOUTH))
        self.assertEqual(self.cur_states.next_player(), PlayerTurn(PlayerPosition.WEST))
        self.assertEqual(self.cur_states.prev_player(), None)
        self.assertEqual(self.cur_states._partial_trick, None)
        self.assertEqual(self.game_env._contract, Contract(3, "NT", PlayerPosition.EAST))

    def test_get_actions(self) -> None:
        
        actions = self.game_env.get_legal_actions(self.cur_states)
        self.assertEqual(len(actions), 13)
        self.assertEqual(actions, self.cardsets[SOUTH])

    def test_lead_a_card(self) -> None:
        """
        The lowest numerical value of the card held by the player is S9.
        S: 985..KJ84.AQT654 
        """
        card_idx = Card.from_str("S9").code()
        self.assertIn(card_idx, self.cardsets[SOUTH])
        self.assertIn(card_idx, self.cur_states._cardsets[SOUTH])

        self.cardsets[SOUTH].remove(card_idx)
        new_states = self.game_env.move_to_next_player(self.cur_states, card_idx)

        self.assertEqual(new_states.cur_player(), PlayerTurn(PlayerPosition.WEST))
        self.assertEqual(new_states.next_player(), PlayerTurn(PlayerPosition.NORTH))
        self.assertEqual(new_states.prev_player(), PlayerTurn(PlayerPosition.SOUTH))
        self.assertEqual(new_states._partial_trick, [(PlayerPosition.SOUTH, card_idx)])
        self.assertEqual(new_states._cardsets[SOUTH], self.cardsets[SOUTH])

    def test_WEST_move(self) -> None:
        """
        W: QT62.KQJ6.73.983
        """
        south_card = Card.from_str("S9").code()
        west_card = Card.from_str("SQ").code()
        self.assertIn(west_card, self.cur_states._cardsets[WEST])

        new_states = self.game_env.move_to_next_player(self.cur_states, south_card)

        actions = self.game_env.get_legal_actions(new_states)
        self.assertEqual(len(actions), 4)
        self.assertEqual(actions, [card for card in new_states._cardsets[WEST] \
                                   if CardSuit.from_card_idx(card) == CardSuit.SPADES])
        
        self.cardsets[WEST].remove(west_card)
        new_states = self.game_env.move_to_next_player(new_states, west_card)

        self.assertEqual(new_states.cur_player(), PlayerTurn(PlayerPosition.NORTH))
        self.assertEqual(new_states.next_player(), PlayerTurn(PlayerPosition.EAST))
        self.assertEqual(new_states.prev_player(), PlayerTurn(PlayerPosition.WEST))
        cur_trick = [(PlayerPosition.SOUTH, south_card), (PlayerPosition.WEST, west_card)]
        self.assertEqual(new_states._partial_trick, cur_trick)
        self.assertEqual(new_states._cardsets[WEST], self.cardsets[WEST])

    def test_NORTH_move(self) -> None:
        """
        N: AJ4.T7.AT652.KJ2 
        """
        south_card = Card.from_str("S9").code()
        west_card = Card.from_str("SQ").code()
        north_card = Card.from_str("SA").code()
        self.assertIn(north_card, self.cur_states._cardsets[NORTH])

        new_states = self.game_env.move_to_next_player(self.cur_states, south_card)
        new_states = self.game_env.move_to_next_player(new_states, west_card)

        actions = self.game_env.get_legal_actions(new_states)
        self.assertEqual(len(actions), 3)
        self.assertEqual(actions, [card for card in new_states._cardsets[NORTH] \
                                   if CardSuit.from_card_idx(card) == CardSuit.SPADES])
        
        self.cardsets[NORTH].remove(north_card)
        new_states = self.game_env.move_to_next_player(new_states, north_card)

        self.assertEqual(new_states.cur_player(), PlayerTurn(PlayerPosition.EAST))
        self.assertEqual(new_states.next_player(), PlayerTurn(PlayerPosition.SOUTH))
        self.assertEqual(new_states.prev_player(), PlayerTurn(PlayerPosition.NORTH))
        cur_trick = [(PlayerPosition.SOUTH, south_card), 
                     (PlayerPosition.WEST, west_card),
                     (PlayerPosition.NORTH, north_card)]
        self.assertEqual(new_states._partial_trick, cur_trick)
        self.assertEqual(new_states._cardsets[NORTH], self.cardsets[NORTH])

    def test_NORTH_win(self) -> None:
        """
        E: K73.A985432.Q9.7 
        """
        south_card = Card.from_str("S9").code()
        west_card = Card.from_str("SQ").code()
        north_card = Card.from_str("SA").code()
        east_card = Card.from_str("S3").code()
        self.assertIn(east_card, self.cur_states._cardsets[EAST])

        new_states = self.game_env.move_to_next_player(self.cur_states, south_card)
        new_states = self.game_env.move_to_next_player(new_states, west_card)
        new_states = self.game_env.move_to_next_player(new_states, north_card)

        actions = self.game_env.get_legal_actions(new_states)
        self.assertEqual(len(actions), 3)
        self.assertEqual(actions, [card for card in new_states._cardsets[EAST] \
                                   if CardSuit.from_card_idx(card) == CardSuit.SPADES])
        
        self.cardsets[EAST].remove(east_card)
        new_states = self.game_env.move_to_next_player(new_states, east_card)

        self.assertEqual(new_states.cur_player(), PlayerTurn(PlayerPosition.NORTH))
        self.assertEqual(new_states.next_player(), PlayerTurn(PlayerPosition.EAST))
        self.assertIsNone(new_states.prev_player())
        self.assertIsNone(new_states._partial_trick)
        self.assertEqual(new_states._cardsets[EAST], self.cardsets[EAST])
        self.assertEqual(new_states._tricks_won, 1)

    def test_WEST_win(self) -> None:
        """
        E: K73.A985432.Q9.7 
        """
        south_card = Card.from_str("S9").code()
        west_card = Card.from_str("SQ").code()
        north_card = Card.from_str("SJ").code()
        east_card = Card.from_str("S3").code()
        self.assertIn(east_card, self.cur_states._cardsets[EAST])

        new_states = self.game_env.move_to_next_player(self.cur_states, south_card)
        new_states = self.game_env.move_to_next_player(new_states, west_card)
        new_states = self.game_env.move_to_next_player(new_states, north_card)

        actions = self.game_env.get_legal_actions(new_states)
        self.assertEqual(len(actions), 3)
        self.assertEqual(actions, [card for card in new_states._cardsets[EAST] \
                                   if CardSuit.from_card_idx(card) == CardSuit.SPADES])
        
        self.cardsets[EAST].remove(east_card)
        new_states = self.game_env.move_to_next_player(new_states, east_card)

        self.assertEqual(new_states.cur_player(), PlayerTurn(PlayerPosition.WEST))
        self.assertEqual(new_states.next_player(), PlayerTurn(PlayerPosition.NORTH))
        self.assertIsNone(new_states.prev_player())
        self.assertIsNone(new_states._partial_trick)
        self.assertEqual(new_states._tricks_won, -0.5)

    def test_EAST_win(self) -> None:
        """
        E: K73.A985432.Q9.7 
        """
        south_card = Card.from_str("S9").code()
        west_card = Card.from_str("ST").code()
        north_card = Card.from_str("SJ").code()
        east_card = Card.from_str("SK").code()
        self.assertIn(east_card, self.cur_states._cardsets[EAST])

        new_states = self.game_env.move_to_next_player(self.cur_states, south_card)
        new_states = self.game_env.move_to_next_player(new_states, west_card)
        new_states = self.game_env.move_to_next_player(new_states, north_card)

        actions = self.game_env.get_legal_actions(new_states)
        self.assertEqual(len(actions), 3)
        self.assertEqual(actions, [card for card in new_states._cardsets[EAST] \
                                   if CardSuit.from_card_idx(card) == CardSuit.SPADES])
        
        self.cardsets[EAST].remove(east_card)
        self.assertTrue(self.game_env.last_card_to_play(new_states))
        new_states = self.game_env.move_to_next_player(new_states, east_card)

        self.assertEqual(new_states.cur_player(), PlayerTurn(PlayerPosition.EAST))
        self.assertEqual(new_states.next_player(), PlayerTurn(PlayerPosition.SOUTH))
        self.assertIsNone(new_states.prev_player())
        self.assertIsNone(new_states._partial_trick)
        self.assertEqual(new_states._tricks_won, -0.5)

if __name__ == "__main__":
    unittest.main()
