import os
os.environ["OPENAI_API_KEY"]= "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" 
api_base = os.environ.get("OPENAI API_BASE""https://api.openai.com/v1")
import json
import platform
import numpy as np
from langchain.llms import OpenAI   
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import json
from pydantic import BaseModel
import asyncio
from tqdm import tqdm

if platform.system()=='Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import unicodedata
def is_chinese(strs):
    for _char in strs:
        if '\u4e00' <= _char <= '\u9fa5':
            return True
    return False

class Translate(BaseModel):
    # data_dir:str = "LLM_PublicHouseAllocation\LLM_decision_test\qa_unclear_data"
    data_dir:str ="LLM_PublicHouseAllocation\LLM_decision_test\qa_translated\judge\error"
    save_dir:str = "LLM_PublicHouseAllocation\LLM_decision_test/qa_translated/judge"
    tenant_path:str = "LLM_PublicHouseAllocation\LLM_decision_test/social_network/tenant.json"
    social_network_dir :str ="LLM_PublicHouseAllocation\LLM_decision_test\social_network\data"
    
    datas:dict = {}
    llm:OpenAI=OpenAI(model_name = "text-davinci-003",
                      verbose = False,
                      temperature = 0.8,
                      openai_api_base=api_base)
    
    
    
    def read_data(self):
        assert os.path.exists(self.data_dir),"no such file path: {}".format(self.data_dir)
        
        files = os.listdir(self.data_dir)
        
        for file in files:
            file_path = os.path.join(self.data_dir,file)
            
            file_name = os.path.basename(file_path).split(".")[0]
            
            with open(file_path,'r',encoding = 'utf-8') as f:
                self.datas[file_name] = json.load(f)
    

    async def translate_to_chinese(self,english_text):
        template="""
            Transfer the following context into Simplified Chinese:
            {english_text}
            
            Here's your translation:
        """  
        input_variables=["english_text"]
        prompt = PromptTemplate(  
            input_variables=input_variables,  
            template=template,  
        )
        chain = LLMChain(llm=self.llm, prompt=prompt)
        chinese_text = await chain.arun(english_text=english_text)
        return chinese_text.strip()
    
    async def translate_judge(self):
        pbar_size = sum([len(value) for value in self.datas.values()])
        
        pbar=tqdm(range(pbar_size), ncols=100) 
        for judge_type,judge_data_list in self.datas.items():
            
            async def translate_one_type(judge_data_list):
                for judge_data in judge_data_list:
                    for judge_key, judge_sub_dict in judge_data.items():
                        for k, v in judge_sub_dict.items():
                            if not isinstance(v,str):
                                continue
                            
                            if is_chinese(v):
                                continue
                            
                            content = await self.translate_to_chinese(v)
                            judge_sub_dict[k] = content
                    pbar.update()
                        
            await asyncio.gather(*[translate_one_type(judge_data_list) for judge_type,judge_data_list \
                in self.datas.items()])

                    

    def save_data(self,error = False):
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        for judge_type, data in self.datas.items():
            if (error):
                save_dir = os.path.join(self.save_dir,"error")
            else:
                save_dir = os.path.join(self.save_dir,"finished")
                
            save_path = os.path.join(save_dir,judge_type+".json")
                
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
                
            with open(save_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4,separators=(',', ':'),ensure_ascii=False)

    
    def run_judge(self):
        
        self.read_data()
        
        try:
            asyncio.run(self.translate_judge())            
            self.save_data()
        except Exception as e:
            self.save_data(True)
            print(e)
        
        
    def run_tranlsate_tenant(self):
        
        asyncio.run(self.translate_sn_tenant_information())
    
    async def translate_sn_tenant_information(self):
        assert os.path.exists(self.tenant_path),"no such file path: {}".format(self.tenant_path)
        with open(self.tenant_path,'r',encoding = 'utf-8') as f:
            tenant_data = json.load(f)
            
        pbar_size = len(tenant_data.values())
        
        pbar = tqdm(range(pbar_size), ncols=100) 
        
        async def translate_one_tenant(tenant_infos):
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
                        
                if not is_chinese(concise_role_description):
                    
                    concise_role_description = await self.translate_to_chinese(concise_role_description)
                tenant_infos['concise_role_description']=concise_role_description    
            if "social_network_str" not in tenant_infos:
                social_network = ["{name}: {relation}".format(
                name = neigh_tenant_info.get("name",neigh_tenant_id),
                relation = neigh_tenant_info.get("relation","friend")
                )
                    for neigh_tenant_id,neigh_tenant_info
                    in tenant_infos.get("social_network",{}).items()] 
    
                social_network_str = "\n".join(social_network)
                if not is_chinese(social_network_str):
                    social_network_str = await self.translate_to_chinese(social_network_str)
                tenant_infos['social_network_str']=social_network_str
            pbar.update()
        try:
            await asyncio.gather(*[translate_one_tenant(tenant_infos) for tenant_id,tenant_infos in tenant_data.items()])
            with open(self.tenant_path,"w", encoding='utf-8') as file:
                json.dump(tenant_data, file, indent=4,separators=(',', ':'),ensure_ascii=False)
        except Exception as e:
            with open(self.tenant_path,"w", encoding='utf-8') as file:
                json.dump(tenant_data, file, indent=4,separators=(',', ':'),ensure_ascii=False)
            print(e)
  
    def run_social_network(self):
        asyncio.run(self.translate_social_network_context())
                        
    async def translate_social_network_context(self):
        social_network_datas = {}
        assert os.path.exists(self.social_network_dir)
        files = os.listdir(self.social_network_dir)
        for file in files:
            file_path = os.path.join(self.social_network_dir,file)
            
            file_name = os.path.basename(file_path).split(".")[0]
            
            with open(file_path,'r',encoding = 'utf-8') as f:
                social_network_datas[file_name] = json.load(f)
                
        pbar_size = len(social_network_datas)
        pbar = tqdm(range(pbar_size), ncols=100) 
            
        async def translate_one_experiment(tenantal_system:dict):
            keys = list(tenantal_system.keys())
            remove_keys = ["group"]
            for remove_key in remove_keys:
                if remove_key in keys:
                    keys.remove(remove_key)
            
            for key in keys:
                if tenantal_system[key] =={}:
                    continue
                try:
                    sn_mem = tenantal_system[key]["log_social_network"]["social_network_mem"]
                    for tenant_id,tenant_sn in sn_mem.items():
                        for ac_id,ac_infos in tenant_sn.get("social_network",{}).items():
                            
                            for dialogue in ac_infos.get("dialogues",{}):
                                
                                if (list(dialogue.get("sender",{}).keys())[0] == tenant_id):
                                    """transfer context"""
                                    context_transfered = []
                                    for context_one in dialogue.get("context",[]):
                                        if not is_chinese(context_one):
                                            context_one = await self.translate_to_chinese(context_one)
                                        context_transfered.append(context_one)
                                    dialogue["context"] = context_transfered
                                    
                                    content = dialogue.get("content",{})
                                    for k,v in content.items():
                                        if isinstance(v,str):
                                            if not is_chinese(v):
                                                v = await self.translate_to_chinese(v)
                                            content[k] = v
                                            
                                    dialogue["content"] = content
                                
                except Exception as e:
                    print(e)
                
            pbar.update()
        
        
        try:
            await asyncio.gather(*[translate_one_experiment(tenantal_json) for tenantal_json in social_network_datas.values()])
            for tenantal_name, tenantal_json in social_network_datas.items():
                save_path = os.path.join(self.social_network_dir,tenantal_name+".json")
                with open(save_path,"w", encoding='utf-8') as file:
                    json.dump(tenantal_json, file, indent=4,separators=(',', ':'),ensure_ascii=False)

        except Exception as e:
            for tenantal_name, tenantal_json in social_network_datas.items():
                save_path = os.path.join(self.social_network_dir,tenantal_name+".json")
                with open(save_path,"w", encoding='utf-8') as file:
                    json.dump(tenantal_json, file, indent=4,separators=(',', ':'),ensure_ascii=False)
            
            print(e)
                    
    

if __name__ == "__main__":
    translator = Translate()
    translator.run_social_network()
    # translator.run_judge()
    # translator.run_tranlsate_tenant()
    