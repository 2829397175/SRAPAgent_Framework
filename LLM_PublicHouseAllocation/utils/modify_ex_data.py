import os
import shutil
import json


           
def modify_result_json(origin_json,
                       result_json):
    
    keys = list(result_json.keys())
    remove_keys = ["group"]
    for remove_key in remove_keys:
        if remove_key in keys:
            keys.remove(remove_key)
            

        for key in keys:
            if result_json[key] =={}:

                continue
            
            try:
                sn_mem = result_json[key]["log_social_network"]["social_network_mem"]
            except:

                continue
            for tenant_id,tenant_sn in sn_mem.items():
                for ac_id,ac_infos in tenant_sn.get("social_network",{}).items():
                    
                    for idx,dialogue in enumerate(ac_infos.get("dialogues",[])):
                        
                        if (list(dialogue.get("sender",{}).keys())[0] == tenant_id):
                           
                            content = dialogue.get("content",{})
                            
                            for k,v in content.items():
                                if k =="plan":
                                    v = origin_json[key]["log_social_network"]["social_network_mem"][tenant_id]["social_network"][ac_id]["dialogues"][idx]["content"]["plan"]
                                content[k]=v
                                
    return result_json

root_dir = "LLM_PublicHouseAllocation/tasks"

# save_root ="LLM_PublicHouseAllocation/LLM_decision_test/data/"
save_root ="LLM_PublicHouseAllocation\LLM_decision_test\social_network\data"

ex_setting = "PHA_51tenant_5community_28house"

if not os.path.exists(save_root):
    os.makedirs(save_root)

tasks = os.listdir(root_dir)
tasks.remove("backup_data")
# tasks =["PHA_5tenant_3community_19house_ver1_nofilter_hightem"]

for task in tasks:
    results_dir = os.path.join(root_dir,task,"result")
    if ex_setting not in task:
        continue
    if os.path.exists(results_dir):
        results = os.listdir(results_dir)
        for result in results:
            result_dir = os.path.join(results_dir,result,"tenental_system.json")
            with open(result_dir,'r',encoding = 'utf-8') as f:
                origin_json = json.load(f)
            
            if not os.path.exists(os.path.join(save_root,f"{task}_{result}_ts.json")):continue
            
            with open(os.path.join(save_root,f"{task}_{result}_ts.json"),'r',encoding = 'utf-8') as f:
                dest_json = json.load(f)
                
            dest_json = modify_result_json(origin_json,dest_json)
            with open(os.path.join(save_root,f"{task}_{result}_ts.json"),'w',encoding = 'utf-8') as f:
                json.dump(dest_json, f, indent=4,separators=(',', ':'),ensure_ascii=False)
                
                
 