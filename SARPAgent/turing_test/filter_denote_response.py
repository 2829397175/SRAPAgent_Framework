import json
import os
import random
import json
from hashlib import md5
import requests

import time
import re

def readinfo(data_dir):
    assert os.path.exists(data_dir),"no such file path: {}".format(data_dir)
    with open(data_dir,'r',encoding = 'utf-8') as f:
        data_list = json.load(f)
    return data_list

def writeinfo(data_dir,info):
    with open(data_dir,'w',encoding = 'utf-8') as f:
            json.dump(info, f, indent=4,separators=(',', ':'),ensure_ascii=False)


def filter_save_response(data_dir = "SARPAgent\LLM_decision_test\denote\judge"):
    dfs = os.listdir(data_dir)

    data_all = {
        "community":[],
        "housetype":[],
        "house":[]
    }
    types = ("community","house type","house")
    for df in dfs:
        data_path = os.path.join(data_dir,df)
        data_list = readinfo(data_path)
        
        data_list = list(filter(lambda x:x["humanjudge"],data_list))
        for data_one in data_list:
            if "community" in data_one["prompt_inputs"]["choose_type"]:
                data_all["community"].append(data_one)
            elif "house type" in data_one["prompt_inputs"]["choose_type"]:
                data_all["housetype"].append(data_one)
            elif "houses" in data_one["prompt_inputs"]["choose_type"]:
                data_all["house"].append(data_one)
                
                
                
    data_dir = os.path.dirname(data_dir)
                
    for k in data_all.keys():
        data_path_one = os.path.join(data_dir,f"{k}_save_response.json")
        with open(data_path_one,'w',encoding = 'utf-8') as f:
            json.dump(data_all[k], f, indent=4,separators=(',', ':'),ensure_ascii=False)  
        
    # with open(os.path.join(os.path.dirname(data_dir),"save_response_.json"),'w',encoding = 'utf-8') as f:
    #     json.dump(data_all, f, indent=4,separators=(',', ':'),ensure_ascii=False)

import unicodedata
def is_chinese(strs):
    for _char in strs:
        if '\u4e00' <= _char <= '\u9fa5':
            return True
    return False


def translate_baidu_6000(english_text, 
                         rules=None):
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
            return "".join(chinese_text)
        except:
            raise Exception("Translation error")


def filter_en_to_cn(type_data,
                    english_data_dir ="SARPAgent\LLM_decision_test/filtered_response_data_simulated\en_ver",
                    chinese_data_dir ="SARPAgent\LLM_decision_test\denote\save_response",
                    save_dir = "SARPAgent\LLM_decision_test/filtered_response_data_simulated\cn_ver"):
    
    data_path = os.path.join(english_data_dir,f"{type_data}.json")
    en_ver_data = readinfo(data_path)
    
    chinese_data_path = os.path.join(chinese_data_dir,
                                     f"{type_data}_save_response.json")
    cn_ver_data = readinfo(chinese_data_path)
    
    for idx, response_data in en_ver_data.items():
        response_data_en_prompt_inputs = cn_ver_data[int(idx)]["prompt_inputs"]
        en_ver_data[idx]["prompt_inputs"] = response_data_en_prompt_inputs
        
    save_path = os.path.join(save_dir,f"{type_data}.json")
    
    with open(save_path,'w',encoding = 'utf-8') as f:
        json.dump(en_ver_data, f, indent=4,separators=(',', ':'),ensure_ascii=False)  
    

def filter_chinese_to_en(type_data,
                         chinese_data_dir ="SARPAgent\LLM_decision_test\denote\save_response",
                         english_data_dir ="SARPAgent\LLM_decision_test\english_judge_data",
                         save_dir = "SARPAgent\LLM_decision_test/filtered_response_data",
                         ):
    files = os.listdir(english_data_dir)
    regex = f"(.*)_qa.*.json"
    
    english_quota = []
    for file in files:
        answer = re.search(regex,file)
        type_file = answer.group(1)
        if type_file == type_data:
            data_path = os.path.join(english_data_dir,
                                     file)
            english_quota.extend(readinfo(data_path))
    
    chinese_data_path = os.path.join(chinese_data_dir,
                                     f"{type_data}_save_response.json")
    chinese_data = readinfo(chinese_data_path)
    
    
    
    
    save_path = os.path.join(save_dir,f"{type_data}.json")
    if os.path.exists(save_path):
        filtered_english_data = readinfo(save_path)
    else:
        filtered_english_data = {}
    
    regex_choice = f"(\d+)"
    regex_names = [f"是(.*?)。",f"叫(.*?)。"]
                   
    
    for idx,save_response_one in enumerate(chinese_data):
        if str(idx) in filtered_english_data.keys():
            continue
        found = False
        for regex_name in regex_names:
            choice_word = save_response_one["prompt_inputs"]["house_info"]
            role_description = save_response_one["prompt_inputs"]["role_description"]
            choice = re.search(regex_choice,choice_word)
            name = re.search(regex_name,role_description)
            try:
                choice = choice.group(1)
                name = name.group(1).strip()
                if is_chinese(name):
                    name = translate_baidu_6000(name)
            except:
                pass
            if choice is not None and name is not None:
                regex_en_choice = f"There are (\d+) .* available"
                regex_en_name = f"You are (.*)."
                for english_one in english_quota:
                    choice_word = english_one["prompt_inputs"]["house_info"]
                    role_description = english_one["prompt_inputs"]["role_description"]
                    choice_en = re.search(regex_en_choice,choice_word).group(1)
                    name_en = re.search(regex_en_name,role_description).group(1)
                    if int (choice)== int(choice_en) \
                        and name in name_en:
                        assert idx not in filtered_english_data.keys(),"error for {idx}"
                        english_one["human_response"] = save_response_one["response"]
                        filtered_english_data[str(idx)] = english_one
                        english_quota.remove(english_one)
                        found = True
                        break
            if found:
                break
                    
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)    
            
    with open(save_path,'w',encoding = 'utf-8') as f:
        json.dump(filtered_english_data, f, indent=4,separators=(',', ':'),ensure_ascii=False)  
         

def filter_same_answer(judge_keys =["robot_response_4_chinese",
                                    "human_response"]):
    data_all =[]
    data_paths =[
        "SARPAgent/LLM_decision_test/11_26_data/denotes_save_response/0.json",
        "SARPAgent/LLM_decision_test/11_26_data/denotes_save_response/2.json",
        "SARPAgent/LLM_decision_test/11_26_data/denotes_save_response/3.json",
        "SARPAgent/LLM_decision_test/11_26_data/denotes_save_response/4.json",
        "SARPAgent/LLM_decision_test/11_26_data/denotes_save_response/5.json",
        "SARPAgent/LLM_decision_test/11_26_data/denotes_save_response/6.json",
        "SARPAgent/LLM_decision_test/11_28_data/denotes_save_response/28_0.json",
        # "SARPAgent/LLM_decision_test/11_28_data/denotes_save_response/28_0_ver2.json",
        "SARPAgent/LLM_decision_test/11_28_data/denotes_save_response/28_1.json",
        "SARPAgent/LLM_decision_test/11_28_data/denotes_save_response/28_2.json",
        ]
    for data_path in data_paths:
        
        data_all.extend(readinfo(data_path))
        
        
    def judge_same(data,type)->bool:
        choice_strs ={key:{"str":data[key]["output"]}
                      for key in judge_keys}
        if type == "housetype":
            for output_type, choice_str in choice_strs.items():
                choice_str = choice_str["str"]
                
                if "不会" in choice_str or "没" in choice_str or "放弃" in choice_str:
                    choice_strs[output_type]["filtered_choice"]= "none"
                elif "small" in choice_str or "小" in choice_str:
                    choice_strs[output_type]["filtered_choice"]= "small_house"
                elif "middle" in choice_str or "中" in choice_str:
                    choice_strs[output_type]["filtered_choice"]= "middle_house"
                elif "large" in choice_str or "大" in choice_str:
                    choice_strs[output_type]["filtered_choice"]= "large_house"
                else:
                    assert False, f"{choice_str},{data}"
        else:
            
            regex = f"(\d+)"
            
            for output_type, choice_str in choice_strs.items():
                choice_str = choice_str["str"]
                if "不" in choice_str or "没" in choice_str or "放弃" in choice_str:
                    choice_strs[output_type]["filtered_choice"]= "none"
                else:
                    try:
                        choice = re.search(regex,choice_str).group(1)
                        choice_strs[output_type]["filtered_choice"]= choice
                    except:
                        print(choice_str,data)
        
        return choice_strs[judge_keys[0]]["filtered_choice"] == \
            choice_strs[judge_keys[1]]["filtered_choice"]
            
    
    filtered_chooses = []
    same_chooses =[]
    for data_one in data_all:
        if "house type" in data_one["prompt_inputs"]["choose_type"]:
            if (not judge_same(data_one,"housetype")):
                filtered_chooses.append(data_one)
            else:
                same_chooses.append(data_one)
                
        else:
            if (not judge_same(data_one,"other_type")):
                filtered_chooses.append(data_one)
            else:same_chooses.append(data_one)
       
    print(f"{judge_keys[0]} same:{len(same_chooses)}, different:{len(filtered_chooses)}")         
    # if not os.path.exists(save_dir):
    #     os.makedirs(save_dir)            
    
    # with open(os.path.join(save_dir,"different.json"),'w',encoding = 'utf-8') as f:
    #     json.dump(filtered_chooses, f, indent=4,separators=(',', ':'),ensure_ascii=False) 
    
    # with open(os.path.join(save_dir,"same.json"),'w',encoding = 'utf-8') as f:
    #     json.dump(same_chooses, f, indent=4,separators=(',', ':'),ensure_ascii=False)  


def filter_group_denote():
    all_path = "SARPAgent/LLM_decision_test/filtered_response_data_simulated/finished_denote/group/all"
    
    jsons_answer = []
    
    json_paths = os.listdir(all_path)
    
    for json_path in json_paths:
        path = os.path.join(all_path,json_path)
        jsons_answer.extend(readinfo(path))

    data_all = {
        "community":{},
        "housetype":{},
        "house":{}
    }
    
    for data_one in jsons_answer:
        if "community" in data_one["prompt_inputs"]["choose_type"]:
            data_all["community"].update({int(data_one["idx"]):data_one})
        elif "house type" in data_one["prompt_inputs"]["choose_type"]:
            data_all["housetype"].update({int(data_one["idx"]):data_one})
        elif "houses" in data_one["prompt_inputs"]["choose_type"]:
            data_all["house"].update({int(data_one["idx"]):data_one})
        
    data_dir = os.path.dirname(all_path)
                
    for k in data_all.keys():
        data_path_one = os.path.join(data_dir,f"{k}.json")
        
        with open(data_path_one,'w',encoding = 'utf-8') as f:
            dict1 = dict(sorted(data_all[k].items(),key = lambda x:x[0]) )#升序
           
            json.dump(dict1, f, indent=4,separators=(',', ':'),ensure_ascii=False)  
    
    
def append_index(data_dir = "SARPAgent/LLM_decision_test/11_28_data/split_data"):
    files = os.listdir(data_dir)
    for file in files:
        json_info = readinfo(os.path.join(data_dir,file))
        if isinstance(json_info,list):
            json_info_dict ={}
            for idx,one_info in enumerate(json_info):
                one_info["idx"] = idx
                one_info["robot_response"] = one_info["response"] 
                del one_info["response"] 
                json_info_dict[idx]=one_info
            json_info = json_info_dict
        elif isinstance(json_info,dict):
            for k,v in json_info.items():
                v["robot_response"] = v["response"] 
                del v["response"] 
           
        writeinfo(os.path.join(data_dir,file),json_info)
                
if __name__=="__main__":
    data_types = [
          "community","housetype","house",
                  ]
    # append_index()
    # for data_type in data_types:
    #     # filter_chinese_to_en(data_type)
    #     filter_en_to_cn(type_data=data_type)
    filter_same_answer(judge_keys=["robot_response_3.5_chinese",
                                    "human_response"])
    # filter_group_denote()
        
    

