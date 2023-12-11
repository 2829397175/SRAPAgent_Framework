""" 需要替换实验表格内的数据 """

import pandas as pd
import os
import json
import numpy as np
import re

def writeinfo(data_dir,info):
    with open(data_dir,'w',encoding = 'utf-8') as f:
            json.dump(info, f, indent=4,separators=(',', ':'),ensure_ascii=False)


def replace_data(ex_csv_dir = "forgpt",
                 ex_setting = "PHA_51tenant_5community_28house",
                 ex_save_root = "LLM_PublicHouseAllocation/experiments"
                 ):
    
    ex_root_dir = os.path.join(ex_save_root,ex_setting,"all")
    
    unfinished_ex_names =[]

    indicator_map ={
        "Avg $House^\{size\}\\uparrow$":"mean_house_area",	
        "Var $House^\{size\}\\downarrow$":"var_mean_house_area",	
        "Rop $\\downarrow$":"Rop",	
        "mean WT $\\downarrow$":"mean_wait_turn",	
        "gini coefficient $\\downarrow$":"GINI_index",	
        "social welfare $\\uparrow$":"sw",
        "Rounds":"ex_len",
        "F(W,G) $\\uparrow$":"F(W,G)"
    }

    ex_csv_dir = os.path.join(ex_save_root,ex_csv_dir)
    
    files = os.listdir(ex_csv_dir)
    
    objective_matrix = pd.read_csv(os.path.join(ex_root_dir,"agg_objective_evaluation_matrix.csv"),index_col=0)
    utility_matrix = pd.read_csv(os.path.join(ex_root_dir,"agg_utility_eval_matrix.csv"),index_col=0)
    
    map_col ="all"
    
    for file in files:
        file_path = os.path.join(ex_csv_dir,file)
        df = pd.read_csv(file_path)
        finished_replace =[]
        for index, row in df.iterrows():
            try:
                ex_name = row["ex_name"]
                for indicator_name, indicator_value in row.items():
                    if indicator_name in indicator_map.keys():
                        indicator_mapped_key = indicator_map[indicator_name]
                        
                        if indicator_mapped_key in objective_matrix.index:
                            indicator_row = objective_matrix[objective_matrix["ex_name"] == ex_name]
                            if isinstance(indicator_row,pd.DataFrame):
                                assert indicator_row.notna().any().any(),"unsupported value"
                            else:
                                pass
                            df.loc[index,indicator_name] = indicator_row.loc[indicator_mapped_key,map_col]
                        elif indicator_mapped_key in utility_matrix.index:
                            indicator_row = utility_matrix[utility_matrix["ex_name"] == ex_name]
                            if isinstance(indicator_row,pd.DataFrame):
                                assert indicator_row.notna().any().any(),"unsupported value"
                            else:
                                pass
                            df.loc[index,indicator_name] = indicator_row.loc[indicator_mapped_key,map_col]
                            
                        elif indicator_mapped_key in objective_matrix.columns:
                            indicator_row = objective_matrix[objective_matrix["ex_name"] == ex_name]
                            df.loc[index,indicator_name] = indicator_row[indicator_mapped_key].values[0]
                        else:
                            raise Exception(f"Unknown indicator {indicator_name}!!!")
                finished_replace.append(True)
            except Exception as e:
                if ex_name not in unfinished_ex_names:
                    unfinished_ex_names.append(ex_name)
                finished_replace.append(False)
                
        df["finished_replace"] = finished_replace                
        df.to_csv(file_path,index=False)
    writeinfo(os.path.join(ex_save_root,ex_setting,"unfinished_table_ex_names.json"),unfinished_ex_names)
        
        
def convert_to_latex(ex_csv_dir = "forgpt",
                     ex_save_root = "LLM_PublicHouseAllocation/experiments",
                     latex_table_file_path ="LLM_PublicHouseAllocation/experiments/latex.txt",
                     bf_ratio = 0.3):
    
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
        # if isinstance(val,float):
        #     return f'{val:.3f}'.rstrip('0').rstrip('.')
        try:
            pattern = r'-?\d+\.\d+'  # 匹配至少一个数字，紧接着一个小数点，然后至少一个数字

            matches = re.findall(pattern, val)
            value = float(matches[0])
            outrange = float(matches[1])
            return "{value:.1f}$\\pm${outrange:.1f}".format(value = value,
                                                            outrange = outrange)
        except:
            try:
                return f'{float(val):.3f}'.rstrip('0').rstrip('.')
            except:
                return val
   
        

    
    latex_table_all =""
    
    latex_table_prefix ="""\\begin{{table*}}[h]
\\renewcommand\\arraystretch{{1.5}}
\\caption{{{ex_name}}}
\\centering"""

    latex_table_suffix ="\\end{table*}"
    
    cut_indicator ="Avg $House^{size}\\uparrow$"
    
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
            
        df = df[df["finished_replace"]]
        columns_to_remove = ["ex_name","finished_replace"]
        df = df.drop(columns=columns_to_remove)
        
        cols_indicators ={"up":["Avg $House^{size}\\uparrow$",
                                "social welfare $\\uparrow$",
                                "F(W,G) $\\uparrow$"],
                        "down":[
                            "Var $House^{size}\\downarrow$",
                            "Rop $\\downarrow$",
                            "mean WT $\\downarrow$",
                            "gini coefficient $\\downarrow$",
                            ]}
        
         # 创建一个格式化函数字典
        formatters = {col: format_float for col in ["Avg $House^{size}\\uparrow$",
                                                "Var $House^{size}\\downarrow$",
                                                "Rop $\\downarrow$",
                                                "mean WT $\\downarrow$",
                                                "gini coefficient $\\downarrow$",
                                                "social welfare $\\uparrow$",
                                                "ratio",
                                                "Rounds",
                                                "$|Batch^{Agent}|$",
                                                "$|Batch_{gap}^{Agent}|$",
                                                "$|Batch^{House}|$",
                                                "$|Batch_{gap}^{House}|$",
                                                "F(W,G) $\\uparrow$"]}
        for col_name in df.columns:
            if col_name in formatters.keys():
                df[col_name] = df[col_name].apply(formatters[col_name])
        
        
        for col_type_indicator,col_names in cols_indicators.items():
            for col_name in col_names:
                if col_name not in df.columns:
                    continue
                values = df[col_name].values.tolist()
                values_transfered_float = []
                for idx, value in enumerate(values):
                    try:
                        pattern = r'-?\d+\.\d+'  # 匹配至少一个数字，紧接着一个小数点，然后至少一个数字

                        matches = re.findall(pattern, value)
                        value = float(matches[0])
                        outrange = float(matches[1])
                        values_transfered_float.append((value,idx))
                    except:
                        values_transfered_float.append((float(value),idx))
                
                bf_num = int(bf_ratio*len(values_transfered_float))
                values_transfered_float.sort(key=lambda x:x[0],reverse=col_type_indicator=="up")
                col_index = df.columns.get_loc(col_name)
                for tuple_val in values_transfered_float[:bf_num]:
                    idx = tuple_val[1]
                    df.iloc[idx,col_index] = f"\\textbf{{{df.iloc[idx,col_index]}}}"
            
       
        
        latex_table = df.to_latex(index=False,column_format=column_format)
        prefix = latex_table_prefix.format(ex_name = ex_name_map[file])
        suffix = latex_table_suffix
        
        latex_table = prefix+latex_table+suffix
        latex_table_all +="\n"+latex_table
        
        
    # # 打印Latex表格
    # print(latex_table)
    
    with open(latex_table_file_path, "w") as file:
    # 将文本写入文件
        file.write(latex_table_all)
    
    
def get_table_ex_names(ex_csv_dir = "forgpt",
                 ex_setting = "PHA_51tenant_5community_28house",
                 ex_save_root = "LLM_PublicHouseAllocation/experiments"):
    ex_csv_dir = os.path.join(ex_save_root,ex_csv_dir)
    
    ex_names = []
    for ex_csv_path in list(os.listdir(ex_csv_dir)):
        df = pd.read_csv(os.path.join(ex_csv_dir,ex_csv_path))
        for ex_name in df["ex_name"]:
            if ex_name not in ex_names:
                ex_names.append(ex_name)
    writeinfo(os.path.join(ex_save_root,ex_setting,"table_ex_names.json"),ex_names)

if __name__ =="__main__":
    
    
    ex_setting = "PHA_51tenant_5community_28house_new_priority_label"
    """替代数据"""
    replace_data(ex_setting=ex_setting)     
    
    get_table_ex_names(ex_setting=ex_setting)
    
    """ 转换成latex数据 """
    # convert_to_latex() 
                    
                    
            