from typing import Union

from .generic_agent import GenericAgent
from .human_agent import HumanAgent
from .naive_agent import NaiveAgent
from .oracle import TheOracle
from ddsolver import dds

# Player seats that uses agents, [North, East, South, West]
# True in a seat means the card will be dealt by an agent
INSTALL_AGENT = True
AGENT_TYPE = NaiveAgent
AGENT_TYPES = Union[HumanAgent, NaiveAgent, TheOracle]

# This has to be initialized once for the entire project
dds.SetMaxThreads(0)