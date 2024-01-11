import json
import os

logs_path = "EconAgent/optimizer/logs"
logs_path = "EconAgent/optimizer/logs_fairness"
files = os.listdir(logs_path)

top_gt_names = []
top_optimize_names = []

good_optimize_logs =[]

for file in files:
    optimize_log_path = os.path.join(logs_path,file,"optimize_log.json")
    if not os.path.exists(optimize_log_path):
        continue
    with open(optimize_log_path,'r',encoding = 'utf-8') as f:
        optimize_log = json.load(f)
    try:
        optimize_result = optimize_log["final_result"]["best_of_all"]
        if optimize_result["max_gt_y"]["gt_y"]<=optimize_result["max_pred_y"]["gt_y"]:
            print(optimize_log_path)
        if (optimize_result["max_gt_y"]["gt_y"]-optimize_result["max_pred_y"]["gt_y"]) \
            <0.05:
            if optimize_result["max_gt_y"]["ex_name"] != optimize_result["max_pred_y"]["ex_name"]:
                top_gt_names.append(optimize_result["max_gt_y"]["ex_name"])
                top_optimize_names.append(optimize_result["max_pred_y"]["ex_name"])
                good_optimize_logs.append(file)
    except:
        pass
    
print(str(top_gt_names))
print(str(top_optimize_names))
print(str(good_optimize_logs))

