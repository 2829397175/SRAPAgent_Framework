from __future__ import annotations

from typing import TYPE_CHECKING, List
from collections import deque
from . import order_registry as OrderRegistry
from .base import BaseOrder
import re
import random





@OrderRegistry.register("priority")
class PriorityOrder(BaseOrder):
    """
    Order for rent.
    random(agents.tenants) (one agent at a time)
    """
    rule_description:str=""
    def get_next_agent_idx(self, environment) :
        """Return the index of the next agent to speak"""
        result=[]
        for _,deque in environment.deque_dict.items():
            if len(deque)>0:
                result.append(deque.popleft())
        return result

    def generate_deque(self, environment):
        priority_queue = []
        non_priority_queue = []
        
        for tenant_info in environment.tenant_manager.data.values():
            if all(not value for value in tenant_info.priority_item.values()):
                non_priority_queue.append(tenant_info)
            else:
                priority_queue.append(tenant_info)
        # 将这两个队列添加到 environment 的 deque_dict 中
        random.shuffle(priority_queue)
        random.shuffle(non_priority_queue)
        environment.deque_dict["priority_queue"]=deque(priority_queue)
        environment.deque_dict["non_priority_queue"]=deque(non_priority_queue)
        return environment.deque_dict

    def requeue(self, environment,tenant):
        """Return the index of the next agent to speak"""
        if all(not value for value in tenant.priority_item.values()):
            environment.deque_dict["priority_queue"].append(tenant)
        else:
            environment.deque_dict["non_priority_queue"].append(tenant)

    def reset(self,environment) -> None:
        environment.deque_dict["priority_queue"].clear()
        environment.deque_dict["non_priority_queue"].clear()
        
        
    def are_all_deques_empty(self,environment) -> bool:
        return all(len(d) == 0 for d in environment.deque_dict.values())