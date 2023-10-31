
import os
import json

def set_queue_name(te_j_path):
    
    with open(f"LLM_PublicHouseAllocation/tasks/PHA_51tenant_5community_20house_ver1_nofilter_multilist_priority/data/tenant_51.json",'r',encoding = 'utf-8') as f:
        tenant_json = json.load(f)
    te_j_path = os.path.join(te_j_path,"tenental_system.json")
    with open(te_j_path,'r',encoding = 'utf-8') as f:
        result=json.load(f)

    for tenant_id in result["group"].keys():
        if not isinstance (result["group"][tenant_id],dict):
            result["group"][tenant_id] ={}
        if tenant_json[tenant_id]["family_members_num"]>2:
            result["group"][tenant_id]["queue_name"] = "large_house"
        elif tenant_json[tenant_id]["family_members_num"]==2:
            result["group"][tenant_id]["queue_name"] = "middle_house"
        else:
            result["group"][tenant_id]["queue_name"] = "small_house"
        # result["group"][tenant_id]["queue_name"] = "default"

            
    with open(te_j_path,'w',encoding = 'utf-8') as f:
        json.dump(result, f, indent=4,separators=(',', ':'),ensure_ascii=False)

if __name__ =="__main__":
    
    
    # global_score = Global_Score.load_from_json("LLM_PublicHouseAllocation/tasks/PHA_51tenant_5community_20house_ver2_nofilter_multilist_priority_7t_5h/global_evaluation/global_score.json")
    
    result_dirs = [
        "LLM_PublicHouseAllocation/tasks/PHA_51tenant_5community_20house_ver2_nofilter_multilist_priority_7t_5h/result/1698634392.3664887",
        # "LLM_PublicHouseAllocation/tasks/PHA_51tenant_5community_20house_ver1_nofilter_multilist_priority_7t_5h/result/1698469201.4552162",
        # "LLM_PublicHouseAllocation/tasks/PHA_51tenant_5community_20house_ver1_nofilter_multilist_priority/result/1698393247.591396",
        # "LLM_PublicHouseAllocation/tasks/PHA_51tenant_5community_20house_ver1_nofilter_multilist/result/1698319444.931747"
    ]
    
    for result_dir in result_dirs:
        set_queue_name(result_dir)
    