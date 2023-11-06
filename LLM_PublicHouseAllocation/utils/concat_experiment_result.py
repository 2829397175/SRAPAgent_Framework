import pandas as pd
import os

def concat_experiment_results(ex_paths:list = [],
                              ex_setting = "PHA_51tenant_5community_28house",
                              save_dir = "LLM_PublicHouseAllocation\experiments"
                              ):
    
    u_types = ["all","choosed"] 
    result_types = [
        "objective_evaluation_matrix",
        "utility_eval_matrix"
    ]
    
    results = {
        
    } # type_ex:u_type:{eval matrix}
    
    
    for ex_path in ex_paths:
        ex_name = os.path.basename(os.path.dirname(os.path.dirname(ex_path)))
        ex_name = ex_name.strip(ex_setting)
        ex_name = ex_name.strip("_")
        if ex_name not in results.keys():
            results[ex_name] = {}
        for u_type in u_types:
            result_path = os.path.join(ex_path,u_type)
            u_type_result_dict = {}
            for result_type in result_types:
                result_u_type_path = os.path.join(result_path,result_type+".csv")
                result_u_type = pd.read_csv(result_u_type_path,index_col=0)
                result_u_type["ex_name"] = ex_name
                result_u_type.set_index('ex_name',inplace=True,append=True)
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
            concated_df.to_csv(os.path.join(u_type_path,
                                            matrix_name+".csv"))
            


if __name__ == "__main__":
    paths = [
        # 注意：ver2 的实验结果
        # 少跑了social net
        #PHA_51tenant_5community_28house_ver1_nofilter_multilist_priority中 没三轮进行一次social
        "LLM_PublicHouseAllocation/tasks/PHA_51tenant_5community_28house_ver2_nofilter_multilist_priority_7t_5h/result/1698634392.3664887",
        "LLM_PublicHouseAllocation/tasks/PHA_51tenant_5community_28house_ver1_nofilter_singlelist_priority/result/1698659088.3178897",
        "LLM_PublicHouseAllocation/tasks/PHA_51tenant_5community_28house_ver1_nofilter_singlelist/result/1698324294.4337833",
        "LLM_PublicHouseAllocation/tasks/PHA_51tenant_5community_28house_ver1_nofilter_multilist_priority_7t_5h/result/1698644954.8669686",
        "LLM_PublicHouseAllocation/tasks/PHA_51tenant_5community_28house_ver1_nofilter_multilist_priority/result/1698393247.591396",
        "LLM_PublicHouseAllocation/tasks/PHA_51tenant_5community_28house_ver1_nofilter_multilist/result/1698319444.931747"
        
    ]
    
    concat_experiment_results(paths)