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
import os

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
        
        if platform.system()=='Windows':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

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
            if "distribution_batch_dir" in config.keys():
                config["distribution_batch_dir"] = os.path.join(task_path,config["distribution_batch_dir"])
        
        save_log = task_config.pop("save_log",True)
        
        tenant_configs = manager_configs.pop('tenant')

        
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
                                       },'community')
        forum_manager = load_manager({**manager_configs.pop('forum'),
                                      "save_dir": os.path.join(save_dir,"forum.json")
                                       },'forum')
        
        system = System(house_manager = house_manager,
                community_manager = community_manager)
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
       
        global_score = Global_Score.initialization(tenant_manager,system,save_dir=save_evaluation_dir,llm_pool=llm_loader)
        # global_score.rate()
        # global_score.save()
        
        env_config['global_score'] = global_score
        
        environment = load_environment({**env_config,
                                        "save_log":save_log})
        
        
        return cls(environment)
    
    
    def load_log(self,result_dir):
        self.environment.load_log(result_dir)

    def run(self):
        """Run the environment from scratch until it is done."""
        # self.environment.reset() # 待改memory模块
                    
        self.environment.log.reset()
        
        # self.environment.group() # tenant->group(tenants)
        # self.environment.line_up()
    
    
        
        while not self.environment.is_done():
            tenant_waitlists = self.environment.rule.get_next_agent_idx(self.environment)
            
            """采样waitlist中的tenant交流"""
            # tenant_ids = []
            # for queue_name, tenant_waitlist in tenant_waitlists.items():
            #     tenant_ids.extend(tenant_waitlist) ## 所有waitlist内的tenant进行交流
            
            """采样所有系统中的tenant交流"""
            tenant_ids = list(self.environment.tenant_manager.data.keys())
                        
            self.environment.communication(tenant_ids,
                                           communication_num = 10)
           
            self.environment.step(tenant_waitlists)
            
            

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
       