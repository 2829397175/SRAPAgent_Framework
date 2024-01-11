from matplotlib import pyplot as plt
import os
import json

def readinfo(data_dir):
    assert os.path.exists(data_dir),"no such file path: {}".format(data_dir)
    with open(data_dir,'r',encoding = 'utf-8') as f:
        data_list = json.load(f)
    return data_list

def draw_train_time(log_root ="LLM_PublicHouseAllocation/optimizer/logs"):
    
    
    log_files =[ "LLM_PublicHouseAllocation/optimizer/logs",
                "LLM_PublicHouseAllocation/optimizer/logs_fairness"]
    train_times_all = []
    samples_all = []
    maes_all = []
    for log_root in log_files:
        train_times = []
        samples = []
        maes = []
        files = os.listdir(log_root)
        for file in files:
            file_path = os.path.join(log_root,file,"optimize_log.json")
            if not os.path.exists(file_path):
                continue
            optimize_log = readinfo(file_path)
            try:
                sample_mae = optimize_log["regressor"]["init"]["mae"]
                sample_num = optimize_log["regressor"]["init"]["optimize_data_len"]
                
                sample_time = optimize_log["regressor"]["init"]["optimize_time"]
                if sample_time >100:
                    continue
                train_times.append(sample_time)
                samples.append(sample_num)
                maes.append(sample_mae)
            except:
                continue
        samples_all.append(samples)
        maes_all.append(maes)
        train_times_all.append(train_times)
        
    # 创建图表
    fig, ax1 = plt.subplots()
    
    # 绘制b列表数据
    ax1.scatter(samples_all[0], train_times_all[0], c='g')
    ax1.set_xlabel('Number of train data',fontsize=14)
    ax1.set_ylabel('Satisfaction-biased regressor(s)',fontsize=14)

    # 创建第二个轴
    ax2 = ax1.twinx()
    ax2.scatter(samples_all[1], train_times_all[1], c='b')
    ax2.set_ylabel('Fairness-biased regressor(s)',fontsize=14)

    # plt.title('Plot with Left and Right Y Axes')
    plt.tight_layout()
    plt.savefig("LLM_PublicHouseAllocation/optimizer/optimize_time.png")
     
    
if __name__=="__main__":
    draw_train_time()