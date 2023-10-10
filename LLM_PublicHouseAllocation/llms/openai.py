from . import api_registry

from pydantic import BaseModel
from typing import List
from langchain.chat_models import ChatOpenAI
from langchain.llms import OpenAI
import copy 
class OpenAILoader(BaseModel):
    serial_api:str=""
    parallel_apis:List[dict]=[]
    
    
    llm_configs :dict            
    def __init__(self, 
                 tenant_llm_configs,
                 communication_llm_configs,
                 **kargs
                 ):
        llm_configs={
        "tenant":tenant_llm_configs,
        "memory":communication_llm_configs
    }   
        parallel_apis = kargs.pop("parallel_apis")
        p_apis = []
        for api in parallel_apis:
            p_apis.append({
                "api":api,
                "used_time":0
            })
        
        super().__init__(llm_configs = llm_configs,
                         parallel_apis = p_apis,
                         **kargs)
            
    
    def get_llm(self,
                api,
                type_config = "tenant"):
        llm_config = copy.deepcopy(self.llm_configs[type_config])
        llm_type = llm_config.pop('llm_type', 'text-davinci-003')
        if llm_type == 'gpt-3.5-turbo':
            return ChatOpenAI(**llm_config,openai_api_key=api)
        elif llm_type == 'text-davinci-003':
            return OpenAI(**llm_config,openai_api_key=api)
        elif llm_type == 'gpt-3.5-turbo-16k-0613':
            return OpenAI(**llm_config,openai_api_key=api)        
        else:
            raise NotImplementedError("LLM type {} not implemented".format(llm_type))

    
    def get_step_llm(self):
        return self.get_llm(self.serial_api,"tenant")
    
    def get_memory_llm(self):
        api = self.get_parallel_api()
        return self.get_llm(api,"memory")
    
    def get_communication_llm(self):
        api = self.get_parallel_api()
        return self.get_llm(api,"tenant")
                
    def get_parallel_api(self):
        self.parallel_apis.sort(key = lambda item:item["used_time"])
        api_info = self.parallel_apis[0]
        api_info["used_time"] +=1
        return api_info["api"] # 这里不在意是否available