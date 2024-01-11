import json
import os
def count_auc(result_dir):
    dir_names = os.listdir(result_dir)
    json_results = []
    sum,correct_num=0,0
    for dir_name in dir_names:
        json_path = os.path.join(result_dir,dir_name,"sn_rounds_data.json")
        with open(json_path,'r',encoding = 'utf-8') as f:
            data_list = json.load(f)
        correct_num_,sum_  =0,0
        for data_dict in data_list:
            correct_num__,sum__ = compute_auc(data_dict)
            correct_num_ += correct_num__
            sum_+=sum__
        correct_num += correct_num_
        sum+=sum_
        print(f"auc:{correct_num_/sum_} judge_len:{sum_} file:{dir_name}")
    return correct_num/sum
        
def compute_auc(data_dict:dict):
        sum,correct_num=0,0
        for tenant_id,tenant_sn in data_dict.items():
            for ac_id,ac_info in tenant_sn.get("social_network",{}).items():
                for dialogue in ac_info.get("dialogues",[]):
                    if "turingflag" in dialogue.keys():
                        if dialogue["turingflag"] == True:
                            correct_num+=1
                        sum +=1
            
        return correct_num,sum

if __name__ =="__main__":
    # test2: 
    result_dir = "LLM_PublicHouseAllocation/LLM_decision_test/social_network/result_modify"
    auc = count_auc(result_dir)
    print(auc)