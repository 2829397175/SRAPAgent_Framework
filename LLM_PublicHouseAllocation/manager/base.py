

from pydantic import BaseModel,PrivateAttr

from typing import Any, List, Optional, Sequence, Tuple, Union
from abc import abstractmethod
from . import manager_registry as ManagerRgistry

@ManagerRgistry.register("base")
class BaseManager(BaseModel):
    data_type:str
    data:dict
    save_dir:str=""
    _step: int = PrivateAttr(0)
    _max_step: int = PrivateAttr(0)
    
    def __init__(self,**kwargs): # kwargs: data_type,data
        super().__init__(**kwargs)          
        self._step = 0
        data = kwargs.get('data', False)
        if data !=False:
            self._max_step = len(data)
        else:
            raise AttributeError(name="data")
       

    
    def __getitem__(self,index):
        return self.data[index]
    
    def __len__(self):
        return len(self.data)
    
    def __iter__(self):
        return self
    
    def __next__(self):
        
        if self._step >= self._max_step:
            self._step = 0
            raise StopIteration()
        else:
            return_val = list(self.data.items())[self._step]
            self._step +=1
            return return_val
        
    def append(self,info):
        
        self.data={**self.data,**info}
        
        
    def remove(self,key):
        return self.data.pop(key)
             
             
    def set_value(self,key,**kwargs):
        tuple_idx=self.data[key]
        for k, v in kwargs.items():
            tuple_idx[k]=v       
            
            
    # load different types of info from file
    @abstractmethod
    def load_data(**kwargs):
        pass

    @abstractmethod
    def save_data(**kwargs):
        pass