from agent.assigners.csp_assigner_v2 import CSPAssignerV2
from agent.assigners.random_assigner import RandomAssigner
from agent.minimax_bayes_agent import MinimaxBayesAgent

class MinimaxOptAgent(MinimaxBayesAgent):
    def __str__(self) -> str:
        return "MinimaxOpt"
    
    def assign_cards(self) -> None:
        unseen_cards, unseen_counts = self.get_unseen_cards()
        player_stats = {}
        suit_seen = set()        
        
        if self.__contract__.declarer is self.__position__:
            assigned_hands = RandomAssigner.assign(unseen_cards, unseen_counts)
        else:
            for player, num_cards in unseen_counts.items():
                bided_suit = self.__bided_suit__[player.value]
                if bided_suit in suit_seen:
                    bided_suit = None
                player_stats[player] = (num_cards, bided_suit)
                suit_seen.add(bided_suit)
            assigner = CSPAssignerV2(unseen_cards, player_stats, self._shown_out_suits)
            try:
                assigned_hands = assigner.assign_cards()
            except:
                assigned_hands = RandomAssigner.assign(unseen_cards, unseen_counts)

        hidden_players = self.get_hidden_players()
        for player in hidden_players:
            self.__cardsets__[player.value] = assigned_hands[player]