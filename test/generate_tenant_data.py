from langchain.chains.llm import LLMChain
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
import os
import yaml
import re
import json
from tqdm import tqdm
import random
import numpy as np
import copy

from langchain.prompts.prompt import PromptTemplate
os.environ["OPENAI_API_KEY"]= "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"

class Data_generater():
    
    def __init__(self,prompt) -> None:
        self.llm = ChatOpenAI(model_name="gpt-3.5-turbo-16k-0613",
                          temperature=0.3,
                          max_tokens=3000)     
        self.llm_chain = LLMChain(llm=self.llm, prompt=prompt)
    
    def generate(self,**inputs):
        return self.llm_chain.predict(**inputs)
        
    def chain(self,prompt):
        self.llm_chain = LLMChain(llm=self.llm, prompt=prompt)
        
class outputparser():
    datas:dict = {}
    
    def tenant_names(self,output):
        name_list = self.datas.get("name",[])
        character_lists = output.split("\n")
        for name in character_lists:
            name = name.strip()
            if name not in name_list:
                name_list.append(name)
        
        self.datas["name"] = name_list
    
    def social_info(self,output):
        regex = r"character.*:(.*)personality.*:(.*)social network:(.*)\n"
        
        if "tenant_social_network" not in self.datas.keys():
            self.datas["tenant_social_network"] = {}
        
        character_lists = output.split("character")
        
        
        characters_dict = {}
        for character_str in character_lists:
            character_str ="character" + character_str
            matchs = re.findall(regex, character_str, re.DOTALL|re.IGNORECASE)
        
            for match in matchs:
                character = {}
                try:
                    name = match[0].strip()
                    
                    personality = match[1].strip()
                    sn = match[2].strip().split("\n")
                    
                    sn_dict = {}
                    for idx, sn_p in enumerate(sn):
                        sn_p = sn_p.split(":")
                        sn_name = sn_p[0].strip()
                        relationship = sn_p[1].strip()
                        sn_dict[sn_name] = relationship
                        
                    character[name]={
                        "personality":personality,
                        "social_network":sn_dict
                    }
                    characters_dict.update(character)
                except:
                    continue
        
        # sn check
        for name,tenant_info in characters_dict.items():
            sn = tenant_info["social_network"]
            judge_this = True
            for sn_name in sn.keys():
                try:
                    assert sn_name in characters_dict.keys()
                except:
                    judge_this = False
            if (judge_this): self.datas["tenant_social_network"].update({name:tenant_info})
        
        
    def tenant_info(self,output):
        
        if "tenant_info" not in self.datas.keys():
            self.datas["tenant_info"] =""
            
        regex = r"\[(.*)\]"
        matchs = re.findall(regex, output, re.DOTALL|re.IGNORECASE)
        for match in matchs:
            tenants = match.strip().strip(",")
            self.datas["tenant_info"] += tenants + ","
            
            
           
    def save_json(self,dir):
        for name, data in self.datas.items():
            if name == "tenant_info":
                with open(os.path.join(dir,name+"1.json"), 'w', encoding='utf-8') as file:
                    file.write(data)
            else:
                with open(os.path.join(dir,name+".json"), 'w', encoding='utf-8') as file:
                    json.dump(data, file, indent=4,separators=(',', ':'),ensure_ascii=False)
                
            
    def load_json(self,dir):
        file_name = os.path.basename(dir)
        with open(dir,'r',encoding = 'utf-8') as f:
            self.datas[file_name.split(".")[0]] = json.load(f)
            
            
def change_names(tenant_jsons,
                 names,
                 dir):
    names_map={} # mapping old name to new name(in names)

    # 将所有的tenant合并到第一个json文件
    tenant_json_target = tenant_jsons[0]
    
    new_names = []
    for name in names:
        if name not in tenant_json_target.keys():
            new_names.append(name) # remove replicate names
    
    for tenant_json in tenant_jsons[1:]:
        assert len(new_names) > len(tenant_json),"There's not enough new names"
        for name, tenant_info in tenant_json.items():
            if (name) in tenant_json_target:
                new_name = new_names.pop()
                names_map[name] = new_name
        
        # change name
        tenant_json_changed = {}
        for name, tenant_info in tenant_json.items():
            sn_changed = {}
            for sn_name,sn_relationship in tenant_info["social_network"].items():
                sn_changed[names_map.get(sn_name,sn_name)] = sn_relationship
                
            tenant_info["social_network"] = sn_changed
            tenant_json_changed[names_map.get(name,name)] = tenant_info
                    
        for name in tenant_json_changed.keys():
            assert name not in tenant_json_target.keys(),"Error concating!!!"
        
        tenant_json_target.update(tenant_json_changed)
        
    with open(os.path.join(dir,"tenant_sn.json"), 'w', encoding='utf-8') as file:
        json.dump(tenant_json_target, file, indent=4,separators=(',', ':'),ensure_ascii=False)
        
        
def concat_sn_info(tenant_sn,
                   tenant_info_list,
                   dir,
                   tenant = None,
                   ):
    index = 0
    if tenant is not None:
        tenant_info = tenant
        index = int(list(tenant_info.keys())[-1])+1
    else:
        tenant_info = {}
        
    for tenant_info_one in tenant_info_list:
        if tenant_info_one["name"] in tenant_sn.keys():
            tenant_info_one.update(tenant_sn.get(tenant_info_one["name"],{}))
            tenant_info[index] = tenant_info_one
            index += 1
            del tenant_sn[tenant_info_one["name"]]
        
    with open(os.path.join(dir,"tenant.json"), 'w', encoding='utf-8') as file:
        json.dump(tenant_info, file, indent=4,separators=(',', ':'),ensure_ascii=False)

    with open(os.path.join(dir,"tenant_social_network.json"), 'w', encoding='utf-8') as file:
        json.dump(tenant_sn, file, indent=4,separators=(',', ':'),ensure_ascii=False)
        
        
        
def check(tenant_sn, tenant_json, dir):
    # for tenant_idx, tenant_info in tenant_json.items():
    #     if tenant_info["name"] in tenant_sn.keys():
    #         try:
    #             assert tenant_info["social_network"] == tenant_sn.get(tenant_info["name"],{}).get("social_network")
    #         except:
    #             print(f"tenant {tenant_idx} is not a valid tenant!")
    
    # change_index
    index = 0
    tenant_json_changed = {}
    tenant_index_name_map = {}
    for tenant_idx, tenant_info in tenant_json.items():
        tenant_json_changed[index] = tenant_info
        tenant_index_name_map[tenant_info["name"]] = index
        index +=1
        
    for tenant_idx, tenant_info in tenant_json_changed.items():
        sn_ori = tenant_sn.get(tenant_info["name"],{}).get("social_network")
        sn = {}
        for name,relation in sn_ori.items():
            if name in tenant_index_name_map.keys():
                sn[tenant_index_name_map[name]] ={
                "relation": relation,
                "name":name
            }
            
        tenant_info["social_network"] = sn
            
            
    # item check
    # keys = list(tenant_json["0"].keys())
    
    # for tenant_idx, tenant_info in tenant_json.items():
    #     for key in keys:
    #         if key not in tenant_info.keys():
    #             print(f"tenant {tenant_idx} is not a valid tenant!")
                
    # index check 
    # index = 0
    # for tenant_idx, tenant_info in tenant_json.items():
    #     assert str(index) ==tenant_idx
    #     index +=1
    
    
    with open(os.path.join(dir,"tenant.json"), 'w', encoding='utf-8') as file:
        json.dump(tenant_json_changed, file, indent=4,separators=(',', ':'),ensure_ascii=False)
        
        
def priority_item(tenant_json,dir):
    rate = 0.2 # 20%的弱势群体
              
    p_item = {
    "Urban_subsistence_allowance_families":False,
    "low_income_families":False,
    "families_with_special_difficulties":False,
    "families_with_severe_disabilities":False,
    "families_with_the_elderly_over_60_years_old":False,
    "families_with_serious_illnesses_or_major_surgeries":False,
    "preferential_care_recipients_families":False,
    "model_worker_families_at_or_above_the_provincial_and_ministerial_level":False,
    "families_with_courageous_acts_of_righteousness":False,
    "families_of_adult_orphans":False,
    "families_of_fire_rescue_personnel":False,
    "families_with_2_or_more_minor_children":False
    }
    
    random_indexs = np.random.choice(list(tenant_json.keys()),
                                 int(rate*len(tenant_json))).tolist()
    
    for tenant_id,tenant_info in tenant_json.items():
        if tenant_id in random_indexs:
            random_p_k = np.random.choice(list(p_item.keys()),1).tolist()[0]
            p_item_cp = copy.deepcopy(p_item)
            p_item_cp[random_p_k] = True
            tenant_info["priority_item"] = p_item_cp
        else:
            tenant_info["priority_item"] = p_item
        
    with open(os.path.join(dir,"tenant.json"), 'w', encoding='utf-8') as file:
        json.dump(tenant_json, file, indent=4,separators=(',', ':'),ensure_ascii=False)
        

if __name__ == "__main__":
    
    prompt_template_yaml = yaml.safe_load(open("test/tenant_template.yaml","rb"))
    prompt_template = prompt_template_yaml["social_info"]
    
    
    prompt = PromptTemplate(input_variables=["used_names"], 
                        template=prompt_template)
    
    generator = Data_generater(prompt=prompt)
    parser = outputparser()    
    
    """ Generate name, personality, social network. """
    
    # # parser.load_json("test\generate_data/tenant_sn.json")
    
    # prompt_template = prompt_template_yaml["social_info"]
    
    
    # prompt = PromptTemplate(input_variables=["used_names"], 
    #                     template=prompt_template)
    
    # generator.chain(prompt)
    # used_names = []

    # for i in tqdm(range(10),"Generating Character Social Network"):
    #     # used_names = list(parser.datas.keys())
    #     output = generator.generate(used_names = [])
    #     parser.social_info(output)
    #     if len(parser.datas.keys())>50:
    #         break
        

    """ Generate names """
    
    # parser.load_json("test\generate_data/name.json")
    # prompt_template = prompt_template_yaml["tenant_names"]
    
    
    # prompt = PromptTemplate(input_variables=[], 
    #                     template=prompt_template)
    # generator.chain(prompt)
    # output = generator.generate()
    
    # parser.tenant_names(output)
    
    
    """replace names for virtual characters"""
    
    # tenant_dirs = ["test\generate_data/tenant_sn.json",
    #                "test\generate_data/tenant_social_network.json",
    #                ]
    # tenant_jsons = []
    # for t_dir in tenant_dirs:
    #     with open(t_dir,'r',encoding = 'utf-8') as f:
    #         tenant_json = json.load(f)
    #     tenant_jsons.append(tenant_json)
        
    # with open("test\generate_data/name.json",'r',encoding = 'utf-8') as f:
    #     tenant_names = json.load(f)
    
    # change_names(tenant_jsons,tenant_names,"test\generate_data")
    
    """ Generate tenant_infos """
    
    # with open("test\generate_data/tenant_social_network.json",'r',encoding = 'utf-8') as f:
    #     tenant_infos = json.load(f)
    # prompt_template = prompt_template_yaml["tenant_info"]
    
    
    # prompt = PromptTemplate(input_variables=["tenant_names"], 
    #                     template=prompt_template)
    # generator.chain(prompt)

    # tenant_names_all = list(tenant_infos.keys())
    
    # group_size = 10
    # group_id = 1
    
    # pbar = tqdm(total = int((len(tenant_names_all)-1)/group_size) + 1 - group_id)
    
    # while group_id*group_size<len(tenant_names_all):
    #     end_p = (group_id+1)*group_size
    #     end_p = end_p if end_p < len(tenant_names_all) else -1
    #     tenant_names = tenant_names_all[group_id*group_size:end_p]
        
    #     output = generator.generate(tenant_names = ",".join(tenant_names))
       
    #     parser.tenant_info(output=output)
    #     group_id +=1
    #     parser.save_json("test\generate_data")
    #     pbar.update(1)
    
    # pbar.close()
    
    # parser.save_json("test\generate_data")
    
    
    """ Concat tenant_info with tenant social network """
    
    # with open("test\generate_data/tenant_sn.json",'r',encoding = 'utf-8') as f:
    #     tenant_sn = json.load(f)
    
    # with open("test\generate_data/tenant_info.json",'r',encoding = 'utf-8') as f:
    #     tenant_info = json.load(f)
    
    # with open("test\generate_data/tenant.json",'r',encoding = 'utf-8') as f:
    #     tenant = json.load(f)
    
    # concat_sn_info(tenant_sn,
    #                tenant_info,
    #                "test\generate_data",
    #                tenant)
    
    
    """ check tenant_sn with tenant """
        
    with open("test\generate_data/tenant_sn.json",'r',encoding = 'utf-8') as f:
        tenant_sn = json.load(f)
        
    with open("test\generate_data/tenant_info.json",'r',encoding = 'utf-8') as f:
        tenant_info = json.load(f)
    
    with open("test\generate_data/tenant.json",'r',encoding = 'utf-8') as f:
        tenant = json.load(f)
    
    check(tenant_sn,
          tenant_json=tenant,
          dir= "test\generate_data")
    
    """ Generate priority item """
    
    # with open("test\generate_data/tenant.json",'r',encoding = 'utf-8') as f:
    #     tenant = json.load(f)
        
    # priority_item(tenant,"test\generate_data")
              
              
              
    """ save data"""
    # parser.save_json("test\generate_data")