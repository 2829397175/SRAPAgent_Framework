from pydantic import BaseModel

from . import policy_optimizer_registry

from typing import Any
import os

import numpy as np
import pandas as pd

from sklearn.preprocessing import MinMaxScaler

from sklearn.preprocessing import LabelEncoder,OneHotEncoder

import warnings
import random
import json
import yaml
import copy
@policy_optimizer_registry.register("base")
class BaseOptimizer(BaseModel):
    
    indicators:dict = {}
    features:dict = {}
    
    x_attrs:pd.DataFrame
    x_dummys:pd.DataFrame
    y_attrs:pd.DataFrame
    
    encoders :dict = {} # col_name：encoder
    
    x:np.ndarray =[]
    y:np.ndarray =[]
    
    weights_y: np.ndarray = []
    normalize: bool= False # 是否要对x对归一化处理
    normalizer: Any = None
    
    ## 用于优化的base_config
    base_config :dict = {}
    ## 优化后的config
    optimized_config:dict = {}
    
    data_setting:str = "" # 记录task文件夹内的data
    
    class Config:
        arbitrary_types_allowed = True
        
        
    
        
    
    @classmethod
    def load_data(cls,
                  data:str,
                  experiment_dir = "LLM_PublicHouseAllocation/experiments",
                  tasks_dir = "LLM_PublicHouseAllocation/tasks",
                  load_feature_col = "all",
                  normalize :bool = False,
                  ):
        indicators:dict = {"up":{"mean_house_area":1,
                           "sw":1,
                            "F(W,G)":1
                            },# indcitor:weight
                       "down": { 
                            "var_mean_house_area":1,
                            "Rop":1,
                            "mean_wait_turn":1,
                            "GINI_index":1
                            } # indcitor:weight
                       }
        features:dict = {"data":["distribution_batch_house_distribution_len",
                                "distribution_batch_house_distribution_step",
                                "distribution_batch_tenant_distribution_len",
                                "distribution_batch_tenant_distribution_step",
                                "environment_max_turns",
                                "group_size",
                                "group_policy_priority",
                                "tenant_max_choose",
                                "order_k",
                                ],
                        "str":[
                            "group_policy_type",
                            "community_patch_method" ,
                            "policy_type",
                            "order_type",
                            "community_patch_method"
                        ]}
        data_dir =  os.path.join(experiment_dir,data,"all")
        assert os.path.exists(data_dir),f"{data_dir} not exist!!"
        
        config_path = os.path.join(tasks_dir,data,"optimize","base_config.yaml")
        config = yaml.safe_load(open(config_path))
        
        objective_matrix_path = os.path.join(data_dir,"objective_evaluation_matrix.csv")
        objective_matrix = pd.read_csv(objective_matrix_path,index_col=0)
        
        utility_matrix_path = os.path.join(data_dir,"utility_eval_matrix.csv")
        utility_matrix = pd.read_csv(utility_matrix_path,index_col=0)
        
        matrix = pd.concat([objective_matrix,utility_matrix])
        
        
        y_attrs = []
        x_attrs = []
        
        """load y"""
        ex_results = matrix.groupby("ex_idx")
        for ex_idx,ex_result in ex_results:
            y_vector ={}
            for type_indicator,indicators_ in indicators.items():
                for indicator in indicators_.keys():
                    if indicator in ex_result.index:
                        y_vector[indicator] = ex_result.loc[indicator,load_feature_col]
            y_attrs.append(y_vector)
            
            x_vector = {}
            for type_x,x_names in features.items():
                for x_name in x_names:
                    x_vector[x_name] = ex_result[x_name].values[0]
            x_attrs.append(x_vector)
       
        y_attrs = pd.DataFrame(y_attrs)
        # 创建MinMaxScaler对象
        scaler = MinMaxScaler()

        # 使用fit_transform方法对DataFrame进行归一化
        y_attrs_normalize = scaler.fit_transform(y_attrs.values)
        
        for idx,indicator in enumerate(y_attrs.columns):
            y_attrs[f"{indicator}_normalize"] = y_attrs_normalize[:,idx]
        
        for indicator_down in indicators.get("down",[]):
            y_attrs[f"{indicator_down}_normalize"] = 1-y_attrs[f"{indicator_down}_normalize"]
            
        y = y_attrs.loc[:,list(filter(lambda col_name:"normalize" in col_name, y_attrs.columns))].values
        weights_y = []
        for column_name in y_attrs.columns:
            for type_indicator,indicators_ in indicators.items():
                if column_name in indicators_.keys():
                    weights_y.append(indicators_[column_name])
                    
        
        assert not y_attrs.isna().any().any(), "Y contain NAN !!"
        
        
        x_attrs = pd.DataFrame(x_attrs)
        
        x_dummys = x_attrs.loc[:,features["data"]]
        x_dummys["order_k"] = x_dummys["order_k"].fillna(1)
        
        
        x_dummys = x_dummys.astype(int)
        encoders = {}
        for feature_name in features["str"]:
            x = x_attrs[feature_name]
            enc = OneHotEncoder()          # 初始化
            enc.fit(x_attrs[[feature_name]].values)    # 模型拟合。注意：data[['一键三连']]是一个dataframe，与data['一键三连']是一个series不同
            array_data = enc.transform(x_attrs[[feature_name]].values).toarray()
            encoders[feature_name]=enc
            for idx in range(array_data.shape[1]):
                x_dummys[f"{feature_name}_transformed_{idx}"] = array_data[:,idx]

       
        x = x_dummys.values
        assert not x_dummys.isna().any().any(), "X contain NAN !!"
        
        
        if (normalize):
            from sklearn.preprocessing import StandardScaler
            normalizer = StandardScaler()
            normalizer = normalizer.fit(x)
            x = normalizer.transform(x)
            
        else:
            normalizer = None
            
        return cls(
            x = x,
            y = y,
            normalize = normalize,
            normalizer = normalizer,
            x_attrs = x_attrs,
            x_dummys = x_dummys,
            encoders = encoders,
            y_attrs = y_attrs,
            features = features,
            indicators = indicators,
            weights_y = np.array(weights_y),
            base_config = config,
            data_setting = data
            
        )
        
    def decode_x(self,
                 x_vector): # 一维：默认data+str的格式排列vector数据
        
        if self.normalize:
            restored_vector = self.normalizer.inverse_transform([x_vector])
            x_vector = restored_vector[0]
                
        x_reverse = np.array(x_vector[:len(self.features["data"])]).tolist()
        x_reverse = np.round(x_reverse).astype(int)
        x_reverse_dict = {feature_name:x_reverse[idx] for idx,feature_name in enumerate(self.features["data"])}
        left_p = len(self.features["data"])
        for feature_name in self.features["str"]:
            # 获取编码后向量的维度
            enc = self.encoders[feature_name]
            num_features = len(enc.get_feature_names_out())
            encoded_x_ = x_vector[left_p:left_p+num_features]
            # 使用 inverse_transform 方法将编码后的数据映射回原始值
            encoded_x_ = np.round(encoded_x_).astype(int)
            if (encoded_x_.sum(axis=0) == 1).all():
                decoded_data = enc.inverse_transform([encoded_x_])[0].tolist()[0]
            else:
                warnings.warn("the optimal answer is not a legal vecotr, so the choice is random given")
                decoded_data = random.choice(self.x_attrs[feature_name])
            
            x_reverse_dict[feature_name] = decoded_data            
            left_p +=num_features
            
        # x_reverse = np.round(encoded_x_).astype(int)
        # for idx, feature_name in enumerate(self.features):
            
        return x_reverse_dict
            
        
    def encode_x(self,
                 x:np.ndarray): # x是一维的
        assert x.shape[0] == self.x_attrs.shape[1],"illegal number of x vector dimensions"
        
        x_encoded_ =  []
        for idx,x_ in enumerate(x):
            indicator_name = self.x_attrs.columns[idx]
            if indicator_name in self.features["str"]:
                enc = self.encoders.get(indicator_name)
                transformed_x_ = enc.transform([[x_]]).toarray()[0].tolist()
                x_encoded_.extend(transformed_x_)
            else:
                try:
                    x_encoded_.append(int(x_))
                except:
                    x_encoded_.append(int(bool(x_)))
                
        x_encoded_ = np.array(x_encoded_)
        if self.normalize:
            x_encoded_ = self.normalizer.transform([x_encoded_])[0]
            
        return x_encoded_
    
    
    def distribution_batch_house(self,
                            data,
                           run_turns,
                           optimized_config_dir:str,
                           step_num =1,
                           tasks_dir = "LLM_PublicHouseAllocation/tasks",
                           ):
        house_path = self.base_config["managers"]["house"]["data_dir"]
        house_path = os.path.join(tasks_dir,data,house_path)
        
        with open(house_path,'r',encoding = 'utf-8') as f:
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
            
        optimize_dir = os.path.join(optimized_config_dir,"data")
        if not os.path.exists(optimize_dir):
            os.makedirs(optimize_dir)
        
        cur_num = len(house_ids)
        with open(os.path.join(optimize_dir,f"distribution_batch_house_{cur_num}_{run_turns}_{step_num}.json"),'w',encoding = 'utf-8') as f:
            json.dump(distribution_batch, f, indent=4,separators=(',', ':'),ensure_ascii=False)
        
        return f"data/distribution_batch_house_{cur_num}_{run_turns}_{step_num}.json"
        
    def distribution_batch_tenant(self,
                                data,
                                run_turns,
                                optimized_config_dir:str ,
                                step_num = 1,
                                tasks_dir = "LLM_PublicHouseAllocation/tasks"):
        tenant_path = self.base_config["managers"]["tenant"]["data_dir"]
        tenant_path = os.path.join(tasks_dir,data,tenant_path)
        with open(tenant_path,'r',encoding = 'utf-8') as f:
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


        optimize_dir = os.path.join(optimized_config_dir,"data")
        if not os.path.exists(optimize_dir):
            os.makedirs(optimize_dir)
        
        cur_num = len(tenant_ids)
        with open(os.path.join(optimize_dir,
                            f"distribution_batch_tenant_{cur_num}_{run_turns}_{step_num}.json"),'w',encoding = 'utf-8') as f:
            json.dump(distribution_batch, f, indent=4,separators=(',', ':'),ensure_ascii=False)
        
        return f"data/distribution_batch_tenant_{cur_num}_{run_turns}_{step_num}.json"

                
                
    def update_config(self,
                      configs:dict,
                      tasks_dir = "LLM_PublicHouseAllocation/tasks"):
        
        for k,v in configs.items():
            try:
                configs[k] = int(v)
            except:
                configs[k] = str(v)
        
        optimized_config_dir = os.path.join(tasks_dir,self.data_setting,"optimize","optimized_task_config")
        
        if not os.path.exists(optimized_config_dir):
            os.makedirs(optimized_config_dir)
        
        distribution_house_path = self.distribution_batch_house(data=self.data_setting,
                                      run_turns = configs['distribution_batch_house_distribution_len'],
                                      step_num = configs['distribution_batch_house_distribution_step'],
                                      optimized_config_dir=optimized_config_dir)
        
        distribution_tenant_path = self.distribution_batch_tenant(data = self.data_setting,
                                                                  run_turns = configs['distribution_batch_tenant_distribution_len'],
                                                                  step_num = configs['distribution_batch_tenant_distribution_step'],
                                                                  optimized_config_dir=optimized_config_dir)
        
        
        optimized_config = copy.deepcopy(self.base_config)
        optimized_config["managers"]["tenant"]["distribution_batch_dir"] = distribution_tenant_path
        optimized_config["managers"]["community"]["distribution_batch_dir"] = distribution_house_path
        
        config_map ={
            "environment_max_turns":["environment","max_turns"],
            'group_policy_priority':["managers","tenant","policy","group_policy","priority"],
            'tenant_max_choose': ["managers","tenant","max_choose"],
            'group_policy_type': ["managers","tenant","policy","group_policy","type"],
            "community_patch_method":["managers","community","patch_method"],
            "policy_type":["managers","tenant","policy","type"],
            'order_type':["environment","rule","order","type"],
            
        }
        
        for optimized_k, config_k_list in config_map.items():
            sub_config = optimized_config
            for config_k in config_k_list[:-1]:
                sub_config = sub_config[config_k]
                
            sub_config[config_k_list[-1]] = configs[optimized_k]
            
            
        if optimized_config["environment"]["rule"]["order"]["type"] == "kwaitlist":
            optimized_config["environment"]["rule"]["order"]["k"] = configs["order_k"]
            
        group_policy_type = configs["group_policy_type"]
        if group_policy_type == "portion":
            group_size = configs["group_size"]
            portion_settings = [1/group_size for _ in range(group_size)]
            optimized_config["managers"]["tenant"]["policy"]["group_policy"]["portion_settings"] = portion_settings
            
            
        self.optimized_config = optimized_config
        
        config_path = os.path.join(optimized_config_dir,"config.yaml")
        with open(config_path, 'w') as outfile:
            yaml.dump(self.optimized_config, outfile, default_flow_style=False)
            