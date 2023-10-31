import os
#os.environ["OPENAI_API_KEY"]= "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"
# JtC492050034@hiziyw.com/hdE31231231291T/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/$5.00
#PQECAt367006191@hiziyw.com/hdE31231231291T/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/$5.00
#os.environ["OPENAI_API_KEY"]= "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"
os.environ["OPENAI_API_KEY"]= "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"

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
executor.load_log(args.log)

# executor.run()