from LLM_PublicHouseAllocation.executor import Executor

import argparse
import os
import shutil

parser = argparse.ArgumentParser(description='housing_system')  # 创建解析器
parser.add_argument('--task', 
                    type=str, 
                    default="PHA_5tenant_3community_19house", 
                    help='The task of simulation system.')  # 添加参数

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
                    default="LLM_PublicHouseAllocation\llms\\api.json",
                    help="The default path of apis json.")

args = parser.parse_args()  # 解析参数

if args.clear_cache:
    
    result_dir = os.path.join("LLM_PublicHouseAllocation\\tasks",
                              args.task,
                              "result")
    if os.path.exists(result_dir):
        shutil.rmtree(result_dir)
    
executor = Executor.from_task(args.task,args.api_path)
executor.load_log(args.log)

#executor.run()