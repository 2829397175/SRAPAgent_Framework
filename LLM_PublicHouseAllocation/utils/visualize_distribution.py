

import matplotlib.pyplot as plt
import os
import json

plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体来显示中文
plt.rcParams['axes.unicode_minus'] = False    # 用来正常显示负号

def visualize_tenant(data_path):
    save_path = os.path.join(data_path,"visualize")
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    with open(os.path.join(data_path,"tenant.json"),'r',encoding = 'utf-8') as f:
        tenant_json = json.load(f)
        
    show_keys_bar =["family_members_num",
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
        
def visualize_tenant_rating(global_rating_path,tenant_ids:list=[]):
    save_path = os.path.join(global_rating_path,"visualize")
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    with open(os.path.join(global_rating_path,"global_score.json"),'r',encoding = 'utf-8') as f:
        score_json = json.load(f)
    
    if tenant_ids ==[]:
        tenant_ids = score_json.keys()
    
    for tenant_id in tenant_ids:
        show_key = f"tenant {tenant_id} rating"
        
        assert tenant_id in score_json.keys()
        
        rating_data = [int(value.get("score",0)) for value in score_json[tenant_id].values()]
        
        frequency_dict = {}
        for size in rating_data:
            
            frequency_dict[size] = frequency_dict.get(size, 0) + 1
        
        family_sizes = list(frequency_dict.keys())
        frequency = list(frequency_dict.values())

        # plt.xticks(range(min(family_sizes),max(family_sizes)))
        # plt.xlim(900,2601)

        # 绘制柱状图
        plt.bar(family_sizes, frequency,width=0.5)
        
        # 添加标题和轴标签
        plt.title(f'{show_key}分布')
        plt.xlabel(show_key)
        plt.ylabel('频率')

        # 显示图形
        # plt.show()
        plt.savefig(os.path.join(save_path,f"{show_key}.png"))
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
    else:
        plt.xticks(range(900, 2501, 100))
        plt.xlim(900,2601)
        width=50
    plt.bar(family_sizes,frequency,label = show_key,width=width)

    # 设置x轴的刻度
    plt.legend()
    
    # 添加标题和轴标签
    plt.title(f'{show_key}分布')
    plt.xlabel(show_key)
    plt.ylabel('频率')

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

    
        
    family_sizes = list(frequency_dict.keys())
    frequency = list(frequency_dict.values())

    # 绘制柱状图
    plt.bar(family_sizes, frequency)
    
    # 添加标题和轴标签
    plt.title(f'{show_key}分布')
    plt.xlabel(show_key)
    plt.ylabel('频率')

    # 显示图形
    # plt.show()
    plt.savefig(os.path.join(save_path,f"{show_key}.png"))
    plt.clf()
    
    
def visualize_house(data_house):
    save_path = os.path.join(data_path,"visualize")
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    with open(os.path.join(data_path,"house.json"),'r',encoding = 'utf-8') as f:
        house_json = json.load(f)
    
    # show_keys_bar =["house_type",
    #             ]
    # for show_key in show_keys_bar:
        
    #     visualize_distribution_bar(house_json,
    #                          save_path,
    #                          show_key,
    #                          "house")
    show_keys_plot =[
                    "rent_money",
                     "house_area",
                     
                     ]
    for show_key in show_keys_plot:
        visualize_distribution_plot(house_json,
                             save_path,
                            
                             show_key,
                             "house")
    
    
if __name__ =="__main__":
    task_path ="LLM_PublicHouseAllocation\\tasks\\test_task"
    data_path = os.path.join(task_path,"data")
    visualize_tenant(data_path)
    
    visualize_house(data_path)
    # global_rating_path = "LLM_PublicHouseAllocation\\tasks\\test_task\global_evaluation"
    global_rating_path="LLM_PublicHouseAllocation\\tasks\PHA_51tenant_5community_28house_ver2_nofilter_multilist_priority_7t_5h\global_evaluation"
    #visualize_tenant_rating(global_rating_path=global_rating_path,tenant_ids=[])