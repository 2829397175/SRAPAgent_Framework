from pydantic import BaseModel
from . import readhouse_registry as ReadHouseRgistry
from .base import Base_ReadHouse
from typing import List

@ReadHouseRgistry.register("page_generator")
class PageGenerator_ReadHouse(Base_ReadHouse):

    
    def filter_house_ids(self,house_data:dict,house_ids:List[str]):
        return list(filter(lambda house_id:house_id in house_data.keys() \
            and house_data[house_id].get("available",False), house_ids))
    
        
    def read_house_list(self, 
                        house_infos: dict,
                        house_ids:List[str],
                        log_round_houses: list = [],
                        round_retry:int = 0):
        
        # house_infos = {}
        # for house_id in house_ids:
        #     house_infos.update({house_id:
        #                         house_data[house_id]})

        len_house = len(house_infos)
        template = """{index}: 
this house costs about {rent_money}. \
It's square fortage is about {house_area}. The orientation of the house is {toward}. It is located at floor {floor}. It {elevator} elevator. \
{description}"""

        houses_str = [
            template.format_map(
                {"index": house_idx,
                    **house_info})
            for house_idx, house_info in house_infos.items()
        ]
        if (round_retry == 0): # 仅存第一轮的house description
            log_round_houses.extend(houses_str)
        houses_str = "\n\n".join(houses_str)
        houses_describe_prompt = "There are {num_houses} houses available. The infomation of these houses are listed as follows:\n{houses} "
        str_house_description = houses_describe_prompt.format(num_houses=len_house,
                                                                houses=houses_str)
        return str_house_description,list(house_infos.keys())
        
        
    def get_houses_generator(self,
                             house_data:dict, 
                             house_ids:List[str], 
                             page_size:int = 20, 
                             log_round_houses:list=[],
                             round_retry:int = 0):
        # 由于community中存储的house index 可能已经被选择过了，所以要进行house index 的filter
        # house_ids = self.filter_house_ids(house_data=house_data,
        #                                   house_ids=house_ids)
        
        len_houses = len(house_ids)
        group_size = int(len_houses / page_size)

        house_ids_grouped = []
        for group_id in range(0, group_size):
            house_ids_grouped.append(house_ids[group_id * page_size:(group_id + 1) * page_size])

        house_ids_grouped.append(house_ids[group_size * page_size:])

        for house_ids in house_ids_grouped:
            yield self.read_house_list(house_infos=house_data,
                                       house_ids=house_ids,
                                       log_round_houses=log_round_houses,
                                       round_retry=round_retry)
    
    
