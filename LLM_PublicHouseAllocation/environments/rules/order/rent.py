from __future__ import annotations

from typing import TYPE_CHECKING, List
from collections import deque
from . import order_registry as OrderRegistry
from .base import BaseOrder
import re
import random





@OrderRegistry.register("rent")
class RentOrder(BaseOrder):
    """
    Order for rent.
    random(agents.tenants) (one agent at a time)
    """

    def get_next_agent_idx(self, environment) :
        """Return the index of the next agent to speak"""
        tenant=environment.deque.popleft()
        return tenant

    def generate_deque(self, environment):
        tenantlist=list(environment.tenant_manager.data.values())
        random.shuffle(tenantlist)
        environment.deque = deque(tenantlist)
        return environment.deque

    def requeue(self, environment,tenant):
        """Return the index of the next agent to speak"""
        environment.deque.append(tenant)

    def reset(self) -> None:
        pass