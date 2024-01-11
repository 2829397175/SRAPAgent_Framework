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
from EconAgent.utils import readinfo
import ast

@policy_optimizer_registry.register("base")
class BaseOptimizer(BaseModel):
    
    indicators:dict = {}
    features:dict = {}
    
    x_attrs:pd.DataFrame
    x_ex_map:dict ={}
    y_attrs:pd.DataFrame
    
    encoders :dict = {} # col_name：encoder
    
    x:np.ndarray =[]
    y:np.ndarray =[]
    
    x_used:np.ndarray = []
    y_used:np.ndarray = []
    
    weights_y: np.ndarray = []
    
    # 对y做normalize的scaler
    y_normalizer: Any = None
    
    normalize: bool = False # 是否要对x对归一化处理
    x_normalizer: Any = None
    
    ## 用于优化的base_config
    base_config :dict = {}
    
    
    data_setting:str = "" # 记录task文件夹内的data
    
    load_feature_col:str = "all" # 默认只取面向系统内所有的租客计算的指标
    
    
    configs_cache :dict = {} # config_name: decoded_config_dict
    
    optimize_type:str =""

    class Config:
        arbitrary_types_allowed = True
        
        
    
        
    
    @classmethod
    def load_data(cls,
                  data:str,
                  experiment_dir = "EconAgent/experiments",
                  tasks_dir = "EconAgent/tasks",
                  load_feature_col = "all",
                  normalize :bool = False,
                  ):
        """k =1"""
        """fairness"""
        indicators:dict = {"up":{"mean_house_area":1,
                           "sw":5,
                            "F(W,G)":1
                            },# indcitor:weight
                       "down": { 
                            "var_mean_house_area":5,
                            "Rop":10,
                            "mean_wait_turn":1,
                            # "mean_idle_wait_turn":1,
                            "GINI_index":10
                            } # indcitor:weight
                       }
        optimize_type:str = "fairness"
        
        """satisfaction"""
        # indicators:dict = {"up":{"mean_house_area":5,
        #                    "sw":10,
        #                     "F(W,G)":1
        #                     },# indcitor:weight
        #                "down": { 
        #                     "var_mean_house_area":1,
        #                     "Rop":5,
        #                     "mean_wait_turn":5,
        #                     # "mean_idle_wait_turn":1,
        #                     "GINI_index":1
        #                     } # indcitor:weight
        #                }
        
        # optimize_type:str = "satisfaction"
        
        features:dict = {"data_int":[
                                "distribution_batch_house_distribution_len",
                                "distribution_batch_house_distribution_step",
                                "distribution_batch_tenant_distribution_len",
                                "distribution_batch_tenant_distribution_step",
                                # "environment_max_turns",
                                # "environment_communication_num",
                                "group_size",
                                "tenant_max_choose",
                                # "order_k",
                                ],
                       
                        "str":[
                            "group_policy_sorting_type",
                            "group_policy_type",
                            "community_patch_method" ,
                            "policy_type",
                            "order_type",
                        ]}
        """process y weights"""
        sum_weights = 0
        for type_indicator,indicators_dict in indicators.items():
            for indicator_name,indicator_weight in indicators_dict.items():
                sum_weights+=indicator_weight
        
        for type_indicator,indicators_dict in indicators.items():
            for indicator_name,indicator_weight in indicators_dict.items():
                indicators[type_indicator][indicator_name] = indicator_weight/sum_weights*10
    
        
        config_path = os.path.join(tasks_dir,data,"optimize","base_config.yaml")
        config = yaml.safe_load(open(config_path))
        
        ## from read data function
        objective_matrix, utility_matrix = cls.concat_experiment_results(task_path = tasks_dir,
                                                                        ex_setting = data,
                                                                        save_all_ex_results = False)
        
        
        ## load from concated experiments csv
        # objective_matrix_path = os.path.join(data_dir,"objective_evaluation_matrix.csv")
        # objective_matrix = pd.read_csv(objective_matrix_path,index_col=0)
        
        # utility_matrix_path = os.path.join(data_dir,"utility_eval_matrix.csv")
        # utility_matrix = pd.read_csv(utility_matrix_path,index_col=0)
        
        
        matrix = pd.concat([objective_matrix,utility_matrix])
        
        
        y_attrs = pd.DataFrame()
        x_attrs = pd.DataFrame()
        
        """load x,y"""
        ex_results = matrix.groupby(["ex_idx"])
        for ex_idx,ex_result in ex_results:
            assert len(ex_idx) ==1 ,"multiple index for one experiment"
            ex_idx = ex_idx[0]
            for type_indicator,indicators_ in indicators.items():
                for indicator in indicators_.keys():
                    if indicator in ex_result.index:
                        y_attrs.loc[ex_idx,indicator] = float(ex_result.loc[indicator,load_feature_col])
            
            for type_x,x_names in features.items():
                for x_name in x_names:
                    x_attrs.loc[ex_idx,x_name] = ex_result[x_name].values[0]
           
       
        

        # 创建MinMaxScaler对象
        scaler = MinMaxScaler()

       

        # 使用fit_transform方法对DataFrame进行归一化
        y_attrs_normalize = scaler.fit_transform(np.array(y_attrs.values))
        
        
        for idx,indicator in enumerate(y_attrs.columns):
            y_attrs[f"{indicator}_normalize"] = y_attrs_normalize[:,idx]
        
        for indicator_down in indicators.get("down",[]):
            y_attrs[f"{indicator_down}_normalize"] = 1 - y_attrs[f"{indicator_down}_normalize"]
            
        y = y_attrs.loc[:,list(filter(lambda col_name:"normalize" in col_name, y_attrs.columns))].values
        
        weights_y = []
        for column_name in y_attrs.columns:
            for type_indicator,indicators_ in indicators.items():
                if column_name in indicators_.keys():
                    weights_y.append(indicators_[column_name])
        y = np.array([np.sum(weights_y*y) for y in y])            
        

        y_attrs["y"] = y       
        
        assert not y_attrs.isna().any().any(), "Y contain NAN !!"
        
        
        
        
        x_dummys = x_attrs.loc[:,features["data_int"]]
        x_dummys = x_dummys.astype(int)
    
        
        encoders = {}
        for feature_name in features["str"]:
            x = x_attrs[feature_name]
            enc = OneHotEncoder()          # 初始化
            enc.fit(x_attrs[[feature_name]].values)    # 模型拟合。注意：data[['一键三连']]是一个dataframe，与data['一键三连']是一个series不同
            array_data = enc.transform(x_attrs[[feature_name]].values).toarray()
            encoders[feature_name] = enc
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
        
        configs_cache = {}
        x_ex_map = {}
        
        for ex_name in matrix["ex_name"].value_counts().index.to_list():
            ex_idxs = matrix[matrix["ex_name"] == ex_name]["ex_idx"]
            for ex_idx in ex_idxs:
                x_ex_map[int(ex_idx)] = ex_name
            configs = x_attrs.iloc[ex_idx,:].to_dict()
            configs_cache[ex_name] = {
                "configs":configs,
                "ex_idx":ex_idx            
            }
            
            
        return cls(
            x = x,
            y = y,
            y_normalizer = scaler,
            normalize = normalize,
            x_normalizer = normalizer,
            x_attrs = x_attrs,
            x_ex_map = x_ex_map,
            encoders = encoders,
            y_attrs = y_attrs,
            features = features,
            indicators = indicators,
            load_feature_col = load_feature_col,
            weights_y = np.array(weights_y),
            base_config = config,
            data_setting = data,
            configs_cache = configs_cache,
            optimize_type = optimize_type
            
        )
        
    
    def filter_x_vector(self,
                        x_vector): 
        # 将遗传算法生成的后代进行filter后变成合法的离散值
        x_config = self.decode_x(x_vector)
        # x_config = self.filter_x_config(x_config)
        return self.encode_x(x_config)
        
    
    def filter_x_config(self,x_config:dict):
        assert len(x_config) == self.x_attrs.shape[1],"illegal number of x vector dimensions"
        
        """优先度：policy_type->tenant->house->group_size"""
        policy_type = x_config["policy_type"]
        if policy_type == "ver2":
            x_config['group_policy_type'] = "house_type"
            x_config['group_size'] = 3 
            x_config['community_patch_method'] ="house_type"
            # x_config[""]
        
        if policy_type == "ver1" and x_config['group_policy_type'] == "house_type":
            x_config['group_policy_type'] = "multi_list"
            x_config['group_size'] = 3
        
            
        """对于不可以同时出现的房屋分配方法"""
        tenant_patch_method = x_config['group_policy_type']
        
        
        
        if tenant_patch_method in ["multi_list",'house_type']:
            if x_config['community_patch_method'] =='single_list':
                x_config["community_patch_method"] = 'house_type'
            x_config['group_size'] = 3
        elif tenant_patch_method == "single_list":
            x_config["community_patch_method"] = 'single_list'
            x_config['group_size'] = 1
        elif tenant_patch_method in ["portionfamily_members_num",
                                     "portionmonthly_rent_budget"]:
            if x_config["community_patch_method"] in ['single_list',
                                                            'house_type']:
                x_config["community_patch_method"] = 'portion_rentmoney'
        
        # x_config["order_k"] = x_config["order_k"] if x_config["order_k"]<= x_config["tenant_max_choose"] else \
        #     x_config["tenant_max_choose"]
        if x_config["distribution_batch_tenant_distribution_step"] == 0:
            x_config["distribution_batch_tenant_distribution_step"] = 1
        if x_config["distribution_batch_house_distribution_step"] == 0:
            x_config["distribution_batch_house_distribution_step"] = 1
            
        if x_config["tenant_max_choose"]==0:
            x_config["tenant_max_choose"]=1
        # 硬性规定最大的round为10
        # x_config["environment_max_turns"] = 10 if x_config["environment_max_turns"]>10 else x_config["environment_max_turns"]
        
        return x_config
        
    def decode_x(self,
                 x_vector): # 一维：默认data+str的格式排列vector数据
        
        
        if self.normalize:
            restored_vector = self.x_normalizer.inverse_transform([x_vector])
            x_vector = restored_vector[0]
            
        x_reverse = np.round(np.array(x_vector[:len(self.features["data_int"])])).astype(int).tolist()
        
        x_config = {feature_name:x_reverse[idx] for idx,feature_name in enumerate(self.features["data_int"])}
        left_p = len(self.features["data_int"])
        for feature_name in self.features["str"]:
            # 获取编码后向量的维度
            enc = self.encoders[feature_name]
            num_features = len(enc.get_feature_names_out())
            encoded_x_ = x_vector[left_p:left_p+num_features]
            
            # 使用 inverse_transform 方法将编码后的数据映射回原始值
            sum_x_ = np.sum(encoded_x_)
            if sum_x_ !=0:
                encoded_x_ = encoded_x_/ sum_x_
                # 找到数组中的最大值
                max_val = np.max(encoded_x_)

                # 找到最大值的所有下标
                indices = np.where(encoded_x_== max_val)[0]
                if indices.shape[0] ==1:
                    encoded_x_onehot = np.zeros(encoded_x_.shape)
                    encoded_x_onehot[indices[0]] = 1
                    decoded_data = enc.inverse_transform([encoded_x_onehot])[0].tolist()[0]
                elif indices.shape[0] >1:
                    encoded_x_onehot = np.zeros(encoded_x_.shape)
                    indice = random.choice(indices)
                    encoded_x_onehot[indice] = 1
                    decoded_data = enc.inverse_transform([encoded_x_onehot])[0].tolist()[0]
                else:
                    decoded_data = random.choice(self.x_attrs[feature_name])
            else:
                decoded_data = random.choice(self.x_attrs[feature_name])
            
            x_config[feature_name] = decoded_data            
            left_p += num_features
            
        # x_reverse = np.round(encoded_x_).astype(int)
        # for idx, feature_name in enumerate(self.features):
            
        """对于给出的不可同时出现的参数值，进行后处理"""
        
        x_config = self.filter_x_config(x_config=x_config)
            
        return x_config
            
        
    def encode_x(self,
                 x): # x是一维的
        
        if isinstance(x,dict):
            x = np.array(list(x.values()))
        assert x.shape[0] == self.x_attrs.shape[1],"illegal number of x vector dimensions"
        
        x_encoded_ =  []
        for idx,x_ in enumerate(x):
            indicator_name = self.x_attrs.columns[idx]
            if indicator_name in self.features["str"]:
                enc = self.encoders.get(indicator_name)
                transformed_x_ = enc.transform([[x_]]).toarray()[0].tolist()
                x_encoded_.extend(transformed_x_)
            elif indicator_name in self.features["data_int"]:
                x_encoded_.append(int(float(x_)))
            else:
                x_encoded_.append(float(x_))
                
                
        x_encoded_ = np.array(x_encoded_)
        if self.normalize:
            x_encoded_ = self.x_normalizer.transform([x_encoded_])[0]
            
        return x_encoded_
    
    
    def distribution_batch_house(self,
                            data,
                           run_turns,
                           optimized_config_dir:str,
                           step_num =1,
                           tasks_dir = "EconAgent/tasks",
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
                                tasks_dir = "EconAgent/tasks"):
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
                      tasks_dir = "EconAgent/tasks",
                      config_name_prefix = "optimized_task_config"): 
        """
        return config_name, runned_before    
        """
        
        """ use cache to omit updating simulated configs"""
        
        for config_name, configs_chache in self.configs_cache.items():
            same = True
            for k in configs.keys():
                if configs[k] != configs_chache["configs"][k]:
                    same = False
                    break
            if same:
                ex_idx = configs_chache["ex_idx"]
                print(f"same experiment have runned for ex_idx:{ex_idx}")
                return config_name,True    
        
        
        for k,v in configs.items():
            if k in self.features["data_int"]:
                configs[k] = int(v)
            elif k in self.features["str"]:
                configs[k] = str(v)
        
        optimize_root = os.path.join(tasks_dir,self.data_setting,"configs")
        
        
        if os.path.exists(optimize_root):
            config_paths = os.listdir(optimize_root)
            max_idx = 0
            for config_path in config_paths:
                regex = f"{config_name_prefix}_(\d+)"
                import re
                try:
                    idx = int(re.search(regex,config_path).group(1))
                    max_idx = idx if max_idx<idx else max_idx
                except:
                    continue
            config_name = f"{config_name_prefix}_{max_idx+1}"
        else:
            config_name = f"{config_name_prefix}_0"
            
        optimized_config_dir = os.path.join(optimize_root,config_name)
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
        
        # distribution_house_path = self.distribution_batch_house(data=self.data_setting,
        #                               run_turns = 6,
        #                               step_num = 1,
        #                               optimized_config_dir=optimized_config_dir)
        
        # distribution_tenant_path = self.distribution_batch_tenant(data = self.data_setting,
        #                                                           run_turns = 8,
        #                                                           step_num = 1,
        #                                                           optimized_config_dir=optimized_config_dir)
        
        
        optimized_config = copy.deepcopy(self.base_config)
        optimized_config["managers"]["tenant"]["distribution_batch_dir"] = distribution_tenant_path
        optimized_config["managers"]["community"]["distribution_batch_dir"] = distribution_house_path
        
        config_map ={
            # "environment_max_turns":["environment","max_turns"],
            # "environment_communication_num":["environment","communication_num"],
            'group_policy_sorting_type':["managers","tenant","policy","group_policy","sorting_type"],
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
            
        if "kwaitlist" in configs["order_type"]:
            regex = r".*k_(\d+)_ratio_(\d+.\d+)"
            try:
                match = re.match(regex,configs["order_type"])
                k = int(match.group(1))
                ratio = float(match.group(2))
            except:
                k = 2
                ratio = 1.2
            optimized_config["environment"]["rule"]["order"]["k"] = k if k <= configs["tenant_max_choose"] else configs["tenant_max_choose"]
            optimized_config["environment"]["rule"]["order"]["waitlist_ratio"] = ratio
            optimized_config["environment"]["rule"]["order"]["type"] = "kwaitlist"
            
        group_policy_type = configs["group_policy_type"]
        
        
        if "portion" in group_policy_type:
            optimized_config["managers"]["tenant"]["policy"]["group_policy"]["type"] = "portion"
            if group_policy_type == "portionfamily_members_num":
                optimized_config["managers"]["tenant"]["policy"]["group_policy"]["portion_attribute"]= \
                    "family_members_num"
            elif group_policy_type == "portionmonthly_income":
                optimized_config["managers"]["tenant"]["policy"]["group_policy"]["portion_attribute"]= \
                "monthly_income"
            elif group_policy_type == "portionmonthly_rent_budget":
                optimized_config["managers"]["tenant"]["policy"]["group_policy"]["portion_attribute"]= \
                "monthly_rent_budget"
                
            group_size = configs["group_size"]
            portion_settings = [1/group_size for _ in range(group_size)]
            optimized_config["managers"]["tenant"]["policy"]["group_policy"]["portion_settings"] = portion_settings
            

            
        
        
        config_path = os.path.join(optimized_config_dir,"config.yaml")
                
        
        """ dump configs """
            
        with open(config_path, 'w') as outfile:
            yaml.dump(optimized_config, outfile, default_flow_style=False)
        

        optimize_params_path = os.path.join(optimized_config_dir,"indicator_weights.json")
        
        with open(optimize_params_path,'w',encoding = 'utf-8') as f:
            json.dump({"indicators":self.indicators,
                       "normalize":self.normalize}, 
                    f,
                    indent=4,
                    separators=(',', ':'),ensure_ascii=False)
        return config_name, False
    
    @classmethod
    def concat_experiment_results(cls,
                                  task_path = "EconAgent/tasks",
                                  ex_setting = "PHA_51tenant_5community_28house",
                                  save_root = "EconAgent/experiments",
                                  save_all_ex_results = False,
                                  config_name :str = None,
                                  offset_index:int = -1
                                ):
        
        
        config_root = os.path.join(task_path,ex_setting,"configs")
        
        
        u_type = "all"
        result_types = [
            "objective_evaluation_matrix",
            "utility_eval_matrix"
        ]
        
        index_cols_map={
            "utility_eval_matrix":["type_indicator"],
            "objective_evaluation_matrix":["type_indicator"]
        }
        
        save_dir = os.path.join(save_root,ex_setting)
        
        config_keys = [["environment","max_turns"],
                       ["environment","communication_num"],
                    ["environment","rule","order"],
                    ["managers","tenant","policy","type"],
                    ["managers","tenant","policy","group_policy"],
                    ["managers","tenant","max_choose"],
                    ["managers","community","patch_method"],
                    ]
        
        
        
        results = {
            
        } # ex_name[{u_type:{eval matrix}},]
        
        exclude_ex_names = [
                    # "ver2_nofilter_multilist(1.2_k2)_housetype_priority_8t_6h(step_num(t1_h1))_p#housetype_choose3",
                    # "ver2_nofilter_multilist(1.2_k2)_housetype_priority_8t_6h(step_num(t1_h1))_p#housetype_choose3",
                    # "ver2_nofilter_multilist(2.1_k3)_housetype_priority_8t_6h(step_num(t1_h1))_p#housetype_choose5",
                    # "ver2_nofilter_multilist(2.1_k4)_housetype_priority_8t_6h(step_num(t1_h1))_p#housetype_choose5",
                    # # "ver2_nofilter_multilist(1.2_k2)_housetype_nopriority_8t_6h(step_num(t1_h1))_p#housetype_choose2",
                    # "ver2_nofilter_multilist(3_k2)_housetype_priority_8t_6h(step_num(t1_h1))_p#housetype_choose3",
                    # "ver2_nofilter_multilist(2.1_k1)_housetype_priority_8t_6h(step_num(t1_h1))_p#housetype_choose5",
                    # "ver2_nofilter_multilist(1.8_k2)_housetype_priority_8t_6h(step_num(t1_h1))_p#housetype_choose3",
                    # "ver2_nofilter_multilist(1.5_k3)_housetype_priority_8t_6h(step_num(t1_h1))_p#housetype_choose3",
                    # "ver2_nofilter_multilist(2.1_k2)_housetype_priority_8t_6h(step_num(t1_h1))_p#housetype_choose2"
                    ]
        if config_name is None:
            config_name_list = os.listdir(config_root)
            for ex_name_exclude in exclude_ex_names:
                if ex_name_exclude in config_name_list:
                    config_name_list.remove(ex_name_exclude)
        elif isinstance(config_name,str):
            config_name_list = [config_name]
        
        
        # config_name_list = list(filter(lambda name:"optimize" not in name,config_name_list))
        random.shuffle(config_name_list)
        # optimize_name_map_path ="EconAgent/optimizer/logs_fairness/1704686424.9090853/ex_name_map.json"
        # name = readinfo(optimize_name_map_path)
        # config_name_list =[]
        # for idx,ex_name in name.items():
        #     if int(idx)<41:
        #         config_name_list.append(ex_name)
        # config_name_list.append("optimized_task_config_242")
        optimized_names =[]
        other_configs = []
        for name in config_name_list:
            if "optimize" not in name:
                other_configs.append(name)
            else:optimized_names.append(name)
            
        config_name_list = [*other_configs,*optimized_names]     
        
        ex_idx = offset_index
        
        for ex_name in config_name_list:
            ex_root_path = os.path.join(config_root,ex_name)
            config_path = os.path.join(ex_root_path,"config.yaml")
            if not os.path.exists(config_path):
                continue
            task_config = yaml.safe_load(open(config_path))
            
            group_policy = task_config["managers"]["tenant"]["policy"]["group_policy"]
            if "portion_attribute" in group_policy:
                group_policy["type"] += group_policy["portion_attribute"]
                group_policy.pop("portion_attribute")
            
            tenant_dt_path = os.path.join(ex_root_path,task_config["managers"]["tenant"]["distribution_batch_dir"])
            tenant_dt = readinfo(tenant_dt_path)
            house_dt_path = os.path.join(ex_root_path,task_config["managers"]["community"]["distribution_batch_dir"])
            house_dt = readinfo(house_dt_path)
            if ex_name not in results.keys():
                results[ex_name] = []
            
            ex_paths = []
            result_path = os.path.join(config_root,ex_name,"result")
            if os.path.exists(result_path):
                # paths.append(os.path.join(result_path,os.listdir(result_path)[-1]))
                result_files = os.listdir(result_path)
                for result_file in result_files:
                    result_file_path = os.path.join(result_path,result_file,"all")
                    if os.path.exists(result_file_path):
                        ex_paths.append(os.path.join(result_path,result_file))
                        
                    
            
                
            configs_cols_append = {
                    "distribution_batch":{
                        "house_distribution_len": len(house_dt),
                        "house_distribution_step": 1 if len(house_dt) ==1 else int(list(house_dt.keys())[1])\
                            -int(list(house_dt.keys())[0]),
                        "tenant_distribution_len": len(tenant_dt),
                        "tenant_distribution_step": 1 if len(tenant_dt) ==1 else int(list(tenant_dt.keys())[1])\
                            -int(list(tenant_dt.keys())[0]),
                    }
                }
            for config_key_list in config_keys:
                
                result = task_config
                for config_key in config_key_list:
                    result = result.get(config_key)
                if config_key_list[-1] == "order":
                    if result["type"]== "kwaitlist":
                        result["type"] = "kwaitlist_k_{k}_ratio_{ratio}".format(
                            k = result["k"],
                            ratio = result.get("waitlist_ratio",1.2)
                        )
                    
                if config_key_list[-1] == "patch_method" and result is None:
                    result = "random_avg"    
                
                root_k =""
                if not isinstance(result,dict):
                    result = {config_key_list[-1]:result}
                    root_k = config_key_list[-2]
                else:
                    root_k = config_key_list[-1]
                
                if root_k in configs_cols_append.keys():
                    configs_cols_append[root_k].update(result)
                else:
                    configs_cols_append[root_k] = result
            
                    
            for ex_path in ex_paths:
                ex_idx += 1
                u_type_dict = {}
                tenental_system_path = os.path.join(ex_path,"tenental_system.json")
                tenental_system = readinfo(tenental_system_path)
                # 把那些没有log_round 的filter了
                tenental_system_filtered = dict(filter(lambda item: isinstance(item[1],dict) and "log_round" in item[1].keys(),tenental_system.items()))

                u_type_dict[u_type] = {}
                
                for result_type in result_types:

                    result_u_type_path = os.path.join(ex_path,u_type,result_type+".csv")
                    try:
                        result_u_type = pd.read_csv(result_u_type_path,
                                                    index_col=index_cols_map[result_type])
                    except:
                        continue
            
                    
                    result_u_type["ex_name"] = ex_name
                    # result_u_type.set_index('ex_name',inplace=True,append=True)
                    
                    ex_timestamp = os.path.basename(ex_path)
                    result_u_type["ex_timestamp"] = ex_timestamp
                    # result_u_type.set_index('ex_idx',inplace=True,append=True)

                    result_u_type["ex_idx"] = ex_idx
                    cols_first_level = ["indicator_values" for i in range(result_u_type.shape[1])]
                    
                    group_policy = task_config["managers"]["tenant"]["policy"]["group_policy"]["type"]
                    if "portion" in group_policy:
                        groups = [group_info["queue_name"] for group_info in tenental_system["group"].values()]
                        group_size = len(np.unique(groups))
                        
                    elif group_policy == "single_list":
                        group_size = 1
                    elif group_policy in ["multi_list","house_type"]:
                        group_size = 3
                    
                    else:
                        raise Exception("Unsupported group policy of tenant")
                    
                    result_u_type["group_size"] = group_size
                    
                    cols_first_level.append("group_size")
                    
                    
                    result_u_type["ex_len"] = list(tenental_system_filtered.keys())[-1]
                    cols_first_level.append("experiment")
                    
                    for k,config in configs_cols_append.items():
                        for config_key,config_value in config.items():
                            assert not isinstance(config_value,dict)
                            if isinstance(config_value,list):
                                config_value =[config_value for i in range(result_u_type.shape[0])]
                            result_u_type[f"{k}_{config_key}"] = config_value
                            cols_first_level.append(k)
                        
                    assert len(cols_first_level) == len(result_u_type.columns)
                    
                    u_type_dict[u_type][result_type] = result_u_type
                
                results[ex_name].append(u_type_dict)
                
            if len(ex_paths) > 1:
                # 如果存在多次实验，那么这里再存一个实验的平均数据   
                ex_idx += 1
                agg_cols = ["all"]
                u_type_dict = {}
                u_type_dict[u_type] = {}
                result_types_indicators ={
                    "objective_evaluation_matrix":["mean_house_area",
                                                "mean_wait_turn",
                                                "var_mean_house_area",
                                                "Rop"
                        ],
                    "utility_eval_matrix":["least_misery","variance","jain'sfair","min_max_ratio",
                                        "sw","F(W,G)","GINI_index"]
                }
                
                for result_type in result_types:
                    result_u_types = []     
                    
                    for result_one in results[ex_name]:
                        result_u_types.append(result_one[u_type][result_type])
                    
                    result_u_type = copy.deepcopy(result_u_types[0])# 用首项初始化 平均的df项 
                    
                    for indicator in result_types_indicators[result_type]:
                        for agg_col in agg_cols:
                            values = []
                            for result_df_one in result_u_types:
                                values.append(result_df_one.loc[indicator,agg_col])
                            result_u_type.loc[indicator,agg_col] = np.mean(values)
                    result_u_type["ex_idx"] = ex_idx
                    u_type_dict[u_type][result_type] = result_u_type
                results[ex_name].append(u_type_dict)
                
        # concat_df: u_type: type_ex:
        
        u_type_path = os.path.join(save_dir,u_type)
        if not os.path.exists(u_type_path) and save_all_ex_results:
            os.makedirs(u_type_path)
        
        frames = {}
        for ex_name in results.keys():
            
            for ex_results in results[ex_name]:
                for matrix_name,matrix in ex_results[u_type].items():
                    if matrix_name not in frames.keys():
                        frames[matrix_name] = []

                    frames[matrix_name].append(matrix)
            
        concated_dfs = {}
            
        for matrix_name,matrixs in frames.items():
            concated_df = pd.concat(matrixs)
            concated_dfs[matrix_name] = concated_df
            if (save_all_ex_results):
                concated_df.to_csv(os.path.join(u_type_path,
                                                matrix_name+".csv"))
                concated_df.to_excel(os.path.join(u_type_path,
                matrix_name+".xlsx"),"sheet_1")
        
        concated_dfs["utility_eval_matrix"].drop('eval_type', axis=1,inplace=True)
        
        
        
        
        
        return concated_dfs["objective_evaluation_matrix"],concated_dfs["utility_eval_matrix"]
        
    def simulate_optimize_task(self,
                               config_name,
                               tasks_dir="EconAgent/tasks",
                               use_cache = False):
        from EconAgent.executor import Executor
        
        args ={
            "data":self.data_setting,
            "task":config_name,
           "api_path":"EconAgent/llms/api.json",
           
        }
        
        done_times = 0
        
        if use_cache:
            result_config_root = os.path.join(tasks_dir,
                                            self.data_setting,
                                            "configs",
                                            config_name,
                                            "result")
            if os.path.exists(result_config_root):
                results = os.listdir(result_config_root)
                for result in results:
                    result_path = os.path.join(result_config_root,result)
                    if os.path.exists(os.path.join(result_path,"all")):
                        done_times +=1
                        
        if done_times == 0:
            executor = Executor.from_task(args)
            ex_timestamp = executor.run()
        
        objective_matrix, utility_matrix = self.concat_experiment_results(task_path = tasks_dir,
                                                                        ex_setting = self.data_setting,
                                                                        save_all_ex_results = True,
                                                                        config_name = config_name,
                                                                        offset_index = self.x.shape[0] - 1)
        try:
            matrix = pd.concat([objective_matrix,utility_matrix])
            assert matrix["ex_name"].iloc[0] == config_name and len(matrix["ex_name"].value_counts().index)==1, \
                "Error when concating experiment results"
                
            if not use_cache:
                matrix = matrix[matrix["ex_timestamp"] == ex_timestamp]
                assert len(matrix["ex_idx"].value_counts().index)[0] == 1
                 
            if matrix.shape[0] ==0:
                warnings.warn(f"Fail to update result for experiment {config_name}")
                return None 
            
            y_attrs = pd.DataFrame()
            x_attrs = pd.DataFrame()
        

            """load x,y"""
            ex_results = matrix.groupby(["ex_idx"])
            for ex_idx,ex_result in ex_results:
                assert len(ex_idx) ==1 ,"multiple index for one experiment"
                ex_idx = ex_idx[0]
                for type_indicator,indicators_ in self.indicators.items():
                    for indicator in indicators_.keys():
                        if indicator in ex_result.index:
                            y_attrs.loc[ex_idx,indicator] = float(ex_result.loc[indicator,self.load_feature_col])
                
                for type_x,x_names in self.features.items():
                    for x_name in x_names:
                        x_attrs.loc[ex_idx,x_name] = ex_result[x_name].values[0]
                

            # 使用fit_transform方法对DataFrame进行归一化
            y_attrs_normalize = self.y_normalizer.transform(y_attrs.values)
            
            for idx,indicator in enumerate(y_attrs.columns):
                y_attrs[f"{indicator}_normalize"] = y_attrs_normalize[:,idx]
        
            for indicator_down in self.indicators.get("down",[]):
                y_attrs[f"{indicator_down}_normalize"] = 1 - y_attrs[f"{indicator_down}_normalize"]
            
            y = y_attrs.loc[:,list(filter(lambda col_name:"normalize" in col_name, y_attrs.columns))].values
            
            weights_y = []
            for column_name in self.y_attrs.columns:
                for type_indicator,indicators_ in self.indicators.items():
                    if column_name in indicators_.keys():
                        weights_y.append(indicators_[column_name])
            
            y = [np.sum(weights_y*y_) for y_ in y]
            y_attrs.loc[ex_idx,"y"] = y       
            
            x_dummys = x_attrs.loc[:,self.features["data_int"]].astype(int)
        
            for feature_name in self.features["str"]:
                x =  x_attrs[feature_name]
                enc = self.encoders[feature_name]
                array_data = enc.transform(x_attrs[[feature_name]].values).toarray()
                for idx in range(array_data.shape[1]):
                    x_dummys[f"{feature_name}_transformed_{idx}"] = array_data[:,idx]

            x = x_dummys.values
            assert not x_dummys.isna().any().any(), "X contain NAN !!"
            
            if (self.normalize):
                x = self.x_normalizer.transform(x)
                
            """更新attribute"""
            """为了多进程执行，这里放进return value中更新"""
            
            
            return x , y, x_attrs, y_attrs
            
        except Exception as e:
            print(e)
            warnings.warn(f"Fail to update result for experiment {config_name}")
            
            return None