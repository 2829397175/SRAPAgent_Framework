

import matplotlib.pyplot as plt
import os
import numpy as np
import pandas as pd

import json

# plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体来显示中文
plt.rcParams['axes.unicode_minus'] = False    # 用来正常显示负号


def readinfo(data_dir):
    assert os.path.exists(data_dir),"no such file path: {}".format(data_dir)
    with open(data_dir,'r',encoding = 'utf-8') as f:
        data_list = json.load(f)
    return data_list

def visualize_tenant(data_path):
    save_path = os.path.join(data_path,"visualize")
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    with open(os.path.join(data_path,"tenant_51.json"),'r',encoding = 'utf-8') as f:
        tenant_json = json.load(f)
        
    for tenant_id,tenant_info in tenant_json.items():
        if tenant_info["family_members_num"]>3:
            tenant_info["family_members_num_group"]="family_members_num>3"
        elif tenant_info["family_members_num"]>1:
            tenant_info["family_members_num_group"]="3>=family_members_num>=2"
        else:
            tenant_info["family_members_num_group"]="family_members_num=1"
        
    show_keys_bar =[
        # "family_members_num",
                    "family_members_num_group",
                ]
    
    for show_key in show_keys_bar:
        
        visualize_distribution_bar(tenant_json,
                             save_path,
                             show_key)
    show_keys_plot =["monthly_rent_budget"]
    for show_key in show_keys_plot:
        visualize_distribution_plot(tenant_json,
                             save_path,
                             show_key)
        
def visualize_tenant_rating(global_rating_path,
                            tenant_ids:list=[],
                            show_score_key:str ="score",
                            house_path:str="EconAgent/tasks/PHA_51tenant_5community_28house/data/house_28.json",
                            tenant_path:str ="EconAgent/tasks/PHA_51tenant_5community_28house/data/tenant_51.json"):
    save_path = os.path.join(global_rating_path,
                             "visualize",
                             show_score_key)
    
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    with open(os.path.join(global_rating_path,"global_score_newver.json"),'r',encoding = 'utf-8') as f:
        score_json = json.load(f)
        
    with open(house_path,'r',encoding = 'utf-8') as f:
        house_json = json.load(f)
    
    with open(tenant_path,'r',encoding = 'utf-8') as f:
        tenant_json = json.load(f)
        
        
        
    house_ids = []
    for house_infos in house_json.values():
        house_ids.extend(list(house_infos.keys()))
    
    if tenant_ids ==[]:
        tenant_ids = tenant_json.keys()
    
    score_gap_var = []
    for tenant_id in tenant_ids:
        show_key = f"tenant {tenant_id} rating"
        
        assert tenant_id in score_json.keys()
        rating_data = []
        
        for house_id in house_ids:
            if show_score_key =="score_gap":
                rating_data.append(np.abs(int(score_json[tenant_id]["ratings"][house_id]["llm_score"])
                                        - int(score_json[tenant_id]["ratings"][house_id]["objective_score"])))
            
            else:
                rating_data.append(int(score_json[tenant_id]["ratings"][house_id][show_score_key]))
              
        if show_score_key =="score_gap":
            # print("var of score gap",np.var(rating_data))
            score_gap_var.append(np.var(rating_data))
            continue
            
        
            
        frequency_dict = {}
        for size in rating_data:
            
            frequency_dict[size] = frequency_dict.get(size, 0) + 1
        
        family_sizes = list(frequency_dict.keys())
        frequency = list(frequency_dict.values())
        frequency = frequency /sum(frequency)

        # plt.xticks(range(min(family_sizes),max(family_sizes)))
        # plt.xlim(900,2601)

        # 绘制柱状图
        
        if show_score_key=="score":
            assert max(frequency_dict)<=20
            plt.xlim(0,20)
            plt.xticks(range(0, 21, 1))
        else:
            plt.xlim(0,10)
            plt.xticks(range(0, 11, 1))
        plt.bar(family_sizes, frequency,width=0.5)
        
        # 添加标题和轴标签
        #plt.title(f'{show_key}_distribution'.replace("_"," "))
        plt.xlabel(show_key)
        plt.ylabel('frequency')

        # 显示图形
        # plt.show()
        plt.savefig(os.path.join(save_path,f"{show_key}.png"))
        plt.clf()
        
    if show_score_key =="score_gap":
        df_var = pd.DataFrame()
        df_var["tenant_ids"] = tenant_ids
        df_var["score_gap_var"] = score_gap_var
        print("mean gap var", np.mean(score_gap_var))
        df_var.to_csv(os.path.join(save_path,f"score_gap_var.csv"))
        
        # frequency_dict = {}
        # for size in score_gap_var:
            
        #     frequency_dict[size] = frequency_dict.get(size, 0) + 1
        
        # family_sizes = list(frequency_dict.keys())
        # frequency = list(frequency_dict.values())
        # plt.bar(family_sizes, frequency,width=0.5)
        plt.xlim(0,52)
        plt.xticks(range(0, 52, 5))
        plt.scatter(tenant_ids,score_gap_var)
        # 添加标题和轴标签
        #plt.title(f'{show_score_key}distribution'.replace("_"," "))
        plt.xlabel("tenant 编号")
        plt.ylabel(show_score_key)

        # 显示图形
        # plt.show()
        plt.savefig(os.path.join(save_path,f"{show_score_key}.png"))
        plt.clf()
        
    
    
        
def visualize_distribution_plot(tenant_data:dict,
                             save_path,
                             show_key,
                             type_data ="tenant",
                             n_groups= None):
    
    # 假设family_data是一个包含家庭人数的列表
    if type_data == "tenant":
        family_data = [value.get(show_key,0) for value in tenant_data.values()]
    else:
        houses = {}
        for c_id,houses_dict in tenant_data.items():
            houses.update(houses_dict)
        family_data = [value.get(show_key,0) for value in houses.values()]
        
        if show_key =='rent_money':
            family_data = [int(value/100)*100 for value in family_data]
        if show_key =='house_area':
            family_data = [int(float(value)/10)*10 for value in family_data]    
        

    frequency_dict = {}
    for size in family_data:
        
        frequency_dict[size] = frequency_dict.get(size, 0) + 1

    family_sizes = sorted(list(frequency_dict.keys()))
    frequency = [frequency_dict[size] for size in family_sizes]

    # plt.plot(family_sizes, frequency, marker='o',label =show_key)

    if show_key == "rent_money":
        plt.xlim(900,2601)
        plt.xticks(range(900, 2601, 100), rotation=45)
        width=50
    elif show_key =='house_area':
        plt.xlim(30,70)
        plt.xticks(range(30, 70, 10), rotation=45)
        width=5
    elif show_key =='rent_money':
        plt.xticks(range(900, 2501, 100))
        plt.xlim(900,2601)
        width=50
    else:
        width=0.8
    
    plt.bar(family_sizes,frequency,label = show_key,width=width)

    # 设置x轴的刻度
    plt.legend()
    
    # 添加标题和轴标签
    #plt.title(f'{show_key}_distribution'.replace("_"," "))
    plt.xlabel(show_key)
    plt.ylabel('frequency')

    # 显示图形
    # plt.show()
    plt.savefig(os.path.join(save_path,f"{show_key}.png"))
    plt.clf()


def visualize_distribution_bar(tenant_data:dict,
                             save_path,
                             show_key,
                             type_data ="tenant",
                             n_groups= None):
    
   
   # 假设family_data是一个包含家庭人数的列表
    if type_data == "tenant":
        family_data = [value.get(show_key,0) for value in tenant_data.values()]
    else:
        houses = {}
        for c_id,houses_dict in tenant_data.items():
            houses.update(houses_dict)
        family_data = [value.get(show_key,0) for value in houses.values()]
    frequency_dict = {}
    for size in family_data:
        
        frequency_dict[size] = frequency_dict.get(size, 0) + 1

    # family_sizes =[
    #     "family_members_num>3",
    #     "3>=family_members_num>=2",
    #     "family_members_num=1"
    # ]
        
    family_sizes = list(frequency_dict.keys())
    frequency = list(frequency_dict.values())
    # frequency =[]
    # for family_size in family_sizes:
    #     frequency.append(frequency_dict[family_size])

    # 绘制柱状图
    plt.bar(family_sizes, frequency,width=0.6)
    
    # 添加标题和轴标签
    #plt.title(f'{show_key}_distribution'.replace("_"," "))
    plt.xlabel(show_key)
    plt.ylabel('frequency')

    # 显示图形
    # plt.show()
    plt.savefig(os.path.join(save_path,f"{show_key}.png"))
    plt.clf()
    
    
def visualize_house(data_house):
    save_path = os.path.join(data_path,"visualize")
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    with open(os.path.join(data_path,"house_46.json"),'r',encoding = 'utf-8') as f:
        house_json = json.load(f)
    
    show_keys_bar =["house_type",
                ]
    for show_key in show_keys_bar:
        
        visualize_distribution_bar(house_json,
                             save_path,
                             show_key,
                             "house")
    show_keys_plot =[
                    "rent_money",
                     "house_area",
                     "house_type"
                     ]
    for show_key in show_keys_plot:
        visualize_distribution_plot(house_json,
                             save_path,
                            
                             show_key,
                             "house")
    
    
def visualize_rating_for_house(tenant_path,
                               global_rating_path,
                               house_path
                               ):
    tenant_info = readinfo(tenant_path)
    global_rating = readinfo(global_rating_path)
    house_info = readinfo(house_path)
    
    house_ids = [list(v.keys()) for v in house_info.values()]
    
    house_ids = np.concatenate(house_ids).tolist()
    
    score_types = ["score",
                   "llm_score",
                   "objective_score",
                   "rent_money_score",
                   "avg_living_score",
                   "orientation_score",
                   "floor_score",
                   "average_living_area_score"]
    save_root = os.path.dirname(global_rating_path)
    save_root = os.path.join(save_root,"visualize_priority_rating")
    df_ratings = pd.DataFrame()
    for score_type in score_types:
        scores ={
            "priority":[],
            "non_priority":[]
        }
        score_save_root = os.path.join(save_root,score_type)
        for tenant_id in tenant_info.keys():
            ratings = global_rating[tenant_id]
            for house_id in house_ids:
                house_rating = ratings["ratings"][house_id]
                if not all(not value for value in tenant_info[tenant_id]["priority_item"].values()):
                    scores["priority"].append(float(house_rating.get(score_type)))
                else:
                    scores["non_priority"].append(float(house_rating.get(score_type)))
            
        for type_tenant,score_tenants in scores.items():
            save_path = os.path.join(score_save_root,f"{score_type}_{type_tenant}.jpg")
            df_ratings.loc[score_type,type_tenant] = np.mean(score_tenants)
            if score_type =="score":
                create_histogram(list(score_tenants),1,save_path,10,20,f"{score_type} score")
            else:
                create_histogram(list(score_tenants),1,save_path,0,10,f"{score_type} score")
        df_ratings.loc[score_type,"gap"] = df_ratings.loc[score_type,"priority"] -\
            df_ratings.loc[score_type,"non_priority"]
    save_df_path = os.path.join(save_root,"score_mean_gap.csv")
    df_ratings.to_csv(save_df_path)
                
def visualize_rating_weights(tenant_path,
                               global_rating_path,
                               
                               ):
    tenant_info = readinfo(tenant_path)
    global_rating = readinfo(global_rating_path)
    
    score_types = ["rent_money",
            "average_living_area",
            "orientation",
            "floor"]
    
    save_root = os.path.dirname(global_rating_path)
    save_root = os.path.join(save_root,"visualize_priority_rating_weights")
    
    for score_type in score_types:
        scores ={
            "priority":[],
            "non_priority":[]
        }
        score_save_root = os.path.join(save_root,score_type)
        for tenant_id in tenant_info.keys():
            ratings = global_rating[tenant_id]
            rating_weights = ratings["weights"]
            sum_ratings = sum(rating_weights.values())
            
            if not all(not value for value in tenant_info[tenant_id]["priority_item"].values()):
                scores["priority"].append(float(rating_weights.get(score_type)/sum_ratings*10))
            else:
                scores["non_priority"].append(float(rating_weights.get(score_type)/sum_ratings*10))
            
        for type_tenant,score_tenants in scores.items():
            save_path = os.path.join(score_save_root,f"{score_type}_{type_tenant}.jpg")
            
            create_histogram(list(score_tenants),1,save_path,0,10,f"{score_type} weights")
    
def visualize_tenant_attrs_priority(tenant_path,
                                    ):
    tenant_info = readinfo(tenant_path)
    
    
    score_types = ["family_members_num",
                  "monthly_income",
                  "monthly_rent_budget"]
    
    save_root = os.path.dirname(tenant_path)
    save_root = os.path.join(save_root,"visualize_priority_attrs")
    
    for score_type in score_types:
        scores ={
            "priority":[],
            "non_priority":[]
        }
        score_save_root = os.path.join(save_root,score_type)
        for tenant_id in tenant_info.keys():
            tenant_attr = tenant_info[tenant_id][score_type]
           
            if not all(not value for value in tenant_info[tenant_id]["priority_item"].values()):
                scores["priority"].append(tenant_attr)
            else:
                scores["non_priority"].append(tenant_attr)
                
        for type_tenant,score_tenants in scores.items():
            save_path = os.path.join(score_save_root,f"{score_type}_{type_tenant}.jpg")
            
            if "monthly_rent_budget" == score_type:
                create_histogram(list(score_tenants),200,save_path,1000,4000,f"{score_type}_{type_tenant}")
            elif "monthly_income" == score_type:
                create_histogram(list(score_tenants),500,save_path,5000,15000,f"{score_type}_{type_tenant}")
            else:
                create_histogram(list(score_tenants),1,save_path,1,5,f"{score_type}_{type_tenant}")
    
    
    
def create_histogram(list_values, 
                     bar_size, 
                     save_path,
                     min_v,
                     max_v,
                     label_name):
    # 计算最大和最小值，以确定直方图的范围
    min_value = min(list_values)
    max_value = max(list_values)
    if max_v is None:
        max_v = int(max_value)
    if min_v is None:
        min_v = int(min_value)
    # 计算需要多少个箱子来覆盖整个范围
    num_bins = int((max_value - min_value) // bar_size + 1)

    # 创建直方图
    frequency_dict = {}
    for size in list_values:
        frequency_dict[size] = frequency_dict.get(size, 0) + 1
        
    family_sizes = list(frequency_dict.keys())
    frequency = list(frequency_dict.values())
    
    frequency = np.array(frequency)/sum(frequency)
    
    # 绘制柱状图
    plt.bar(family_sizes, frequency,width = bar_size-0.1)
    
    # plt.hist(list_values, bins=num_bins, range=(min_value, max_value + bar_size), edgecolor='black')

    # 设置图表的标题和坐标轴标签
    #plt.title(f'{label_name}'.replace("_"," "))
    plt.xlabel(f'{label_name}'.replace("_"," "),fontsize=20)
    plt.ylabel('Frequency',fontsize=20)
    plt.tight_layout()
    # 调整x轴的刻度以匹配箱子的大小
    plt.xticks(range(min_v, max_v + bar_size, bar_size),rotation=45,fontsize=10)
    
    dir_name  = os.path.dirname(save_path)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    # plt.show()
    plt.savefig(save_path)
    plt.clf()
    

def visualize_experiment_result(save_path = "EconAgent/experiments/PHA_51tenant_5community_28house_new_priority_label/hongkong_case"):
    # change k
    save_path = os.path.join(save_path,"change_k")
    k = [1,2,3,4,5]
    wt = [1.833333333,3.470588235,1.928571429,1.904761905,1.952380952]
    iwt = [1.476190476,2.490196078,1.404761905,1.5,1.523809524]
    sw = [433.5,425.7,413.1,416.2,419.6,]

    # change max_choose
    # save_path = os.path.join(save_path,"change_max_choose")
    # max_choose = [1,2,3,4,5]
    # wt = [2.470588235,1.785714286,1.928571429,1.904761905,1.952380952]
    # iwt = [1.490196078,1.523809524,1.595238095,1.476190476,1.52380952380952]
    # sw =[433.1,421.3,409,415,419.6]
    
    if not os.path.exists(save_path):
        os.makedirs(save_path)
        
    plt_configs ={
        "Waiting Time":wt,
        "Idle Waiting Time":iwt,
        "Social Welfare":sw
    }
    
    for config_name, config_data in plt_configs.items():    
        plt.figure(figsize=(10, 6))
        plt.xticks(k)
        plt.plot(k, config_data, marker='*')
        fig_base_name = config_name.replace(" ","_")
        fig_path = os.path.join(save_path,f"{fig_base_name}.png")
        # Adding labels and title
        #plt.xlabel('Max choose for tenant')
        plt.xlabel('Number of Deferrals for tenant')
        plt.ylabel(config_name)
        #plt.title(config_name.replace("_"," "))
        plt.savefig(fig_path)
    
    
    
if __name__ =="__main__":
    
    ex_setting = "PHA_51tenant_5community_28house_new_priority_perpersonlabel"
    ex_setting = "PHA_51tenant_5community_28house_new_priority_label"
    task_path = f"EconAgent/tasks/{ex_setting}"
    data_path = os.path.join(task_path,"data")
    # visualize_tenant(data_path)
    
    # visualize_house(data_path)
    # global_rating_path = "EconAgent/tasks/test_task/global_evaluation"
    global_rating_path= f"EconAgent/tasks/{ex_setting}/global_evaluation"
    #global_rating_path="EconAgent/tasks/PHA_51tenant_5community_28house_ver2_nofilter_multilist_priority_7t_5h/global_evaluation"
    show_score_keys =[
                        # "score",
                      "llm_score",
                      "objective_score",
                    #   "rent_money_score",
                    #     "avg_living_score",
                    #     "orientation_score",
                    #     "floor_score",
                    #     "score_gap"
                      ]
    # if os.path.exists(os.path.join(global_rating_path,"visualize")):
    #     import shutil
    #     shutil.rmtree(os.path.join(global_rating_path,"visualize"))
    
    # for show_score_key in show_score_keys:
    #     visualize_tenant_rating(global_rating_path=global_rating_path,
    #                         tenant_ids=[],
    #                         show_score_key=show_score_key,
    #                         house_path = f"EconAgent/tasks/{ex_setting}/data/house_28.json",
    #                         tenant_path =f"EconAgent/tasks/{ex_setting}/data/tenant_51.json")
    
    
    # visualize_rating_for_house(tenant_path = "EconAgent/tasks/PHA_51tenant_5community_28house_new_priority_label/data/tenant_51.json",
    #                            global_rating_path= "EconAgent/tasks/PHA_51tenant_5community_28house_new_priority_label/global_evaluation/global_score_newver.json",
    #                            house_path="EconAgent/tasks/PHA_51tenant_5community_28house_new_priority_label/data/house_28.json")
    
    visualize_rating_weights(tenant_path = "EconAgent/tasks/PHA_51tenant_5community_28house_new_priority_perpersonlabel/data/tenant_51.json",
                               global_rating_path= "EconAgent/tasks/PHA_51tenant_5community_28house_new_priority_perpersonlabel/global_evaluation/global_score_newver.json")
    
    # visualize_tenant_attrs_priority(tenant_path = "EconAgent/tasks/PHA_51tenant_5community_28house_new_priority_perpersonlabel/data/tenant_51.json")
    
    # visualize_experiment_result()