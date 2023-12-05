import os
import json
import pandas as pd


def readinfo(data_dir):
    assert os.path.exists(data_dir),"no such file path: {}".format(data_dir)
    with open(data_dir,'r',encoding = 'utf-8') as f:
        data_list = json.load(f)
    return data_list

def compute_auc(data_list):
    sum,correct_num=0,0
    
    ro_sum,ro_c=0,0
    for data in data_list:
        if data.get("testflag")==True:
            humanjudge=data.get("humanjudge")
            turingresult=data.get("turingflag")
            if humanjudge!=None and turingresult!=None:
                if humanjudge==turingresult:
                    correct_num+=1
                if not humanjudge:
                    if not turingresult:
                        ro_c+=1
                    ro_sum+=1
                sum+=1
    return correct_num/sum,correct_num,sum, ro_c/ro_sum


def compute_auc_choose_one(type_keys = ["4","3.5"]):
    results ={f"reasonal_{type_key}":{"human_response":0,
                        f"robot_response_{type_key}_chinese":0,
                        "both":0,
                        "none":0
                        } for type_key in type_keys}
    
    data_paths =[
        "LLM_PublicHouseAllocation/LLM_decision_test/11_26_data/denotes_save_response/0.json",
        "LLM_PublicHouseAllocation/LLM_decision_test/11_26_data/denotes_save_response/2.json",
        "LLM_PublicHouseAllocation/LLM_decision_test/11_26_data/denotes_save_response/5.json",
        "LLM_PublicHouseAllocation/LLM_decision_test/11_28_data/denotes_save_response/28_1.json",
        "LLM_PublicHouseAllocation/LLM_decision_test/11_28_data/denotes_save_response/28_2.json",
        "LLM_PublicHouseAllocation/LLM_decision_test/11_26_data/denotes_save_response/6.json",
        "LLM_PublicHouseAllocation/LLM_decision_test/11_28_data/denotes_save_response/28_0.json",
        ]
    
    data_all =[]
    
    for data_path in data_paths:
        data_all.extend(readinfo(data_path))
    
    for data_one_response in data_all:
        for type_key in results.keys():
            denote_response = data_one_response.get(type_key)
            if isinstance(denote_response,list):
                for denote_one_response in denote_response:
                    results[type_key][denote_one_response] +=1
            elif isinstance(denote_response,str):
                results[type_key][denote_response] +=1
            
            
    df_acc = pd.DataFrame()
    
    
    for type_key in type_keys:
        result_type_key = results[f"reasonal_{type_key}"]
        
        for k, v in result_type_key.items():
            print(f"{type_key} {k}: {v}")
            if "robot_response" in k:
                k = "robot_response"
            df_acc.loc[type_key,k] = v   
            
        human_robot =(result_type_key['human_response']+result_type_key['both']) / \
        (result_type_key[f'robot_response_{type_key}_chinese']+result_type_key['both'])
        print(f"human/robot {human_robot:.3f} ")
        len_data = sum(result_type_key.values())
        df_acc.loc[type_key,"human/robot"] =human_robot
        df_acc.loc[type_key,"data_len"] = len_data
        
    df_acc.to_csv("LLM_PublicHouseAllocation/LLM_decision_test/acc_choose_one.csv")
    
    

    
    
if __name__ == "__main__":
    # data_dir="LLM_PublicHouseAllocation\LLM_decision_test\denote\judge"
    # dfs = os.listdir(data_dir)
    # correct_num=0
    # sum=0
    # for df in dfs:
    #     data_path = os.path.join(data_dir,df)
    #     data_list=readinfo(data_path)

    #     auc,correct_num_,sum_,ro_auc=compute_auc(data_list)
    #     denoter = df.split(".")[0].split("_")[0]
    #     print("auc: {:.3f}".format(auc),"ro_auc: {:.3f}".format(ro_auc),f"num:{sum_}", f"denoter:{denoter}")
    #     correct_num +=correct_num_
    #     sum+=sum_
        
    # print("auc: {:.3f}".format(correct_num/sum),f"num:{sum}")
    
    compute_auc_choose_one()

    
