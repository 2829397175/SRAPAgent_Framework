
import os

import shutil

def update_optimize_ex_logs(ori_dir ="EconAgent/tasks/PHA_51tenant_5community_28house_new_priority_label",
                            dst_dir = "EconAgent/tasks/PHA_51tenant_5community_28house_new_priority_label_optimizer"):
    ori_files = os.listdir(os.path.join(ori_dir,"configs"))
    
    dst_files = os.listdir(os.path.join(dst_dir,"configs"))
    
    for ori_file in ori_files:
        if "optimize" in ori_file:
            continue
        dst_file_path = os.path.join(dst_dir,"configs",ori_file)
        ori_file_path = os.path.join(ori_dir,"configs",ori_file)
        if os.path.exists(dst_file_path):
           shutil.rmtree(dst_file_path)
        
        shutil.copytree(ori_file_path,dst_file_path) 
        
        
if __name__ == "__main__":
    update_optimize_ex_logs()