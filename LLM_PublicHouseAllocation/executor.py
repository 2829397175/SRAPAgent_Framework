import asyncio
import logging
from typing import List

from .environments import RentEnvironment
from .involvers import System,Tool,LogRound
from .initialization import (load_environment,
                             load_manager,
                             prepare_task_config)
from LLM_PublicHouseAllocation.global_score import Global_Score
from LLM_PublicHouseAllocation.llms import APIKeyPool
import platform

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', datefmt='%m/%d/%Y %H:%M:%S', level=logging.INFO)

openai_logger = logging.getLogger("openai")
openai_logger.setLevel(logging.WARNING)


# 删掉load agent，因为environment中不止agent参与，不限制参与类型


class Executor():
    def __init__(self,
                 environment:RentEnvironment):
        self.environment = environment

    @classmethod
    def from_task(cls, task: str):
        """Build an LLM_PublicHousingAllocation from a task name.
        The task name should correspond to a directory in `tasks` directory.
        Then this method will load the configuration from the yaml file in that directory.
        """
        # Prepare the config of the task
        task_config,task_path = prepare_task_config(task)
        
        
        import time
        import os
        save_dir = task_config.pop("save_root_dir","")
        time_stamp = time.time()
        save_dir = os.path.join(task_path,
                                f"{save_dir}/{time_stamp}")
        
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        manager_configs = task_config.pop('managers')
        for _, config in manager_configs.items():
            if "data_dir" in config.keys():
                config["data_dir"] = os.path.join(task_path,config["data_dir"])
        
        save_log = task_config.pop("save_log",True)
        
        tenant_configs = manager_configs.pop('tenant')
        tenant_llm_configs = tenant_configs["llm"]       
        communication_llm_configs = tenant_configs["memory"]["llm"]       
        
        llm_loader = APIKeyPool()
        
        tenant_manager = load_manager({**tenant_configs,
                                       "save_dir": os.path.join(save_dir,"tenant.json")
                                       },'tenant')
        
        #print(tenant_manager)
        house_manager = load_manager({**manager_configs.pop('house'),
                                     "save_dir": os.path.join(save_dir,"house.json")
                                       },'house')
        community_manager = load_manager({**manager_configs.pop('community'),
                                         "save_dir": os.path.join(save_dir,"community.json"),
                                         "distribution_batch_dir":os.path.join(task_path,"data/distribution_batch.json")
                                       },'community')
        forum_manager = load_manager({**manager_configs.pop('forum'),
                                      "save_dir": os.path.join(save_dir,"forum.json")
                                       },'forum')
        
        system = System(house_manager=house_manager,
                community_manager=community_manager)
        env_config = task_config.pop('environment')
        env_config['llm_loader'] = llm_loader
        env_config['system'] = system
        env_config['tenant_manager'] = tenant_manager
        env_config["forum_manager"] = forum_manager
        env_config["log"] = LogRound(save_dir = os.path.join(save_dir,"tenental_system.json"))
        if env_config.get('tool',False):
            tool = Tool(forum_manager)
            env_config['tool'] = tool
        else:
            env_config['tool'] = None
        
        save_evaluation_dic = os.path.join(task_path,
                                f"global_evaluation")
        if not os.path.exists(save_evaluation_dic):
            os.makedirs(save_evaluation_dic) 
        save_evaluation_dir = os.path.join(save_evaluation_dic,
                                f"global_score.json") 
        if not os.path.exists(save_evaluation_dir):
            global_score = Global_Score.initialization(tenant_manager,system,save_dir=save_evaluation_dir)
            global_score.rate_score()
            global_score.save_score()
        else:
            global_score = Global_Score.load_from_json(tenant_manager,system,json_path=save_evaluation_dir)
        
        env_config['global_score'] = global_score
        
        environment = load_environment({**env_config,
                                        "save_log":save_log})
        
        
        return cls(environment)

    def run(self):
        """Run the environment from scratch until it is done."""
        # self.environment.reset() # 待改memory模块
        
        if platform.system()=='Windows':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            
        self.environment.log.reset()
        
       
        self.environment.group() # tenant->group(tenants)
        self.environment.line_up()
        self.environment.broadcast()
        
        while not self.environment.is_done():
            
            self.environment.communication(communication_num = 3)
           
            #self.environment.step()
            
            

    def reset(self):
        self.environment.reset()
        
    # def next(self):
    #     """Run the environment for one step and return the return message."""
    #     return_message = asyncio.run(self.environment.step())
    #     return return_message
    
    # def test(self):
    #     for _,tenant in self.environment.tenant_manager.data.items():
    #         tenant2=self.environment.llm_loader.get_key(tenant)
    #         tenant2
       