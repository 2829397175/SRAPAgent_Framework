import os
import shutil
root_dir = "LLM_PublicHouseAllocation/tasks"

tasks = os.listdir(root_dir)
tasks.remove("backup_data")

for task in tasks:
    results_dir = os.path.join(root_dir,task,"result")
    results = os.listdir(results_dir)
    for result in results:
        result_dir = os.path.join(results_dir,result,"tenental_system.json")
        if (os.path.exists(result_dir)):
            shutil.copyfile(result_dir,f"LLM_PublicHouseAllocation/LLM_decision_test/data/{task}_{result}_ts.json")
