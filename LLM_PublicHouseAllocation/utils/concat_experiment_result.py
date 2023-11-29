import pandas as pd
import os
import numpy as np
import yaml
import json
def readinfo(data_dir):
    assert os.path.exists(data_dir),"no such file path: {}".format(data_dir)
    with open(data_dir,'r',encoding = 'utf-8') as f:
        data_list = json.load(f)
    return data_list

def concat_experiment_results(task_path = "LLM_PublicHouseAllocation/tasks",
                              ex_setting = "PHA_51tenant_5community_28house",
                              save_root = "LLM_PublicHouseAllocation/experiments",
                              ):
    
    
    config_root = os.path.join(task_path,ex_setting,"configs")
    
    
    u_types = ["all","choosed"] 
    result_types = [
        "objective_evaluation_matrix",
        "utility_eval_matrix"
    ]
    
    index_cols_map={
         "utility_eval_matrix":["type_indicator","eval_type"],
         "objective_evaluation_matrix":["type_indicator"]
    }
    
    save_dir = os.path.join(save_root,ex_setting)
    
    config_keys = [["environment","max_turns"],
                   ["environment","rule","order"],
                   ["managers","tenant","policy","type"],
                   ["managers","tenant","policy","group_policy"],
                   ["managers","tenant","max_choose"],
                   ["managers","community","patch_method"],
                   ]
    
    
    
    results = {
        
    } # ex_name[{u_type:{eval matrix}},]
    
    
    for ex_name in os.listdir(config_root):
        ex_root_path = os.path.join(config_root,ex_name)
        config_path = os.path.join(ex_root_path,"config.yaml")
        task_config = yaml.safe_load(open(config_path))
        
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
            if not isinstance(result,dict):
                result = {config_key_list[-1]:result}
                configs_cols_append[config_key_list[-2]] = result
            else:
                configs_cols_append[config_key_list[-1]] = result
                
        for ex_path in ex_paths:
            u_type_dict = {}
            tenental_system_path = os.path.join(ex_path,"tenental_system.json")
            tenental_system = readinfo(tenental_system_path)
            
            for u_type in u_types:
                u_type_dict[u_type] = {}
                
                for result_type in result_types:

                    result_u_type_path = os.path.join(ex_path,u_type,result_type+".csv")
                    try:
                        result_u_type = pd.read_csv(result_u_type_path,index_col=index_cols_map[result_type])
                    except:
                        continue
            
                    
                    result_u_type["ex_name"] = ex_name
                    result_u_type.set_index('ex_name',inplace=True,append=True)
                        

                    cols_first_level = ["indicator_values" for i in range(result_u_type.shape[1])]
                    
                    result_u_type["ex_len"] = list(tenental_system.keys())[-1]
                    cols_first_level.append("experiment")
                    
                    for k,config in configs_cols_append.items():
                        for config_key,config_value in config.items():
                            assert not isinstance(config_value,dict)
                            if isinstance(config_value,list):
                                config_value =[config_value for i in range(result_u_type.shape[0])]
                            result_u_type[f"{k}_{config_key}"] = config_value
                            cols_first_level.append(k)
                        
                    assert len(cols_first_level) == len(result_u_type.columns)
                    columns = [cols_first_level,list(result_u_type.columns)]
                    values = result_u_type.values
                        
                    #[["indicator_values" for i in range(len(list(cols)))],list(cols)]
                    # matrix = pd.DataFrame(values,
                    #                     columns=columns,
                    #                     index=pd.MultiIndex.from_tuples(
                    #                         list(result_u_type.index)
                    #                     )
                    #                     )
                    u_type_dict[u_type][result_type] = result_u_type
                
            results[ex_name].append(u_type_dict)
            
            
                
    
    
    # concat_df: u_type: type_ex:
    
    for u_type in u_types:
        u_type_path = os.path.join(save_dir,u_type)
        if not os.path.exists(u_type_path):
            os.makedirs(u_type_path)
        
        
        frames = {}
        for ex_name in results.keys():
            
            for ex_results in results[ex_name]:
                for matrix_name,matrix in ex_results[u_type].items():
                    if matrix_name not in frames.keys():
                        frames[matrix_name] = []

                    frames[matrix_name].append(matrix)
                
        for matrix_name,matrixs in frames.items():
            concated_df = pd.concat(matrixs)
            cols = concated_df.columns
            indexs = concated_df.index
            # concated_df = pd.DataFrame(concated_df.values,
            #                            columns=pd.MultiIndex.from_product(
            #                               [["indicator_values"],list(cols)]
            #                           ),
            #                            index=pd.MultiIndex.from_tuples(list(indexs))
            #                            )
            concated_df.to_csv(os.path.join(u_type_path,
                                            matrix_name+".csv"))
            concated_df.to_excel(os.path.join(u_type_path,
            matrix_name+".xlsx"),"sheet_1")
            

def group_multi_experiment_results(ex_setting = "PHA_51tenant_5community_28house",
                              save_root = "LLM_PublicHouseAllocation/experiments"):
    save_dir = os.path.join(save_root,ex_setting)
    u_types = ["all","choosed"] 
    result_types_indicators ={
        "objective_evaluation_matrix":["mean_house_area",
                                       "mean_wait_turn",
                                       "var_mean_house_area",
                                       "Rop"
            ],
        "utility_eval_matrix":["least_misery","variance","jain'sfair","min_max_ratio",
                               "sw","F(W,G)","GINI_index"]
    }
    cols_agg =["all","3>=family_num>=2","family_num=1","family_num>3","ex_len"]
    
    for u_type in u_types:
        for result_type in result_types_indicators.keys():
            result_u_type_agg = []
            result_u_type_path = os.path.join(save_dir,u_type,result_type+'.csv')
            result = pd.read_csv(result_u_type_path,index_col=0)
            
            result_groups = result.groupby("ex_name")
            
            
            for ex_name, ex_result_grouped  in result_groups:
                result_one_ex = pd.DataFrame()
                    
                for col_name in ex_result_grouped.columns:
                    if col_name =="ex_name":
                        continue
                    if col_name in cols_agg:   
                        for indicator in result_types_indicators[result_type]:
                            one_indicator_df = ex_result_grouped[ex_result_grouped.index == indicator] 
                            values = one_indicator_df[col_name].values
                            if values.shape[0]>1:
                                err = np.std(values, ddof=1)/np.sqrt(values.shape[0])
                                result_one_ex.loc[indicator,col_name]="{mean_value:.4f}$\pm${err:.4f}".format(mean_value =np.mean(values),
                                                                                                          err=err)
                                result_one_ex["multi_ex"] = True
                            else:  
                                for indicator in result_types_indicators[result_type]:
                                    result_one_ex.loc[indicator,col_name] = ex_result_grouped.loc[indicator,col_name]
                                result_one_ex["multi_ex"] = False
                    else:
                        for indicator in result_types_indicators[result_type]:
                            # one_indicator_df = ex_result_grouped[ex_result_grouped.index == indicator] 
                            value = ex_result_grouped.loc[indicator,col_name]
                            if isinstance(value,pd.Series):
                                value_last = value.values[-1]
                                for one_value in value.values[:-1]:
                                    if value_last is np.nan:
                                        continue
                                    else:
                                        assert value_last == one_value,f"incompatible value for col '{col_name}'"
                                value = value_last
                            result_one_ex.loc[indicator,col_name] = value
                            
                result_one_ex["ex_name"] = ex_name
                result_one_ex.set_index('ex_name',inplace=True,append=True)
                result_one_ex.set_index("multi_ex",inplace=True,append=True)
                result_u_type_agg.append(
                    result_one_ex
                )
            result_u_type_agg = pd.concat(result_u_type_agg)
            result_u_type_agg.to_csv(os.path.join(save_dir,u_type,f'agg_{result_type}.csv'))
            

def writeinfo(data_dir,info):
    with open(data_dir,'w',encoding = 'utf-8') as f:
            json.dump(info, f, indent=4,separators=(',', ':'),ensure_ascii=False)

def readinfo(data_dir):
    assert os.path.exists(data_dir),"no such file path: {}".format(data_dir)
    with open(data_dir,'r',encoding = 'utf-8') as f:
        data_list = json.load(f)
    return data_list

def get_ex_names_single_experiment(ex_setting = "PHA_51tenant_5community_28house",
                              save_root = "LLM_PublicHouseAllocation/experiments"):
    u_types = ["all"] 
    result_types = [
        "objective_evaluation_matrix",
    ]
    used_names = readinfo("LLM_PublicHouseAllocation/experiments/PHA_51tenant_5community_28house/all/ex_used_names.json")
    
    for u_type in u_types:
        for result_type in result_types:
            agg_result_matrix_path = os.path.join(save_root,
                                                  ex_setting,
                                                  u_type,
                                                  f'agg_{result_type}.csv')
            
            agg_result_matrix = pd.read_csv(agg_result_matrix_path)
            agg_result_matrix_single = agg_result_matrix[agg_result_matrix["multi_ex"]!= True]
            agg_result_matrix_single = agg_result_matrix_single["ex_name"]
            agg_result_matrix_single =  np.unique(agg_result_matrix_single).tolist()
            
            path_single_test_ex_path = os.path.join(save_root,
                                                  ex_setting,
                                                  u_type,
                                                  f"agg_{result_type}_single.json")
            names =[]
            for ex_name in agg_result_matrix_single:
                if ex_name in used_names:
                    names.append(ex_name)
            writeinfo(path_single_test_ex_path,names)
            


if __name__ == "__main__":
    # paths = [
    #         "LLM_PublicHouseAllocation/tasks/PHA_51tenant_5community_28house/configs/ver1_nofilter_singlelist/result/1699431290.0382807",
    #         "LLM_PublicHouseAllocation/tasks/PHA_51tenant_5community_28house/configs/ver2_nofilter_multilist_priority_7t_5h/result/1699435988.0701036"
    #         ]
    
        
    
    concat_experiment_results(ex_setting="PHA_51tenant_5community_28house",
                              save_root="LLM_PublicHouseAllocation/experiments")
    group_multi_experiment_results()
    # get_ex_names_single_experiment()