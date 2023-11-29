
import pandas as pd
import os
def replace_data(ex_csv_dir = "forgpt",
                 ex_setting = "PHA_51tenant_5community_28house",
                 ex_save_root = "LLM_PublicHouseAllocation/experiments"
                 ):
    
    result_types = [
        "objective_evaluation_matrix",
        "utility_eval_matrix"
    ]
    ex_root_dir = os.path.join(ex_setting,ex_save_root,"all")
    

    indicator_map ={
        "Avg $House^{size}$":"mean_house_area",	
        "Var $House^{size}$":"var_mean_house_area",	
        "Rop":"Rop",	
        "mean WT":"mean_wait_turn",	
        "gini coefficient":"GINI_index",	
        "social welfare":"sw",
        "Rounds":"ex_len"
    }
    
    ex_csv_dir = os.path.join(ex_save_root,ex_csv_dir)
    
    files = os.listdir(ex_csv_dir)
    
    objective_matrix = pd.read_csv(os.path.join(ex_save_root,"objective_evaluation_matrix.csv"))
    utility_matrix = pd.read_csv(os.path.join(ex_save_root,"utility_eval_matrix.csv"))
    
    for file in files:
        file_path = os.path.join(ex_csv_dir,file)
        df = pd.read_csv(file_path)
        for ex_name in df["ex_name"]:
            for indicator in indicator_map.keys():
                indicator_mapped_key = indicator_map[indicator]
                if indicator_mapped_key in objective_matrix.columns:
                    df[]
        