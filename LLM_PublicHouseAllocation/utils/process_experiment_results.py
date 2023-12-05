""" 需要替换实验表格内的数据 """

import pandas as pd
import os




def replace_data(ex_csv_dir = "forgpt",
                 ex_setting = "PHA_51tenant_5community_28house",
                 ex_save_root = "LLM_PublicHouseAllocation/experiments"
                 ):
    
    result_types = [
        "agg_objective_evaluation_matrix",
        "agg_utility_eval_matrix"
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
        for index, row in df.iterrows():
            ex_name = row["ex_name"]
            for indicator_name, indicator_value in row.items():
                indicator_mapped_key = indicator_map[indicator_name]
                
                if indicator_mapped_key in objective_matrix.columns:
                    row[indicator_name] = objective_matrix[objective_matrix["ex_name"] == ex_name][indicator_mapped_key]
                elif indicator_mapped_key in utility_matrix.columns:
                    row[indicator_name] = utility_matrix[objective_matrix["ex_name"] == ex_name][indicator_mapped_key]
                else:
                    raise Exception(f"Unknown indicator {indicator_name}!!!")
                
                
        df.to_csv(file_path)
        
        
def convert_to_latex(ex_csv_dir = "forgpt",
                     ex_save_root = "LLM_PublicHouseAllocation/experiments",
                     latex_table_file_path ="LLM_PublicHouseAllocation/experiments/latex.txt"):
    
    ex_csv_dir = os.path.join(ex_save_root,ex_csv_dir)
    
    files = os.listdir(ex_csv_dir)
    
    ex_name_map ={
        "allocation.csv":"Comparative experiments on different allocation methods.",
        "k_ratio.csv":"Comparative experiments on $k$ and $ratio$ in k-waitlist",
        "gap_house.csv":"Comparative experiments on $Batch^{House}$",
        "gap_tenant.csv":"Comparative experiments on $Batch^{Agent}$",
        "priority.csv":"Comparison experiments on whether to consider vulnerable groups",
        "queue.csv":"Comparative experiments on $|Queue|$"
    }
    
    # 定义一个格式化函数，将浮点数格式化为小数点后三位，并删除多余的零
    def format_float(val):
        return f'{val:.3f}'.rstrip('0').rstrip('.')

    # 创建一个格式化函数字典
    formatters = {col: format_float for col in ["Avg $House^{size}$",
                                                "Var $House^{size}$",
                                                "Rop",
                                                "mean WT",
                                                "gini coefficient",
                                                "social welfare",
                                                "ratio",
                                                "$|Batch^{Agent}|$",
                                                "$|Batch_{gap}^{Agent}|$",
                                                "$|Batch^{House}|$",
                                                "$|Batch_{gap}^{House}|$",
                                                "F(W,G)"]}
    latex_table_all =""
    
    latex_table_prefix ="""\\begin\{table*\}[h]
\\renewcommand\\arraystretch\{1.5\}
\caption\{{ex_name}.\}
\centering"""

    latex_table_suffix ="\end{table*}"
    
    cut_indicator ="Avg $House^{size}$"
    
    for file in files:
        file_path = os.path.join(ex_csv_dir,file)
        df = pd.read_csv(file_path)
        # 将DataFrame转换为Latex三线表格
        df = df.round(3)
        columns = df.columns
        column_format =""
        
        for idx,column in enumerate(columns):
            if cut_indicator == column:
                break
            elif column in ["Rounds"]:
                column_format+="r"
            else:
                column_format+="l"
                
        column_format+="|"+"r"*(len(columns)-idx)
            
            
        latex_table = df.to_latex(index=False,formatters=formatters,column_format=column_format)
        prefix = latex_table_suffix.format(ex_name = ex_name_map[file])
        suffix =latex_table_suffix
        
        latex_table = prefix+latex_table+suffix
        latex_table_all +="\n"+latex_table
        
        
    # # 打印Latex表格
    # print(latex_table)
    
    with open(latex_table_file_path, "w") as file:
    # 将文本写入文件
        file.write(latex_table_all)
    

if __name__ =="__main__":
    
    """替代数据"""
    replace_data()     
    
    
    """ 转换成latex数据 """
    files = os.listdir("forgpt")
    files = ["priority.csv"]
    for file in files:
        file_path = os.path.join("forgpt",file)
        df = pd.read_csv(file_path)
        convert_to_latex(df) 
                    
            