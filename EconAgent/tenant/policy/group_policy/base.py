from . import group_registry
from pydantic import BaseModel
from abc import abstractmethod



@group_registry.register("base")
class BaseGroupPolicy(BaseModel):
    
    type = "base"
    
    sorting_type:str = "base" # ["base", "priority", "housing_points"]
    
    log_fixed = {} # fixed_log for tenants : tenant_id[house_type_id,house_choose_reason]
    async def group(self,
                tenant,
                tenant_manager,
                forum_manager, 
                system, 
                tool, 
                rule,
                log_round_tenant,
                tenant_ids): # tenant_ids 为最新添加的一批tenant
        # return group_id
        return "default" # 所有tenant分在同一组
    
    
    def sort_tenant_groups(self,
             tenant_groups,
             tenant_manager):
        if self.sorting_type == "priority":
            for key in tenant_groups.keys():
                p_tenants = []
                normal_tenants = []
                for tenant_id in tenant_groups[key]:
                    tenant = tenant_manager[tenant_id]
                    if all(not value for value in tenant.priority_item.values()):
                        normal_tenants.append(tenant_id)
                    else:
                        p_tenants.append(tenant_id)
                        
                tenant_groups[key] = [*p_tenants,*normal_tenants]
        elif self.sorting_type == "housing_points":
            # 暂定
            
            for key in tenant_groups.keys():
                tenant_ids = tenant_groups[key]
                assert isinstance(tenant_ids,list)
                tenant_ids.sort(key = lambda x: float(tenant_manager[x].infos["monthly_rent_budget"])/int(tenant_manager[x].infos["family_members_num"]))    
                
                tenant_groups[key] = tenant_ids
            
        return tenant_groups