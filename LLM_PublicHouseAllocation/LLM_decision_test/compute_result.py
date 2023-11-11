import os
import json
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

data_dir="LLM_PublicHouseAllocation\LLM_decision_test\denote\judge"
dfs = os.listdir(data_dir)
correct_num=0
sum=0
for df in dfs:
    data_path = os.path.join(data_dir,df)
    data_list=readinfo(data_path)

    auc,correct_num_,sum_,ro_auc=compute_auc(data_list)
    denoter = df.split(".")[0].split("_")[0]
    print("auc: {:.3f}".format(auc),"ro_auc: {:.3f}".format(ro_auc),f"num:{sum_}", f"denoter:{denoter}")
    correct_num +=correct_num_
    sum+=sum_
    
print("auc: {:.3f}".format(correct_num/sum),f"num:{sum}")

    
