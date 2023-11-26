import os
import shutil
import json
def readinfo(data_dir):
    assert os.path.exists(data_dir),"no such file path: {}".format(data_dir)
    with open(data_dir,'r',encoding = 'utf-8') as f:
        data_list = json.load(f)
    return data_list

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
        
        
        task = task.replace("(","\(").replace(")","\)")
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
                    
            
def test_task_logs(data ="PHA_51tenant_5community_28house",
                   ):
    
    config_root = f"LLM_PublicHouseAllocation/tasks/{data}/configs"
    
    configs = os.listdir(config_root)
  
    not_available_results =[]
    
    for config in configs:
        
        result_path = os.path.join(config_root,config,"result")
        
        if os.path.exists(result_path):
            # paths.append(os.path.join(result_path,os.listdir(result_path)[-1]))
            result_files = os.listdir(result_path)
            paths = []
            ok = False
            for result_file in result_files:
                if os.path.exists(os.path.join(result_path,result_file,"tenental_system.json")):
                    tenental_info = readinfo(os.path.join(result_path,result_file,"tenental_system.json"))
                    last_round = list(tenental_info.keys())[-1]
                    try:
                        if (int(last_round)>=9):
                            ok = True
                    except:
                        pass
            if (not ok):not_available_results.append([config,list(tenental_info.keys())[-1]])
                        
    with open("LLM_PublicHouseAllocation/tasks/PHA_51tenant_5community_28house/cache/not_available_tasks.json",
              'w',encoding = 'utf-8') as f:
        json.dump(not_available_results, f, indent=4,separators=(',', ':'),ensure_ascii=False)
    

if __name__ == "__main__":
    
    task_dir ="LLM_PublicHouseAllocation/tasks"
    data = "PHA_51tenant_5community_28house"
    config_root = os.path.join(task_dir,data,"configs")
    task_names = os.listdir(config_root)


    task_names = list(filter(lambda x: 
        not os.path.exists(os.path.join(config_root,x,"result")),
                             task_names))
    
    
    task_names =[
        "ver2_nofilter_multilist(1.2_k2)_housetype_priority_8t_6h(step_num(t1_h1))_p#random_avg",
        "ver2_nofilter_multilist(1.2_k2)_housetype_priority_8t_6h(step_num(t1_h1))_p#portion_rentmoney",
        "ver2_nofilter_multilist(1.2_k2)_housetype_priority_8t_6h(step_num(t1_h1))_p#portion_housesize",
        "ver1_nofilter_multilist(1.2)_multilist_priority_8t_6h_p#random_avg",
        "ver1_nofilter_multilist(1.2)_multilist_priority_8t_6h_p#portion_rentmoney",
        "ver1_nofilter_multilist(1.2)_multilist_priority_8t_6h_p#portion_housesize",
        "ver1_nofilter_multilist(1.2)_portion3(f_rent_money_budget)_priority_8t_6h_p#random_avg"
    ]
   
    
    log_dir = "LLM_PublicHouseAllocation/tasks/PHA_51tenant_5community_28house/cache"

    run_tasks(task_names,
              data,
              log_dir)
    
    # run_tasks_logs()
    
    # test_task_logs()