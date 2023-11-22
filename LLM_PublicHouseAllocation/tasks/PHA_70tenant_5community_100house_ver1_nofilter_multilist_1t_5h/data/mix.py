import json
import os

description_path="LLM_PublicHouseAllocation/tasks/PHA_70tenant_5community_100house_ver1_nofilter_multilist_1t_5h/data/description.json"
house_path="LLM_PublicHouseAllocation/tasks/PHA_70tenant_5community_100house_ver1_nofilter_multilist_1t_5h/data/house_100.json"
assert os.path.exists(description_path),"no such file path: {}".format(description_path)
with open(description_path,'r',encoding = 'utf-8') as f:
    description_data = json.load(f)
    
assert os.path.exists(house_path),"no such file path: {}".format(house_path)
with open(house_path,'r',encoding = 'utf-8') as f:
    house_data = json.load(f)
    
house_num=0
for community_name,house_datas in house_data.items():
    for house_id,house_info in house_datas.items():
        house_info["description"]=description_data[house_num]["description"]
        house_info["potential_information_house"]=description_data[house_num]["potential_information_house"]
        house_num+=1
        
with open(house_path, 'w', encoding='utf-8') as file:
    json.dump(house_data, file, indent=4,separators=(',', ':'),ensure_ascii=False)
        