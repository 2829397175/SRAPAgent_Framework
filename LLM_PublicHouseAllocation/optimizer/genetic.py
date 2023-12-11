
from .base import BaseOptimizer

from . import policy_optimizer_registry

import numpy as np
import random
from typing import Any
from deap import base, creator, tools, algorithms

import os

@policy_optimizer_registry.register("genetic_algorithm")
class Genetic_algorithm_Optimizer(BaseOptimizer):
    
    # 为了计算遗传算法中的适应度，训练的回归模型
    regressor_model: Any
    
    # 遗传算法参数
    population_size = 50
    generations = 10
    crossover_prob = 0.7
    mutation_prob = 0.2
     
    def prepare_individual_regressor(self):# 给定X，训练一个可以给出对应y值的模型
        #scikit-learn LinearModel predict
        from sklearn.linear_model import LinearRegression
        lin_reg=LinearRegression()
        lin_reg.fit(self.x,self.y)
        self.regressor_model = lin_reg
    
   
    
    # 定义适应度函数
    def evaluate_individual(self,individual):
        # 将个体的基因编码（例如：二进制）解码为x的值
        y_value = self.regressor_model.predict([individual])[0]
        y_values = self.weights_y*y_value
        return (np.sum(y_values),) 

   
    def generate_x(self):
        random_values = [self.x_attrs[column].sample().values[0] for column in self.x_attrs.columns]
        x_encoded = self.encode_x(np.array(random_values))
        return x_encoded
    
    def fit(self,tasks_dir = "LLM_PublicHouseAllocation/tasks"):
        self.prepare_individual_regressor()
        
        # 创建DEAP种群
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", np.ndarray, fitness=creator.FitnessMax)

        toolbox = base.Toolbox()
        # 注册自定义的初始化方法
        toolbox.register("individual", tools.initIterate, creator.Individual, self.generate_x)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)



        # 创建种群
        population = toolbox.population(n = self.population_size)

       
        
        # 注册自定义适应度评估函数
        toolbox.register("evaluate", self.evaluate_individual)       
        toolbox.register("mate", tools.cxTwoPoint)
        toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=0.2, indpb=0.2)
        toolbox.register("select", tools.selTournament, tournsize=3)

        # 创建种群并运行遗传算法
        population = toolbox.population(n=self.population_size)
        NGEN = self.generations # 迭代次数

        best_of_all = {"best_ind_y" : 0}
        for gen in range(NGEN):

            offspring = algorithms.varAnd(population, toolbox, cxpb=0.7, mutpb=0.2)
            fits = toolbox.map(toolbox.evaluate, offspring)
            for fit, ind in zip(fits, offspring):
                ind.fitness.values = fit
            population = offspring

            # 打印每代的最优解和目标函数值
            best_ind = tools.selBest(population, k=1)[0]
            print(f"第 {gen+1} 代的最优解：{best_ind}")
            print("最优解：", self.decode_x(best_ind))
            print(f"第 {gen+1} 代的最优解的目标函数值：{best_ind.fitness.values[0]}")
            if best_of_all["best_ind_y"] <best_ind.fitness.values[0]:
                best_of_all ={
                    "best_ind_y" :best_ind.fitness.values[0],
                    "best_ind":best_ind
                }
        best_ind = best_of_all["best_ind"]
        configs = self.decode_x(best_ind)
        print(f"第 {gen+1} 代的最优解：{best_ind}")
        print(f"最优解：{configs}", )
        print(f"第 {gen+1} 代的最优解的目标函数值：{best_ind.fitness.values[0]}")
        
        self.update_config(configs=configs,tasks_dir=tasks_dir)

    