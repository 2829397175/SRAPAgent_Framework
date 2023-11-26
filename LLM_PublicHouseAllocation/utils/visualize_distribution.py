

import matplotlib.pyplot as plt
import os
import numpy as np
import pandas as pd

import json

# plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体来显示中文
plt.rcParams['axes.unicode_minus'] = False    # 用来正常显示负号

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
                            house_path:str="LLM_PublicHouseAllocation/tasks\PHA_51tenant_5community_28house\data\house_28.json",
                            tenant_path:str ="LLM_PublicHouseAllocation/tasks\PHA_51tenant_5community_28house\datatenant_51.json"):
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
                rating_data.append(np.abs(int(score_json[tenant_id][house_id]["llm_score"])
                                        - int(score_json[tenant_id][house_id]["objective_score"])))
            
            else:
                rating_data.append(int(score_json[tenant_id][house_id][show_score_key]))
              
        if show_score_key =="score_gap":
            # print("var of score gap",np.var(rating_data))
            score_gap_var.append(np.var(rating_data))
            continue
            
        
            
        frequency_dict = {}
        for size in rating_data:
            
            frequency_dict[size] = frequency_dict.get(size, 0) + 1
        
        family_sizes = list(frequency_dict.keys())
        frequency = list(frequency_dict.values())

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
        plt.title(f'{show_key}_distribution')
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
        plt.title(f'{show_score_key}distribution')
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
    plt.title(f'{show_key}_distribution')
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
    plt.title(f'{show_key}_distribution')
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
    
    
if __name__ =="__main__":
    task_path ="LLM_PublicHouseAllocation/tasks/test_task"
    task_path = "LLM_PublicHouseAllocation/tasks/PHA_51tenant_5community_28house_newver_housedata"
    data_path = os.path.join(task_path,"data")
    # visualize_tenant(data_path)
    
    visualize_house(data_path)
    # global_rating_path = "LLM_PublicHouseAllocation/tasks/test_task\global_evaluation"
    global_rating_path="LLM_PublicHouseAllocation/tasks\PHA_51tenant_5community_28house\global_evaluation"
    #global_rating_path="LLM_PublicHouseAllocation/tasks\PHA_51tenant_5community_28house_ver2_nofilter_multilist_priority_7t_5h\global_evaluation"
    show_score_keys =[
                    #     "score",
                    #   "llm_score",
                    #   "objective_score",
                    #   "rent_money_score",
                    #     "avg_living_score",
                    #     "orientation_score",
                    #     "floor_score",
                        "score_gap"
                      ]
    # if os.path.exists(os.path.join(global_rating_path,"visualize")):
    #     import shutil
    #     shutil.rmtree(os.path.join(global_rating_path,"visualize"))
    
    # for show_score_key in show_score_keys:
    #     visualize_tenant_rating(global_rating_path=global_rating_path,
    #                         tenant_ids=[],
    #                         show_score_key=show_score_key,
    #                         house_path = "LLM_PublicHouseAllocation/tasks\PHA_51tenant_5community_28house\data\house_28.json",
    #                         tenant_path ="LLM_PublicHouseAllocation/tasks\PHA_51tenant_5community_28house\data/tenant_51.json")