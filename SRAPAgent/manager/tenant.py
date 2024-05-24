import json
import os

from SARPAgent.tenant.multiprompt_tenant import CAHTTenant
from SARPAgent.tenant.langchain_tenant import LangchainTenant
from SARPAgent.tenant.langchain_tenant.tenant_log import Log_Round_Tenant

from SARPAgent.tenant.policy import policy_registry
from SARPAgent.tenant.policy.group_policy import group_registry
from SARPAgent.output_parser import output_parser_registry
from . import manager_registry as ManagerRgistry
from .base import BaseManager
from SARPAgent.prompt.chat_prompt import chat_prompt_registry
from SARPAgent.message import Message
from SARPAgent.initialization import load_llm,load_prompt,load_memory,load_agentrule
from SARPAgent.tenant.policy import BasePolicy
from SARPAgent.llms.api_key_pool import APIKeyPool
@ManagerRgistry.register("tenant")
class TenantManager(BaseManager):
    """
    manager of tenants.
    
    Args:
        tenants: list[Tenant]
    """
    total_tenant_datas:dict={}
    distribution_batch_data:dict={} 
    
    groups:dict = {} # group_id:[tenant_id]
    policy: BasePolicy # 每个tenant共享的政策
    llm_loader:APIKeyPool


    @classmethod
    def load_data(
            cls,
            data_dir: str,
            **kwargs
    ):
        """Construct list[tenant] from an LLM and tools."""
        assert os.path.exists(data_dir), "no such file path: {}".format(data_dir)
        with open(data_dir, 'r', encoding='utf-8') as f:
            tenant_configs = json.load(f)

        base_config = kwargs
        
        policy_kwargs = base_config.get("policy")
        
        group_policy_kwargs = policy_kwargs.pop("group_policy",{"type":"base",
                                                                "priority":False})
        if group_policy_kwargs["type"] == "portion":
            group_policy = group_registry.build(tenant_configs = tenant_configs,**group_policy_kwargs)
        else:
            group_policy = group_registry.build(**group_policy_kwargs)
        

        policy = policy_registry.build(group_policy=group_policy,
                                       **policy_kwargs)
        
        
        
        tenants = {}
        if base_config.get("type_tenant") == "LangchainTenant":
            
            memory_config = base_config.pop('memory')
            
            max_choose = base_config.pop('max_choose')
            choose_rating = base_config.pop('choose_rating',False)
            tenant_llm_config = base_config.pop('llm')
            
            # default setting
            output_parser_base = output_parser_registry.build('choose')
            prompt_base = chat_prompt_registry.build('choose')


            for tenant_id, tenant_config in tenant_configs.items():
                priority_item=tenant_config.get("priority_item",{})
                social_network=tenant_config.get("social_network",{})
                for neigh_tenant_id,neigh_tenant_info in social_network.items():
                    if neigh_tenant_id in tenant_configs.keys():
                        neigh_tenant_info["name"] = tenant_configs[neigh_tenant_id].get("name",tenant_id)
                memory_config.update({"social_network":social_network})
                
                
                memory_llm_configs = memory_config.pop("llm",tenant_llm_config)
                llm_loader = kwargs.get("llm_loader")
                memory_llm, llm_base = llm_loader.get_llm(
                    self_llm_configs = tenant_llm_config,
                    memory_llm_configs = memory_llm_configs)
                memory_config["memory_llm_configs"] = memory_llm_configs
                memory_config["llm_loader"] = llm_loader
                memory = load_memory(memory_config,memory_llm)
                
                tenant = LangchainTenant.from_llm_and_tools(name=tenant_config.get("name",tenant_id),
                                                            id=tenant_id,
                                                            infos=tenant_config,
                                                            memory = memory,
                                                            llm = llm_base,
                                                            llm_loader = llm_loader,
                                                            prompt=prompt_base,
                                                            output_parser=output_parser_base,
                                                            policy = policy,
                                                            max_choose=max_choose,
                                                            rule=base_config["agent_rule"],
                                                            work_place = tenant_config.get("work_place",""),
                                                            priority_item = priority_item,
                                                            family_num=tenant_config.get("family_members_num",0),
                                                            choose_rating = choose_rating,
                                                            llm_config={"self":tenant_llm_config,
                                                                        "memory":memory_llm_configs},
                                                            log_round_tenant=Log_Round_Tenant()
                                                            )
                tenants[tenant_id] = tenant

        if base_config.get("type_tenant") == "CAHTTenant":
            prompt = {}
            prompt_type = ['choose_community', 'choose_house', 'comment', 'forum','correct_choose_community','correct_choose_house']
            for prompt_name in prompt_type:
                prompt[prompt_name] = load_prompt(prompt_name)
            max_choose_time = base_config.pop('max_choose_time')
            llmname = base_config.pop('llm')
            memoryname = base_config.pop('memory')
            
            
            
            role_description_template = """\
                    You are {name}.You live with {family_members}.
                    You are {age} years old. Your job is {profession}. \
                    Your company is located in {en_work_place}. \
                    {special_request_poor} \
                    You expect to rent a house for {monthly_rent_budget}.
                    Your acceptable price beyond the rental budget is {acceptable_outrange}.\
                """
            id = 0
            agentrule = load_agentrule(base_config.pop("agent_rule"))
            for tenant_name,tenant_config in tenant_configs.items():
                
                monthly_income = tenant_config["monthly_income"] - tenant_config["monthly_rent_budget"] 
                role_description = role_description_template.format(name=tenant_name,
                                                                    family_members=tenant_config["family_members"],
                                                                    monthly_income=tenant_config["monthly_income"],
                                                                    age=tenant_config["age"],
                                                                    profession=tenant_config["profession"],
                                                                    en_work_place=tenant_config["en_work_place"],
                                                                    acceptable_outrange=int(monthly_income/100)*2,
                                                                    special_request_poor=tenant_config["special_request_poor"],
                                                                    monthly_rent_budget=tenant_config["monthly_rent_budget"],
                                                                    ).replace("\n","").strip()
                llm_base = load_llm(llmname)
                memory_base = load_memory(memoryname)
                tenant_agent = CAHTTenant(id=id,
                                          name=tenant_name,
                                          role_description=role_description,
                                          memory=memory_base,
                                          max_choose_time=max_choose_time,
                                          workplace=tenant_config["work_place"],
                                          llm=llm_base,
                                          prompt=prompt,
                                          agentrule=agentrule
                                          )

                tenants[id] = tenant_agent
                id += 1



        with open(os.path.join(kwargs["distribution_batch_dir"]),'r',encoding = 'utf-8') as f:
            distribution_batch_data = json.load(f)
        
        
        return cls(
            distribution_batch_data = distribution_batch_data,
            total_tenant_datas = tenants,
            data = {},
            data_type="tenants",
            save_dir=kwargs["save_dir"],
            policy = policy,
            llm_loader = llm_loader
        )
        
        
    def add_tenant_pool(self,
                        add_tenant_ids,
                        system,
                        rule):
        for tenant_id in add_tenant_ids:
            self.data[tenant_id] = self.total_tenant_datas[tenant_id]
            self.broadcast(system,tenant_id)
            self.broadcast_rule(rule,tenant_id)
        return add_tenant_ids
                   
                   
    def get_tenant_enter_turn(self,tenant):
        for turn, batch_tenant_ids in self.distribution_batch_data.items():
            if tenant.id in batch_tenant_ids:
                return turn
        
        raise Exception(f"This tenant {tenant.id} didn't enter system in the simulation experiment")
                   
    def add_tenants(self,cnt_turn,system,rule):
        if str(cnt_turn) in self.distribution_batch_data.keys():
            print("New tenants are added!")
            return self.add_tenant_pool(self.distribution_batch_data[str(cnt_turn)],
                                 system,
                                 rule)
        else:
            return []
           

        
    def available_tenant_num(self):
        num = 0
        for tenant_name, tenant in self.data.items():
            if tenant.available:
                num += 1
        return num
        
    def set_chosed(self,tenant_id):
        try:
            self.data[tenant_id].available = False
        except Exception as e:
            print("Fail to change choosing state in TenantManger!!")
        
    def reset(self):
        for tenant_name, tenant in self.data:
            tenant.reset()

    def save_data(self):
        # assert os.path.exists(self.save_dir), "no such file path: {}".format(self.save_dir)
        with open(self.save_dir, 'w') as file:
            json.dump(self.data, file, indent=4,separators=(',', ':'),ensure_ascii=False)

    def broadcast(self,system,tenant_id):
        
        broadcast_template = """You are in rent system. Choosing one house needs the following steps:
1.choose community 
2.choose type of house 
3.choose house
\n{community_info}"""
        community_info,community_ids = system.get_community_abstract(concise=True)
        #待改，等community_manager接口
        broadcast_str = broadcast_template.format(community_info=community_info) 
        broadcast_message = Message(message_type = "community",
                        content = broadcast_str,
                        sender = {"system":"system"},
                    ) # 暂时视作小区类信息        
        tenant = self.data[tenant_id]
        
        assert isinstance(tenant,LangchainTenant)
        tenant.memory.add_message([broadcast_message]) # 不发送，在自己的行为队列
            
    def broadcast_rule(self,
                       rule,
                       tenant_id):
        
        broadcast_template = """
You are in rent system. The queuing rules of this system is as follows:
{rule_order}
"""
        rule_description = rule.rule_description()
        #待改，等community_manager接口
        broadcast_str = broadcast_template.format(rule_order=rule_description) 
        broadcast_message = Message(message_type = "base",
                        content = broadcast_str,
                        sender = {"system":"system"}
                    ) # 暂时视作小区类信息        
        tenant = self.data[tenant_id]
        assert isinstance(tenant,LangchainTenant)
        tenant.memory.add_message([broadcast_message]) # 不发送，在自己的行为队列