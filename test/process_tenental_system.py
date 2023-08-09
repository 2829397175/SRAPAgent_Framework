import os
import json
import re

root_dir=os.getcwd()
dirs=["/experiments/experiment_9/filtered_data/",
      "/experiments/experiment_8/filtered_data/"]

c_dir="/LLM_PublicHouseAllocation/tasks/PHA_50tenant_3community_19house/data/community.json"
with open(root_dir+c_dir,'r',encoding = 'utf-8') as f:
    community_datas = json.load(f)

for dir_ in dirs:
    with open(root_dir+dir_+"tenantal_system.json",'r',encoding = 'utf-8') as f:
        tenental = json.load(f)
    
    for output in tenental:
        c_des = output["community_available_description"]
        
        
        regex = r"There are (\d+) communitys available"
        match = re.search(regex, c_des, re.DOTALL)
        assert match.group(1) is not None
        new_c_des=""
        c_num = int(match.group(1))
        idx=0
        c_template="""{community_name}:
located at {en_location}. {description}
"""
        template="""There are {num} communitys available. The infomation of these communitys are listed as follows:
{c_des}"""
        for c_name in ["community_1","community_2","community_3"]:
            if c_name in c_des:
                new_c_des+=c_template.format_map(community_datas[c_name])
                idx+=1
        assert c_num ==idx
        
        new_c_des=template.format(num=c_num,
                                    c_des=new_c_des)
        new_c_des = new_c_des.replace("..",".")
        output["community_available_description"]=new_c_des

    with open(root_dir+dir_+"tenantal_system.json",'w',encoding = 'utf-8') as f:
        json.dump(tenental, f, indent=4, separators=(',', ':'), ensure_ascii=False)
        
        