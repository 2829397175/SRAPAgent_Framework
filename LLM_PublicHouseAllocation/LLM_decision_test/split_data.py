import json

import os

def split_save_response(json_types,
                        limit = 100,
                        num_groups = 10,
                        save_dir ="LLM_PublicHouseAllocation\LLM_decision_test\qa_clear_data\groups"
                        ):
    
    import numpy as np
    import random
    def avg_groups(data, num_groups):
        random.shuffle(data)
        n_per_group = len(data) // num_groups
        end_p = n_per_group*num_groups
        if end_p == len(data):
            end_p = -1
            groups = np.array(data).reshape(num_groups, n_per_group)
        else:
            groups = np.array(data[:end_p]).reshape(num_groups, n_per_group)
            
        groups = groups.tolist()
        if (end_p != -1):
            groups.append(data[end_p:])
        return groups
    
    
    for json_type in json_types:
        json_dir = "LLM_PublicHouseAllocation\LLM_decision_test\qa_clear_data\{}_qa.json".format(json_type)
        with open(json_dir,'r',encoding = 'utf-8') as f:
            data = json.load(f)
            
        data = data[:limit]
        
        
        data_groups = avg_groups(data,num_groups)        

        data_json_type_dir = os.path.join(save_dir,
                                          json_type)
        if not os.path.exists(data_json_type_dir):
            os.makedirs(data_json_type_dir)
        
        with open(os.path.join(save_dir,f"{json_type}_qa_{limit}.json"),'w',encoding = 'utf-8') as f:
            json.dump(data,f, indent=4,separators=(',', ':'),ensure_ascii=False)
        
        for idx,data_group in enumerate(data_groups):
            json_path = os.path.join(data_json_type_dir,
                                     f"{json_type}_qa_{idx}.json")
            
            with open(json_path,'w',encoding = 'utf-8') as f:
                json.dump(data_group,f, indent=4,separators=(',', ':'),ensure_ascii=False)

if __name__ =="__main__":
    
    json_types = ["community","house","housetype"]
    split_save_response(json_types)