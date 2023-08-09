from pydantic import BaseModel
from . import readhouse_registry as ReadHouseRgistry
from .base import Base_ReadHouse

from typing import List

@ReadHouseRgistry.register("topk")
class Topk_ReadHouse(Base_ReadHouse):

    # def read_house_list(self,available_house_info,k=5):
    #     house_info_description="""
    #                             {house_id}: The house is a {house_type} with an area of {house_area} square meters and a monthly rent of {rent_money} yuan.
    #                              It {balcony} a balcony and {elevator} an elevator. It's on the {floor}th floor. Its description is that {description}
    #                          """
    #     housedes_list=[]
    #     for house_id,house_info  in available_house_info.items():
    #         h=house_info_description.format(house_id=house_id,
    #                                         house_type=house_info["house_type"],
    #                                         house_area=house_info["house_area"],
    #                                         rent_money=house_info["rent_money"],
    #                                         balcony=house_info["balcony"],
    #                                         elevator=house_info["elevator"],
    #                                         floor=house_info["floor"],
    #                                         description=house_info["description"],
    #                                         )
    #         housedes_list.append(h)
    #     if k > len(housedes_list):
    #         return "\n".join(housedes_list[:])
    #     else:
    #         return "\n".join(housedes_list[:k])
        
        
    def read_house_list(self,
                        house_data:dict,
                        house_ids:List[str],
                        k=5):
        
        available_house_info = {}
        available_house_info = dict(filter(lambda x: x[0] in house_ids, house_data.items()))
             
             
        house_info_description="""
                                {house_id}: The house is a {house_type} with an area of {house_area} square meters and a monthly rent of {rent_money} yuan.
                                 It {balcony} a balcony and {elevator} an elevator. It's on the {floor}th floor. Its description is that {description}
                             """
        housedes_list=[]
        for house_id,house_info  in available_house_info.items():
            h=house_info_description.format(house_id=house_id,
                                            house_type=house_info["house_type"],
                                            house_area=house_info["house_area"],
                                            rent_money=house_info["rent_money"],
                                            balcony=house_info["balcony"],
                                            elevator=house_info["elevator"],
                                            floor=house_info["floor"],
                                            description=house_info["description"],
                                            )
            housedes_list.append(h)
        if k > len(housedes_list):
            return "\n".join(housedes_list[:])
        else:
            return "\n".join(housedes_list[:k])