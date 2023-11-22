import pandas as pd
import os
import yaml
import json
def readinfo(data_dir):
    assert os.path.exists(data_dir),"no such file path: {}".format(data_dir)
    with open(data_dir,'r',encoding = 'utf-8') as f:
        data_list = json.load(f)
    return data_list

def concat_experiment_results(ex_paths:list = [],
                              ex_setting = "PHA_51tenant_5community_28house",
                              save_root = "LLM_PublicHouseAllocation/experiments"
                              ):
    
    
    
    
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
        
    } # type_ex:u_type:{eval matrix}
    
    
    for ex_path in ex_paths:
        ex_root_path = os.path.dirname(os.path.dirname(ex_path))
        config_path = os.path.join(ex_root_path,"config.yaml")
        ex_name = os.path.basename(ex_root_path)
        task_config = yaml.safe_load(open(config_path))
        
        tenant_dt_path = os.path.join(ex_root_path,task_config["managers"]["tenant"]["distribution_batch_dir"])
        tenant_dt = readinfo(tenant_dt_path)
        house_dt_path = os.path.join(ex_root_path,task_config["managers"]["community"]["distribution_batch_dir"])
        house_dt = readinfo(house_dt_path)
        
        tenental_system_path = os.path.join(ex_path,"tenental_system.json")
        tenental_system = readinfo(tenental_system_path)
        
        if ex_name not in results.keys():
            results[ex_name] = {}
        for u_type in u_types:
            result_path = os.path.join(ex_path,u_type)
            u_type_result_dict = {}
            
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
            
            for result_type in result_types:
                
                result_u_type_path = os.path.join(result_path,result_type+".csv")
                try:
                    result_u_type = pd.read_csv(result_u_type_path,index_col=index_cols_map[result_type])
                except:
                    continue
                result_u_type
                
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
                matrix = pd.DataFrame(values,
                                      columns=columns,
                                      index=pd.MultiIndex.from_tuples(
                                          list(result_u_type.index)
                                      )
                                      )
                u_type_result_dict[result_type] = result_u_type
            
            results[ex_name][u_type] = u_type_result_dict
            
    # concat_df: u_type: type_ex:
    
    for u_type in u_types:
        u_type_path = os.path.join(save_dir,u_type)
        if not os.path.exists(u_type_path):
            os.makedirs(u_type_path)
        
        
        frames = {}
        for ex_name in results.keys():

           
            for matrix_name,matrix in results[ex_name][u_type].items():
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
            


if __name__ == "__main__":
    # paths = [
    #         "LLM_PublicHouseAllocation/tasks/PHA_51tenant_5community_28house/configs/ver1_nofilter_singlelist/result/1699431290.0382807",
    #         "LLM_PublicHouseAllocation/tasks/PHA_51tenant_5community_28house/configs/ver2_nofilter_multilist_priority_7t_5h/result/1699435988.0701036"
    #         ]
    
    config_root = "LLM_PublicHouseAllocation/tasks/PHA_51tenant_5community_28house/configs"
    paths = []
    configs = os.listdir(config_root)
    for config in configs:
        result_path = os.path.join(config_root,config,"result")
        if os.path.exists(result_path):
            # paths.append(os.path.join(result_path,os.listdir(result_path)[-1]))
            result_files = os.listdir(result_path)
            for result_file in result_files:
                result_file_path = os.path.join(result_path,result_file,"all")
                if os.path.exists(result_file_path):
                    paths.append(os.path.join(result_path,result_file))
        
    
    concat_experiment_results(paths,
                              "PHA_51tenant_5community_28house",
                              "LLM_PublicHouseAllocation/experiments")