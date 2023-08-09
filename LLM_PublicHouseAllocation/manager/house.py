from .base import BaseManager
import os
import json

import copy
from . import manager_registry as ManagerRgistry
@ManagerRgistry.register("house")
class HouseManager(BaseManager):
    community_to_house: dict = {}

    @classmethod
    def load_data(cls,
                  data_dir: str,
                  **kwargs):
        def merge_dicts(*dict_args):
            """
            Given any number of dicts, shallow copy and merge into a new dict,
            precedence goes to key value pairs in latter dicts.
            """
            result = {}
            for dictionary in dict_args:
                result.update(dictionary)
            return result

        assert os.path.exists(data_dir), "no such file path: {}".format(data_dir)
        with open(data_dir, 'r', encoding='utf-8') as f:
            house_datas = json.load(f)

        community_to_house = {}
        house_info_table = {}
        for community_name, community_house in house_datas.items():
            community_to_house_temp = {community_name: list(community_house.keys())}
            community_to_house.update(community_to_house_temp)
            for house_id, house_attr in community_house.items():
                house_attr["available"] = True  # 是否选择了
                house_info_table[house_id] = house_attr

        return cls(
            data=house_info_table,
            community_to_house=community_to_house,
            data_type="house_data",
            save_dir=kwargs["save_dir"],
        )


    def set_chosed_house(self,house_id):
            try:
                self.data[house_id]['available']=False
            except Exception as e:
                print("Fail to change house state in HouseManager!!")
            #print(house_id)
            return self.data[house_id]["description"],self.data[house_id]["potential_information_house"]

    # def filter_house_ids(self,house_ids):
    #     return list(filter(lambda house_id:house_id in self.data.keys(), house_ids))
    
    def jug_house_valid(self,house_name):
        if house_name in self.data and self.data[house_name]["available"]==True:
            return True
        else:
            return False

    def get_available_houses(self,community_name=None,house_type=None):
        house_table = {}
        if (community_name) is not None:
            house_ids = self.community_to_house[community_name]

            for house_id in house_ids:
                house_table[house_id] = self.data["house_id"]
        else:
            house_table = self.data

        house_available = {}

        house_dict = copy.deepcopy(house_table)
        if house_dict == None:
            return {}
        for house_id, house_info in house_dict.items():
            if house_info['available'] == True and house_info["house_type"] == house_type:
                del house_info["potential_information_house"]
                del house_info["available"]
                house_available.update({house_id: house_info})
        return house_available
    
    def available_house_num(self,community_name,housetype):
        houses=self.get_available_houses(community_name,housetype)
        return len(houses)


    def save_data(self):
        # assert os.path.exists(self.save_dir), "no such file path: {}".format(self.save_dir)
        with open(self.save_dir, 'w') as file:
            json.dump(self.data, file,indent=4,separators=(',', ':'),ensure_ascii=False)


