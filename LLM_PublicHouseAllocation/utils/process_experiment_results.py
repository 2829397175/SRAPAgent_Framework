""" 需要替换实验表格内的数据 """

import pandas as pd
import os
import json
import numpy as np
import re
import copy

def writeinfo(data_dir,info):
    with open(data_dir,'w',encoding = 'utf-8') as f:
            json.dump(info, f, indent=4,separators=(',', ':'),ensure_ascii=False)


def process_delta_data(*datas):
    processed_datas = []
    for data in datas:
        try:
            pattern = r'-?\d+\.\d+'  # 匹配至少一个数字，紧接着一个小数点，然后至少一个数字
            matches = re.findall(pattern,data)
            value = float(matches[0])
            outrange = float(matches[1])
            processed_datas.append({
                "mean":value,
                "delta":outrange
            })
        except:
            try:
                processed_datas.append({
                    "mean":float(data),
                    "delta":0
                })
            except Exception as e:
                raise Exception(e)

    sigma_difference = np.sqrt(processed_datas[0]["delta"]**2 + processed_datas[1]["delta"]**2)
    difference = processed_datas[0]["mean"] - processed_datas[1]["mean"]
    
    if abs(sigma_difference) < 1e-10:
        return difference
    else:
        return "{value:.4f}$\\pm${outrange:.4f}".format(value = difference,
                                                        outrange = sigma_difference)
    
def replace_data(ex_csv_dir = "forgpt",
                 ex_setting = "PHA_51tenant_5community_28house",
                 ex_save_root = "LLM_PublicHouseAllocation/experiments",
                 tasks_dir = "LLM_PublicHouseAllocation/tasks"
                 ):
    
    ex_root_dir = os.path.join(ex_save_root,ex_setting,"all")
    
    unfinished_ex_names =[]
    ex_names = []
    indicator_map ={
        "Avg $House^{size}\\uparrow$":"mean_house_area",	
        "Var $House^{size}\\downarrow$":"var_mean_house_area",	
        "Rop $\\downarrow$":"Rop",	
        "Avg WT $\\downarrow$":"mean_wait_turn",	
        "gini coefficient $\\downarrow$":"GINI_index",	
        "SW $\\uparrow$":"sw",
        "Rounds":"ex_len",
        "F(W,G) $\\uparrow$":"F(W,G)",
        "k":"order_k",
        "$Agent^{max(choose)}$":"tenant_max_choose",
        "mean IWT $\\downarrow$":"mean_idle_wait_turn",

    }
    
    delta_indicator_map ={
        "$\\Delta$Avg $House^{size}\\uparrow$": "mean_house_area",
        "$\\Delta$Var $House^{size}\\downarrow$":"var_mean_house_area",
        "$\\Delta$Rop $\\downarrow$":"Rop",
        "$\\Delta$Avg WT $\\downarrow$":"mean_wait_turn",	
        "$\\Delta$gini coefficient $\\downarrow$":"GINI_index",	
        "$\\Delta$SW $\\uparrow$":"sw",
        "$\\Delta F(W,G) \\uparrow$":"F(W,G)",
    }

    ex_csv_dir = os.path.join(ex_save_root,ex_csv_dir)
    
    files = os.listdir(ex_csv_dir)
    # files = list(filter(lambda file:"optimize" in file, files))
    # files =["priority.csv",
    #         "housing_points.csv"]
    # files =["priority_housing_points.csv"]
    # files =["hongkong.csv"]
    files =["optimize_sw.csv",
            "optimize_fair.csv"]
    
    objective_matrix = pd.read_csv(os.path.join(ex_root_dir,"agg_objective_evaluation_matrix.csv"),index_col=0)
    utility_matrix = pd.read_csv(os.path.join(ex_root_dir,"agg_utility_eval_matrix.csv"),index_col=0)
    matrix = pd.concat([objective_matrix,utility_matrix])
    
    map_col ="all"
    
    ex_save_dir = os.path.join(ex_save_root,ex_setting,os.path.basename(ex_csv_dir))
    
    if any(["optimize" in file for file in files]):
        km_max_objective_matrix = pd.read_csv(os.path.join(tasks_dir,
                                                        ex_setting,
                                                        "global_evaluation/KM_max_pair/all",
                                                        "objective_evaluation_matrix.csv"),
                                            index_col=0)
        km_max_utility_matrix = pd.read_csv(os.path.join(tasks_dir,
                                                        ex_setting,
                                                        "global_evaluation/KM_max_pair/all",
                                                        "utility_eval_matrix.csv"),
                                            index_col=0)
        
        km_max_matrix = pd.concat([km_max_objective_matrix,
                                km_max_utility_matrix])
        
        km_max_matrix["ex_name"] = "optimal_utility"
        
        matrix = pd.concat([matrix,km_max_matrix])
    
    
    if not os.path.exists(ex_save_dir):
        os.makedirs(ex_save_dir)
    
    finished_ex_names = matrix["ex_name"].value_counts().keys().to_list()
    
    
    
    for file in files:
        file_path = os.path.join(ex_csv_dir,file)
        df = pd.read_csv(file_path)
        finished_replace =[]
        for index, row in df.iterrows():
            try:
                
                for indicator_name, indicator_value in row.items():
                    if indicator_name in indicator_map.keys():
                        ex_name = row["ex_name"]
                        if ex_name !="optimal_utility" and \
                            ex_name not in ex_names:
                                ex_names.append(ex_name)
                        if ex_name not in finished_ex_names:
                            if ex_name not in unfinished_ex_names:
                                unfinished_ex_names.append(ex_name)
                        indicator_mapped_key = indicator_map[indicator_name]
                        indicator_row = matrix[matrix["ex_name"] == ex_name]
                        
                        if indicator_mapped_key in indicator_row.index:
                            if isinstance(indicator_row,pd.DataFrame):
                                assert indicator_row.notna().any().any(),"unsupported value"
                            df.loc[index,indicator_name] = indicator_row.loc[indicator_mapped_key,map_col]

                        elif indicator_mapped_key in indicator_row.columns:
                            try:
                                df.loc[index,indicator_name] = indicator_row[indicator_mapped_key].values[0]
                            except:
                                df.loc[index,indicator_name] = np.NaN
                        else:
                            if ex_name == "optimal_utility":
                                continue
                            else:
                                raise Exception(f"Unknown indicator {indicator_name}!!!")
                    elif indicator_name in delta_indicator_map.keys():

                        ex_name_priority = row["ex_name_prority"]
                        ex_name_nopriority = row["ex_name_nopriority"]
                        
                        if ex_name_priority not in finished_ex_names:
                            if ex_name_priority not in unfinished_ex_names:
                                unfinished_ex_names.append(ex_name_priority)
                        
                        if ex_name_nopriority not in finished_ex_names:
                            if ex_name_nopriority not in unfinished_ex_names:
                                unfinished_ex_names.append(ex_name_nopriority)
                        
                        priority_row = copy.deepcopy(matrix[matrix["ex_name"] == ex_name_priority])
                        nopriority_row = copy.deepcopy(matrix[matrix["ex_name"] == ex_name_nopriority])
                        
                        
                        indicator_mapped_key = delta_indicator_map[indicator_name]
                        
                        if indicator_mapped_key in matrix.index:
                            if isinstance(priority_row,pd.DataFrame):
                                assert priority_row.notna().any().any(),"unsupported value"
                            if isinstance(nopriority_row,pd.DataFrame):
                                assert nopriority_row.notna().any().any(),"unsupported value"
                                
                            value = process_delta_data(priority_row.loc[indicator_mapped_key,map_col],\
                                nopriority_row.loc[indicator_mapped_key,map_col])
                            df.loc[index,indicator_name] = value

                        elif indicator_mapped_key in matrix.columns:
                            value = process_delta_data(priority_row[indicator_mapped_key].values[0],\
                                nopriority_row[indicator_mapped_key].values[0])
                            df.loc[index,indicator_name] = value
                        else:
                            raise Exception(f"Unknown indicator {indicator_name}!!!")
                finished_replace.append(True)
            except Exception as e:
                print(e)
                finished_replace.append(False)
                
        save_file_path = os.path.join(ex_save_dir,file)
        df["finished_replace"] = finished_replace                
        df.to_csv(save_file_path,index=False)
    writeinfo(os.path.join(ex_save_root,ex_setting,"unfinished_table_ex_names.json"),unfinished_ex_names)
    writeinfo(os.path.join(ex_save_root,ex_setting,"table_ex_names.json"),ex_names)
        
        
def convert_to_latex(ex_csv_dir = "forgpt",
                     ex_setting = "PHA_51tenant_5community_28house",
                     ex_save_root = "LLM_PublicHouseAllocation/experiments",
                     latex_table_file_path ="LLM_PublicHouseAllocation/experiments/latex.txt",
                     bf_ratio = 0.4):
    
    ex_csv_dir = os.path.join(ex_save_root,ex_setting,ex_csv_dir)
    
    files = os.listdir(ex_csv_dir)
    
    ex_name_map ={
        "allocation.csv":"Comparative experiments on different allocation methods.",
        "k_ratio.csv":"Comparative experiments on $k$ and $ratio$ in k-waitlist",
        "gap_house.csv":"Comparative experiments on $Batch^{House}$",
        "gap_tenant.csv":"Comparative experiments on $Batch^{Agent}$",
        "priority.csv":"Comparison experiments on whether to consider vulnerable groups",
        "queue.csv":"Comparative experiments on $|Queue|$",
        "optimize.csv":"Experiments on Optimizer",
        "hongkong.csv":"Comparison with data from theoretical experiments",
        "optimize_100p_data.csv": "Experiments on Optimizer: Population Initialization Using a Blend of Random and Original Data",
        "optimize_compare_100p_data.csv":"Experiments on Optimizer (Init. random and data): $y_{gt}$ and $y_{predict}$",
        "optimize_data.csv": "Experiments on Optimizer: Population Initialization Using Original Data",
        "optimize_compare_data.csv":"Experiments on Optimizer (Init. data): $y_{gt}$ and $y_{predict}$",
        "housing_points.csv":"Experiments on whether to consider housing points",
        "priority_housing_points.csv":"Comparative experiments on different Queue policies.",
        "optimize_sw.csv":"Experiments on Optimizer: Biased towards high social satisfaction",
        "optimize_fair.csv":"Experiments on Optimizer: Biased towards high social fairness"
        
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
    def format_float_2(val):
        try:
            pattern = r'-?\d+\.\d+'  # 匹配至少一个数字，紧接着一个小数点，然后至少一个数字

            matches = re.findall(pattern, val)
            value = float(matches[0])
            outrange = float(matches[1])
            return "{value:.2f}$\\pm${outrange:.1f}".format(value = value,
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
    
    cut_indicators =["Avg $House^{size}\\uparrow$",
                     "$\\Delta$Avg $House^{size}\\uparrow$",
                     "$y_{gt}$"]
    
    # files = list(filter(lambda file:"optimize" in file, files))
    # files =[]
    files = ["optimize_sw.csv","optimize_fair.csv"]
    # files =["hongkong.csv"]
    # files =["priority.csv",
    #         "housing_points.csv"]
    # files =["priority_housing_points.csv"]
    cols_indicators ={"up":["Avg $House^{size}\\uparrow$",
                                "SW $\\uparrow$",
                                "F(W,G) $\\uparrow$",
                                "$\\Delta$Avg $House^{size}\\uparrow$",
                                "$\\Delta$SW $\\uparrow$",
                                "$\\Delta F(W,G) \\uparrow$",
                                "$y_{gt}$",
                                "$y_{predict}$"],
                        "down":[
                            "Var $House^{size}\\downarrow$",
                            "Rop $\\downarrow$",
                            "Avg WT $\\downarrow$",
                            "gini coefficient $\\downarrow$",
                            "$\\Delta$Var $House^{size}\\downarrow$",
                            "$\\Delta$Rop $\\downarrow$",
                            "$\\Delta$Avg WT $\\downarrow$",	
                            "$\\Delta$gini coefficient $\\downarrow$",	
                            ]}
        
    indicator_types={
        "satisfaction":[
            "Avg WT $\\downarrow$",
            "$\\Delta$Avg WT $\\downarrow$",	
            "Avg $House^{size}\\uparrow$",
            "SW $\\uparrow$",
            "$\\Delta$Avg $House^{size}\\uparrow$",
            "$\\Delta$SW $\\uparrow$",
            
        ],
        "fairness":[
            "Var $House^{size}\\downarrow$",
            "Rop $\\downarrow$",
            "gini coefficient $\\downarrow$",
            "F(W,G) $\\uparrow$",
            "$\\Delta$Var $House^{size}\\downarrow$",
            "$\\Delta$Rop $\\downarrow$",
            "$\\Delta$gini coefficient $\\downarrow$",	
            "$\\Delta F(W,G) \\uparrow$",
        ]
    }
    
    for file in files:
        file_path = os.path.join(ex_csv_dir,file)
        df = pd.read_csv(file_path)
        # 将DataFrame转换为Latex三线表格
        df = df.round(3)
        columns = df.columns.to_list()
        for idx,column in enumerate(columns):
            if column in cut_indicators:
                break
        
        
        new_columns = columns[:idx]
        satis =[]
        fair =[]
        others =[]
        for column in columns[idx:]:
            if column in indicator_types["satisfaction"]:
                satis.append(column)
            elif column in indicator_types["fairness"]:
                fair.append(column)
            else:
                others.append(column)
        new_columns.extend([*satis,*fair,*others])
        
        df = df[new_columns]
        
        if "optimize_compare" in file:
            pass
        
        else:
            df = df[df["finished_replace"]]
        
            if "optimize" in file:
                columns_to_remove = ["finished_replace","ex_name"]
                # df['ex_name'] = [ex_name.replace("_"," ") for ex_name in df['ex_name']]
                # df.rename({"ex_name": "Ex.setting"}, axis=1,inplace=True)
            elif file in ["priority.csv","housing_points.csv","priority_housing_points.csv"]:
                columns_to_remove = ["ex_name_prority","ex_name_nopriority","finished_replace"]
            else:
                columns_to_remove = ["ex_name","finished_replace"]
            
            if "Rounds" in df.columns:
                columns_to_remove.append("Rounds")
            
            df = df.drop(columns=columns_to_remove)
        
        columns = df.columns.to_list()
        column_format =""  
        for idx,column in enumerate(columns):
            if column in cut_indicators:
                break
            elif column in ["Rounds"]:
                column_format+="r"
            else:
                column_format+="l"
        column_format+="|"+"r"*(len(columns)-idx)
        
         # 创建一个格式化函数字典
        formatters = {**{col: format_float for col in ["Avg $House^{size}\\uparrow$",
                                                "Var $House^{size}\\downarrow$",
                                                "Rop $\\downarrow$",
                                                "Avg WT $\\downarrow$",
                                                
                                                "SW $\\uparrow$",
                                                "ratio",
                                                "Rounds",
                                                "$|Batch^{Agent}|$",
                                                "$|Batch_{gap}^{Agent}|$",
                                                "$|Batch^{House}|$",
                                                "$|Batch_{gap}^{House}|$",
                                                "F(W,G) $\\uparrow$",
                                                "$\\Delta$Avg $House^{size}\\uparrow$",
                                                "$\\Delta$Var $House^{size}\\downarrow$",
                                                "$\\Delta$Rop $\\downarrow$",
                                                "$\\Delta$Avg WT $\\downarrow$",	
                                                "$\\Delta$gini coefficient $\\downarrow$",	
                                                "$\\Delta$SW $\\uparrow$",
                                                "$\\Delta F(W,G) \\uparrow$",
                                                "mean IWT $\\downarrow$",
                                                "$y_{gt}$",
                                                "$y_{predict}$"]},
                      **{
                        col:format_float_2 for col in [
                            "gini coefficient $\\downarrow$",
                        ]  
                      },
                      **{col:int for col in ["k",
                                             "$Agent^{max(choose)}$"]}
                      }
        
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
                        if value == "nan":
                            continue
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
    # files = os.listdir(ex_csv_dir)
    files = ["priority_housing_points.csv"]
    for ex_csv_path in files:
        df = pd.read_csv(os.path.join(ex_csv_dir,ex_csv_path))
        ex_name_cols =["ex_name_prority","ex_name","ex_name_noprority"]
        try:
            for ex_name_col in ex_name_cols:
                for ex_name in df[ex_name_col]:
                    if ex_name not in ex_names:
                        ex_names.append(ex_name)
        except:
            pass
    writeinfo(os.path.join(ex_save_root,ex_setting,"table_ex_names.json"),ex_names)

if __name__ =="__main__":
    
    
    # ex_setting = "PHA_51tenant_5community_28house_new_priority_label"
    ex_setting = "PHA_51tenant_5community_28house_new_priority_label_optimizer"
    # ex_setting = "PHA_70tenant_100houses_hongkong"
    # ex_setting ="PHA_51tenant_5community_28house_new_priority_perpersonlabel"   
    """替代数据"""
    replace_data(ex_setting=ex_setting)     
    
    #get_table_ex_names(ex_setting=ex_setting)
    
    """ 转换成latex数据 """
    convert_to_latex(ex_setting=ex_setting) 
                    
                    
            