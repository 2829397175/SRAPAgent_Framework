
from .base import BaseOptimizer

from . import policy_optimizer_registry

import numpy as np
import random
from typing import Any
from deap import base, creator, tools, algorithms

import os
import json
import pandas as pd

import pickle
# 监视某行代码是否执行时间超过threshold
import multiprocessing
import time

class TimeoutException(Exception):
    pass


def read_in_json_info(optimize_log_path):
    with open(optimize_log_path,'r',encoding = 'utf-8') as f:
        optimize_log = json.load(f)
    return optimize_log

def long_running_task(queue,
                      optimizer, 
                      **kwargs):
    # 执行一些操作
    result = optimizer.simulate_optimize_task(**kwargs)
    # 将结果放入队列
    queue.put(result)

def run_with_timeout(proc, timeout):
    proc.start()
    proc.join(timeout)
    if proc.is_alive():
        proc.terminate()  # 超时后终止进程
        raise TimeoutException("长时间运行的操作超时")

@policy_optimizer_registry.register("genetic_algorithm")
class Genetic_algorithm_Optimizer(BaseOptimizer):
    
    # 为了计算遗传算法中的适应度，训练的回归模型
    regressor_model: Any = None
    
    # 遗传算法参数
    population_size = 100
    generations = 10
    crossover_prob = 0.7
    mutation_prob = 0.2
     
    # 优化器政策历史 
    optimize_log = {} # config_name: optimizer_y, gt_y
    
    # 存储上一次训练结束的population
    population :Any = None
    
    
    # 存储连续值的训练值, 每次加入新的gt值后清0
    x_continous:np.ndarray = None
    y_continous:np.ndarray = None
    
    
    # 存储所有实验的best_offspring
    best_offsprings:list = []
    optimize_names:list = []
    
    # 存储所有实验中的index(对应self.x)
    used_index:list = []
    
    def prepare_individual_regressor(self):# 给定X，训练一个可以给出对应y值的模型
       
        
        train_x, train_y = self.x_used,self.y_used
        # 示例：使用随机过采样
        from sklearn.utils import resample
        sorted_indexes = sorted(range(self.y.shape[0]), key=lambda i: self.y[i], reverse=True)

        # 提取前五个最大值的索引
        top_indexes = sorted_indexes[:int(0.1*self.y.shape[0])]
        
        positive_samples_resampled_indexs = resample(top_indexes, 
                                       replace=True,  # 允许重复采样
                                       n_samples = int(0.5*self.y.shape[0]),  
                                       random_state = 42)  # 设置随机种子以复现结果

        # 合并重采样后的数据
        train_x = np.concatenate([train_x, train_x[positive_samples_resampled_indexs,:]])
        train_y = np.concatenate([train_y, train_y[positive_samples_resampled_indexs]])
        
        from sklearn.linear_model import LinearRegression,Ridge
        # if self.regressor_model is None:
        #     lin_reg = LinearRegression()
        if self.regressor_model is None:
            lin_reg = Ridge()
        else:
            lin_reg = self.regressor_model
        
        if self.x_continous is not None:
            train_x = np.concatenate([train_x,self.x_continous],axis=0)
            train_y = np.concatenate([train_y,self.y_continous],axis=0)
        
        lin_reg.fit(train_x,train_y)

        self.regressor_model = lin_reg
        
        
    
    def prepare_individual_regressor_with_refinement(self,
                                                     threshold = 0.5,
                                                     tasks_dir = "LLM_PublicHouseAllocation/tasks",
                                                     sample_size_round = 1, 
                                                     max_round = 10,
                                                     model_save_dir = ""):# 给定X，训练一个可以给出对应y值的模型
        """ 这个接口是对于新的数据集做的 真实模拟（利用现有的数据，再sample） """
        if not os.path.exists(model_save_dir):
            os.makedirs(model_save_dir)
        
        
        
        from sklearn.linear_model import LinearRegression,Ridge
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import mean_squared_error,mean_absolute_error
        # if self.regressor_model is None:
        #     lin_reg = LinearRegression()
       
        ridge_model = Ridge(alpha=1.0)
        
        gap = 100
        round_idx = 0
        import time
        start_time = time.time()
        init_data_size = self.y.shape[0]
        
        while (gap > threshold and round_idx<max_round):
            
            X, Y = self.x_used, self.y_used
            
            """ evaluate regressor"""
            # 将数据集分为训练集和测试集
            X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=0)
            
            
            ridge_model.fit(X_train, Y_train)
            
            model_save_path = os.path.join(model_save_dir,f"regressor_model_{round_idx}.pkl")
            #保存Model(save文件夹要预先建立)
            with open(model_save_path, 'wb') as f:  #write byte
                pickle.dump(ridge_model, f)
            # 在测试集上进行预测并计算误差
            Y_pred = ridge_model.predict(X_test)
            
            mse = mean_squared_error(Y_test, Y_pred)
            mae = mean_absolute_error(Y_test ,Y_pred)
            
            if (mse<=threshold):
                break
            """ 用新的数据进行refinement """
            random_configs = []
            for _ in range(sample_size_round):
                random_configs.append({column:self.x_attrs[column].sample().values[0] for column in self.x_attrs.columns})
            
            random_configs = list(map(self.filter_x_config, random_configs))
            
            
            for random_config in random_configs:
                config_name, runned_before = self.update_config(configs=random_config,tasks_dir=tasks_dir)
                try:
                    queue = multiprocessing.Queue()
                    # 创建进程
                    process = multiprocessing.Process(target=long_running_task,kwargs={"config_name":config_name,
                                                                                    "use_cache":True,
                                                                                    "queue":queue,
                                                                                    "optimizer":self},)

                    # 执行进程并设置超时
                    run_with_timeout(process, 3*60*60) #这个进程最长允许的运行时间为3h，否则kill
                    
                    if process.exitcode == 0:
                        # 从队列中获取返回值
                        return_values = queue.get()
                        print("代码执行完成")
                    else:
                        return_values = None
                        print("代码执行被终止")
                        round_idx += 1
                        continue

                except TimeoutException as e:
                    print(e)
                    return_values = None
                    round_idx += 1
                    continue
                
                
                if return_values is not None:
                    simulate_x_array, simulate_y_array, x_attrs, y_attrs = return_values
                    self.x = np.concatenate([self.x,simulate_x_array],axis = 0)
                    self.y = np.concatenate([self.y,simulate_y_array],axis = 0)     
                    
                    self.x_attrs = pd.concat([self.x_attrs,
                                            x_attrs],axis = 0)
                    self.y_attrs = pd.concat([self.y_attrs,
                                            y_attrs],axis = 0)
                    
                    
                    for ex_idx in x_attrs.index:
                        self.x_ex_map[int(ex_idx)] = config_name
                    
            
            """ 进行数据重采样"""
            
            # 示例：使用随机过采样
            from sklearn.utils import resample
            sorted_indexes = sorted(range(self.y.shape[0]), key=lambda i: self.y[i], reverse=True)

            top_indexes = sorted_indexes[:int(0.1*self.y.shape[0])]
            
            positive_samples_resampled_indexs = resample(top_indexes, 
                                        replace = True,  # 允许重复采样
                                        n_samples = int(0.5*self.y.shape[0]),  
                                        random_state = 42)  # 设置随机种子以复现结果

            # 合并重采样后的数据
            X = np.concatenate([X, X[positive_samples_resampled_indexs,:]])
            Y = np.concatenate([Y, Y[positive_samples_resampled_indexs]])
            
            round_idx += 1

        self.regressor_model = ridge_model
        self.optimize_log["regressor"] = {
            "optimize_time":time.time()-start_time,
            "mse":mse,
            "mae":mae,
            "optimize_data_len": init_data_size + sample_size_round*round_idx
        }
        
    def prepare_individual_regressor_with_refinement_experiment(self,
                                                     threshold = 0.5,
                                                     tasks_dir = "LLM_PublicHouseAllocation/tasks",
                                                     init_data_size = 50,
                                                     sample_size_round = 1, 
                                                     max_round = 1000,
                                                     max_run_task_round = 3,
                                                     model_save_dir = "",
                                                     geneic_fit_round = "init"):# 给定X，训练一个可以给出对应y值的模型
        """ 这个接口是对于 已经跑了比较多实验的 refinement """
        model_save_dir = os.path.join(model_save_dir,geneic_fit_round)
        if not os.path.exists(model_save_dir):
            os.makedirs(model_save_dir)
        max_round = max_round if max_round>0 else 1
        
        import time
        
        from sklearn.linear_model import LinearRegression,Ridge
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import mean_squared_error, mean_absolute_error
        from sklearn.utils import resample
        # if self.regressor_model is None:
        #     lin_reg = LinearRegression()
       
        
        start_time = time.time()
        if len(self.x_used) == 0:
            init_data_size = init_data_size if init_data_size<self.x.shape[0] else self.x.shape[0]
            if init_data_size<self.x.shape[0]:
                self.x_used,self.y_used = self.x[:init_data_size],self.y[:init_data_size]
                self.used_index.extend(list(range(init_data_size)))
            else:
                self.x_used,self.y_used = self.x,self.y
                self.used_index.extend(list(range(self.x.shape[0])))
                
        used_len = self.x_used.shape[0]
        X,Y = self.x_used,self.y_used
        if used_len < self.x.shape[0]:
            X_append, Y_append = self.x[used_len:],self.y[used_len:]
        else:
            X_append, Y_append = np.array([]),np.array([])

        gap = 100
        round_idx = 0
        round_run_idx = 0
        
        train_loss_pic_sizes = []
        train_loss_pic_y_mae = []
        train_loss_pic_y_mse = []
        
        train_loss_pic_y_mae_all = []
        train_loss_pic_y_mse_all = []
        
        while (gap > threshold and \
            round_idx < max_round and \
                (round_run_idx < max_run_task_round or max_run_task_round == 0)):
            
            """ evaluate regressor"""
            # 将数据集分为训练集和测试集
            X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=0)
            
            
            
            """ 进行数据重采样"""
            
            sorted_indexes = sorted(range(Y_train.shape[0]), key=lambda i: Y_train[i], reverse=True)

            top_indexes = sorted_indexes[:int(0.1*Y_train.shape[0])]
            
            if len(top_indexes)>0:
                positive_samples_resampled_indexs = resample(top_indexes, 
                                            replace = True,  # 允许重复采样
                                            n_samples = int(0.5*Y_train.shape[0]),  
                                            random_state = 42)  # 设置随机种子以复现结果

                # 合并重采样后的数据
                X_train = np.concatenate([X_train, X_train[positive_samples_resampled_indexs,:]])
                Y_train = np.concatenate([Y_train, Y_train[positive_samples_resampled_indexs]])
            
            
            ridge_model = Ridge(alpha=1.0)
            ridge_model.fit(X_train, Y_train)
            
            model_save_path = os.path.join(model_save_dir,f"regressor_model_{round_idx}.pkl")
            #保存Model(save文件夹要预先建立)
            with open(model_save_path, 'wb') as f:  #write byte
                pickle.dump(ridge_model, f)
            # 在测试集上进行预测并计算误差
            Y_pred = ridge_model.predict(X_test)
            
            mse = mean_squared_error(Y_test, Y_pred)
            mae = mean_absolute_error(Y_test ,Y_pred)
            gap = mae
            train_loss_pic_sizes.append(self.x_used.shape[0])
            train_loss_pic_y_mae.append(mae)
            train_loss_pic_y_mse.append(mse)
            
            ## debug 在整个数据集上测试误差
            Y_pred = ridge_model.predict(self.x)
            
            mse_all = mean_squared_error(self.y, Y_pred)
            mae_all = mean_absolute_error(self.y ,Y_pred)         
            train_loss_pic_y_mae_all.append(mae_all)
            train_loss_pic_y_mse_all.append(mse_all)
            
            if (mae<=threshold):
                break
            
            """ 用新的数据进行refinement """
            if sample_size_round < X_append.shape[0]:

                X = np.concatenate([X,X_append[:sample_size_round]],axis=0)
                self.used_index.extend(list(range(self.x_used.shape[0],self.x_used.shape[0]+sample_size_round)))
                self.x_used = np.concatenate([self.x_used,X_append[:sample_size_round]],axis = 0)
                X_append = X_append[sample_size_round:]
                
                Y = np.concatenate([Y,Y_append[:sample_size_round]],axis=0)
                self.y_used = np.concatenate([self.y_used,Y_append[:sample_size_round]],axis = 0)    
                Y_append = Y_append[sample_size_round:]
                

            else:
                if X_append.shape[0]!= 0:
                    X = np.concatenate([X,X_append],axis=0)
                    Y = np.concatenate([Y,Y_append],axis=0)
                    self.used_index.extend(list(range(self.x_used.shape[0],self.x_used.shape[0] + X_append.shape[0])))
                    self.x_used = np.concatenate([self.x_used,X_append],axis = 0)
                    self.y_used = np.concatenate([self.y_used,Y_append],axis = 0)     
                    
                    
                    X_append = np.array([])
                    Y_append = np.array([])
                if (max_run_task_round ==0):
                    break
                sample_size = sample_size_round - X_append.shape[0]
                random_configs = []
                for _ in range(sample_size):
                    random_configs.append({column:self.x_attrs[column].sample().values[0] for column in self.x_attrs.columns})
                
                random_configs = list(map(self.filter_x_config, random_configs))
                
                
                for random_config in random_configs:
                    config_name, runned_before = self.update_config(configs=random_config,tasks_dir=tasks_dir)
                    try:
                        queue = multiprocessing.Queue()
                        # 创建进程
                        process = multiprocessing.Process(target=long_running_task,kwargs={"config_name":config_name,
                                                                                        "use_cache":True,
                                                                                        "queue":queue,
                                                                                        "optimizer":self},)

                        # 执行进程并设置超时
                        run_with_timeout(process, 3*60*60) #这个进程最长允许的运行时间为3h，否则kill
                        
                        if process.exitcode == 0:
                            # 从队列中获取返回值
                            return_values = queue.get()
                            print("代码执行完成")
                            round_run_idx+=1
                        else:
                            return_values = None
                            print("代码执行被终止")
                            round_idx += 1
                            round_run_idx +=1
                            continue

                    except TimeoutException as e:
                        print(e)
                        return_values = None
                        round_idx += 1
                        round_run_idx +=1
                        continue
                
                
                    if return_values is not None:
                        simulate_x_array, simulate_y_array, x_attrs, y_attrs = return_values
                        self.x = np.concatenate([self.x,simulate_x_array],axis = 0)
                        self.y = np.concatenate([self.y,simulate_y_array],axis = 0)     
                        self.used_index.extend(list(range(self.x_used.shape[0],self.x_used.shape[0] + simulate_x_array.shape[0])))
                        self.x_used = np.concatenate([self.x_used,simulate_x_array],axis = 0)
                        self.y_used = np.concatenate([self.y_used,simulate_y_array],axis = 0)     
                        
                        
                        self.x_attrs = pd.concat([self.x_attrs,
                                                x_attrs],axis = 0)
                        self.y_attrs = pd.concat([self.y_attrs,
                                                y_attrs],axis = 0)
                        X = np.concatenate([X,simulate_x_array],axis=0)
                        Y = np.concatenate([Y,simulate_y_array],axis=0)
                        
                        for ex_idx in x_attrs.index:
                            self.x_ex_map[int(ex_idx)] = config_name
            round_idx += 1
            
        # 在测试集上达到目标值后，重新在整个数据集上训练一遍
        """ 进行数据重采样"""
        sorted_indexes = sorted(range(Y.shape[0]), key=lambda i: Y[i], reverse=True)

        top_indexes = sorted_indexes[:int(0.1*Y.shape[0])]
        
        if len(top_indexes)>0:
            positive_samples_resampled_indexs = resample(top_indexes, 
                                        replace = True,  # 允许重复采样
                                        n_samples = int(0.3*Y.shape[0]),  
                                        random_state = 42)  # 设置随机种子以复现结果

            # 合并重采样后的数据
            X = np.concatenate([X, X[positive_samples_resampled_indexs,:]])
            Y = np.concatenate([Y, Y[positive_samples_resampled_indexs]])
        
        
        ridge_model.fit(X, Y)
        
        pic_path = "LLM_PublicHouseAllocation/optimizer/train_size.png"
        from matplotlib import pyplot as plt
        plt.plot(train_loss_pic_sizes,train_loss_pic_y_mae,label = "mae")
        plt.plot(train_loss_pic_sizes,train_loss_pic_y_mse,label = "mse")
        plt.xlabel("|train samples|")
        plt.ylabel("Loss")
        plt.legend()
        plt.savefig(pic_path)
        plt.clf()
        
        ## debug
        plt.plot(train_loss_pic_sizes,train_loss_pic_y_mae_all,label = "mae")
        plt.plot(train_loss_pic_sizes,train_loss_pic_y_mse_all,label = "mse")
        plt.xlabel("|train samples|")
        plt.ylabel("Loss")
        plt.legend()
        plt.savefig("LLM_PublicHouseAllocation/optimizer/train_size_all.png")
        plt.clf()
        
        
        plt.plot(train_loss_pic_sizes,train_loss_pic_y_mae_all,label = "mae:complete dataset")
        plt.plot(train_loss_pic_sizes,train_loss_pic_y_mse_all,label = "mse:complete dataset")
        plt.plot(train_loss_pic_sizes,train_loss_pic_y_mae,label = "mae:test dataset")
        plt.plot(train_loss_pic_sizes,train_loss_pic_y_mse,label = "mse:test dataset")
        plt.xlabel("|train samples|")
        plt.ylabel("Loss")
        plt.legend()
        plt.savefig("LLM_PublicHouseAllocation/optimizer/train_size_both.png")
        plt.clf()
        
        assert len(self.used_index) == self.x_used.shape[0] and self.x_used.shape[0] == self.y_used.shape[0], f"{len(self.used_index)}, {self.x_used.shape[0]},{self.y_used.shape[0]}"
        self.regressor_model = ridge_model
        if "regressor" not in self.optimize_log.keys(): 
            self.optimize_log["regressor"] = {}
        
        self.optimize_log["regressor"][geneic_fit_round] = {
            "optimize_time":time.time()-start_time,
            "mse":mse,
            "mae":mae,
            "mse_all":mse_all,
            "mae_all":mae_all,
            "optimize_data_len": len(self.used_index)
        }
    
    
    # 定义适应度函数
    def evaluate_individual(self,individual):
        # 将个体的基因编码（例如：二进制）解码为x的值
        # configs = self.decode_x(individual)
        # vector_x = self.encode_x(np.array(list(configs.values())))
        y_value = self.regressor_model.predict([individual])[0]
        
        return y_value,
    
    
    # def refine_regressor(self,
    #                      population):
        # refine regressor (为了将连续值和离散值 映射到 同一个y值)    
    #     for individual in random.sample(population,int(len(population)/self.generations)):
    #     # for individual in population:
    #         x_reverse_dict = self.decode_x(individual)
    #         encoded_x = self.encode_x(np.array(list(x_reverse_dict.values())))
    #         if np.array_equal(individual.base,encoded_x):
    #             continue
    #         else:
    #             y = self.regressor_model.predict([encoded_x])
    #             continuous_x = np.reshape(np.array(individual),(1,-1))
    #             if self.x_continous is not None:
    #                 self.x_continous = np.concatenate([self.x_continous,continuous_x],
    #                                                   axis=0)
    #                 self.y_continous = np.concatenate([self.y_continous,y],
    #                                                   axis=0)
    #             else:
    #                 self.x_continous = continuous_x
    #                 self.y_continous = y
    #     self.prepare_individual_regressor()
   
    def generate_x(self):
        # ks = [2,3,4,5]
        # ratios = [1.2,1.5,1.8,2.1]
        # order_types = []
        # for k in ks:
        #     for ratio in ratios:
        #         order_types.append("kwaitlist_k_{k}_ratio_{ratio}".format(k = k,ratio= ratio))
        available_column_values = {
            "distribution_batch_house_distribution_len":list(range(1,8)),
            "distribution_batch_house_distribution_step":[1],
            "distribution_batch_tenant_distribution_len":list(range(1,8)),
            "distribution_batch_tenant_distribution_step":[1],
            "group_size":[2,3,4,5],
            "tenant_max_choose":[1,2,3,4,5],
            "group_policy_sorting_type":['priority', 'base', 'housing_points'],
            "group_policy_type":['house_type', 'single_list', 'portionfamily_members_num', 'multi_list','portionmonthly_rent_budget'],
            "community_patch_method":['house_type', 'single_list', 'portion_housesize', 'portion_rentmoney','random_avg'],
            "policy_type":["ver2","ver1"],
            "order_type":list(self.x_attrs["order_type"].value_counts().keys())
        }
        
        random_values = {column:random.choice(available_column_values[column]) for column in available_column_values.keys()}
        random_values = self.filter_x_config(random_values)
        # random_values = [random.choice(self.x_attrs[column].values) for column in self.x_attrs.columns]
        x_encoded = self.encode_x(random_values)
        return x_encoded
    
    
    def initilize_population(self, pcls, ind_init, custom_array):
        
        return pcls(ind_init(c) for c in custom_array)
    
    
    def save_log(self,
                 optimize_log_path):
        
        with open(optimize_log_path,'w',encoding = 'utf-8') as f:
            json.dump(self.optimize_log, f, indent=4,separators=(',', ':'),ensure_ascii=False)
       
       
       
    def fit_experiment_evaluate_ver_2(self,
                                tasks_dir = "LLM_PublicHouseAllocation/tasks",
                                optimize_regressor_threshold = 1,
                                optimize_regressor_max_samples = 100):
        import time
        root_optimize = f"LLM_PublicHouseAllocation/optimizer/logs_{self.optimize_type}/{time.time()}"
        
      
        self.prepare_individual_regressor_with_refinement_experiment(threshold = optimize_regressor_threshold,
                                                    sample_size_round = 1,
                                                    init_data_size = 40,
                                                    max_round = int((optimize_regressor_max_samples-40)/1),
                                                    max_run_task_round = 0, # debug用
                                                    model_save_dir= os.path.join(root_optimize,"regressor_model"),
                                                    geneic_fit_round="init")
        round_ex_path = os.path.join(root_optimize,"round_0")
        if not os.path.exists(round_ex_path):
            os.makedirs(round_ex_path)
        
        self.debug_csv(os.path.join(round_ex_path,"debug.csv"))
        self.debug_csv(os.path.join(round_ex_path,"debug_used_data.csv"), used_data = True)
        self.save_log(os.path.join(root_optimize,"optimize_log.json"))
        self.save_ex_map(os.path.join(root_optimize,"ex_name_map.json"))
        optimized_config_name, runned_before, best_config_vector, best_configs = self.fit(tasks_dir,
                     fit_round = 0)
        
        # debug
        encoded_vector = self.encode_x(np.array(list(best_configs.values())))
        pred_y = self.regressor_model.predict([np.array(encoded_vector)])[0]
       
        self.optimize_log[0]={
                "optimized":{
                    optimized_config_name:[]
                }
        }
        max_retry = 3
        for _ in range(max_retry):
            try:
                queue = multiprocessing.Queue()
                # 创建进程
                process = multiprocessing.Process(target=long_running_task,kwargs={"config_name":optimized_config_name,
                                                                                   "use_cache":True,
                                                                                   "queue":queue,
                                                                                   "optimizer":self},)

                # 执行进程并设置超时
                run_with_timeout(process, 3*60*60) #这个进程最长允许的运行时间为3h，否则kill
                
                if process.exitcode == 0:
                     # 从队列中获取返回值
                    return_values = queue.get()
                    print("代码执行完成")
                    break
                else:
                    return_values = None
                    print("代码执行被终止")
                    continue

            except TimeoutException as e:
                print(e)
                return_values = None
                continue
            
        if return_values is not None: 
            simulate_x_array, simulate_y_array, x_attrs, y_attrs = return_values
           
            self.x = np.concatenate([self.x,simulate_x_array],axis = 0)
            self.y = np.concatenate([self.y,simulate_y_array],axis = 0)     
            
            self.x_used = np.concatenate([self.x_used,simulate_x_array],axis = 0)
            self.y_used = np.concatenate([self.y_used,simulate_y_array],axis = 0)     
            
            self.x_attrs = pd.concat([self.x_attrs,
                                        x_attrs],axis = 0)
            self.y_attrs = pd.concat([self.y_attrs,
                                    y_attrs],axis = 0)

        
            for ex_idx in x_attrs.index:
                self.x_ex_map[int(ex_idx)] = optimized_config_name
                self.used_index.append(ex_idx)
            assert len(self.used_index) == self.x_used.shape[0] and self.x_used.shape[0] == self.y_used.shape[0], f"{len(self.used_index)}, {self.x_used.shape[0]},{self.y_used.shape[0]}"
            for simulate_x, simulate_y, ex_idx in zip(simulate_x_array, simulate_y_array, x_attrs.index.to_list()):
                
                self.optimize_log[0]["optimized"][optimized_config_name].append({
                    "gt_y":simulate_y,
                    "predict_y":pred_y,
                    "ex_idx":int(ex_idx),
                    "runned_before":runned_before
                    })
        
        self.debug_csv(os.path.join(round_ex_path,"debug.csv"))
        self.debug_csv(os.path.join(round_ex_path,"debug_used_data.csv"), used_data = True)
        
        self.process_optimized_tasks()
        self.save_log(os.path.join(root_optimize,"optimize_log.json"))
        self.save_ex_map(os.path.join(root_optimize,"ex_name_map.json"))
        
        
    def fit_experiment_evaluate(self,
                                tasks_dir = "LLM_PublicHouseAllocation/tasks",
                                threshold = 1,
                                max_round = 3,
                                optimize_regressor_max_samples = 15,
                                optimize_regressor_threshold = 0.01):
        i = 0
        simulate_y = 0
        pred_y = 100
        
        optimization_done = False
        
        import time
        root_optimize = f"LLM_PublicHouseAllocation/optimizer_{self.optimize_type}/logs/{time.time()}"
      
        # self.prepare_individual_regressor()
        
        self.prepare_individual_regressor_with_refinement_experiment(threshold = 0.3,
                                                          sample_size_round = 5,
                                                          init_data_size = 40,
                                                          max_run_task_round = 0,
                                                          max_round = int((optimize_regressor_max_samples-40)/1),
                                                          model_save_dir= os.path.join(root_optimize,"regressor_model"),
                                                          geneic_fit_round="init")
        
        
        
        while (i < max_round and not optimization_done):
            self.optimize_log[i] = {
                "optimized":{},
            }
            round_ex_path = os.path.join(root_optimize,f"round_{i}")
            if not os.path.exists(round_ex_path):
                os.makedirs(round_ex_path)
            self.debug_csv(os.path.join(round_ex_path,"debug.csv"))
            optimized_config_name, runned_before, best_config_vector, best_configs = self.fit(tasks_dir,
                     fit_round = i,run_every_gen=True)
            
            
            
            if optimized_config_name not in self.optimize_log[i]["optimized"].keys():
                self.optimize_log[i]["optimized"][optimized_config_name] = []
                
            
            # debug
            encoded_vector = self.encode_x(np.array(list(best_configs.values())))
            pred_y = self.regressor_model.predict([np.array(encoded_vector)])[0]
            
            self.save_log(os.path.join(root_optimize,"optimize_log.json"))
            try:
                queue = multiprocessing.Queue()
                # 创建进程
                process = multiprocessing.Process(target=long_running_task,kwargs={"config_name":optimized_config_name,
                                                                                   "use_cache":True,
                                                                                   "queue":queue,
                                                                                   "optimizer":self},)

                # 执行进程并设置超时
                run_with_timeout(process, 3*60*60) #这个进程最长允许的运行时间为3h，否则kill
                
                if process.exitcode == 0:
                     # 从队列中获取返回值
                    return_values = queue.get()
                    print("代码执行完成")
                else:
                    return_values = None
                    print("代码执行被终止")
                    continue

            except TimeoutException as e:
                print(e)
                return_values = None
                continue
            
            
            if return_values is not None:
                
                simulate_x_array, simulate_y_array, x_attrs, y_attrs = return_values
                self.x = np.concatenate([self.x,simulate_x_array],axis = 0)
                self.y = np.concatenate([self.y,simulate_y_array],axis = 0)     
                
                self.x_used = np.concatenate([self.x_used,simulate_x_array],axis = 0)
                self.y_used = np.concatenate([self.y_used,simulate_y_array],axis = 0)     
                
                self.x_attrs = pd.concat([self.x_attrs,
                                         x_attrs],axis = 0)
                self.y_attrs = pd.concat([self.y_attrs,
                                        y_attrs],axis = 0)
                
                
                for ex_idx in x_attrs.index:
                    self.x_ex_map[int(ex_idx)] = optimized_config_name
                    self.used_index.append(ex_idx)
                assert len(self.used_index) == self.x_used.shape[0] and self.x_used.shape[0] == self.y_used.shape[0], f"{len(self.used_index)}, {self.x_used.shape[0]},{self.y_used.shape[0]}"
                for simulate_x, simulate_y, ex_idx in zip(simulate_x_array, simulate_y_array, x_attrs.index.to_list()):
                    
                    
                    self.optimize_log[i]["optimized"][optimized_config_name].append({
                        "gt_y":simulate_y,
                        "predict_y":pred_y,
                        "ex_idx":int(ex_idx),
                        "runned_before":runned_before
                        })
                
                simulate_y_mean = np.mean([item["gt_y"] for item in \
                    self.optimize_log[i]["optimized"][optimized_config_name]])
                pred_y_mean = np.mean([item["predict_y"] for item in \
                    self.optimize_log[i]["optimized"][optimized_config_name]])
                
                if np.abs(simulate_y_mean - pred_y_mean) < threshold :
                    optimization_done = True
                
            self.debug_csv(os.path.join(round_ex_path,"debug.csv"))
            self.debug_csv(os.path.join(round_ex_path,"debug_used_data.csv"), used_data = True)
            self.save_log(os.path.join(root_optimize,"optimize_log.json"))
            if (i+1)!= max_round and not optimization_done:
                self.prepare_individual_regressor_with_refinement_experiment(threshold = 0.5,
                                                          sample_size_round = 5,
                                                          max_run_task_round = 1,
                                                          init_data_size = 40,
                                                          max_round = int((optimize_regressor_max_samples-40)/1),
                                                          model_save_dir = os.path.join(root_optimize,"regressor_model"),
                                                          geneic_fit_round = str(i))
    
            i+=1
            
        self.process_optimized_tasks()
        self.save_log(os.path.join(root_optimize,"optimize_log.json"))
        self.save_ex_map(os.path.join(root_optimize,"ex_name_map.json"))

    def process_optimized_tasks(self):
        
        optimize_ex_idxs = []
        for optimize_round,optimize_log in self.optimize_log.items():
            if isinstance(optimize_log,dict):
                if "optimized" in optimize_log.keys():
                    for optimize_config_name in optimize_log["optimized"].keys():
                        for optimized_config in optimize_log["optimized"][optimize_config_name]:
                            optimize_ex_idxs.append(optimized_config.get("ex_idx"))
        
        debug_df = self.debug_csv(save=False, used_data=True)
        optimize_matix = debug_df.loc[optimize_ex_idxs]
        max_op_gt_y_index = optimize_matix['gt_y'].idxmax()
        max_op_pred_y_index = optimize_matix['predict_y'].idxmax()
        
        max_gt_y_index = debug_df['gt_y'].idxmax()
        max_pred_y_index = debug_df['predict_y'].idxmax()
        
        best_config_log = {
            "optimized":{
                "max_gt_y":{
                    "gt_y":debug_df.loc[max_op_gt_y_index,"gt_y"],
                    "pred_y":debug_df.loc[max_op_gt_y_index,"predict_y"],
                    "ex_idx":int(max_op_gt_y_index),
                    "ex_name":self.x_ex_map[int(max_op_gt_y_index)]
                },
                "max_pred_y":{
                    "gt_y":debug_df.loc[max_op_pred_y_index,"gt_y"],
                    "pred_y":debug_df.loc[max_op_pred_y_index,"predict_y"],
                    "ex_idx":int(max_op_pred_y_index),
                    "ex_name":self.x_ex_map[int(max_op_pred_y_index)]
                }
            },
            "best_of_all":{
                "max_gt_y":{
                    "gt_y":debug_df.loc[max_gt_y_index,"gt_y"],
                    "pred_y":debug_df.loc[max_gt_y_index,"predict_y"],
                    "ex_idx":int(max_gt_y_index),
                    "ex_name":self.x_ex_map[int(max_gt_y_index)]
                },
                "max_pred_y":{
                    "gt_y":debug_df.loc[max_pred_y_index,"gt_y"],
                    "pred_y":debug_df.loc[max_pred_y_index,"predict_y"],
                    "ex_idx":int(max_pred_y_index),
                    "ex_name":self.x_ex_map[int(max_pred_y_index)]
                }
            }
        }
        self.optimize_log["final_result"] = best_config_log
        
    
    def save_ex_map(self,path):
    
        with open(path,'w',encoding = 'utf-8') as f:
            json.dump(self.x_ex_map, f, indent=4,separators=(',', ':'),ensure_ascii=False)
    
    
    def generate_optimized_result_gt(self,
                                     optimize_log_dir,
                                     tasks_dir):
        used_data_path = os.path.join(optimize_log_dir,
                                      "round_0",
                                      "debug_used_data.csv"
                                      )
        used_data = pd.read_csv(used_data_path,
                                index_col=0)
        from sklearn.preprocessing import MinMaxScaler

        from sklearn.preprocessing import LabelEncoder,OneHotEncoder
        ex_name_map_path = os.path.join(optimize_log_dir,
                                      "ex_name_map.json")
        ex_name_map = read_in_json_info(ex_name_map_path)
        
        used_ex_names = []
        for used_ex_index in used_data.index:
            ex_name = ex_name_map[str(used_ex_index)]
            used_ex_names.append(ex_name)
        
        optimized_log_path = os.path.join(optimize_log_dir,
                                      "optimize_log.json")
        optimize_log = read_in_json_info(optimized_log_path)
        try:
            optimized_ex = optimize_log["final_result"]["optimized"]["max_gt_y"]["ex_name"]
            optimized_index = optimized_ex["ex_idx"]
            optimized_ex_name = optimized_ex["ex_name"]

        except:
            return
        
        objective_matrix, utility_matrix = self.concat_experiment_results(task_path = tasks_dir,
                                        ex_setting = self.data_setting,
                                        save_all_ex_results = False,
                                        )
        
        matrix = pd.concat([objective_matrix,utility_matrix])
        
        matrix = matrix[matrix["ex_name"] in [*used_ex_names,optimized_ex_name]]
        
        y_attrs = pd.DataFrame()
        x_attrs = pd.DataFrame()
        
        """load x,y"""
        ex_results = matrix.groupby(["ex_idx"])
        for ex_idx,ex_result in ex_results:
            assert len(ex_idx) ==1 ,"multiple index for one experiment"
            ex_idx = ex_idx[0]
            for type_indicator,indicators_ in self.indicators.items():
                for indicator in indicators_.keys():
                    if indicator in ex_result.index:
                        y_attrs.loc[ex_idx,indicator] = float(ex_result.loc[indicator,"all"])
            
            for type_x,x_names in self.features.items():
                for x_name in x_names:
                    x_attrs.loc[ex_idx,x_name] = ex_result[x_name].values[0]
           
       
        

        # 创建MinMaxScaler对象
        scaler = MinMaxScaler()

       

        # 使用fit_transform方法对DataFrame进行归一化
        y_attrs_normalize = scaler.fit_transform(np.array(y_attrs.values))
        
        
        for idx,indicator in enumerate(y_attrs.columns):
            y_attrs[f"{indicator}_normalize"] = y_attrs_normalize[:,idx]
        
        for indicator_down in self.indicators.get("down",[]):
            y_attrs[f"{indicator_down}_normalize"] = 1 - y_attrs[f"{indicator_down}_normalize"]
            
        y = y_attrs.loc[:,list(filter(lambda col_name:"normalize" in col_name, y_attrs.columns))].values
        
        weights_y = []
        for column_name in y_attrs.columns:
            for type_indicator,indicators_ in self.indicators.items():
                if column_name in indicators_.keys():
                    weights_y.append(indicators_[column_name])
        y = np.array([np.sum(weights_y*y) for y in y])            
        

        y_attrs["y"] = y       
        
        assert not y_attrs.isna().any().any(), "Y contain NAN !!"
        
        
        
        
        x_dummys = x_attrs.loc[:,self.features["data_int"]]
        x_dummys = x_dummys.astype(int)
    
        
        encoders = {}
        for feature_name in self.features["str"]:
            x = x_attrs[feature_name]
            enc = OneHotEncoder()          # 初始化
            enc.fit(x_attrs[[feature_name]].values)    # 模型拟合。注意：data[['一键三连']]是一个dataframe，与data['一键三连']是一个series不同
            array_data = enc.transform(x_attrs[[feature_name]].values).toarray()
            encoders[feature_name] = enc
            for idx in range(array_data.shape[1]):
                x_dummys[f"{feature_name}_transformed_{idx}"] = array_data[:,idx]

       
        x = x_dummys.values
        assert not x_dummys.isna().any().any(), "X contain NAN !!"
        
        if (self.normalize):
            from sklearn.preprocessing import StandardScaler
            normalizer = StandardScaler()
            normalizer = normalizer.fit(x)
            x = normalizer.transform(x)
            
        else:
            normalizer = None
        
        configs_cache = {}
        x_ex_map = {}
        
        for ex_name in matrix["ex_name"].value_counts().index.to_list():
            ex_idxs = matrix[matrix["ex_name"] == ex_name]["ex_idx"]
            for ex_idx in ex_idxs:
                x_ex_map[int(ex_idx)] = ex_name
            configs = x_attrs.iloc[ex_idx,:].to_dict()
            configs_cache[ex_name] = {
                "configs":configs,
                "ex_idx":ex_idxs            
            }
        
        debug_df = pd.DataFrame()
        for used_ex_name in used_ex_names:
            indexs = configs_cache[used_ex_name]["ex_idx"]
            worst_index = indexs[0]
            for index in indexs:
                if (y_attrs.loc[index,"y"] < y_attrs.loc[worst_index,"y"]):
                    worst_index = index
            debug_df.loc[used_ex_name,"y"] = y_attrs.loc[worst_index,"y"]

        optimize_ex_indexs = configs_cache[optimized_ex_name]["ex_idx"]
        best_index = optimize_ex_indexs[0]
        for index in optimize_ex_indexs:
            if (y_attrs.loc[index,"y"] > y_attrs.loc[worst_index,"y"]):
                best_index = index
        debug_df.loc[optimized_ex_name,"y"] = y_attrs.loc[best_index,"y"]
        file_path = os.path.join(optimize_log_dir,
                                "round_0",
                                "debug_used_data_2.csv")
        debug_df.to_csv(file_path)
            
    
    def fit(self,
            tasks_dir = "LLM_PublicHouseAllocation/tasks",
            fit_round = 0,
            run_every_gen = False):
        
        # 创建DEAP种群
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", np.ndarray, fitness=creator.FitnessMax)

        toolbox = base.Toolbox()
        
        # 注册自定义的初始化方法
        toolbox.register("individual", tools.initIterate, creator.Individual, self.generate_x)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)
        toolbox.register("init_population",
                         self.initilize_population, 
                         list, 
                         creator.Individual, 
                         custom_array = self.x_used)

       
        
        # 注册自定义适应度评估函数
        toolbox.register("evaluate", self.evaluate_individual)       
        toolbox.register("mate", tools.cxTwoPoint)
        toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=0.2, indpb=0.2)
        toolbox.register("select", tools.selTournament, tournsize=3)

        # 创建种群并运行遗传算法
        if fit_round == 0:
            population = toolbox.init_population()
            population_add = toolbox.population(n = self.population_size)
            population.extend(population_add)
            random.shuffle(population)
            
        else:
            population = self.population
            
        fits = toolbox.map(toolbox.evaluate, population)
        for fit, ind in zip(fits, population):
            ind.fitness.values = fit
        
        NGEN = self.generations # 迭代次数

        
        
        for gen in range(NGEN):
            # 这步是为了处理连续值的问题，但是现在filter了子代以后没有这个问题了
            # self.refine_regressor(population) 
            
            # 打印每代的最优解和目标函数值
            
            best_ind = tools.selBest(population, k=1)[0]
            if run_every_gen:
                configs = self.decode_x(best_ind)
                print(f"第 {gen+1} 代的最优解：{best_ind}")
                print("最优解：", configs)
                config_name, runned_before = self.update_config(configs=configs,tasks_dir=tasks_dir)
                max_retry = 3
                for _ in range(max_retry):
                    try:
                        queue = multiprocessing.Queue()
                        # 创建进程
                        process = multiprocessing.Process(target=long_running_task,kwargs={"config_name":config_name,
                                                                                        "use_cache":True,
                                                                                        "queue":queue,
                                                                                        "optimizer":self},)

                        # 执行进程并设置超时
                        run_with_timeout(process, 3*60*60) #这个进程最长允许的运行时间为3h，否则kill
                        
                        if process.exitcode == 0:
                            # 从队列中获取返回值
                            return_values = queue.get()
                            print("代码执行完成")
                            break
                        else:
                            return_values = None
                            print("代码执行被终止")
                            continue

                    except TimeoutException as e:
                        print(e)
                        return_values = None
                        continue
                if return_values is not None:
                    simulate_x_array, simulate_y_array, x_attrs, y_attrs = return_values
                    self.configs_cache[config_name] = {
                        "configs":configs,
                        "ex_idx": x_attrs.index.tolist()
                    }
                    self.x = np.concatenate([self.x,simulate_x_array],axis = 0)
                    self.y = np.concatenate([self.y,simulate_y_array],axis = 0)     
                    
                    self.x_attrs = pd.concat([self.x_attrs,
                                            x_attrs],axis = 0)
                    self.y_attrs = pd.concat([self.y_attrs,
                                            y_attrs],axis = 0)
                    
                    
                    for ex_idx in x_attrs.index:
                        self.x_ex_map[int(ex_idx)] = config_name
                        
                    self.optimize_names.append([config_name,simulate_y_array.tolist()])

                    self.optimize_log["genetic_offsprings"] = self.optimize_names
            
            
            print(f"第 {gen+1} 代的最优解的目标函数值：{best_ind.fitness.values[0]}")

            self.best_offsprings.append(best_ind)
                    
            offspring = algorithms.varAnd(population, toolbox, cxpb=0.7, mutpb=0.8)
            
            offspring = list(map(self.filter_x_vector,offspring))
            offspring = [creator.Individual(offspring_) for offspring_ in offspring]
            fits = toolbox.map(toolbox.evaluate, offspring)
            
            for fit, ind in zip(fits, offspring):
                ind.fitness.values = fit
            population = offspring
          
          
        fits = toolbox.map(toolbox.evaluate, self.best_offsprings)
        for fit, ind in zip(fits, self.best_offsprings):
            ind.fitness.values = fit 
            
        best_of_all_y = self.best_offsprings[0].fitness.values[0]
        best_of_all_ind = self.best_offsprings[0]
        for best_ind in self.best_offsprings[1:]:
            if best_ind.fitness.values[0] > best_of_all_y:
                best_of_all_ind = best_ind
                best_of_all_y = best_ind.fitness.values[0]
                
        configs = self.decode_x(best_of_all_ind)
        print(f"全局最优x：{best_of_all_ind}")
        print(f"全局最优解：{configs}", )
        print(f"全局最优解的目标函数值：{best_of_all_ind.fitness.values[0]}")
        
        self.population = population
        
        config_name, runned_before = self.update_config(configs=configs,tasks_dir=tasks_dir)
        return  config_name, \
                runned_before, \
                self.encode_x(np.array(list(configs.values()))),\
                configs
                
        
    def debug_csv(self, 
                  df_debug_path ="",
                  save = True,
                  used_data = False) -> pd.DataFrame:
        
        y = self.y
        if used_data:
            x_attrs = self.x_attrs.loc[self.used_index]
           
        else:
            x_attrs = self.x_attrs
            
        debug_df = pd.DataFrame(x_attrs)
        # assert y.shape[0] == x_attrs.shape[0],"Error shape!"
        
        assert not x_attrs.index.duplicated().any(), "Error index!!"
        
        for ex_idx in x_attrs.index:
            config_dict = x_attrs.loc[ex_idx,:].to_dict()
            encoded_vector = self.encode_x(np.array(list(config_dict.values())))
            predict_y = self.regressor_model.predict([encoded_vector])[0]
            gt_y = y[ex_idx]
            debug_df.loc[ex_idx,"gt_y"] = gt_y
            debug_df.loc[ex_idx,"predict_y"] = predict_y
            debug_df.loc[ex_idx,"gap_y"] = abs(gt_y - predict_y)
            
                
        """debug"""
        if save:
            debug_df.to_csv(df_debug_path)
        return debug_df
