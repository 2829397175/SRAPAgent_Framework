import asyncio
import logging
from typing import List, Deque, Optional
from LLM_PublicHouseAllocation.tenant.multiprompt_tenant import BaseMultiPromptTenant
from LLM_PublicHouseAllocation.tenant.langchain_tenant import LangchainTenant
import json
from LLM_PublicHouseAllocation.manager import TenantManager,ForumManager
from LLM_PublicHouseAllocation.involvers import System,Tool,Search_forum_topk,LogRound
from . import env_registry as EnvironmentRegistry
from .base import BaseEnvironment
import copy
import os
@EnvironmentRegistry.register("rent")
class RentEnvironment(BaseEnvironment):
    """
    A environment implementing the logic of conversation.

    Args:
        agents: tenant_manager
        rule: Rule for the environment
        max_turns: Maximum number of turns
        cnt_turn: Current turn number
        last_messages: Messages from last turn
        rule_params: Variables set by the rule
    """
    tenant_manager: TenantManager
    forum_manager: ForumManager
    system: System
    tool: Optional[Tool] = None
    deque_dict: dict = {}
    log:Optional[LogRound] = None
    save_log:bool = True
    
    class Config:
        arbitrary_types_allowed = True

    def __init__(self, rule,**kwargs):

        super().__init__(rule=rule, **kwargs)

    def line_up(self):
        self.deque_dict=self.rule.generate_deque(self)

    def broadcast(self):
        self.tenant_manager.broadcast(self.system)
        self.tenant_manager.broadcast_rule(self.rule) # 公布排队规则

    def reset(self) -> None:
        """Reset the environment"""
        self.deque_dict.clear()
        self.rule.reset(self)
        self.tenant_manager.reset()
        self.system.reset()
        self.cnt_turn = 0

    def is_done(self) -> bool:
        """Check if the environment is done"""
        self.log.step()
        if (self.save_log):
            self.log.save_data() # 每一步的log
            
        cur,fur = self.system.community_manager.split(self.system.community_manager.get_available_community_info())
        self.cnt_turn += 1
        
        if self.cnt_turn > self.max_turns:
            if(self.save_log): # 整体系统的log，仅在退出时save
                self.system.save_data()
                self.forum_manager.save_data()
            return True
        elif (cur==[] and fur==[] ) or self.rule.are_all_deques_empty(self):
            if(self.save_log):
                self.system.save_data()
                self.forum_manager.save_data()
            return True
        else:
            return False
        

    #test 测试用 要改
    def communication(self, communication_num = 3):
        tenant_ids = list(self.tenant_manager.data.keys())
        
        c_num = 0
        while (len(tenant_ids) > 0 and c_num < communication_num):
            tenant_id = tenant_ids[0]
            tenant_ids.pop(0)
            tenant = self.tenant_manager.data[tenant_id]
            if isinstance(tenant, LangchainTenant):
                continue_communication = asyncio.run(tenant.async_communication(self.forum_manager, 
                                                                                self.system,
                                                                                self.rule,
                                                                                self.log,
                                                                                c_num))
                receiver_ids = self.update_social_net(tenant=tenant) # 先把receiver放进communication队列
                for r_id in receiver_ids:
                    if (r_id) not in tenant_ids:
                        tenant_ids.append(r_id)
                if (continue_communication): tenant_ids.append(tenant_id)
            else:
                raise NotImplementedError("Tenant type {} not implemented".format(tenant.__class__))
            
            c_num += 1 
        self.set_tenant_memory_log() ## log
            
        

    def step(self):
        tenant_list = self.rule.get_next_agent_idx(self)
        for tenant in tenant_list:
            tenant_id = tenant.id
            if isinstance(tenant, LangchainTenant):
                choose_state= tenant.choose_process(self.forum_manager, self.system, self.rule,self.tool, self.log)
            elif isinstance(tenant,BaseMultiPromptTenant):
                choose_state = tenant.choose(self.forum_manager, self.system, self.log)
            else:
                raise NotImplementedError("Tenant type {} not implemented".format(tenant.__class__))
            if not choose_state and tenant.available==True:
                self.rule.requeue(self,tenant)
                
            self.log.set_one_tenant_choose_process(tenant_id)
            self.update_social_net(tenant=tenant)

        if (self.cnt_turn + 1) %5==0:
            self.system.community_manager.publish_community()

    
    def group(self):
        tenant_groups = {}
        for tenant_id,tenant in self.tenant_manager.data.items():
            group_id = tenant.group(self.forum_manager, self.system, self.rule,self.tool, self.log)
            self.log.set_group_log(tenant_id)
            if group_id in tenant_groups.keys():
                tenant_groups[group_id].append(tenant_id)
            else:
                tenant_groups[group_id] = [tenant_id]
        self.tenant_manager.groups = tenant_groups
       
    
    def update_social_net(self,tenant):
        assert isinstance(tenant,LangchainTenant)
        post_messages = tenant.post_messages()
        if len(post_messages)>0:
            return self.rule.post_messages(post_messages=post_messages,
                                tenant_manager=self.tenant_manager)
        else:
            return []
        

    def set_tenant_memory_log(self):
        log_memory={}
        for tenant_id,tenant in self.tenant_manager.data.items():
            assert isinstance(tenant,LangchainTenant)
            memory_temp=copy.deepcopy(tenant.memory)
            memory_tenant = {
                            #  "received_messages":memory_temp.received_messages.get("social_network",""),
                            #  "received_summarys":memory_temp.received_summarys,
                            #  "post_message_buffer":memory_temp.post_message_buffer,
                             "mail":memory_temp.mail,
                             "social_network":memory_temp.social_network,
                             }
            
            keys_message = ["timestamp",
                    "content",
                    "output_keys",
                    "sender",
                    "receivers",
                    "conver_num",
                    "context",
                    "continue_dialogue"]
            for k,v in memory_tenant.items():
                if k=="mail":
                    v=[
                        { 
                        self.tenant_manager[list(v_.sender.keys())[0]].name : \
                        str(v_.content["output"]) for v_ in v
                        }
                        ]
                elif k == "social_network":
                    for t_id, t_infos in v.items():
                        dialogue_transfered = []
                        for dialogue in t_infos.get("dialogues",[]):
                            dialogue_dict = {}
                            for key in keys_message:
                                dialogue_dict[key] = getattr(dialogue,key)
                            dialogue_transfered.append(dialogue_dict)
                        t_infos["dialogues"] = dialogue_transfered
                        
                elif k == "post_message_buffer":
                    dialogue_transfered = []
                    for dialogue in v:
                        dialogue_dict = {}
                        for key in keys_message:
                            dialogue_dict[key] = getattr(dialogue,key)
                        dialogue_transfered.append(dialogue_dict)
                    v = dialogue_transfered
                    
                    
                elif isinstance(v,list):
                    v=[str(v_) for v_ in v]
                elif isinstance(v,dict):
                    for m_k,m_v in v.items():
                      if isinstance(m_v,list):
                        m_v=[str(m_v_) for m_v_ in m_v]  
                        v[m_k]=m_v
                else:
                    v=str(v)
                memory_tenant[k]=v
            memory_tenant["name"] = tenant.name        
            log_memory[tenant_id] = memory_tenant
        self.log.set_social_network_mem(social_network_mem=log_memory)






