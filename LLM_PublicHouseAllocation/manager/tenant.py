import json
import os

from LLM_PublicHouseAllocation.tenant.multiprompt_tenant import CAHTTenant
from LLM_PublicHouseAllocation.tenant.langchain_tenant import LangchainTenant
from LLM_PublicHouseAllocation.output_parser import output_parser_registry
from . import manager_registry as ManagerRgistry
from .base import BaseManager
from LLM_PublicHouseAllocation.prompt.chat_prompt import chat_prompt_registry
from LLM_PublicHouseAllocation.message import Message
from LLM_PublicHouseAllocation.initialization import load_llm,load_prompt,load_memory,load_agentrule

@ManagerRgistry.register("tenant")
class TenantManager(BaseManager):
    """
    manager of tenants.
    
    Args:
        tenants: list[Tenant]
    """

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
        tenants = {}
        if base_config.get("type_tenant") == "LangchainTenant":
            llm_base = load_llm(base_config.pop('llm'))
            memory_config = base_config.pop('memory')
            max_choose = base_config.pop('max_choose')

            # default setting
            output_parser_base = output_parser_registry.build('choose')
            prompt_base = chat_prompt_registry.build('choose')


            for tenant_id, tenant_config in tenant_configs.items():
                friends=tenant_config.get("friends",{})
                for neigh_tenant_id,neigh_tenant_info in friends.items():
                    if neigh_tenant_id in tenant_configs.keys():
                        neigh_tenant_info["name"] = tenant_configs[neigh_tenant_id].get("name",tenant_id)
                
                tenant = LangchainTenant.from_llm_and_tools(name=tenant_config.get("name",tenant_id),
                                                            id=tenant_id,
                                                            infos=tenant_config,
                                                            memory_config=memory_config,
                                                            llm=llm_base,
                                                            prompt=prompt_base,
                                                            output_parser=output_parser_base,
                                                            max_choose=max_choose,
                                                            rule=base_config["agent_rule"],
                                                            work_place=tenant_config.get("work_place",""),
                                                            friends=friends
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
                    You are {name}.You live with {family_members}. You earn {monthly_income} per month.\
                    You are {age} years old. Your job is {profession}. \
                    Your company is located in {en_work_place}. \
                    {special_request} \
                    You expect to rent a house for {monthly_rent_budget}.
                """
            id = 0
            agentrule = load_agentrule(base_config.pop("agent_rule"))
            for tenant_name,tenant_config in tenant_configs.items():
                role_description = role_description_template.format(name=tenant_name,
                                                                    family_members=tenant_config["family_members"],
                                                                    monthly_income=tenant_config["monthly_income"],
                                                                    age=tenant_config["age"],
                                                                    profession=tenant_config["profession"],
                                                                    en_work_place=tenant_config["en_work_place"],
                                                                    special_request=tenant_config["special_request"],
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

        return cls(
            data=tenants,
            data_type="tenants",
            save_dir=kwargs["save_dir"]
        )

        
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
            json.dump(self.record, file, indent=4,separators=(',', ':'),ensure_ascii=False)

    def broadcast(self,system):
        
        broadcast_template = """You are in rent system. Choosing one house needs the following steps:\
1.choose community 2.choose type of house 3.choose house
{community_info}"""
        community_info = system.get_community_abstract()
        #待改，等community_manager接口
        broadcast_str = broadcast_template.format(community_info=community_info) 
        broadcast_message = Message(message_type = "community",
                        content = broadcast_str,
                        sender = {"system":"system"}
                    ) # 暂时视作小区类信息        
        for tenant in self.data.values():
            assert isinstance(tenant,LangchainTenant)

            tenant.memory.add_message([broadcast_message]) # 不发送，在自己的行为队列