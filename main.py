from LLM_PublicHouseAllocation.executor import Executor

import argparse
import os
import shutil

parser = argparse.ArgumentParser(description='housing_system')  # 创建解析器
parser.add_argument('--task', 
                    type=str, 
                    default="ver2_nofilter_multilist_priority_7t_5h", 
                    help='The task of simulation system.')  # 添加参数

parser.add_argument('--data', 
                    type=str, 
                    default="PHA_51tenant_5community_28house", 
                    help='The data setting for the task')  # 添加参数

parser.add_argument("--log",
                    type=str,
                    default="",
                    help="The default path of log.")

parser.add_argument("--clear_cache",
                    action="store_true",
                    default= False,
                    help="The default path of log.")

parser.add_argument("--api_path",
                    type=str,
                    default="LLM_PublicHouseAllocation/llms/api.json",
                    help="The default path of apis json.")


parser.add_argument("--optimizer_type",
                    type=str,
                    default="genetic_algorithm",
                    help="the type of the optimzer")

parser.add_argument("--optimize",
                    action='store_true',
                    default=False,
                    help="start the parameter optimization")

parser.add_argument("--simulate",
                    action='store_true',
                    default=False,
                    help="start the simulation process")



args = parser.parse_args()  # 解析参数



if __name__ == "__main__":
    if args.clear_cache:
        
        result_dir = os.path.join("LLM_PublicHouseAllocation/tasks",
                                args.data,
                                "configs",
                                args.task,
                                "result")
        if os.path.exists(result_dir):
            shutil.rmtree(result_dir)
        
    if args.optimize:
        from LLM_PublicHouseAllocation.optimizer import policy_optimizer_registry
        optimizer = policy_optimizer_registry.load_data(args.optimizer_type,
                                                        data = args.data,
                                                        normalize = True)
        optimizer.fit()
        
    if args.simulate:
        executor = Executor.from_task(args)
        # executor.load_log(args.log)
        executor.run()