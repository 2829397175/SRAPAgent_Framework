import os
import shutil
import json

import platform

def run_tasks(tasks,
              data,
              log_dir):

    success_tasks = []
    
    failed_tasks = []
    
    command_template = "python main.py --task {task} --data {data} >> {log_path}"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_tasks_dir = os.path.join(log_dir,"log")
    if not os.path.exists(log_tasks_dir):
        os.makedirs(log_tasks_dir)

    complete_path = os.path.join(log_dir,"complete.json")            
    
    for idx,task in enumerate(tasks):
        log_task_path = os.path.join(log_tasks_dir,f"{task}.log")
        
        
        command = command_template.format(task = task,
                                          data = data,
                                          log_path = log_task_path)
        try:
            return_val = os.system(command)
            if return_val ==0:
                success_tasks.append(task)
            else:
                failed_tasks.append(task)
        except:
            failed_tasks.append(task)
            
   
        with open(complete_path,'w',encoding = 'utf-8') as f:
            uncomplete_tasks =tasks[idx+1:] if (idx+1)< len(tasks) else []
            json.dump({"success":success_tasks,
                    "failed":failed_tasks,
                    "uncomplete":uncomplete_tasks}, 
                    f,
                    indent=4,
                    separators=(',', ':'),ensure_ascii=False)
        
def run_tasks_logs(data ="PHA_51tenant_5community_28house",
                   ):
    config_root = f"LLM_PublicHouseAllocation/tasks/{data}/configs"
    
    configs = os.listdir(config_root)
    
    
    command_template = "python main.py --task {task} --data {data} --log {log}"
    
    count = {}
    for config in configs:
        
        
        result_path = os.path.join(config_root,config,"result")
        config = config.replace("(","\(").replace(")","\)")
        
        if os.path.exists(result_path):
            # paths.append(os.path.join(result_path,os.listdir(result_path)[-1]))
            result_files = os.listdir(result_path)
            paths = []
            for result_file in result_files:
                if os.path.exists(os.path.join(result_path,result_file,"tenental_system.json")):
                # result_file_path = os.path.join(result_path,result_file,"all")
                # if os.path.exists(result_file_path):
                    paths.append(os.path.join(result_path,result_file))
            for path in paths:
                path = path.replace("(","\(").replace(")","\)")
                command = command_template.format(task = config,
                                                  data = data,
                                                  log = path)
                try:
                    return_val = os.system(command)
                except Exception as e:
                    print(e)
        count[config]=paths
                
                
    print(count)
    
    print(len(count))
                    
            

    
    
    

if __name__ == "__main__":
    
    task_dir ="LLM_PublicHouseAllocation/tasks"
    data = "PHA_51tenant_5community_28house"
    config_root = os.path.join(task_dir,data,"configs")
    task_names = os.listdir(config_root)


    # task_names = list(filter(lambda x: 
    #     not os.path.exists(os.path.join(config_root,x,"result")),
    #                          task_names))
    
    
    
    task_names = [
        "ver1_nofilter_singlelist_4t_6h\(step_num\(t1_h1\)\)_p#singlelist",
        "ver1_nofilter_singlelist_2t_6h\(step_num\(t3_h1\)\)_p#singlelist",
        "ver1_nofilter_singlelist_2t_6h\(step_num\(t1_h1\)\)_p#singlelist",
        "ver1_nofilter_singlelist_5t_3h\(step_num\(t1_h3\)\)_p#singlelist"
    ]
    
    task_names = [
        "ver2_nofilter_multilist\\(1.2_k2\\)_housetype_priority_5t_3h\\(step_num\\(t2_h3\\)\\)_p#housetype_choose2",
        "ver2_nofilter_multilist\\(1.2_k2\\)_housetype_priority_5t_3h\\(step_num\\(t2_h3\\)\\)_p#portion_housesize_choose2"
    ]
    
    log_dir = "LLM_PublicHouseAllocation/tasks/PHA_51tenant_5community_28house/cache"

    run_tasks(task_names,
              data,
              log_dir)
    
    # run_tasks_logs()