from LLM_PublicHouseAllocation.executor import Executor

import argparse

parser = argparse.ArgumentParser(description='housing_system')  # 创建解析器
parser.add_argument('--task', 
                    type=str, 
                    default="PHA_5tenant_3community_19house", 
                    help='The task of simulation system.')  # 添加参数

parser.add_argument("--log",
                    type=str,
                    default="",
                    help="The default path of log.")

args = parser.parse_args()  # 解析参数



executor = Executor.from_task(args.task)
# executor.load_log(args.log)

executor.run()