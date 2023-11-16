import os
import shutil
import json

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
            
            json.dump({"success":success_tasks,
                    "failed":failed_tasks,
                    "uncomplete":tasks[idx:]}, 
                    f,
                    indent=4,
                    separators=(',', ':'),ensure_ascii=False)
        
def test_os_command():
    command ="python test.py>>temp.txt"
    return_val = os.system(command) 
    return_val 

if __name__ == "__main__":
    
    task_dir ="LLM_PublicHouseAllocation/tasks"
    data = "PHA_51tenant_5community_28house"
    config_root = os.path.join(task_dir,data,"configs")
    task_names = os.listdir(config_root)


    print(str(list(task_names)))
    # task_names = list(filter(lambda x: 
    #     not os.path.exists(os.path.join(config_root,x,"result")),
    #                          task_names))
    
    task_names = [
        # "ver1_nofilter_singlelist_8t_6h",
        # "ver2_nofilter_multilist(1.2_k2)_housetype_priority_5t_3h(step_num(t2_h3))_p#housetype_choose2",
        # "ver2_nofilter_multilist(1.2_k2)_housetype_priority_5t_3h(step_num(t2_h3))_p#portion_housesize_choose2",
        # "ver2_nofilter_multilist(1.2_k3)_housetype_priority_8t_6h(step_num(t1_h1))_p#housetype_choose3",
        # "ver2_nofilter_multilist(1.5_k2)_housetype_priority_8t_6h(step_num(t1_h1))_p#housetype_choose2",
        "ver2_nofilter_multilist(1.8_k2)_housetype_priority_8t_6h(step_num(t1_h1))_p#housetype_choose2"
    ]
    
    
    log_dir = "LLM_PublicHouseAllocation/tasks\PHA_51tenant_5community_28house\cache"

    run_tasks(task_names,
              data,
              log_dir)