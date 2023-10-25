import asyncio
import logging
from typing import List, Deque, Optional
from LLM_PublicHouseAllocation.tenant.multiprompt_tenant import BaseMultiPromptTenant
from LLM_PublicHouseAllocation.tenant.langchain_tenant import LangchainTenant
import json
from LLM_PublicHouseAllocation.manager import TenantManager,ForumManager
from LLM_PublicHouseAllocation.involvers import System,Tool,Search_forum_topk,LogRound
from LLM_PublicHouseAllocation.llms import APIKeyPool
from LLM_PublicHouseAllocation.global_score import Global_Score

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
    log: Optional[LogRound] = None
    save_log:bool = True
    

    
    # 对于api调换的Loader类
    llm_loader:APIKeyPool
    
    
    # rating benchmark
    global_score: Global_Score
    
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
        self.system.community_manager.publish_house(self.cnt_turn)
        # self.rule.order.enter_waitlist(self)
        if (self.save_log):
            self.log.save_data() # 每一步的log

        self.cnt_turn += 1
        self.log.step(round_id = self.cnt_turn)
        
        if self.cnt_turn > self.max_turns:
            if(self.save_log): # 整体系统的log，仅在退出时save
                self.system.save_data()
                self.forum_manager.save_data()
                #self.log.evaluation_matrix(self.tenant_manager)
            return True
        elif  self.rule.are_all_deques_empty(self):
            if(self.save_log):
                self.system.save_data()
                self.forum_manager.save_data()
                #self.log.evaluation_matrix(self.tenant_manager,self.global_score,self.system)
            return True
        else:
            return False
        
    async def communication_one(self,tenant_id,c_num):
            """
            the async run parse of tenant(tenant_id) communication.
            return: the receivers, self(if continue_communication)
            """
            tenant = self.tenant_manager.data[tenant_id]
            
            if isinstance(tenant, LangchainTenant):
                m_llm,llm = self.llm_loader.get_llm(tenant)
                tenant.reset_memory_llm(m_llm)
                tenant.reset_llm(llm)
        
                continue_communication = await tenant.async_communication(self.forum_manager, 
                                                            self.system,
                                                            self.rule,
                                                            c_num)
                
                receiver_ids = self.update_social_net(tenant=tenant) # 先把receiver放进communication队列
                self.llm_loader.release_llm(tenant)
                
                return [receiver_ids,continue_communication]
            else:
                raise NotImplementedError("Tenant type {} not implemented".format(tenant.__class__))
            
    #test 测试用 要改
    def communication(self, communication_num = 3):
        tenant_ids = list(self.tenant_manager.data.keys())        
        c_num = 0
        while(len(tenant_ids) > 0 and c_num < communication_num):
            async def run_parallel(tenant_ids):
                return_ids_list = await asyncio.gather(*[self.communication_one(tenant_id,c_num) for c_num,tenant_id in enumerate(tenant_ids)])
                return return_ids_list
            
           
            return_ids_list = asyncio.run(run_parallel(tenant_ids=tenant_ids)) # 需要进行讨论的tenant
            c_num += len(tenant_ids)
            tenant_ids_temp = copy.deepcopy(tenant_ids)
            tenant_ids = []
            
            for idx,return_ids in enumerate(return_ids_list):
                receiver_ids = return_ids[0]
                continue_communication = return_ids[1]
                for receiver_id in receiver_ids:
                    if receiver_id not in tenant_ids:
                        tenant_ids.append(receiver_id)
                if continue_communication and tenant_ids_temp[idx] not in tenant_ids:
                    tenant_ids.append(tenant_ids_temp[idx])
                        
        self.set_tenant_memory_log() ## log
    
    async def tenant_step(self,
                          tenant):
        m_llm,llm = self.llm_loader.get_llm(tenant)
        tenant.reset_memory_llm(m_llm)
        tenant.reset_llm(llm)
        
        
        if isinstance(tenant, LangchainTenant):
            choose_state = await tenant.choose_process(self.forum_manager, self.system, self.rule,self.tool)
        elif isinstance(tenant,BaseMultiPromptTenant):
            choose_state = tenant.choose(self.forum_manager, self.system)
        else:
            raise NotImplementedError("Tenant type {} not implemented".format(tenant.__class__))
        
        self.llm_loader.release_llm(tenant)
        
        if not choose_state: # 不判断是否available
            self.rule.requeue(self,tenant)
        self.log.set_one_tenant_choose_process(tenant.id, tenant.log_round_tenant)
        self.update_social_net(tenant=tenant)

    
    
    def step(self):
        tenant_waitlists = self.rule.get_next_agent_idx(self)
                    
        while not all(len(waitlist)==0 for waitlist in tenant_waitlists):
            # change tenant api
            first_tenant_ids = []
            for waitlist in tenant_waitlists:
                if len(waitlist) > 0:
                    first_tenant_ids.append(waitlist.pop(0))
            
            async def run_parallel(first_tenant_ids):
                await asyncio.gather(*[self.tenant_step(self.tenant_manager[tenant_id]) for tenant_id in first_tenant_ids])
                
                
            asyncio.run(run_parallel(first_tenant_ids))
            
                
                
    
    def group(self):
        
        tenant_groups = {}
        
        async def tenant_group_id(tenant_ids,
                                  tenant_manager,
                                  forum_manager,
                                  system,
                                  rule,
                                  tool,
                                  log):
            
            group_ids = await asyncio.gather(*[tenant_manager[tenant_id].group(forum_manager, system, rule, tool) for \
                tenant_id in tenant_ids])

            for tenant_id in tenant_ids:
                log.set_group_log(tenant_id,\
                    tenant_manager[tenant_id].log_round_tenant)
            return group_ids
        
        tenant_ids = list(self.tenant_manager.data.keys())
      
        return_group_ids = asyncio.run(tenant_group_id(tenant_ids,
                                                        self.tenant_manager,
                                                        self.forum_manager,
                                                        self.system,
                                                        self.rule,
                                                        self.tool,
                                                       self.log))
        
        for idx, return_group_id in enumerate(return_group_ids):
            if return_group_id not in tenant_groups.keys():
                tenant_groups[return_group_id] = [tenant_ids[idx]]
            else:
                tenant_groups[return_group_id].append(tenant_ids[idx])
                
            self.tenant_manager[tenant_ids[idx]].queue_name = return_group_id  
            
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






