import json

import os

with open(f"LLM_PublicHouseAllocation/tasks\PHA_51tenant_5community_28house\global_evaluation\global_score_newver.json",'r',encoding = 'utf-8') as f:
    tenant_json = json.load(f)
    
for tenant_id,eval_tenant in tenant_json.items():
    for house_id,house_eval in eval_tenant.items():
        if "llm_score" not in house_eval.keys():
            house_eval["llm_score"] = int(house_eval["score"])
        assert house_eval["llm_score"]<=10
        # del house_eval["score"]

with open("LLM_PublicHouseAllocation/tasks\PHA_51tenant_5community_28house\global_evaluation\global_score_newver.json",'w',encoding = 'utf-8') as f:
    json.dump(tenant_json, f, indent=4,separators=(',', ':'),ensure_ascii=False)
        
        

# files = os.listdir("LLM_PublicHouseAllocation/tasks")

# for file in files:
#     if "PHA_51tenant_5community_28house" in file:
#         global_eval_path = os.path.join("LLM_PublicHouseAllocation/tasks",
#                                         file,
#                                         "global_evaluation\global_score_newver.json")
        
#         with open(global_eval_path,'w',encoding = 'utf-8') as f:
#             json.dump(tenant_json, f, indent=4,separators=(',', ':'),ensure_ascii=False)
        
        
        