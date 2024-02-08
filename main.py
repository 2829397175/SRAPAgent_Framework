from SARPAgent.executor import Executor

import argparse
import os
import shutil

parser = argparse.ArgumentParser(description='housing_system')  # 创建解析器
parser.add_argument('--config', 
                    type=str, 
                    default="ver1_nofilter_multilist(1.2)_multilist_nopriority_8t_6h_p#housetype", 
                    help='The config of policy for simulation system.')  # 添加参数

parser.add_argument('--task', 
                    type=str, 
                    default="public_housing", 
                    help='The task setting for the SARPAgent')  # 添加参数

parser.add_argument("--log",
                    type=str,
                    default=None,
                    help="The default path of log.")

parser.add_argument("--clear_cache",
                    action="store_true",
                    default= False,
                    help="The default path of log.")

parser.add_argument("--api_path",
                    type=str,
                    default="SARPAgent/llms/api.json",
                    help="The default path of apis json.")


parser.add_argument("--optimizer_type",
                    type=str,
                    default="genetic_algorithm",
                    help="the type of the optimzer")

parser.add_argument("--optimize",
                    action='store_true',
                    default=False,
                    help="start the parameter optimization")

parser.add_argument("--optimize_refine_first",
                    action='store_true',
                    default=False,
                    help="refine_the_regressor_ahead")


parser.add_argument("--optimize_threshold",
                    type=float,
                    default=0.05,
                    help="threshold of the optimization process")

parser.add_argument("--optimize_rounds",
                    type=int,
                    default=10,
                    help="max running rounds of the optimization process")

parser.add_argument("--optimize_regressor_max_samples",
                    type=int,
                    default=10,
                    help="max running samples of the regressor optimization process")

parser.add_argument("--optimize_regressor_threshold",
                    type=float,
                    default=0.5,
                    help="threshold of the optimization process")



parser.add_argument("--simulate",
                    action='store_true',
                    default=False,
                    help="start the simulation process")

parser.add_argument("--max_utility",
                    action='store_true',
                    default=False,
                    help="calculate the maximum utility for public house renting")


args = parser.parse_args()  # 解析参数



if __name__ == "__main__":
    
    args = {**vars(args)}
    
    if args["clear_cache"]:
        
        result_dir = os.path.join("SARPAgent/tasks",
                                args["task"],
                                "configs",
                                args["config"],
                                "result")
        if os.path.exists(result_dir):
            shutil.rmtree(result_dir)
        
    if args["optimize"]:
        from SARPAgent.optimizer import policy_optimizer_registry
        optimizer = policy_optimizer_registry.load_data(args["optimizer_type"],
                                                        data = args["task"],
                                                        normalize = False)
        # optimizer.fit()
        # optimizer.simulate_optimize_task("optimized_task_config_1",
        #                                  use_cache=True)
        

        optimizer.fit_experiment_evaluate(threshold = args["optimize_threshold"],
                                        max_round = args["optimize_rounds"],
                                        optimize_regressor_rounds = args["optimize_regressor_rounds"],
                                        optimize_regressor_threshold = args["optimize_regressor_threshold"])
        
    if args["log"] is not None:
        executor = Executor.from_task(args)
        executor.load_log(args["log"])

    if args["simulate"]:
        
        executor = Executor.from_task(args)
        executor.run()
    
    if args["max_utility"]:
        executor = Executor.from_task(args)
        executor.calculate_max_utility()