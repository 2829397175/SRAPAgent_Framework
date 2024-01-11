import os
import shutil

def copy_optimize_configs(config_root ="EconAgent/tasks/PHA_51tenant_5community_28house_new_priority_label",
                          ):
    src_optimize_root = os.path.join(config_root,"optimize")
    dst_configs_root = os.path.join(config_root,"configs")
    optimize_config_names = []
    for path in os.listdir(src_optimize_root):
        
        src_path = os.path.join(src_optimize_root,path)
        dst_path = os.path.join(dst_configs_root,path)
        if not os.path.isfile(src_path):
            if not os.path.exists(dst_path):
                shutil.copytree(src_path,dst_path)
            optimize_config_names.append(path)
    print(optimize_config_names)
        
if __name__ =="__main__":
    copy_optimize_configs()