from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, List

from pydantic import BaseModel
if TYPE_CHECKING:
    from LLM_PublicHouseAllocation.environments import BaseEnvironment


class BaseOrder(BaseModel):
    rule_description:str=""
    
    @abstractmethod
    def get_next_agent_idx(self, environment: BaseEnvironment) -> List[int]:
        """Return the index of the next agent to speak"""

    @abstractmethod
    def generate_deque(self, environment: BaseEnvironment) :
        """Return the index of the next agent to speak"""

    @abstractmethod
    def requeue(self, environment: BaseEnvironment,tenant):
        """Return the index of the next agent to speak"""
    def are_all_deques_empty(self,environment):
        pass
    def reset(self) -> None:
        pass
