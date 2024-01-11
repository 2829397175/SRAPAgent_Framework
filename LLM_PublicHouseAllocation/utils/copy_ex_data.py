import os
import shutil
root_dir = "LLM_PublicHouseAllocation/tasks"

# save_root ="LLM_PublicHouseAllocation/LLM_decision_test/data/"
save_root ="LLM_PublicHouseAllocation/LLM_decision_test/data"

ex_setting = "PHA_70tenant_5community_100house"
ex_dir = os.path.join(root_dir,ex_setting,"configs")


if not os.path.exists(save_root):
    os.makedirs(save_root)

configs = os.listdir(ex_dir)

# tasks.remove("backup_data")
# tasks =["PHA_5tenant_3community_19house_ver1_nofilter_hightem"]

for config in configs:
    
    results_dir = os.path.join(ex_dir,config,"result")
    for time_stamp in list(os.listdir(results_dir)):
        result_path = os.path.join(results_dir,time_stamp,"tenental_system.json")
        if (os.path.exists(result_path)):
            shutil.copyfile(result_path,os.path.join(save_root,f"{ex_setting}_{config}_{time_stamp}.json"))
