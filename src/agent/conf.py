from typing import Union

from agent.minimax_bayes_agent import MinimaxBayesAgent
from agent.minimax_opt_agent import MinimaxOptAgent

from .generic_agent import GenericAgent
from .human_agent import HumanAgent
from .naive_agent import NaiveAgent
from .oracle import TheOracle
from .minimax_agent import MinimaxAgent
from ddsolver import dds

# Player seats that uses agents, [North, East, South, West]
# True in a seat means the card will be dealt by an agent
INSTALL_AGENT = True
AGENT_TYPE = MinimaxOptAgent
AGENT_TYPES = Union[HumanAgent, NaiveAgent, TheOracle, MinimaxAgent, MinimaxBayesAgent, MinimaxOptAgent]

# This has to be initialized once for the entire project
dds.SetMaxThreads(0)