"""
evaluator.py
------------

This module defines the AgentEvaluator class that is used to evaluate the
agent's performance.
"""

from typing import List
import logging
import json

from agent.card_stats import CardPlayed, CardSuit, PlayerPosition
from agent.conf import AGENT_TYPES
from agent.generic_agent import Contract
import os

from agent.human_agent import HumanAgent
from agent.naive_agent import NaiveAgent
from agent.oracle import TheOracle

def log_subfolder(agent: AGENT_TYPES):
    if isinstance(agent, NaiveAgent):
        return "naive"
    elif isinstance(agent, TheOracle):
        return "oracle"
    elif isinstance(agent, HumanAgent):
        return "human"

class AgentEvaluator:
    def __init__(self, file_name: str, deal_str: str, agent: AGENT_TYPES, tricks_result: List[int]) -> None:
        """
        @param deal_str: The deal string (AJ4.T7.AT652.KJ2 K73.A985432.Q9.7 985..KJ84.AQT654 QT62.KQJ6.73.983)
        @param agent: The agent object (e.g. TheOracle, NaiveAgent, etc), can access contract and played deque
        @param tricks_result: The player (identified by the play seqno) who won each trick
        """
        self.__deal_str__ = deal_str
        self.__agent__ = agent
        find_seat = lambda seqno: PlayerPosition((agent.__contract__.declarer.value + 1 + seqno) % 4)
        self.__tricks_result__ = [find_seat(seqno) for seqno in tricks_result]
        LOG_FOLDER = f"agent/logs/{log_subfolder(agent)}"
        os.makedirs(LOG_FOLDER, exist_ok=True)
        self.__log_file__ = f"{LOG_FOLDER}/{file_name}.json"

        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', 
                            datefmt='%Y-%m-%d %H:%M:%S', filemode="a")
        
        # Create the folder if it doesn't exist
        
        try:
            with open(self.__log_file__, 'x') as f:
                json.dump([], f)
        except FileExistsError:
            pass

    def print_result(self) -> None:
        """
        Print the contents of the agent's played cards.
        """
        print(f"Deal: {self.__deal_str__}")
        print(f"Contract: {self.__agent__.__contract__}")
        print(f"Won tricks: {self.__agent__.n_tricks_taken} / score: {self.calculate_score()}")
        self.__agent__.print_deque(tricks_result=self.__tricks_result__)

    def win_deal(self) -> bool:
        """
        Determine if the agent has fulfilled/defended the contract.
        """
        contract_level = self.__agent__.__contract__.level
        trick_to_win = 6 + contract_level
        if self.__agent__.is_declarer:
            return self.__agent__.n_tricks_taken >= trick_to_win
        else:
            return 13 - self.__agent__.n_tricks_taken < trick_to_win
        
    def calculate_score(self):
        """
        Simplified scoring mechanism based on the Duplicate Bridge 
        Scoring system to give another numerical estimate of the agent's
        performance other than number of tricks won.
        """
        # Scoring constants
        MAJOR_SUIT = [CardSuit.SPADES, CardSuit.HEARTS]
        MINOR_SUIT = [CardSuit.DIAMONDS, CardSuit.CLUBS]
        NOTRUMP = CardSuit.NT
        BASE_POINTS = {
            CardSuit.SPADES: 30,
            CardSuit.HEARTS: 30,
            CardSuit.DIAMONDS: 20,
            CardSuit.CLUBS: 20,
            CardSuit.NT: 40
        }
        
        contract_level = self.__agent__.__contract__.level
        contract_suit = self.__agent__.__contract__.trump_suit
        is_vulnerable = False  # Example, you can set this based on actual game context
        
        # Determine base points for contract
        if contract_suit == NOTRUMP:
            base_points = BASE_POINTS[NOTRUMP] + (BASE_POINTS[NOTRUMP] - 10) * (contract_level - 1)
        else:
            base_points = BASE_POINTS[contract_suit] * contract_level
        
        # Determine overtrick points
        tricks_won = self.__agent__.n_tricks_taken
        overtricks = tricks_won - (contract_level + 6)
        overtrick_points = overtricks * BASE_POINTS[contract_suit if contract_suit != NOTRUMP else MAJOR_SUIT[0]]
        
        # Calculate total points
        total_points = base_points + overtrick_points
        
        return total_points
    
    def log_result(self):
        """
        Data to log for each deal.
        Declarer, Contract, Tricks won, Score, Deal string, Fulfill contract or Defend contract
        """
        score = self.calculate_score()
        contract_fulfilled_defended = self.win_deal()
        declarer = self.__agent__.__contract__.declarer
        contract = self.__agent__.__contract__
        tricks_won = self.__agent__.n_tricks_taken

        log_message = {
            "Declarer": f"{declarer}",
            "Contract": f"{contract.level}{contract.trump_suit}",
            "Tricks won": tricks_won,
            "Score": score,
            "Deal": self.__deal_str__,
            "Fulfilled/Defended": contract_fulfilled_defended
        }

        # Read the existing log file
        with open(self.__log_file__, 'r') as f:
            logs = json.load(f)

        # Append the new log entry
        logs.append(log_message)

        # Write the updated log back to the file
        with open(self.__log_file__, 'w') as f:
            json.dump(logs, f, indent=4)
        
        logging.info(log_message)
