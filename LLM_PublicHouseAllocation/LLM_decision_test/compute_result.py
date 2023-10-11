import os
import json
def readinfo(data_dir):
    assert os.path.exists(data_dir),"no such file path: {}".format(data_dir)
    with open(data_dir,'r',encoding = 'utf-8') as f:
        data_list = json.load(f)
    return data_list

def compute_auc(data_list):
    sum,correct_num=0,0
    for data in data_list:
        if data.get("testflag")==True:
            humanjudge=data.get("humanjudge")
            turingresult=data.get("turingflag")
            if humanjudge!=None and turingresult!=None:
                if humanjudge==turingresult:
                    correct_num+=1
                sum+=1
    return correct_num/sum

data_dir="LLM_PublicHouseAllocation/LLM_decision_test/test/finished_saving_QA.json"
data_list=readinfo(data_dir)

auc=compute_auc(data_list)
print(auc)