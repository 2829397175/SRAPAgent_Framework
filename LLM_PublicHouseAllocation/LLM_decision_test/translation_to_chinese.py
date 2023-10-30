import os
import json
import numpy as np
from langchain.llms import OpenAI   
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import json
from pydantic import BaseModel
os.environ["OPENAI_API_KEY"]= "sk-YZyToq4keshPgAw8vUqtT3BlbkFJ1Zwdp6NdxzbtcksjMBw"
api_base = os.environ.get("OPENAI API_BASE""https://api.openai.com/v1")
api_type = os.environ.get("OPENAI API_TYPE","open_ ai")
class Translate(BaseModel):
    data_path:str="LLM_PublicHouseAllocation/LLM_decision_test/data/unfinished_QA_result.json"
    save_path:str="LLM_PublicHouseAllocation/LLM_decision_test/data/Chinese_unfinished_QA_result.json"
    tenant_path:str="LLM_PublicHouseAllocation/LLM_decision_test/social_network/tenant.json"
    datas:list=[]
    llm:OpenAI=OpenAI(model="text-davinci-003",verbose=False,temperature=1)
    def read_data(self):
        assert os.path.exists(self.data_path),"no such file path: {}".format(self.data_path)
        with open(self.data_path,'r',encoding = 'utf-8') as f:
            self.datas = json.load(f)
    

    def translate_to_chinese(self,english_text):
    
        template="""
            {english_text}
            
            中文：
        """  
        input_variables=["english_text"]
        prompt = PromptTemplate(  
            input_variables=input_variables,  
            template=template,  
        )
        chain = LLMChain(llm=self.llm, prompt=prompt)
        chinese_text=chain.run(input)
        return chinese_text
    
    def translate_judge(self):
        for data in self.datas:
            for value in data.values():
                if isinstance(value,dict):
                    for content in value.values():
                        content=self.translate_to_chinese(content)
            
                    

    def save_data(self):
        with open(self.save_path, 'w', encoding='utf-8') as file:
            json.dump(self.datas, file, indent=4,separators=(',', ':'),ensure_ascii=False)

    
    def run_judge(self):
        self.read_data()
        self.translate_judge()
        self.save_data()
        
    def translate_sn_tenant_information(self):
        assert os.path.exists(self.tenant_path),"no such file path: {}".format(self.tenant_path)
        with open(self.tenant_path,'r',encoding = 'utf-8') as f:
            tenant_data = json.load(f)
        for tenant_id,tenant_infos in tenant_data.items():
            if "concise_role_description" not in tenant_infos:
                role_description_template="""\
                You are {name}. You earn {monthly_income} per month.\
                Your family members include: {family_members}."""
                concise_role_description = role_description_template.format_map({"name":tenant_infos["name"],
                                            **tenant_infos}
                                        )
                if tenant_infos.get("personal_preference",False):
                        concise_role_description += "Up to now, your personal preference for house is :{}".format(
                            tenant_infos.get("personal_preference")
                        )
                tenant_infos['concise_role_description']=concise_role_description    
            if "social_network_str" not in tenant_infos:
                social_network = ["{name}: {relation}".format(
                name = neigh_tenant_info.get("name",neigh_tenant_id),
                relation = neigh_tenant_info.get("relation","friend")
                )
                    for neigh_tenant_id,neigh_tenant_info
                    in tenant_infos.get("social_network",{}).items()] 
    
                social_network_str = "\n".join(social_network)
        
                tenant_infos['social_network_str']=social_network_str
                
        with open(self.tenant_path,"w", encoding='utf-8') as file:
            json.dump(tenant_data, file, indent=4,separators=(',', ':'),ensure_ascii=False)
  
                        

                    
    

if __name__ == "__main__":
    translator=Translate()
    #translator.run()
    translator.translate_sn_tenant_information