import os
import json
import numpy as np

def read_data(path="LLM_PublicHouseAllocation/LLM_decision_test/data/1.json"):
    assert os.path.exists(path),"no such file path: {}".format(path)
    with open(path,'r',encoding = 'utf-8') as f:
        testdata = json.load(f)
    communityQA,housetypeQA,houseQA=[],[],[]
    for c_num,record in testdata.items():
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



def batch_read_data():
    current_directory = os.getcwd()
    datafile_directory=os.path.join(current_directory,"LLM_PublicHouseAllocation","LLM_decision_test","data")
    all_files_and_dirs = os.listdir(datafile_directory)
    absolute_all_files_path= [os.path.join(datafile_directory, filename) for filename in all_files_and_dirs]
    for path in absolute_all_files_path:
        communityQA,housetypeQA,houseQA=read_data(path)
        save_database(communityQA,housetypeQA,houseQA)
        
     
def clear_response(json_types,rate = 0.1):
    """
    rate 代表clear response的比例
    """
    for json_type in json_types:
        json_dir = "LLM_PublicHouseAllocation\LLM_decision_test\{}_qa.json".format(json_type)
        with open(json_dir,'r',encoding = 'utf-8') as f:
            data = json.load(f)
        clear_indexs = np.random.choice(list(range(len(data))),
                                        size=int(rate*len(data)),replace=False)
        for c_idx in clear_indexs:
            del data[c_idx]["response"]
            
        save_dir = "LLM_PublicHouseAllocation\LLM_decision_test\qa_clear_data\{}_qa.json".format(json_type)
        with open(save_dir,'w',encoding = 'utf-8') as f:
            json.dump(data,f, indent=4,separators=(',', ':'),ensure_ascii=False)
        
    

if __name__ == "__main__":
    # make data
    # clear_database()
    # batch_read_data()
    
    
    # clear response
    json_types = ["community","house","housetype"]
    clear_response(json_types)