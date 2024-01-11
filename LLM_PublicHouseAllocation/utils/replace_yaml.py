import os
import shutil

def replace_yaml(src_ex_setting:str ="PHA_51tenant_5community_28house",
                 dst_ex_setting:str ="PHA_51tenant_5community_28house_new_priority_label",
                 task_root ="LLM_PublicHouseAllocation/tasks"):
    
    src_root_dir = os.path.join(task_root,src_ex_setting,"configs")
    dst_root_dir = os.path.join(task_root,dst_ex_setting,"configs")
    for task_name in os.listdir(src_root_dir):
        src_config_path = os.path.join(src_root_dir,task_name,"config.yaml")
        dst_config_path = os.path.join(dst_root_dir,task_name,"config.yaml")
        os.remove(dst_config_path)
        shutil.copyfile(src_config_path,dst_config_path)
        
        
if __name__ =="__main__":
    replace_yaml()