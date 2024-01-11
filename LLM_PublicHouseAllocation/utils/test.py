from matplotlib import pyplot as plt
import os
import pandas as pd


def draw_train_time(log_root ="LLM_PublicHouseAllocation/optimizer/logs"):
    files = os.listdir(log_root)
    for file in files:
        file_path = os.path.join(log_root,file,"optimize_log.json")
        
def get_ex_names():
    files =["LLM_PublicHouseAllocation/experiments/forgpt/optimize_sw.csv",
            "LLM_PublicHouseAllocation/experiments/forgpt/optimize_fair.csv"]
    for file in files:
        df = pd.read_csv(file)
        ex_names = df["ex_name"].to_list()
        print(str(ex_names))
    
if __name__=="__main__":
    # draw_train_time()
    get_ex_names()