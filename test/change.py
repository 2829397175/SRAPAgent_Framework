import json
import pandas as pd
data_dir="tenant.json"
from translate import Translator
with open(data_dir,'r',encoding = 'utf-8') as f:
    tenants=json.load(f)



# 这是用于将"monthly_income"映射到（800,2500）范围的函数。
# 这个函数需要根据你的具体需求进行调整
def calculate_rent_budget(income):
    return max(800, min(income * 0.2, 2500))
translator = Translator(from_lang='zh', to_lang='en')
# 对每个人进行处理
for person, info in tenants.items():
    # 翻译工作地点
    translation = translator.translate(info["work_place"])
    info["en_work_place"] = translation

    # 计算租金预算
    info["monthly_rent_budget"] = calculate_rent_budget(info["monthly_income"])

# 打印结果
with open(data_dir, 'w',encoding='utf-8') as f:
    json.dump(tenants, f, indent=4,ensure_ascii=False)














# #print(pd.DataFrame(tenants)['monthly_rent_budget'].describe())
# for tenant in tenants:
#     if tenant['monthly_rent_budget']>=1496:
#         tenant['monthly_rent_budget']=random.randint(2300,2500)
#     elif tenant['monthly_rent_budget']>=1456:
#         tenant['monthly_rent_budget'] = random.randint(2100,2300)
#     elif tenant['monthly_rent_budget']>=1405:
#         tenant['monthly_rent_budget'] = random.randint(1900,2100)
#     elif tenant['monthly_rent_budget'] >= 1353:
#         tenant['monthly_rent_budget'] = random.randint(1700, 1900)
#     else:
#         tenant['monthly_rent_budget'] = random.randint(1300,1500)
# with open(data_dir, 'w') as file:
#     json.dump(tenants, file)
#print(pd.DataFrame(tenants)['monthly_rent_budget'].describe())
# for community_name, community_house in house_datas.items():
#     for house_id, house_attr in community_house.items():
#         house_attr["available"] = True  # 是否选择了
# def load_data(data_dir: str):
#
#
#     assert os.path.exists(data_dir), "no such file path: {}".format(data_dir)
#     with open(data_dir, 'r', encoding='utf-8') as f:
#         house_datas = json.load(f)
#
#     for community_name, community_house in house_datas.items():
#         for house_id, house_attr in community_house.items():
#             house_attr["available"] = True  # 是否选择了
#
#     return cls(
#         data=house_datas,
#         data_type="house_data",
#         save_dir=kwargs["save_dir"]
#     )
#
# def save_data(tenant):
#     assert os.path.exists(self.save_dir), "no such file path: {}".format(self.save_dir)
#     with open(self.save_dir, 'w') as file:
#         json.dump(self.data, file)
# house=add_house_id(house)
# def convert_to_list(data):
#     data = data.copy()  # 创建一个新的字典副本
#     for community in data:
#         data[community] = list(data[community].values())
#     return data
# house=convert_to_list(house)
#print(tenants)
