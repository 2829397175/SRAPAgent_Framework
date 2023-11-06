import os
import json
import numpy as np
import re

def read_data(path="LLM_PublicHouseAllocation/LLM_decision_test/data/1.json"):
    assert os.path.exists(path),"no such file path: {}".format(path)
    with open(path,'r',encoding = 'utf-8') as f:
        testdata = json.load(f)
    communityQA,housetypeQA,houseQA=[],[],[]
    for c_num,record in testdata.items():
        if c_num == "group":
            for tenant_id, group_info in record.items():
                if "choose_house_type" in group_info["log_round_prompts"].keys():
                    housetypeQA.append( group_info["log_round_prompts"]["choose_house_type"])
        
        if c_num!="group" and record!={}:
            for log_key,log_value in record.items():
                if log_key =="log_round_prompts":
                    for tenant_id,decision_content in log_value.items():
                        for decision_type,decision_qa in decision_content.items():
                            if decision_type=="choose_house_type":
                                housetypeQA.append(decision_qa)
                            elif decision_type=="choose_community":
                                communityQA.append(decision_qa)
                            elif decision_type=="choose_house":
                                for pagenum,pagecontent in decision_qa["log_round_houses_dict"].items():                             
                                    houseQA.append(pagecontent)
    return communityQA,housetypeQA,houseQA

def save_database(communityQA,housetypeQA,houseQA):
    cqa="LLM_PublicHouseAllocation/LLM_decision_test/community_qa.json"
    htqa="LLM_PublicHouseAllocation/LLM_decision_test/housetype_qa.json"
    hqa="LLM_PublicHouseAllocation/LLM_decision_test/house_qa.json"
    assert os.path.exists(cqa),"no such file path: {}".format(cqa)
    with open(cqa,'r',encoding = 'utf-8') as f:
        communityQA_data = json.load(f)
        communityQA_data.extend(communityQA)
    assert os.path.exists(htqa),"no such file path: {}".format(htqa)
    with open(htqa,'r',encoding = 'utf-8') as f:
        housetypeQA_data = json.load(f)
        housetypeQA_data.extend(housetypeQA)
    assert os.path.exists(hqa),"no such file path: {}".format(hqa)
    with open(hqa,'r',encoding = 'utf-8') as f:
        houseQA_data = json.load(f) 
        houseQA_data.extend(houseQA)
        
        
    with open(cqa, 'w', encoding='utf-8') as file:
        json.dump(communityQA_data, file, indent=4,separators=(',', ':'),ensure_ascii=False)
    with open(htqa, 'w', encoding='utf-8') as file:
        json.dump(housetypeQA_data, file, indent=4,separators=(',', ':'),ensure_ascii=False)

    with open(hqa, 'w', encoding='utf-8') as file:
        json.dump(houseQA_data, file, indent=4,separators=(',', ':'),ensure_ascii=False)
    
def clear_database():
    filelist=["LLM_PublicHouseAllocation/LLM_decision_test/community_qa.json",
              "LLM_PublicHouseAllocation/LLM_decision_test/housetype_qa.json",
              "LLM_PublicHouseAllocation/LLM_decision_test/house_qa.json"]
    for filepath in filelist:
        with open(filepath, 'w') as f:
            f.write('[]')


def clear_1(data:list):
    data_return = []
    for dict_one in data:
        v = dict_one["prompt_inputs"]["house_info"]
        if "没有可用的" in v or "有0个社区" in v:

            continue
        if "有1种" in v:

            continue
        if is_chinese(v):
            available_num = re.search("有(.*)。",v,re.I | re.M)
            available_num_str = available_num.groups()[0]
            try:
                available_num = re.search("(\d+)",available_num_str,re.I | re.M)
                available_num = available_num.groups()[0]
                assert available_num is not None
            except:
                if "两" in available_num_str:
                    available_num =2
                elif "三" in available_num_str:
                    available_num =3
                elif "四" in available_num_str:
                    available_num =4
        else:
            available_num = re.search("(\d+).*可供选择",v,re.I | re.M)
        if int(available_num) > 1:
            data_return.append(dict_one)
    return data_return


def batch_read_data():
    current_directory = os.getcwd()
    datafile_directory=os.path.join(current_directory,"LLM_PublicHouseAllocation","LLM_decision_test","data")
    all_files_and_dirs = os.listdir(datafile_directory)
    if "unfinished_QA_result.json" in all_files_and_dirs:
        all_files_and_dirs.remove("unfinished_QA_result.json")
    absolute_all_files_path= [os.path.join(datafile_directory, filename) for filename in all_files_and_dirs]
    for path in absolute_all_files_path:
        communityQA,housetypeQA,houseQA=read_data(path)
        communityQA = clear_1(communityQA)
        housetypeQA = clear_1(housetypeQA)
        houseQA = clear_1(houseQA)
        save_database(communityQA,housetypeQA,houseQA)
        
def clear_1_json_memory(json_types):
    """
    rate 代表clear response的比例
    """
    for json_type in json_types:
        json_dir = "LLM_PublicHouseAllocation\LLM_decision_test\old_ver_11_3\qa_translated\judge\\finished\{}_qa.json".format(json_type)
        with open(json_dir,'r',encoding = 'utf-8') as f:
            data = json.load(f)
        data = clear_1(data)
        if not json_type == "community":
            for data_one in data:
                data_one["prompt_inputs"]["memory"] =""
        
        save_path = "LLM_PublicHouseAllocation\LLM_decision_test\qa_unclear_data\\filtered\{}_qa.json".format(json_type)
        save_dir = os.path.dirname(save_path)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        with open(save_path,'w',encoding = 'utf-8') as f:
            json.dump(data,f, indent=4,separators=(',', ':'),ensure_ascii=False)
     
def clear_response(json_types,rate = 0.1):
    """
    rate 代表clear response的比例
    """
    for json_type in json_types:
        json_dir = "LLM_PublicHouseAllocation\LLM_decision_test\qa_unclear_data\\filtered\{}_qa.json".format(json_type)
        with open(json_dir,'r',encoding = 'utf-8') as f:
            data = json.load(f)
        clear_indexs = np.random.choice(list(range(len(data))),
                                        size=int(rate*len(data)),replace=False)
        for c_idx in clear_indexs:
            data[c_idx]["response"]={}
            
        save_path = "LLM_PublicHouseAllocation\LLM_decision_test\qa_clear_data\{}_qa.json".format(json_type)
        save_dir = os.path.dirname(save_path)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        with open(save_path,'w',encoding = 'utf-8') as f:
            json.dump(data,f, indent=4,separators=(',', ':'),ensure_ascii=False)
        
import unicodedata
def is_chinese(strs):
    for _char in strs:
        if '\u4e00' <= _char <= '\u9fa5':
            return True
    return False

    
def concat_translation(json_types=["community","house","housetype"]):
    for json_type in json_types:
        json_dir = "LLM_PublicHouseAllocation\LLM_decision_test\qa_translated\judge\\finished copy\{}_qa.json".format(json_type)
        with open(json_dir,'r',encoding = 'utf-8') as f:
            data = json.load(f)
            
        json_ori_dir =  "LLM_PublicHouseAllocation\LLM_decision_test\qa_translated\judge\\finished_old_ver\{}_qa.json".format(json_type)
        with open(json_ori_dir,'r',encoding = 'utf-8') as f:
            ori_data = json.load(f)
            
        update_keys = ["thought",
                      "output"]
        # update_keys = ["house_info"]
        for ori_dict,dict_now in zip(ori_data,data):
            for key,dict_one in dict_now.items():
                for k,v in dict_one.items():
                    if k in update_keys:
                        if is_chinese(ori_dict[key][k]):
                            dict_one[k] = ori_dict[key][k]
        with open(json_dir,'w',encoding = 'utf-8') as f:
            json.dump(data,f, indent=4,separators=(',', ':'),ensure_ascii=False)
            
def clear_house_json():
    house_json_dir = "LLM_PublicHouseAllocation\LLM_decision_test\qa_translated\judge\\finished\house_qa.json"
    with open(house_json_dir,'r',encoding = 'utf-8') as f:
        data = json.load(f)
    
    for dict in data:
        try:
            assert "output" in data["response"].keys()
        except:
            data.remove(dict)
            
    with open(house_json_dir,'w',encoding = 'utf-8') as f:
        json.dump(data,f, indent=4,separators=(',', ':'),ensure_ascii=False)

        
def clear_house_5():
    path ="qa_unclear_data\\filtered\groups\house\house_qa_5_judge.json"
    with open(path,'r',encoding = 'utf-8') as f:
        communityQA_data = json.load(f)
    for data in communityQA_data:
        data["response"] ={}
        
    with open("qa_unclear_data\\filtered\groups\house\house_qa_5_save_response.json", 'w', encoding='utf-8') as file:
        json.dump(communityQA_data, file, indent=4,separators=(',', ':'),ensure_ascii=False)

if __name__ == "__main__":
    # make data
    # clear_database()
    # batch_read_data()
    
    
    # clear response
    json_types = ["housetype","house","community"]
    clear_house_5()
    # clear_response(json_types,rate= 1)
    # clear_1_json_memory(json_types)
    
    # json_types = ["community"]
    # concat_translation(json_types)
    # clear_house_json()