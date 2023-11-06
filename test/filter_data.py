import json
import numpy as np
import random
# 从tenant 数据集中，挑选部分社交子网

def filter_tenant(num = 50):
    with open("test\generate_data/tenant.json",'r',encoding = 'utf-8') as f:
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
        
        
def filter_house(num = 30):
    with open("test\generate_data/community.json",'r',encoding = 'utf-8') as f:
        community_json = json.load(f)
        
    with open("test\generate_data/house.json",'r',encoding = 'utf-8') as f:
        house_json = json.load(f)
        
    
    rate = 30/ 100
    
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
                
    with open(f"test\generate_data/house_{cur_num}.json",'w',encoding = 'utf-8') as f:
        json.dump(house_json, f, indent=4,separators=(',', ':'),ensure_ascii=False)
        
    with open(f"test\generate_data/community_{cur_num}.json",'w',encoding = 'utf-8') as f:
        json.dump(community_json, f, indent=4,separators=(',', ':'),ensure_ascii=False)
        
        
def distribution_batch(run_turns,cur_num):
    with open(f"test\generate_data/house_{cur_num}.json",'r',encoding = 'utf-8') as f:
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
            groups.append(data[end_p:])
        return groups
    
    grouped_house_ids = avg_groups(house_ids,run_turns)
    run_turns = len(grouped_house_ids)
    distribution_batch ={}
    for group,grouped_houses in zip(range(run_turns),grouped_house_ids):
        distribution_batch[group] =  grouped_houses
        
    with open(f"test\generate_data/distribution_batch_{cur_num}_{run_turns}.json",'w',encoding = 'utf-8') as f:
        json.dump(distribution_batch, f, indent=4,separators=(',', ':'),ensure_ascii=False)
    
    
def distribution_batch_tenant(run_turns,cur_num):
    with open(f"test\generate_data/tenant_{cur_num}.json",'r',encoding = 'utf-8') as f:
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
            groups.append(data[end_p:])
        return groups
    
    grouped_tenant_ids = avg_groups(tenant_ids,run_turns)
    run_turns = len(grouped_tenant_ids)
    distribution_batch ={}
    for group,grouped_tenants in zip(range(run_turns),grouped_tenant_ids):
        distribution_batch[group] =  grouped_tenants
        
    with open(f"test\generate_data/distribution_batch_tenant_{cur_num}_{run_turns}.json",'w',encoding = 'utf-8') as f:
        json.dump(distribution_batch, f, indent=4,separators=(',', ':'),ensure_ascii=False)
    

               
    
if __name__ =="__main__":
    # filter_tenant()
    # filter_house()
    distribution_batch(5,100)
    # distribution_batch_tenant(1,70)