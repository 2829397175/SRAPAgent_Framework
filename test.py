from sklearn.preprocessing import Normalizer,StandardScaler
import numpy as np

# 创建一个Normalizer实例
normalizer = StandardScaler()

# 原始二维数组
original_data = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])

# 使用Normalizer进行归一化
normalized_data = normalizer.fit_transform(original_data)

# # 假设要还原的行数据
# row_to_restore = normalized_data

# # 获取原始二维数组的'L1'范数
# l1_norms = np.linalg.norm(original_data, axis=1, ord=1)

# # 将归一化的数据行除以'L1'范数以还原行数据
# restored_row = row_to_restore * l1_norms

print("原始二维数组:")
print(original_data)

print("归一化后的数据:")
print(normalized_data)

print("还原的行数据:")
print(normalizer.inverse_transform(normalized_data))
