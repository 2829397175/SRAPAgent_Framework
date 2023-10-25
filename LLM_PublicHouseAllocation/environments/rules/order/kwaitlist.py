from __future__ import annotations

from typing import TYPE_CHECKING, List
from collections import deque
from . import order_registry as OrderRegistry
from .base import BaseOrder
import copy
import random





@OrderRegistry.register("kwaitlist")
class KWaitListOrder(BaseOrder):
    """
    k deferral waitlist order for tenants
    
    k (tenant.max_choose): the tenant has k times to choose
    if tenant.choose_times < tenant.max_choose: tenant remain in waitlist
    
    waitlist_ratio : waitlist shortlisted ratio (default = 0.3 )
    
    """
    
    rule_description:str=""
    waitlist_ratio = 1.2 
    def get_next_agent_idx(self, environment) :
        
        """Return the index of the next agent to speak"""
        waitlist_return = []
        for queue_name, queue_info in environment.deque_dict.items():
            waitlist = copy.deepcopy(queue_info["waitlist"])
            queue_info["waitlist"] = []
            waitlist_return.append(waitlist)
        return waitlist_return

    def generate_deque(self, environment):
        queues = copy.deepcopy(environment.tenant_manager.groups)
        
        for queue_name,queue_tenant_ids in queues.items():
            
            environment.deque_dict[queue_name]={
                "queue":queue_tenant_ids,
                "waitlist":[]
            }
        
        return environment.deque_dict

    def requeue(self, environment, tenant):
        """re-queue"""
        if tenant.available:
            round_choose = tenant.choose_times % (tenant.max_choose)            
            for queue_name, queue_info in environment.deque_dict.items():
                if queue_name == tenant.queue_name:
                    if round_choose == 0:
                        queue_info['queue'].append(tenant.id)
                    else:
                        queue_info["waitlist"].append(tenant.id)
                    break
                        
        
    def reset(self,environment) -> None:
        environment.deque_dict={}

    
    def enter_waitlist(self,environment):
        # 根据小区的数量改pool的大小
        pool_num_dict = environment.system.community_manager.get_pool_num() 
        for pool_name,pool_num in pool_num_dict.items():
            if pool_name not in environment.deque_dict.keys():
                continue
            
            if int(pool_num*self.waitlist_ratio)>len(environment.deque_dict[pool_name]["queue"])+len(environment.deque_dict[pool_name]["waitlist"]):
                environment.deque_dict[pool_name]["waitlist"].extend(environment.deque_dict[pool_name]["queue"])
                environment.deque_dict[pool_name]["queue"]=[]
            elif int(pool_num*self.waitlist_ratio)<len(environment.deque_dict[pool_name]["waitlist"]):
                continue
            else:
                enter_num=int(pool_num*self.waitlist_ratio)-len(environment.deque_dict[pool_name]["waitlist"])
                environment.deque_dict[pool_name]["waitlist"].extend(environment.deque_dict[pool_name]["queue"][:enter_num])
                del environment.deque_dict[pool_name]["queue"][:enter_num]
                
    def are_all_deques_empty(self,environment) -> bool:
        self.enter_waitlist(environment)
        if all(len(queue_info["queue"])<=0 for _,queue_info in environment.deque_dict.items()):
            return False
        return True

                  