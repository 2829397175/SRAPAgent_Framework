import asyncio
import logging
from typing import List

from .environments import RentEnvironment
from .involvers import System,Tool,LogRound
from .initialization import (load_environment,
                             load_manager,
                             prepare_task_config)

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
        task_config = prepare_task_config(task)

        manager_configs = task_config.pop('managers')
        tenant_manager = load_manager(manager_configs.pop('tenant'),'tenant')
        #print(tenant_manager)
        house_manager = load_manager(manager_configs.pop('house'),'house')
        community_manager = load_manager(manager_configs.pop('community'),'community')
        forum_manager = load_manager(manager_configs.pop('forum'),'forum')
        system = System(house_manager=house_manager,
                community_manager=community_manager)
        env_config = task_config.pop('environment')
        env_config['system'] = system
        env_config['tenant_manager']=tenant_manager
        env_config["forum_manager"]=forum_manager
        env_config["log"]=LogRound()
        if env_config.get('tool',False):
            tool = Tool(forum_manager)
            env_config['tool'] = tool
        else:
            env_config['tool'] = None

        environment = load_environment(env_config)

        return cls(environment)

    def run(self):
        """Run the environment from scratch until it is done."""
        # self.environment.reset() # 待改memory模块
        
        # while not self.environment.is_done():
        #     # asyncio.run(self.environment.step())
        #     loop = asyncio.get_event_loop()
        #     loop.run_until_complete(self.environment.step())
        self.environment.log.reset()
        self.environment.group()
        self.environment.line_up()
        self.environment.broadcast()
        
        while self.environment.is_done():
            self.environment.communication(communication_num=3) #测试用
            #if self.environment.cnt_turn>3:
            # self.environment.step()

    def reset(self):
        self.environment.reset()
        
    # def next(self):
    #     """Run the environment for one step and return the return message."""
    #     return_message = asyncio.run(self.environment.step())
    #     return return_message