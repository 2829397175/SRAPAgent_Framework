from . import group_registry
from .base import BaseGroupPolicy

@group_registry.register("portion")
class PortionPolicy(BaseGroupPolicy):
    
    portion_settings = [0.2,0.3,0.3,0.2]
    portion_attribute = "family_members_num"
    portioned_cache = {} # 保存第一次分组的结果，后续调用可以直接取cache
    
    def __init__(self,**kargs) -> None:
        portion_settings = kargs.pop("portion_settings")
        if sum(portion_settings)!=1:
            import numpy as np
            portion_settings =  np.array(portion_settings)
            portion_settings = (portion_settings/portion_settings.sum()).tolist()
            assert sum(portion_settings) == 1,"error in portion setting"
            
        return super().__init__(type = "portion",
                                portion_settings = portion_settings,
                                **kargs)
    
    async def group(self,
                tenant,
                tenant_manager,
                forum_manager, 
                system, 
                tool, 
                rule,
                log_round_tenant,
                tenant_ids):
        
        if tenant.id in self.portioned_cache.keys():
            return self.portioned_cache[tenant.id]
        
        portion_settings = self.portion_settings
        
        
        index_tenant_basic_infos = {tenant_id:tenant_manager[tenant_id].infos for tenant_id in tenant_ids}
        
        list_sorted_index_tenant_basic_infos = sorted(index_tenant_basic_infos.items(),
                                                      key =lambda x: float(x[1].get(self.portion_attribute,0)))
        portioned_cache = {}
        ptr_l = 0
        ptr_l_portion = 0
        ptr_r_portion = 0
        n = len(list_sorted_index_tenant_basic_infos)
        for idx_group,portion in enumerate(portion_settings):
            
            ptr_r = int(ptr_l + portion*n)
            ptr_r_portion = ptr_l_portion + portion
            if idx_group == len(portion_settings) -1:
                portion_indexs = [ x[0] for x in list_sorted_index_tenant_basic_infos[ptr_l:]]
            else:
                portion_indexs = [ x[0] for x in list_sorted_index_tenant_basic_infos[ptr_l:ptr_r]]
                
                
            for t_index in portion_indexs:
                portioned_cache[t_index] = f"{ptr_l_portion:.1f}<{self.portion_attribute}<{ptr_r_portion:.1f}"
            
            ptr_l_portion = ptr_r_portion
            ptr_l = ptr_r
                
        
                
        self.portioned_cache.update(portioned_cache)
        
        if tenant.id not in self.portioned_cache.keys():
            raise Exception()
        return self.portioned_cache[tenant.id]
    