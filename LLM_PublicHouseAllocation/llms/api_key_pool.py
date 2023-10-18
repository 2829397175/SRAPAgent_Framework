import asyncio
import json
import copy
from langchain.chat_models import ChatOpenAI
from langchain.llms import OpenAI
from LLM_PublicHouseAllocation.tenant.langchain_tenant import LangChain_tenant
class APIKeyPool:
    def __init__(self,llm_config={}):
        with open("LLM_PublicHouseAllocation/llms/api.json",'r',encoding = 'utf-8') as f:
            keys=json.load(f)
        self.available_keys = set(keys)
        self.in_use_keys = set()
        self.condition = asyncio.Condition()
        self.llm_config=llm_config
    
    async def get_key(self,tenant):
        if tenant.memory.llm==None or tenant.llm==None:
            async with self.condition:
                while not self.available_keys:
                    await self.condition.wait()
                key = self.available_keys.pop()
                self.in_use_keys.add(key)
                tenant.memory.llm=self.get_llm(key)
                tenant.llm=self.get_llm(key)
            return tenant

    async def release_key(self, tenant):
        async with self.condition:
            key=tenant.llm.openai_api_key
            tenant.llm=None
            tenant.memory.llm=None
            self.in_use_keys.remove(key)
            self.available_keys.add(key)
            self.condition.notify_all()
        return tenant
            
    def get_llm(self,
                api
                ):
        return  OpenAI(openai_api_key=api,verbose=False,temperature=0.8)

    
