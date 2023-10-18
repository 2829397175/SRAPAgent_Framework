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
        waitlist_return=[]
        for queue_name, queue_info in environment.deque_dict.items():
            waitlist_return.append(queue_info["waitlist"])
        return waitlist_return

    def generate_deque(self, environment):
        waitlist_queue0= []
        waitlist_queue1= []
        waitlist_queue2= []
        queue_0 = []
        queue_1 = []
        queue_2 = []
        for _,tenant in environment.tenant_manager.data.items():
            if all(not value for value in tenant.priority_item.values()) and tenant.family_num<2:
                tenant.queue_name='0'
                queue_0.append(tenant)
            elif all(not value for value in tenant.priority_item.values()) and tenant.family_num>=2: 
                tenant.queue_name='1'
                queue_1.append(tenant)
            else:
                tenant.queue_name='2'
                queue_2.append(tenant)
                
        
            # 将这两个队列添加到 environment 的 deque_dict 中
        random.shuffle(queue_1)
        random.shuffle(queue_2)
        random.shuffle(queue_0)

        
        environment.deque_dict["0"] = {
            "queue":queue_0,
            "waitlist":waitlist_queue0
        }
        environment.deque_dict["1"] = {
            "queue":queue_1,
            "waitlist":waitlist_queue1
        }
        environment.deque_dict["2"] = {
            "queue":queue_2,
            "waitlist":waitlist_queue2
        }
        
        return environment.deque_dict

    def requeue(self, environment,tenant):
        """re-queue"""
        round_choose = tenant.choose_times % (tenant.max_choose)
        for queue_name, queue_info in environment.deque_dict.items():
                if queue_name == tenant.queue_name:
                    if round_choose==0:
                        queue_info['queue'].append(tenant)
                    else:
                        tenant.choose_times+=1
                        queue_info["waitlist"].append(tenant)
                    break
                        
        
    def reset(self,environment) -> None:
        environment.deque_dict={}

    
    def enter_waitlist(self,environment):
        pool_num_dict=environment.system.community_manager.get_pool_num()
        for pool_name,pool_num in pool_num_dict.items():
            if int(pool_num*self.waitlist_ratio)>len(environment.deque_dict[pool_name]["queue"])+len(environment.deque_dict[pool_name]["waitlist"]):
                enter_num=len(environment.deque_dict[pool_name]["queue"])
                environment.deque_dict[pool_name]["waitlist"].extend(environment.deque_dict[pool_name]["queue"])
                environment.deque_dict[pool_name]["queue"]=[]
            elif int(pool_num*self.waitlist_ratio)<len(environment.deque_dict[pool_name]["waitlist"]):
                continue
            else:
                enter_num=int(pool_num*self.waitlist_ratio)-len(environment.deque_dict[pool_name]["waitlist"])
                environment.deque_dict[pool_name]["waitlist"].extend(environment.deque_dict[pool_name]["queue"][:enter_num])
                del environment.deque_dict[pool_name]["queue"][:enter_num]
                
    def are_all_deques_empty(self,environment) -> bool:
        if all(len(queue_info["queue"])<=0 for _,queue_info in environment.deque_dict.items()):
            return False
        return True

                  