import json
import random
import os
import shutil

def split_save_response(json_types,
                        limit = 100,
                        num_groups = 10,
                        save_dir ="LLM_PublicHouseAllocation\LLM_decision_test\qa_clear_data\groups",
                        data_dir ="LLM_PublicHouseAllocation\LLM_decision_test\qa_clear_data"
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
        json_dir = os.path.join(data_dir,"{}_qa.json".format(json_type))
        with open(json_dir,'r',encoding = 'utf-8') as f:
            data = json.load(f)
            
        random.shuffle(data)
        data = data[:limit]
        
        
        data_groups = avg_groups(data,num_groups)        

        data_json_type_dir = os.path.join(save_dir,
                                          json_type)
        if not os.path.exists(data_json_type_dir):
            os.makedirs(data_json_type_dir)
        else:
            shutil.rmtree(data_json_type_dir)
            os.makedirs(data_json_type_dir)
        
        with open(os.path.join(save_dir,f"{json_type}_qa_{limit}.json"),'w',encoding = 'utf-8') as f:
            json.dump(data,f, indent=4,separators=(',', ':'),ensure_ascii=False)
        
        data_types=["judge","save_response"]
        for idx,data_group in enumerate(data_groups):
            for data_type in data_types:
                json_path = os.path.join(data_json_type_dir,
                                     f"{json_type}_qa_{idx}_{data_type}.json")
                if data_type =="save_response":
                    for data_one in data_group:
                        data_one["response"] = {}
                with open(json_path,'w',encoding = 'utf-8') as f:
                    json.dump(data_group,f, indent=4,separators=(',', ':'),ensure_ascii=False)

def shuffle_for_user(json_types,
                    user_index=0,
                    save_dir ="LLM_PublicHouseAllocation\LLM_decision_test\qa_unclear_data\\filtered\groups",
                    data_dir ="LLM_PublicHouseAllocation\LLM_decision_test\qa_unclear_data\\filtered\groups"
                 ):
    user_index_map={
        0:6,
        1:9,
        2:7,
        3:4,
        4:3,
        5:8,
        6:0,
        7:2,
        8:5,
        9:1
    }
    
    data_types=["judge","save_response"]
    
    mixed_json = []
    for json_type in json_types:

        mapped_index = user_index_map[user_index]
        for data_type in data_types:
            json_dir = os.path.join(save_dir, json_type,f"{json_type}_qa_{mapped_index}_{data_type}.json")
            with open(json_dir,'r',encoding = 'utf-8') as f:
                data_ = json.load(f)
            for data_one in data_:
                data_one["humanjudge"] = data_type == "save_response"
           
            mixed_json.extend(data_)
            
    random.shuffle(mixed_json)
    save_dir = os.path.join(save_dir,"mixed_judge_data")
    if not os.path.exists(save_dir):
            os.makedirs(save_dir)
    else:
        # shutil.rmtree(save_dir)
        # os.makedirs(save_dir)
        pass
    for data in mixed_json:
        assert data["response"]!={}
        
    save_path = os.path.join(save_dir,f"{user_index}_judge.json")
    if os.path.exists(save_path):
        os.unlink(save_path)
    with open(save_path,'w',encoding = 'utf-8') as f:
        json.dump(mixed_json,f, indent=4,separators=(',', ':'),ensure_ascii=False)
     

def shuffle_for_user_human(json_types,
                    user_index=0,
                    users_index =list(range(10)),
                    data_len_limit = 30,
                    save_dir ="LLM_PublicHouseAllocation\LLM_decision_test\qa_unclear_data\\filtered\groups",
                    data_dir ="LLM_PublicHouseAllocation\LLM_decision_test\qa_unclear_data\\filtered\groups"
                 ):
    
    data_types=["save_response"]
    
    mixed_json = []
    assert user_index in users_index
    users_index.remove(user_index)
    
    for json_type in json_types:
        for other_index in users_index:
            for data_type in data_types:
                json_dir = os.path.join(save_dir, json_type,f"{json_type}_qa_{other_index}_{data_type}.json")
                with open(json_dir,'r',encoding = 'utf-8') as f:
                    data_ = json.load(f)
                for data_one in data_:
                    data_one["humanjudge"] = data_type == "save_response"
            
                mixed_json.extend(data_)
            
    random.shuffle(mixed_json)
    mixed_json = random.sample(mixed_json,data_len_limit)
    
    save_dir = os.path.join(save_dir,"mixed_human_data")
    if not os.path.exists(save_dir):
            os.makedirs(save_dir)
    else:
        # shutil.rmtree(save_dir)
        # os.makedirs(save_dir)
        pass
    for data in mixed_json:
        assert data["response"]!={}
        
    save_path = os.path.join(save_dir,f"{user_index}_judge.json")
    if os.path.exists(save_path):
        os.unlink(save_path)
    with open(save_path,'w',encoding = 'utf-8') as f:
        json.dump(mixed_json,f, indent=4,separators=(',', ':'),ensure_ascii=False)
     


if __name__ =="__main__":
    
    json_types = ["community","house","housetype"]
    data_dir = "LLM_PublicHouseAllocation\LLM_decision_test\qa_unclear_data\\filtered"
    save_dir ="LLM_PublicHouseAllocation\LLM_decision_test\qa_unclear_data\\filtered\groups"
    # split_save_response(json_types,
    #                     data_dir=data_dir,
    #                     save_dir=save_dir)
    
    # 标注版本10人
    # shuffle_for_user(json_types,
    #                  3,
    #                  save_dir=save_dir,
    #                  data_dir=data_dir)
    
    # 后续和实验data的混杂版本，仅仅为i号标注者 取人类标注数据
    shuffle_for_user_human(json_types=json_types,
                           user_index=0)
