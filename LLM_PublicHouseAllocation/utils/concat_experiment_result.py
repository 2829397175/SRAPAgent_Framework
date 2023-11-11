import pandas as pd
import os

def concat_experiment_results(ex_paths:list = [],
                              ex_setting = "PHA_51tenant_5community_28house",
                              save_dir = "LLM_PublicHouseAllocation/experiments/oldver_data/newver_eval"
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
    
    results = {
        
    } # type_ex:u_type:{eval matrix}
    
    
    for ex_path in ex_paths:
        ex_name = os.path.basename(os.path.dirname(os.path.dirname(ex_path)))
        if ex_name not in results.keys():
            results[ex_name] = {}
        for u_type in u_types:
            result_path = os.path.join(ex_path,u_type)
            u_type_result_dict = {}
            for result_type in result_types:
                result_u_type_path = os.path.join(result_path,result_type+".csv")
                result_u_type = pd.read_csv(result_u_type_path,index_col=index_cols_map[result_type])
                result_u_type["ex_name"] = ex_name
                result_u_type.set_index('ex_name',inplace=True,append=True)
                result_u_type = result_u_type.stack()
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
            "LLM_PublicHouseAllocation/tasks/PHA_51tenant_5community_28house/configs/ver1_nofilter_singlelist/result/1699431290.0382807",
            "LLM_PublicHouseAllocation/tasks/PHA_51tenant_5community_28house/configs/ver2_nofilter_multilist_priority_7t_5h/result/1699435988.0701036"
            ]
    
    concat_experiment_results(paths)