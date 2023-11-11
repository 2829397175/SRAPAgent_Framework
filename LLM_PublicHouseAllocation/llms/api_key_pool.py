import asyncio
import json
import copy
from langchain.chat_models import ChatOpenAI
from langchain.llms import OpenAI
from LLM_PublicHouseAllocation.tenant.langchain_tenant import LangChain_tenant

from LLM_PublicHouseAllocation.initialization import load_llm
from pydantic import BaseModel
class APIKeyPool(BaseModel):
    
    available_keys: set = ()
    in_use_keys: set = ()    
    llm_data_path:str = "LLM_PublicHouseAllocation/llms/api.json"
    
    
    def __init__(self,
                 llm_data_path = "LLM_PublicHouseAllocation/llms/api.json"):
        
        with open(llm_data_path,'r',encoding = 'utf-8') as f:
            keys=json.load(f)

        super().__init__(
            available_keys = set(keys),
            in_use_keys = ()    ,
            llm_data_path = llm_data_path
        )
        
    def save_apis(self):
        apis = [*self.available_keys,*self.in_use_keys]
        with open(self.llm_data_path,'w',encoding = 'utf-8') as f:
            json.dump(apis, f, indent=4,separators=(',', ':'),ensure_ascii=False)
        # 有必要做临界资源处理吗?实际上同时用一个api是被允许的行为.
    
    def get_llm(self,
                tenant=None,
                self_llm_configs = {},
                memory_llm_configs = {}):
        """_summary_

        Args:
            tenant (_type_): _description_

        Returns:
            _type_: _description_
        """
        # 临界资源版本 P 操作
        # if tenant.memory.llm==None or tenant.llm==None:
            # async with self.condition:
            #     while not self.available_keys:
            #         await self.condition.wait()
            #     key = self.available_keys.pop()
            #     self.in_use_keys.add(key)
            #     memory_llm=self.get_llm(key)
            #     llm=self.get_llm(key)
            #     tenant.reset_memory_llm(memory_llm)
            #     tenant.reset_llm(llm)
                
            # return tenant
            
        if len(self.available_keys) == 0:
            self.available_keys = self.in_use_keys
            self.in_use_keys = set()
            
        if len(self.available_keys) == 0:
            self.save_apis()
            raise Exception("No valid OPENAI_API_KEY !!!")
        
        key = self.available_keys.pop()
        self.in_use_keys.add(key)
        
        if tenant is not None:
            memory_llm_configs = tenant.llm_config["memory"]
            self_llm_configs = tenant.llm_config["self"] 
        return self.llm(key,**memory_llm_configs),self.llm(key,**self_llm_configs) # memory + self
    
    
    
    def get_llm_single(self,llm_configs):

        if len(self.available_keys) == 0:
            self.available_keys = self.in_use_keys
            self.in_use_keys = set()
            
        if len(self.available_keys) == 0:
            self.save_apis()
            raise Exception("No valid OPENAI_API_KEY !!!")
            
        key = self.available_keys.pop()
        self.in_use_keys.add(key)
        return self.llm(key,**llm_configs)

    def release_llm(self, tenant=None):
        # 临界资源版本 V 操作
        # async with self.condition:
        #     key=tenant.llm.openai_api_key
        #     # tenant.llm=None
        #     # tenant.memory.llm=None
        #     self.in_use_keys.remove(key)
        #     self.available_keys.add(key)
        #     self.condition.notify_all()
        # return tenant
        
        
        # 这里释放最先被使用的key，不一定是tenant的api key（概率上来说很可能是）
        if len(self.in_use_keys)>0:
            key = self.in_use_keys.pop()
            self.available_keys.add(key)
            
            
    def invalid(self,
                api_key):
        print(f"{api_key} expires!!")
        if api_key in self.available_keys:
            self.available_keys.remove(api_key)
        if api_key in self.in_use_keys:
            self.in_use_keys.remove(api_key)
        print(f"{api_key} removed from pool!!")
            
    def llm(self,
            api,
            **llm_config,
            ):
        # 这里少了config文件中的设置，需要修改，
        # 用 sk-UduOWZ3yEtC9mFxy52397cB469884a288f6dC565Fd33377d 封装的方法写
        # return OpenAI(openai_api_key=api,verbose=False,temperature=0.8)
        llm_config["openai_api_key"] = api
        return load_llm(**llm_config)

    
