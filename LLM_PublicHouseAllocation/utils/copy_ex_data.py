import os
import shutil
root_dir = "LLM_PublicHouseAllocation/tasks"

tasks = os.listdir(root_dir)
tasks.remove("backup_data")
# tasks =["PHA_5tenant_3community_19house_ver1_nofilter_hightem"]

for task in tasks:
    results_dir = os.path.join(root_dir,task,"result")
    if os.path.exists(results_dir):
        results = os.listdir(results_dir)
        for result in results:
            result_dir = os.path.join(results_dir,result,"tenental_system.json")
            if (os.path.exists(result_dir)):
                shutil.copyfile(result_dir,f"LLM_PublicHouseAllocation/LLM_decision_test/data/{task}_{result}_ts.json")
