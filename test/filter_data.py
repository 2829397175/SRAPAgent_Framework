import json
import numpy as np
import random
# 从tenant 数据集中，挑选部分社交子网
import copy

def filter_tenant(num = 50):
    with open("test\generate_data/tenant_70.json",'r',encoding = 'utf-8') as f:
        tenant_json = json.load(f)
        
    
    tenant_ids = list(tenant_json.keys())
    
    collected_ids = []
    
    def collect_net(tenant_id,cur_num =0, num=50):
        if (cur_num>num):
            return 
        tenant_sn_ids = list(tenant_json[tenant_id]["social_network"].keys())
        
        for t_id in tenant_sn_ids:
            if t_id not in collected_ids:
                collected_ids.append(t_id)
                tenant_ids.remove(t_id)
                cur_num += 1
                cur_num += collect_net(t_id)

        return cur_num
    cur_num = 0
    while(cur_num<num):
        tenant_id = tenant_ids.pop()
        if tenant_id not in collected_ids:
            collected_ids.append(tenant_id)
            cur_num += 1
            cur_num = collect_net(tenant_id,cur_num=cur_num,num=num)

                
    collected_infos = {}
    for t_id in collected_ids:
        collected_infos.update({t_id:tenant_json[t_id]})
    
    # check sn
    
    for t_id,t_info in collected_infos.items():
        sn_ids = list(t_info["social_network"].keys())
        for sn_id in sn_ids:
            assert sn_id in list(collected_infos.keys()),f"{sn_id}"
        
    
    with open(f"test\generate_data/tenant_{cur_num}.json",'w',encoding = 'utf-8') as f:
        json.dump(collected_infos, f, indent=4,separators=(',', ':'),ensure_ascii=False)
        
        
def filter_house(num = 3,
                  house_type_ratios = {"large_house":4,
                                       "middle_house":5,
                                       "small_house":1}
                  # 不规定ratio 则设为none
                  ):
    with open("test/generate_data/community.json",'r',encoding = 'utf-8') as f:
        community_json = json.load(f)
        
    with open("test/generate_data/house_diverse_100.json",'r',encoding = 'utf-8') as f:
        house_json = json.load(f)
        
    
    
    
    rate = num/ sum([len(house_list) for house_list in house_json.values()])
    
    
    if house_type_ratios is not None:
        
        cur_num = 0
        for c_id,c_info in community_json.items():
            c_name = c_info["community_name"]
            temp_ratio = copy.deepcopy(house_type_ratios)
            for house_type in house_type_ratios.keys():
                if house_type not in c_info.keys():
                    del temp_ratio[house_type]
            sum_ratio = sum(list(temp_ratio.values()))
            for k,v in temp_ratio.items():
                temp_ratio[k] = v/sum_ratio
            house_indexs =[]
            for house_type_key in temp_ratio.keys():
                house_type_len = int(temp_ratio[house_type_key]*c_info[house_type_key]["remain_number"])
                house_indexs.extend(random.sample(c_info[house_type_key]["index"],house_type_len))
                
            house_json[c_name] = {h_id:house_json[c_name][h_id] for h_id in house_indexs}
        
            cur_num += len(house_indexs)
                    
                
    else:  
        cur_num = 0

        for c_name, c_houses in house_json.items():
            
            
            random_h_ids = random.sample(list(c_houses.keys()),int(rate*len(c_houses)))
            house_json[c_name] = {h_id:c_houses[h_id] for h_id in random_h_ids}
            
            cur_num += len(random_h_ids)
        
        
    house_type_indexs =["large_house","small_house","middle_house"]
    for c_name, c_houses in house_json.items():
        for c_id,c_info in community_json.items():
            if c_name == c_info["community_name"]:
                break
                
        sum_h =0
        for house_type in house_type_indexs:
            if house_type in c_info.keys():
                house_type_info = c_info[house_type]
                house_indexs = house_type_info["index"]
                f_h_indexs = []
                for house_index in house_indexs:
                    if house_index in c_houses.keys():
                        f_h_indexs.append(house_index)
                house_type_info["index"] = f_h_indexs
                house_type_info["remain_number"] = len(f_h_indexs)
                sum_h += len(f_h_indexs)
                
        c_info["sum_num"] = sum_h
        c_info["sum_remain_num"] = sum_h
                
    with open(f"test/generate_data/house_{cur_num}.json",'w',encoding = 'utf-8') as f:
        json.dump(house_json, f, indent=4,separators=(',', ':'),ensure_ascii=False)
        
    with open(f"test/generate_data/community_{cur_num}.json",'w',encoding = 'utf-8') as f:
        json.dump(community_json, f, indent=4,separators=(',', ':'),ensure_ascii=False)
        
        
def distribution_batch(run_turns,cur_num,step_num =1):
    with open(f"test/generate_data/house_{cur_num}.json",'r',encoding = 'utf-8') as f:
        house_json = json.load(f)
    
    house_ids = []
    for c_name in house_json.keys():
        house_ids.extend(list(house_json[c_name].keys()))
    random.shuffle(house_ids)
    
    def avg_groups(data, num_groups):
        n_per_group = len(data) // num_groups
        end_p = n_per_group*num_groups
        if end_p == len(data):
            end_p = -1
            groups = np.array(data).reshape(num_groups,n_per_group)
        else:
            groups = np.array(data[:end_p]).reshape(num_groups,n_per_group)
        groups = groups.tolist()
        if (end_p != -1):
            groups[-1].extend(data[end_p:])
        return groups
    
    run_turns_range = run_turns*step_num
    assert run_turns < len(house_ids),"error !!"
    
    grouped_house_ids = avg_groups(house_ids,run_turns)
    run_turns = len(grouped_house_ids)
    distribution_batch ={}
    run_turns_list = range(0,run_turns_range,step_num)
    for group,grouped_houses in zip(run_turns_list,grouped_house_ids):
        distribution_batch[group] =  grouped_houses
        
    with open(f"test/generate_data/distribution_batch_{cur_num}_{run_turns}_{step_num}.json",'w',encoding = 'utf-8') as f:
        json.dump(distribution_batch, f, indent=4,separators=(',', ':'),ensure_ascii=False)
    
    
def distribution_batch_tenant(run_turns,cur_num,step_num = 1):
    with open(f"test/generate_data/tenant_{cur_num}.json",'r',encoding = 'utf-8') as f:
        tenant_json = json.load(f)
    
    tenant_ids = list(tenant_json.keys())
    
    
    def avg_groups(data, num_groups):
        n_per_group = len(data) // num_groups
        end_p = n_per_group*num_groups
        if end_p == len(data):
            end_p = -1
            groups = np.array(data).reshape(num_groups,n_per_group)
        else:
            groups = np.array(data[:end_p]).reshape(num_groups,n_per_group)
        groups = groups.tolist()
        if (end_p != -1):
            groups[-1].extend(data[end_p:])
        return groups
    
    run_turns_range = run_turns*step_num
    assert run_turns < len(tenant_ids),"error !!"
    
    grouped_tenant_ids = avg_groups(tenant_ids,run_turns)
    run_turns = len(grouped_tenant_ids)
    distribution_batch ={}
    run_turns_list = range(0,run_turns_range,step_num)
    for group,grouped_tenants in zip(run_turns_list,grouped_tenant_ids):
        distribution_batch[group] =  grouped_tenants
        
    with open(f"test/generate_data/distribution_batch_tenant_{cur_num}_{run_turns}_{step_num}.json",'w',encoding = 'utf-8') as f:
        json.dump(distribution_batch, f, indent=4,separators=(',', ':'),ensure_ascii=False)
    

               
    
if __name__ =="__main__":
    # filter_tenant(num=5)
    # filter_house(num=30)
    distribution_batch(6,100,1)
    # distribution_batch_tenant(8,70,1)