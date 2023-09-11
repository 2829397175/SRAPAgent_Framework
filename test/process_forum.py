import os
import json


tenant_dir="LLM_PublicHouseAllocation/tasks/PHA_50tenant_3community_19house/data/tenant.json"
with open(tenant_dir,'r',encoding = 'utf-8') as f:
    tenant_datas = json.load(f)


def search_id(name):
    for tenant_id,tenant_info in tenant_datas.items():
        if (tenant_info.get("name","")==name):
            return tenant_id

def generate_personality():
    personlity_str="""Outgoing: Friendly, sociable, and extroverted, enjoys being around people and thrives in social situations.

Introverted: Reserved, reflective, and often prefers solitude or small group settings to recharge.

Confident: Self-assured, poised, and has a strong belief in their abilities.

Insecure: Lacks self-confidence, often doubting their abilities or self-worth.

Optimistic: Positive outlook on life, always sees the silver lining in situations.

Pessimistic: Tends to focus on the negative aspects of situations, expecting the worst.

Adventurous: Enjoys taking risks and seeking out new experiences and challenges.

Cautious: Prefers to play it safe, carefully considering potential risks and consequences.

Empathetic: Highly attuned to the emotions and needs of others, often offering support and understanding.

Self-centered: Primarily concerned with their own needs and desires, often oblivious to the needs of others.

Compassionate: Demonstrates kindness and empathy toward others, often going out of their way to help.

Competitive: Thrives on challenges and strives to outperform others in various aspects of life.

Cooperative: Values collaboration and teamwork, often prioritizing group goals over personal success.

Stubborn: Resistant to change or new ideas, often sticking to their own beliefs or opinions.

Open-minded: Willing to consider new ideas and perspectives, adaptable to change.

Impatient: Has a low tolerance for delays or waiting, often seeking immediate results.

Patient: Can endure delays and setbacks calmly, willing to wait for the right moment.

Loyal: Devoted and committed to their relationships and obligations.

Fickle: Easily changes their mind or loyalties, often without a clear reason.
"""
    personlity_list = personlity_str.split("\n\n")
    
    for tenant_id,tenant_info in tenant_datas.items():
        personlity= personlity_list.pop()
        personlity = personlity.replace(":",",")
        tenant_info["personlity"] =  personlity.strip().lower()
        
        
generate_personality()

# for file_dir in files_dir:
#     with open(experiment_dir+file_dir+"/data/forum.json",'r',encoding = 'utf-8') as f:
#         forum_datas = json.load(f)
#     forum_new={}
#     for com_id,com_info in forum_datas.items():
#         com_new={}
#         for tenant_name,infos in com_info.items():
#             tenant_id = search_id(tenant_name)
#             com_new[tenant_id] = infos
#         forum_new[com_id]=com_new
#     with open(experiment_dir+file_dir+"/data/forum.json", encoding='utf-8', mode='w') as fr:
#         json.dump(forum_new, fr, indent=4, separators=(',', ':'), ensure_ascii=False)

# for file_dir in files_dir:
#     with open(experiment_dir+file_dir+"/data/house.json",'r',encoding = 'utf-8') as f:
#         house_ori_datas = json.load(f)
#     with open(experiment_dir+file_dir+"/result/house.json",'r',encoding = 'utf-8') as f:
#         house_res_datas = json.load(f)
    
#     houses_new={}
    
#     for com_id, houses in house_ori_datas.items():
#         for house_id,house_info in houses.items():
#             house_info["available"]=house_res_datas[house_id]["available"]
#             houses_new.update({house_id:house_info})
            
#     with open(experiment_dir+file_dir+"/result/house.json", encoding='utf-8', mode='w') as fr:
#         json.dump(houses_new, fr, indent=4, separators=(',', ':'), ensure_ascii=False)

# group_size=5
# relation="friend"

# for idx in range(int(51/group_size)):
#     id_g_tenants=[f"{idx*group_size+id_g}" 
#                   for id_g in range(group_size)]
    
#     for id_g in range(group_size):
#         id_t = f"{idx*group_size+id_g}"
#         id_g_tenants_temp=id_g_tenants.copy()
#         id_g_tenants_temp.remove(id_t)
#         tenant_info = tenant_datas[id_t]
#         tenant_info["friends"]={}
#         for id_g_ in id_g_tenants_temp:
#             tenant_info["friends"][id_g_]={"relation":relation}

# id_g_tenants=[f"{id_}"  for id_ in range(int(51/group_size)*group_size,51)]     
   
# for id_t in range(int(51/group_size)*group_size,51):
#     id_t = f"{id_t}"
#     id_g_tenants_temp=id_g_tenants.copy()
#     id_g_tenants_temp.remove(id_t)
#     tenant_info = tenant_datas[id_t]
#     tenant_info["friends"]={}
#     for id_g_ in id_g_tenants_temp:
#         tenant_info["friends"][id_g_]={"relation":relation}

        
with open(tenant_dir, encoding='utf-8', mode='w') as fr:
    json.dump(tenant_datas, fr, indent=4, separators=(',', ':'), ensure_ascii=False)
