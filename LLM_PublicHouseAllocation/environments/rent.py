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
    communication_num :int = 10
    
    # 对于api调换的Loader类
    llm_loader: APIKeyPool

    # rating benchmark
    global_score: Global_Score
    
    class Config:
        arbitrary_types_allowed = True

    def __init__(self, rule,**kwargs):

        super().__init__(rule=rule, **kwargs)

    def line_up(self):
        self.deque_dict=self.rule.generate_deque(self)
        
    def load_log(self,result_dir):
        self.log = LogRound.load_from_json(os.path.join(result_dir,
                                             "tenental_system.json"))
        self.log.evaluation_matrix(self.global_score,self.system)
        print("finished matrix calculation!")
        
    def patch_houses(self):
        
        self.system.community_manager.patch_houses(self.tenant_manager,
                                                   self.system.house_manager,
                                                   self.cnt_turn)
        
    def reset(self) -> None:
        """Reset the environment"""
        self.deque_dict.clear()
        self.rule.reset(self)
        self.tenant_manager.reset()
        self.system.reset()
        self.cnt_turn = 0

    def is_done(self) -> bool:
        """Check if the environment is done"""
        
        add_tenant_ids = self.tenant_manager.add_tenants(self.cnt_turn,
                                        self.system,
                                        self.rule)
        if add_tenant_ids != []:
            tenant_groups = self.group(add_tenant_ids) # tenant->group(tenants)
            
            self.group_update(tenant_groups)
        
            self.line_up()
            
        self.patch_houses() # houses -> group(houses) 
        
        self.system.community_manager.publish_house(self.cnt_turn)
        
        # self.rule.order.enter_waitlist(self)
        if (self.save_log):
            self.log.save_data() # 每一步的log

        self.cnt_turn += 1
        self.log.step(round_id = self.cnt_turn)
        
        if self.cnt_turn > self.max_turns or \
            self.rule.are_all_deques_empty(self) or \
            (self.system.available_house_num() <= 0 and self.system.unreleased_house_num(self.cnt_turn)<= 0):
            if(self.save_log): # 整体系统的log，仅在退出时save
                self.log.evaluation_matrix(self.global_score,
                            self.system)

                self.system.save_data()
                self.forum_manager.save_data()


                #self.log.evaluation_matrix(self.tenant_manager)
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
    def communication(self, 
                      tenant_ids):
             
        communication_num = self.communication_num
        c_num = 0
        while(len(tenant_ids) > 0 and c_num < communication_num):
            async def run_parallel(tenant_ids):
                return_ids_list = await asyncio.gather(*[self.communication_one(tenant_id,c_num) for c_num,tenant_id in enumerate(tenant_ids)])
                return return_ids_list
            
            remain_num = communication_num - c_num
            if remain_num < len(tenant_ids):
                import random
                tenant_ids = random.sample(tenant_ids,remain_num)
                
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
    
    
    def clear_tenant(self,tenant:LangchainTenant):
        for group_id,groups in self.tenant_manager.groups.items():
            if tenant.id in groups:
                groups.remove(tenant.id)
                break
        for queue_name,queues in self.deque_dict.items():
            for queue_k,queue_v in queues.items():
                if tenant.id in queue_v:
                    queue_v.remove(tenant.id)
                    break
        # del self.tenant_manager.data[tenant.id]
        
        
        
    
    async def tenant_step(self,
                          tenant):
        # if not tenant.available:
        #     return 
        m_llm, llm = self.llm_loader.get_llm(tenant)
        tenant.reset_memory_llm(m_llm)
        tenant.reset_llm(llm)
        
        
        if isinstance(tenant, LangchainTenant):
            choose_state = await tenant.choose_process(self.forum_manager, self.system, self.rule,self.tool)
        elif isinstance(tenant,BaseMultiPromptTenant):
            choose_state = tenant.choose(self.forum_manager, self.system)
        else:
            raise NotImplementedError("Tenant type {} not implemented".format(tenant.__class__))
        
        self.llm_loader.release_llm(tenant)

        self.log.set_one_tenant_choose_process(tenant.id, tenant.log_round_tenant)
        self.update_social_net(tenant=tenant)
        
        tenant.update_times(choose_state)
        if not choose_state: # 不判断是否available
            self.rule.requeue(self,tenant)
        else: # 清空tenant 所在的队列
            self.clear_tenant(tenant)
            
            


    
    
    def step(self,tenant_waitlists):
        """step process for tenant: choose house

        Args:
            tenant_waitlists (dict): queue_name:list[tenant_ids]
        """
        
        pool_num_dict = self.system.community_manager.get_pool_num() 
        
        while not all(len(waitlist)==0 for waitlist in tenant_waitlists.values()) :
            # change tenant api
            first_tenant_ids = []
            for queue_name, waitlist in tenant_waitlists.items():
                if pool_num_dict.get(queue_name,0)==0:
                    for tenant_id in waitlist:
                        self.rule.requeue(self,self.tenant_manager[tenant_id])
                    continue # 如果当前queue_name 队列中，没有可以选择的房子，直接requeue
                
                if len(waitlist) > 0:
                    first_tenant_ids.append(waitlist.pop(0))
            
            async def run_parallel(first_tenant_ids):
                if len(first_tenant_ids) ==0:
                    return
                await asyncio.gather(*[self.tenant_step(self.tenant_manager[tenant_id]) for tenant_id in first_tenant_ids])
                
            if len(first_tenant_ids)==0:
                return
            asyncio.run(run_parallel(first_tenant_ids))
            
                
                
    
    def group(self,tenant_ids :list = []): # 需要group的tenant_ids
        """group tenants: set tenant_manager.groups

        Args:
            priority (bool, optional): True: the tenants who has priority item, 
            will be put front in the queue. Defaults to False.

        Returns:
            None
        """
        tenant_groups = {}
        
        async def tenant_group_id(tenant_ids,
                                  tenant_manager,
                                  forum_manager,
                                  system,
                                  rule,
                                  tool,
                                  log):
            
            group_ids = await asyncio.gather(*[tenant_manager[tenant_id].group(tenant_manager,forum_manager, system, rule, tool, tenant_ids) for \
                tenant_id in tenant_ids])

            for tenant_id in tenant_ids:
                log.set_group_log(tenant_manager[tenant_id],\
                    tenant_manager[tenant_id].log_round_tenant,
                    )
            return group_ids
        
   
      
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
                
            # self.tenant_manager[tenant_ids[idx]].queue_name = return_group_id  
            

        return tenant_groups # group_id:[queue of tenant ids]
                  
        
    
    def group_update(self,
                     tenant_groups):
        
        # update init group
        groups = {}
        
        for group_id, queues in self.deque_dict.items():
            groups[group_id] = [*queues["waitlist"],*queues["queue"]]
        
        
        if "default" in tenant_groups.keys() and \
            self.tenant_manager.policy.group_policy.type in ["house_type"] \
            and len(tenant_groups) > 1: 
            # 如果通过house_type进行tenant分组, 需要将default分组中的tenant重新random分配
            import random    
            default_tenant_ids = tenant_groups.get("default",[])
            for default_tenant_id in default_tenant_ids:
                random_group_id = random.sample(list(tenant_groups.keys()),1)[0]
                tenant_groups[random_group_id].append(default_tenant_id)
            del tenant_groups["default"]
        
        
        tenant_groups = self.tenant_manager.policy.group_policy.sort_tenant_groups(tenant_groups=tenant_groups,
                                                                                   tenant_manager=self.tenant_manager)
                
            
                
        for key,tenant_ids in tenant_groups.items():
            self.tenant_manager.groups[key]=[*groups.get(key,[]),
                                             *tenant_ids]
        
        
        
    
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
                    v = self.filter_memory_tenant_social_network(v,
                                                                 keys_message)
                        
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


    def filter_memory_tenant_social_network(self,
                                            memory_tenant_sn,
                                            keys_message):
        for t_id, t_infos in memory_tenant_sn.items():
            dialogue_transfered = []
            for dialogue in t_infos.get("dialogues",[]):
                dialogue_dict = {}
                for key in keys_message:
                    dialogue_dict[key] = getattr(dialogue,key)
                
                processed = False
                for idx_t,dialogue_buffer_one in enumerate(dialogue_transfered):
                    dialogue_buffer_one_context = dialogue_buffer_one["context"]
                    same = True
                    ## 检查新的dialogue更少的情况，直接不用处理
                    if len(dialogue_dict["context"])<=len(dialogue_buffer_one_context):
                        for idx in range(len(dialogue_dict["context"])):
                            if dialogue_dict["context"][idx] != dialogue_buffer_one_context[idx]:
                                same = False
                                break
                        if same:
                            processed = True
                            break
                    else:
                        for idx in range(len(dialogue_buffer_one_context)):
                            if dialogue_dict["context"][idx] != dialogue_buffer_one_context[idx]:
                                same = False
                                break
                        if same:
                            dialogue_transfered[idx_t] = dialogue_dict
                            processed = True
                            break
                    
                if not processed:
                    dialogue_transfered.append(dialogue_dict)
                    
            t_infos["dialogues"] = dialogue_transfered
        return memory_tenant_sn

    def calculate_max_utility(self):
        self.global_score.calculate_max_utility()