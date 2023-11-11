from . import group_registry
from .base import BaseGroupPolicy

@group_registry.register("portion")
class PortionPolicy(BaseGroupPolicy):
    
    portion_settings = [0.2,0.3,0.3,0.2]
    portion_attribute = "family_members_num"
    portioned_cache = {} # 保存第一次分组的结果，后续调用可以直接取cache
    
    def __init__(self,tenant_configs ,**kargs) -> None:
        portion_settings = kargs.pop(portion_settings)
        if sum(portion_settings)!=1:
            import numpy as np
            portion_settings =  np.array(portion_settings)
            portion_settings = (portion_settings/portion_settings.sum()).tolist()
        
        index_tenant_basic_infos = tenant_configs
        
        list_sorted_index_tenant_basic_infos = sorted(index_tenant_basic_infos.items(),
                                                      key =lambda x: int(x[1].get(self.portion_attribute,0)))
        portioned_cache={}
        ptr_l =0
        n = len(list_sorted_index_tenant_basic_infos)
        for idx_group,portion in enumerate(portion_settings):
            
            ptr_r = ptr_l + portion*n
            if ptr_r ==n:
                portion_indexs = [ x[0] for x in list_sorted_index_tenant_basic_infos[ptr_l:]]
            else:
                portion_indexs = [ x[0] for x in list_sorted_index_tenant_basic_infos[ptr_l:ptr_r]]
                
            ptr_l = ptr_r
                
            for t_index in portion_indexs:
                portioned_cache[t_index] = f"{ptr_l/n}<{self.portion_attribute}<{ptr_r/n}"
            
        super().__init__(portioned_cache = portioned_cache,
                         **kargs)
    
    async def group(self,
                tenant,
                tenant_manager,
                forum_manager, 
                system, 
                tool, 
                rule,
                log_round_tenant):
        
        if tenant.id not in self.portioned_cache.keys():
            raise Exception()
        return self.portioned_cache[tenant.id]
    