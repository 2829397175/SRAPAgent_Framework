import os
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
from langchain.chat_models import ChatOpenAI
import http.client
import hashlib
import urllib
import random
import json
from hashlib import md5
import requests

import re

import time

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
    # data_dir:str ="LLM_PublicHouseAllocation\LLM_decision_test\qa_translated\judge\error"
    data_dir:str ="LLM_PublicHouseAllocation\LLM_decision_test\data\save"
    # save_dir:str = "LLM_PublicHouseAllocation\LLM_decision_test/qa_translated/judge"
    save_dir:str = "LLM_PublicHouseAllocation\LLM_decision_test\data\\translated"
    tenant_path:str = "LLM_PublicHouseAllocation\LLM_decision_test/social_network/tenant.json"
    # social_network_dir :str ="LLM_PublicHouseAllocation\LLM_decision_test\social_network\data"
    social_network_dir :str ="LLM_PublicHouseAllocation\LLM_decision_test\social_network\data\labeled_11_3"


    
    datas:dict = {}
    count_sn = 0
    # llm:OpenAI=OpenAI(model_name = "text-davinci-003",
    #                   verbose = False,
    #                   temperature = 0.8)
    
    # apis_a =["sk-H3ENZsWqvSKnlb88A329FeEbCb6745D7A6E25eA71287E95d",
    # "sk-1TSrETkbF3yOSFeo51E36d199dF04038B6900314Aa475b5e",
    # "sk-LJQomCIuhDuqTu0EA9C634F05a0646F99f743204BeE9B2B7",
    # "sk-fc1wKOWUqic07eWN8159EcA20f0c40299a8e2552F34d2e3a",
    # "sk-Hsyu43W1aJROiSTH3eAe26F219E24992B47b098b00E324A2",
    # "sk-dCzZFatXAVVSW067D1333fC17b8f4c5e95076f9bA113805c"  ]
    apis_a=["sk-n96DTK9y2MV9oS6m1eBc68E6C4Ab419b95F68f91F8A4C6Fc",
        "sk-UduOWZ3yEtC9mFxy52397cB469884a288f6dC565Fd33377d",
        "sk-IBDKadyW7ri8QTRJEdA4F5C9694d40138b5f0d1e43FcE52d"]
    
    apis_u =[]
    
    def get_llm(self):
        if self.apis_a == []:
            self.apis_a = self.apis_u
            self.apis_u = []
        
        api = self.apis_a.pop()
        self.apis_u.append(api)
        llm = ChatOpenAI(model_name="gpt-3.5-turbo-16k-0613",
                       verbose = False,
                       max_tokens = 500,
                       openai_api_key=api
                       )  
        return llm   
    
    def read_data(self):
        assert os.path.exists(self.data_dir),"no such file path: {}".format(self.data_dir)
        
        files = os.listdir(self.data_dir)# 只对community做处理
        
        for file in files:
            file_path = os.path.join(self.data_dir,file)
            
            file_name = os.path.basename(file_path).split(".")[0]
            
            with open(file_path,'r',encoding = 'utf-8') as f:
                self.datas[file_name] = json.load(f)
    

    async def atranslate_to_chinese(self,
                                   english_text,
                                   rules = ""):
        template="""
            Transfer the following context into Simplified Chinese {rules}:
            {english_text}
            
            Here's your translation:
        """  
        

        input_variables=["english_text",
                         "rules"]
        prompt = PromptTemplate(  
            input_variables=input_variables,  
            template=template,  
        )
        llm = self.get_llm()
        chain = LLMChain(llm=llm, prompt=prompt)
        chinese_text = await chain.arun(english_text=english_text,
                                        rules = rules)
        return chinese_text.strip()
    
    def translate_baidu(self,english_text,rules):
        limit = 500
        content = ""
        len_char = len(english_text)
        idx = 0
        
        while((idx+1)*limit <= len_char):
            content += self.translate_baidu_6000(english_text[idx*limit:(idx+1)*limit],rules)
            idx+=1

        if ((idx*limit)<len_char):
            content += self.translate_baidu_6000(english_text[idx*limit:],rules)
        return content
            
    
    def translate_baidu_6000(self,english_text,rules):
        # Set your own appid/appkey.
        appid = '20231103001868360'
        appkey = '9gbHiX6Y1hDJ21XPmVtG'

        # For list of language codes, please refer to `https://api.fanyi.baidu.com/doc/21`
        from_lang = 'en'
        to_lang =  'zh'

        endpoint = 'http://api.fanyi.baidu.com'
        path = '/api/trans/vip/translate'
        url = endpoint + path

        query = english_text
        
        # Generate salt and sign
        def make_md5(s, encoding='utf-8'):
            return md5(s.encode(encoding)).hexdigest()

        
        
        salt = random.randint(32768, 65536)
        sign = make_md5(appid + query + str(salt) + appkey)

        # Build request
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        payload = {'appid': appid, 'q': query, 'from': from_lang, 'to': to_lang, 'salt': salt, 'sign': sign}

        # Send request
        r = requests.post(url, params=payload, headers=headers)
        result = r.json()
        try:
            chinese_text =[]
            for trans_res in result["trans_result"]:
                chinese_text.append(trans_res["dst"])
                time.sleep(1)
            return "\n".join(chinese_text)
        except:
            raise Exception("Translation error")
    
    
    def translate_to_chinese(self,
                                   english_text,
                                   rules = ""):
        template="""
            Transfer the following context into Simplified Chinese {rules}:
            {english_text}
            
            
        """  
        

        input_variables=["english_text",
                         "rules"]
        prompt = PromptTemplate(  
            input_variables=input_variables,  
            template=template,  
        )
        llm = self.get_llm()
        chain = LLMChain(llm=llm, prompt=prompt)
        chinese_text =  chain.run(english_text=english_text,
                                        rules = rules)
        return chinese_text.strip()
    
    # async def translate_judge(self):
    #     pbar_size = sum([len(value) for value in self.datas.values()])
        
    #     pbar=tqdm(range(pbar_size), ncols=100) 
    #     for judge_type,judge_data_list in self.datas.items():
            
    #         async def translate_one_type(judge_data_list):
    #             for judge_data in judge_data_list:
    #                 for judge_key, judge_sub_dict in judge_data.items():
    #                     for k, v in judge_sub_dict.items():
    #                         if not isinstance(v,str):
    #                             continue
                            
    #                         if is_chinese(v):
    #                             continue
                            
    #                         content = await self.translate_to_chinese(v)
    #                         judge_sub_dict[k] = content
    #                 pbar.update()
                        
    #         await asyncio.gather(*[translate_one_type(judge_data_list) for judge_type,judge_data_list \
    #             in self.datas.items()])
    async def translate_judge(self):
        rules_template = "(Requirement: 1. English names should not be translated 2. the index of {judge_type} shouldn't be changed, exp.({judge_type_indexs}))"
        
        rules_ex ={
            "community_qa":"community_1,community_2,community_3 ……",
            "housetype_qa":"small_house,middle_house,large_house",
            "house_qa":"house_1",
        }
        
        pbar_size = sum([len(value) for value in self.datas.values()])
        
        pbar=tqdm(range(pbar_size), ncols=100) 
        # for judge_type,judge_data_list in self.datas.items():
            
        async def translate_one_type(judge_data_list,
                                judge_type):
            for judge_data in judge_data_list:
                for judge_key, judge_sub_dict in judge_data.items():
                    for k, v in judge_sub_dict.items():
                        if judge_type == "house_qa" or judge_type == "housetype_qa":
                            translate_keys =[
                            "house_info",
                            # "memory",
                            "role_description",
                            "output",
                            "thought"
                        ]
                        elif judge_type == "community_qa":
                            translate_keys =[
                            "house_info",
                            "memory",
                            "role_description",
                            "output",
                            "thought"
                        ]
                        if not isinstance(v,str):
                            continue
                        
                        if is_chinese(v):
                            continue
                        if k not in translate_keys:
                            continue
                        
                        if not is_chinese(v):
                            rules = rules_template.format(judge_type = judge_type,
                                                            judge_type_indexs = rules_ex.get(judge_type,""))
                            content = await self.atranslate_to_chinese(v,rules=rules)
                            #content = self.translate_baidu(v,rules=rules)
                            judge_sub_dict[k] = content
                pbar.update()
                        
        await asyncio.gather(*[translate_one_type(judge_data_list,judge_type) for judge_type,judge_data_list \
                in self.datas.items()])
        # [translate_one_type(judge_data_list,judge_type) for judge_type,judge_data_list \
        #         in self.datas.items()]

                    

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
        
        done = False
        
        while (not done):
            try:
                asyncio.run(self.translate_judge())  
                # self.translate_judge()
                # self.translate_judge()          
                self.save_data()
                done = True
            except Exception as e:
                self.save_data(True)
                print(e)
                
    
        
        
    def run_tranlsate_tenant(self):
        
        # asyncio.run(self.translate_sn_tenant_information())
        self.translate_sn_tenant_information()
        
    
    # async def translate_sn_tenant_information(self):
    #     rules = "(Requirement: English names should not be translated)"
    #     assert os.path.exists(self.tenant_path),"no such file path: {}".format(self.tenant_path)
    #     with open(self.tenant_path,'r',encoding = 'utf-8') as f:
    #         tenant_data = json.load(f)
            
    #     pbar_size = len(tenant_data.values())
        
    #     pbar = tqdm(range(pbar_size), ncols=100) 
        
    #     async def translate_one_tenant(tenant_infos):
    #         if "concise_role_description" not in tenant_infos:
    #             role_description_template="""\
    #             You are {name}. You earn {monthly_income} per month.\
    #             Your family members include: {family_members}."""
    #             concise_role_description = role_description_template.format_map({"name":tenant_infos["name"],
    #                                         **tenant_infos}
    #                                     )
    #             if tenant_infos.get("personal_preference",False):
    #                     concise_role_description += "Up to now, your personal preference for house is :{}".format(
    #                         tenant_infos.get("personal_preference")
    #                     )
                        
    #             if not is_chinese(concise_role_description):
                    
    #                 concise_role_description = await self.translate_to_chinese(concise_role_description,
    #                                                                            rules=rules)
    #             tenant_infos['concise_role_description']=concise_role_description    
    #         if "social_network_str" not in tenant_infos:
    #             social_network = ["{name}: {relation}".format(
    #             name = neigh_tenant_info.get("name",neigh_tenant_id),
    #             relation = neigh_tenant_info.get("relation","friend")
    #             )
    #                 for neigh_tenant_id,neigh_tenant_info
    #                 in tenant_infos.get("social_network",{}).items()] 
    
    #             social_network_str = "\n".join(social_network)
    #             if not is_chinese(social_network_str):
    #                 social_network_str = await self.translate_to_chinese(social_network_str,
    #                                                                      rules=rules)
    #             tenant_infos['social_network_str']=social_network_str
    #         pbar.update()
    #     try:
    #         await asyncio.gather(*[translate_one_tenant(tenant_infos) for tenant_id,tenant_infos in tenant_data.items()])
    #         with open(self.tenant_path,"w", encoding='utf-8') as file:
    #             json.dump(tenant_data, file, indent=4,separators=(',', ':'),ensure_ascii=False)
    #     except Exception as e:
    #         with open(self.tenant_path,"w", encoding='utf-8') as file:
    #             json.dump(tenant_data, file, indent=4,separators=(',', ':'),ensure_ascii=False)
    #         print(e)


    def translate_sn_tenant_information(self):
        rules = "(Requirement: English names should not be translated)"
        assert os.path.exists(self.tenant_path),"no such file path: {}".format(self.tenant_path)
        with open(self.tenant_path,'r',encoding = 'utf-8') as f:
            tenant_data = json.load(f)
            
        pbar_size = len(tenant_data.values())
        
        pbar = tqdm(range(pbar_size), ncols=100) 
        
        def translate_one_tenant(tenant_infos):
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
                    
                    concise_role_description = self.translate_to_chinese(concise_role_description,
                                                                               rules=rules)
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
                    social_network_str = self.translate_to_chinese(social_network_str,
                                                                         rules=rules)
                tenant_infos['social_network_str']=social_network_str
            pbar.update()
        try:
            # await asyncio.gather(*[translate_one_tenant(tenant_infos) for tenant_id,tenant_infos in tenant_data.items()])
            
            [translate_one_tenant(tenant_infos) for tenant_id,tenant_infos in tenant_data.items()]
            with open(self.tenant_path,"w", encoding='utf-8') as file:
                json.dump(tenant_data, file, indent=4,separators=(',', ':'),ensure_ascii=False)
        except Exception as e:
            with open(self.tenant_path,"w", encoding='utf-8') as file:
                json.dump(tenant_data, file, indent=4,separators=(',', ':'),ensure_ascii=False)
            print(e)
  
  
    def save_tenenatal_json(self,tenantal_system,save_path):
        with open(save_path,"w", encoding='utf-8') as file:
            json.dump(tenantal_system, file, indent=4,separators=(',', ':'),ensure_ascii=False)
        
        
    def run_social_network(self):
        
        # done = False
        # while (not done):
            done = asyncio.run(self.translate_social_network_context())
                        
    async def translate_social_network_context(self):
        social_network_datas = {}
        assert os.path.exists(self.social_network_dir)
        files = os.listdir(self.social_network_dir) # 翻译一个试试
        for file in files:
            file_path = os.path.join(self.social_network_dir,file)
            
            file_name = os.path.basename(file_path)
            
            with open(file_path,'r',encoding = 'utf-8') as f:
                social_network_datas[file_name] = json.load(f)
                
        pbar_size = len(social_network_datas)
        pbar = tqdm(range(pbar_size), ncols=100) 
        rules = "(Requirement: English names should not be translated)"
            
        async def translate_one_experiment(tenantal_system:dict,
                                           tenantal_name:str
                                           ):
            keys = list(tenantal_system.keys())
            remove_keys = ["group"]
            for remove_key in remove_keys:
                if remove_key in keys:
                    keys.remove(remove_key)
                    
            pbar_2 = tqdm(range(len(keys)),desc=f"translating [{tenantal_name}]") 
            try:
                for key in keys:
                    if tenantal_system[key] =={}:
                        pbar_2.update()
                        continue
                    
                    try:
                        sn_mem = tenantal_system[key]["log_social_network"]["social_network_mem"]
                    except:
                        pbar_2.update()
                        continue
                    for tenant_id,tenant_sn in sn_mem.items():
                        for ac_id,ac_infos in tenant_sn.get("social_network",{}).items():
                            
                            for dialogue in ac_infos.get("dialogues",{}):
                                
                                if (list(dialogue.get("sender",{}).keys())[0] == tenant_id):
                                    """transfer context"""
                                    context_transfered = []
                                    self.count_sn += 1
                                    # for context_one in dialogue.get("context",[]):
                                        # if not is_chinese(context_one):
                                            # context_one = await self.atranslate_to_chinese(context_one,rules=rules)
                                            
                                        # context_transfered.append(context_one)
                                    dialogue["context"] = context_transfered
                                    
                                    content = dialogue.get("content",{})
                                    
                                    for k,v in content.items():
                                        if k == "plan":
                                            # if not is_chinese(v):
                                                # v = await self.atranslate_to_chinese(v,rules=rules)
                                                
                                        
                                        # if k in ["output",
                                        #         "acquaintance_names"]:
                                        #     continue
                                        
                                        # if isinstance(v,str):
                                        #     if v.strip() == "":
                                        #         continue
                                        #     if not is_chinese(v):
                                        #         v = await self.translate_to_chinese(v)
                                            content[k] = v
                                            
                                    dialogue["content"] = content
                                    
                    
                        
                    pbar_2.update()
                    save_path = os.path.join(self.social_network_dir,tenantal_name)
                    self.save_tenenatal_json(tenantal_system=tenantal_system,
                                        save_path=save_path)
                    
                pbar.update()
                
                save_path = os.path.join(self.social_network_dir,tenantal_name)
                self.save_tenenatal_json(tenantal_system=tenantal_system,
                                        save_path=save_path)
                return True
                
            except Exception as e:
                print(e)
                save_path = os.path.join(self.social_network_dir,tenantal_name)
                self.save_tenenatal_json(tenantal_system=tenantal_system,
                        save_path=save_path)
                # with open(save_path,"w", encoding='utf-8') as file:
                #     json.dump(tenantal_system, file, indent=4,separators=(',', ':'),ensure_ascii=False)
                    
                return False

        
        
        return_states = await asyncio.gather(*[translate_one_experiment(tenantal_json,json_name) for json_name,tenantal_json in social_network_datas.items()])
        for return_state in return_states:
            if not return_state: return False
        return True

    
    

if __name__ == "__main__":
    translator = Translate()
    # translator.run_social_network()
    # print(translator.count_sn)
    translator.run_judge()
    # translator.run_tranlsate_tenant()
    