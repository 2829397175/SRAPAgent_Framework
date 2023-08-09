from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

if TYPE_CHECKING:
    from LLM_PublicHouseAllocation.environments import BaseEnvironment
from . import visibility_registry

@visibility_registry.register("base")
class BaseVisibility(BaseModel):

    def update_visible_agents(self, environment: BaseEnvironment):
        """Update the set of visible agents for the agent"""
        pass

    def reset(self):
        pass