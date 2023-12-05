import os
import shutil
import json
import yaml
import time

def readinfo(data_dir):
    assert os.path.exists(data_dir),"no such file path: {}".format(data_dir)
    with open(data_dir,'r',encoding = 'utf-8') as f:
        data_list = json.load(f)
    return data_list



def run_tasks(tasks,
              data,
              log_dir,
              run_ex_times = 1):

    
    
    success_tasks = []
    
    failed_tasks = []
    
    command_template = "python main.py --task {task} --data {data}"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_tasks_dir = os.path.join(log_dir,"log")
    if not os.path.exists(log_tasks_dir):
        os.makedirs(log_tasks_dir)

    complete_path = os.path.join(log_dir,"complete.json")            
    
    
    for idx,task in enumerate(tasks):
        
        task_root_path =os.path.join("LLM_PublicHouseAllocation/tasks",data,"configs",task,"result")

        done_times = 0
        if os.path.exists(task_root_path):
            results = os.listdir(task_root_path)

            for result in results:
                result_path = os.path.join(task_root_path,result)
                if os.path.exists(os.path.join(result_path,"all")):
                    done_times +=1
            
            
        while(done_times<run_ex_times):
            task = task.replace("(","\(").replace(")","\)")
            log_task_path = os.path.join(log_tasks_dir,f"{task}.log")
            command = command_template.format(task = task,
                                            data = data,
                                            log_path = log_task_path)
            
            try:
                return_val = os.system(command)
                if return_val ==0:
                    success_tasks.append(task.replace("\(","(").replace("\)",")"))
                else:
                    failed_tasks.append(task.replace("\(","(").replace("\)",")"))
            except:
                failed_tasks.append(task.replace("\(","(").replace("\)",")"))
                
            done_times+=1
   
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
    
    
def clear_all_cache_ex_data(data):
    task_root_dir = os.path.join("LLM_PublicHouseAllocation/tasks",data)
    configs = os.listdir(os.path.join(task_root_dir,"configs"))
    for config in configs:
        config_path = os.path.join(task_root_dir,"configs",config)
        result_path = os.path.join(config_path,"result")
        if os.path.exists(result_path):
            shutil.rmtree(result_path)
            
def clear_unfinished_ex_data(data):
    task_root_dir = os.path.join("LLM_PublicHouseAllocation/tasks",data)
    configs = os.listdir(os.path.join(task_root_dir,"configs"))
    for config in configs:
        config_path = os.path.join(task_root_dir,"configs",config)
        result_path = os.path.join(config_path,"result")
        if os.path.exists(result_path):
            results = os.listdir(result_path)
            for result_one in results:
                result_one_path = os.path.join(result_path,result_one)
                if not os.path.exists(os.path.join(result_one_path,"all")):
                    shutil.rmtree(result_one_path)
            results = os.listdir(result_path)
            if len(results) ==0:
                shutil.rmtree(result_path)
            
            
            
def set_data_configs(data):
    task_dir ="LLM_PublicHouseAllocation/tasks"
    
    config_root = os.path.join(task_dir,data,"configs")
    task_names = os.listdir(config_root)


    # task_names = list(filter(lambda x: 
    #     not os.path.exists(os.path.join(config_root,x,"result")),
    #                          task_names))
    
    dirs = {
        "house":"",
        "tenant":"",
        "forum":"",
        "community":""
    }
    
    distribution_batch_dir={
        "tenant":"",
        "community":""
    }
    
    data_files = os.listdir(os.path.join(task_dir,data,"data"))
    
    data_files = list(filter(lambda x:x!="visualize",data_files))
    
    for data_type  in dirs.keys():
        for data_file in data_files:
            if (data_type in data_file):
                dirs[data_type] = os.path.join("data",data_file)
                break
    
    for task_name in task_names:
        config_path = os.path.join(config_root,task_name,"config.yaml")
        task_config = yaml.safe_load(open(config_path))
        
        distribution_data_paths = os.listdir(os.path.join(config_root,task_name,"data"))
        for data_path in distribution_data_paths:
            if "tenant" in data_path:
                distribution_batch_dir["tenant"] =  os.path.join("data",data_path)
            else: distribution_batch_dir["community"] = os.path.join("data",data_path)
        
        for data_type,data_dir in dirs.items():
            task_config["managers"][data_type]["data_dir"] = data_dir
        
        for distribution_key,distribution_path in distribution_batch_dir.items():
            task_config["managers"][distribution_key]["distribution_batch_dir"] = distribution_path

            
        task_config["name"] = task_name
        with open(config_path, 'w') as outfile:
            yaml.dump(task_config, outfile, default_flow_style=False)
    
    
def replace_distribution_batch(data):
    task_dir ="LLM_PublicHouseAllocation/tasks"
    
    config_root = os.path.join(task_dir,data,"configs")
    task_names = os.listdir(config_root)
    
    origin_name = "distribution_batch_28_3.json"
    
    new_name = "distribution_batch_39_3_1.json"
    
    new_json_path = "test/generate_data/distribution_batch_39_3_1.json"
    
    for task_name in task_names:
        if os.path.exists(os.path.join(config_root,task_name,"data",origin_name)):
            origin_file = readinfo(os.path.join(config_root,task_name,"data",origin_name))
            assert len(origin_file)==3
            assert list(origin_file.keys())[1]=="1"
            os.remove(os.path.join(config_root,task_name,"data",origin_name))
            shutil.copyfile(new_json_path,
                            os.path.join(config_root,task_name,"data",new_name))
        
    
if __name__ == "__main__":
    
    task_dir ="LLM_PublicHouseAllocation/tasks"
    # data = "PHA_51tenant_5community_28house"
    
    data = "PHA_51tenant_5community_28house_new_priority_label"
    
    # data = "PHA_51tenant_5community_39house_new_priority_label"
    
    config_root = os.path.join(task_dir,data,"configs")
    task_names = os.listdir(config_root)

    
    task_names =[
        "ver2_nofilter_multilist(1.2_k2)_housetype_priority_2t_2h(step_num(t5_h5))_p#housetype_choose2",
        "ver2_nofilter_multilist_1.2_k2_housetype_priority_5t_3h_step_num_t2_h3_p#housetype_choose2",
        "ver2_nofilter_multilist(1.2_k2)_housetype_priority_8t_6h(step_num(t1_h1))_p#portion_rentmoney",
        "ver2_nofilter_multilist(1.8_k2)_housetype_priority_8t_6h(step_num(t1_h1))_p#housetype_choose2",
        "ver2_nofilter_multilist(1.2_k2)_housetype_priority_5t_3h(step_num(t2_h3))_p#housetype_choose2",
        "ver2_nofilter_multilist(1.5_k3)_housetype_priority_8t_6h(step_num(t1_h1))_p#housetype_choose3",
        "ver2_nofilter_multilist(1.2_k1)_housetype_priority_8t_6h(step_num(t1_h1))_p#housetype_choose1",
        "ver1_nofilter_singlelist_2t_6h(step_num(t1_h1))_p#singlelist",
        "ver1_nofilter_multilist(1.2)_portion5(f_member_num)_priority_8t_6h_p#portion_housesize"
    ]
    
    # task_names = list(filter(lambda x: 
    #     not os.path.exists(os.path.join(config_root,x,"result")),
    #                          task_names))
    
    
    # task_names =["ver1_nofilter_multilist(1.5)_portion3(f_member_num)_priority_8t_6h_p#portion_housesize",
    #     "ver2_nofilter_multilist(1.8_k1)_housetype_priority_8t_6h(step_num(t1_h1))_p#housetype_choose3",
    #     "ver1_nofilter_singlelist_5t_3h_p#singlelist",
    #     "ver2_nofilter_multilist(1.2_k1)_housetype_priority_8t_6h(step_num(t1_h1))_p#housetype_choose3",
    #     "ver1_nofilter_singlelist_2t_6h(step_num(t3_h1))_p#singlelist"]
    
    log_dir = f"LLM_PublicHouseAllocation/tasks/{data}/cache"
    


    run_tasks(task_names,
              data,
              log_dir)
    
    # replace_distribution_batch(data)
    
    # set_data_configs(data)
    
    # run_tasks_logs()
    
    # test_task_logs()
    
    
    """ 请谨慎执行，确保备份 """
    # clear_cache_ex_data(data)
    
    # clear_unfinished_ex_data(data)