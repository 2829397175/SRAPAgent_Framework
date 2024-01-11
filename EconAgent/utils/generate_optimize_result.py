import pandas as pd
import json

import os

def generate_optimize_df(optimize_log_dir):
    
    
    with open(os.path.join(optimize_log_dir,
                           "optimize_log.json"),'r',encoding = 'utf-8') as f:
        optimize_log = json.load(f)
        
    with open(os.path.join(optimize_log_dir,
                           "ex_name_map.json"),'r',encoding = 'utf-8') as f:
        ex_name_map = json.load(f)
        
        
    """ 先filter掉没有值的结果项 """
    round_k = 0
    max_round = 0
    processed_optimize_log = {}
    for k in optimize_log.keys():
        if k == "regressor":
            continue
        optimize_name = list(optimize_log[k]["optimized"].keys())[0]
        if k == "final_result":
            processed_optimize_log[k] = optimize_log[k]
        else:
            max_round = int(k) if int(k) > max_round else max_round
            if optimize_log[k]["optimized"][optimize_name] != []:
                processed_optimize_log[f"{round_k}"]  ={
                    "optimized":{
                        optimize_name:
                            optimize_log[k]["optimized"][optimize_name]
                            }
                    }
                round_k+=1
            
        

    optimize_log = processed_optimize_log  
    
    path = os.path.join(optimize_log_dir,
                                        f"round_{max_round}",
                                        "debug_used_data.csv")
    if not os.path.exists(path):
        path = os.path.join(optimize_log_dir,
                                        f"round_{max_round}",
                                        "debug.csv")
    
    debug_df = pd.read_csv(path,
                           index_col=0)
    
    for index in debug_df.index:
        debug_df.loc[index,"ex_name"] = ex_name_map[str(index)]

    base_matrix = pd.read_csv("EconAgent/experiments/forgpt/optimize.csv",
                              index_col=0)
    
    
    
    save_matrix_root = os.path.join(optimize_log_dir,"matrix")
    
    if not os.path.exists(save_matrix_root):
        os.makedirs(save_matrix_root)
    
    """ 生成与全局最优的比较（每轮迭代的最优值） """
    for optimize_round, optimized_data in optimize_log.items():
        if optimize_round ==  "final_result":
            optimized_data = optimized_data["optimized"]["max_gt_y"]
            base_matrix.loc["$\pi_{optimized}$","ex_name"] = optimized_data["ex_name"]
        # else:
        #     base_matrix.loc[int(optimize_round)+1,"ex_name"] = list(optimized_data["optimized"].keys())[0]
    
    debug_df_filtered = debug_df[debug_df["ex_name"] != optimized_data["ex_name"]]
    
    top_three_indices = debug_df_filtered['gt_y'].nlargest(10).index
    for idx,indice in enumerate(top_three_indices):
        base_matrix.loc[f"$\pi:f(\pi)^{idx+1}$","ex_name"] = ex_name_map[str(indice)]
    
    top_three_indices = debug_df_filtered['predict_y'].nlargest(10).index
    for idx,indice in enumerate(top_three_indices):
        base_matrix.loc[f"$\pi:\widetilde{f}(\pi)^{idx+1}$","ex_name"] = ex_name_map[str(indice)]
    
    
    for idx_r in base_matrix.index:
        ex_name = base_matrix.loc[idx_r,"ex_name"]
        ex_idxs = []
        for ex_idx_,ex_name_ in ex_name_map.items():
            if ex_name_ == ex_name:
                ex_idx = int(ex_idx_)
                ex_idxs.append(ex_idx)
        for ex_idx in ex_idxs:
            try:
                if ex_idx != -1:
                    base_matrix.loc[idx_r,"$y_{gt}$"] = debug_df.loc[ex_idx,'gt_y']
                    base_matrix.loc[idx_r,"$y_{predict}$"] = debug_df.loc[ex_idx,'predict_y']
                else:
                    base_matrix.loc[idx_r,"$y_{gt}$"] = "nan"
                    base_matrix.loc[idx_r,"$y_{predict}$"] = "nan"
                break
            except:
                continue
    
    base_matrix.to_csv(os.path.join(save_matrix_root,"optimize_data.csv"))
    
    """ 生成与所有实验数据（取最优的三个）的对比 """
    
    df_optimize_y = []
    
    for optimize_round, optimized_data in optimize_log.items():
        if optimize_round ==  "final_result":
            
            best_ex_id_op = optimized_data["optimized"]["max_gt_y"]["ex_idx"]
            
            df_optimize_y.append(
                {
                    "Optimizer Round":"final",
                    "$y_{gt}$":debug_df.loc[best_ex_id_op,
                                                "gt_y"],
                    "$y_{predict}$":debug_df.loc[best_ex_id_op,
                                                     "predict_y"]
                }
            )
        else:
            for ex_name, optimized_ex_results in optimized_data["optimized"].items():
                for optimize_ex_result in optimized_ex_results:
                    df_optimize_y.append(
                        {
                            "Optimizer Round":int(optimize_round)+1,
                            "$y_{gt}$":debug_df.loc[optimize_ex_result["ex_idx"],
                                                "gt_y"],
                            "$y_{predict}$":debug_df.loc[optimize_ex_result["ex_idx"],
                                                     "predict_y"]
                        }
                    )
                    
    top_three_indices = debug_df_filtered['gt_y'].nlargest(10).index
    for idx,indice in enumerate(top_three_indices):
        df_optimize_y.append({
            "Optimizer Round":f"best $y_{{gt}}^{{\\text{idx+1}}}$",
            "$y_{gt}$":debug_df.loc[indice,
                                "gt_y"],
            "$y_{predict}$":debug_df.loc[indice,
                                "predict_y"] 
        })
    
    top_three_indices = debug_df_filtered['predict_y'].nlargest(10).index
    for idx,indice in enumerate(top_three_indices):
        df_optimize_y.append({
            "Optimizer Round":f"best $y_{{predict}}^{{\\text{idx+1}}}$",
            "$y_{gt}$":debug_df.loc[indice,
                                "gt_y"],
            "$y_{predict}$":debug_df.loc[indice,
                                "predict_y"] 
        })
        
    df_optimize_y = pd.DataFrame(df_optimize_y)
    df_optimize_y.to_csv(os.path.join(save_matrix_root,"optimize_compare.csv"),
                         index=False)
    
if __name__ == "__main__":
    # generate_optimize_df("EconAgent/optimizer/logs/1703218764.1385152")
    
    """fairness"""
    # generate_optimize_df("EconAgent/optimizer/logs/1704249275.8022254")

    # generate_optimize_df("EconAgent/optimizer/logs/1704249344.8196857")
    
    
    generate_optimize_df("EconAgent/optimizer/logs_fairness/1704684718.9230282")
    """satisfaction"""
    # generate_optimize_df("EconAgent/optimizer/logs/1704196514.0865245")
    # generate_optimize_df("EconAgent/optimizer/logs/1703290655.310023")
    generate_optimize_df("EconAgent/optimizer/logs/1704367257.8943155")
    