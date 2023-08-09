
from pydantic import BaseModel
from abc import abstractmethod
from . import readhouse_registry as ReadHouseRgistry
from typing import List

@ReadHouseRgistry.register("base")
class Base_ReadHouse(BaseModel):
    @abstractmethod
    def read_house_list(self,
                        house_data:dict,
                        house_ids:List[str]):
        pass
    
    # @abstractmethod
    # def get_houses_generator(self,**kwargs):
    #     return self.get_houses_generator(**kwargs)