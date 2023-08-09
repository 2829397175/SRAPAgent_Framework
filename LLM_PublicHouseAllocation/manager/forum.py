import json
import os

from .base import BaseManager
from . import manager_registry as ManagerRgistry



@ManagerRgistry.register("forum")
class ForumManager(BaseManager):
    """
        manage forum.
    """
    

    @classmethod
    def load_data(cls,
                  data_dir,
                  **kwargs):
        
        assert os.path.exists(data_dir),"no such file path: {}".format(data_dir)
        with open(data_dir,'r',encoding = 'utf-8') as f:
            forum_datas = json.load(f)     

        
        return cls(
            data = forum_datas,
            data_type= "forum_data",
            save_dir=kwargs["save_dir"]
            )
        
    def add_comment(self,tenant_name,community_name,comment):
        if community_name not in self.data:
            self.data[community_name]={}
        for user_id ,user_comment  in self.data[community_name].items():
            if tenant_name==user_id:
                user_comment.append(comment)
        self.data[community_name][tenant_name]=[comment]

    def save_data(self):
        # assert os.path.exists(self.save_dir), "no such file path: {}".format(self.save_dir)
        with open(self.save_dir, encoding='utf-8',mode='w') as file:
            json.dump(self.data, file,indent=4,separators=(',', ':'),ensure_ascii=False)

    # def readforumrule_topk(self,community_name,k):
    #     commentlen=len(list(self.data[community_name]))
    #     if k > commentlen:
    #         comments=[" ".join(line) for line in list(self.data[community_name].values())[:]]
    #         return  "\n".join(comments)
    #     else:
    #         comments = [" ".join(line) for line in list(self.data[community_name].values())[:k]]
    #         return  "\n".join(comments)




# data_dir="F:/LLM_publichousing/me/LLM_PublicHouseAllocation/tasks/PHA_50tenant_3community_19house/data/forum.json"
# f=ForumManager.load_data(data_dir)
# print(f.readforumrule_topk("longxing Garden",2))