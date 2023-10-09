from langchain.llms import OpenAI   
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from pydantic import BaseModel
from LLM_PublicHouseAllocation.manager import TenantManager,HouseManager
from LLM_PublicHouseAllocation.involvers import System
class Global_Score(BaseModel):
    tenant_manager:TenantManager
    system:System
    save_dir:str
    result:dict={}
    llm:LLMChain
    @classmethod
    def initialization(
        cls,
        tenant_manager:TenantManager,
        system:System,
        save_dir:str
    ):
        llm = OpenAI(temperature=0.9)
        template="""
        {role_description}
        """  
        input_variables=[""]
        prompt = PromptTemplate(  
            input_variables=input_variables,  
            template=template,  
        )
        chain = LLMChain(llm=llm, prompt=prompt)

        return cls(
            tenant_manager=tenant_manager,
            system=system,
            save_dir=save_dir,
            result={},
            llm=chain
        )
    def 
    def get_house_info_description(self,):
        return tenant.get_role_description()
    def parse():
        
    def score():
        
