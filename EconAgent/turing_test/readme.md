## 数据集格式

dict 结构：
- data: 保存tenantal_system.json


list结构:
- data_label: 人类标注需要的数据（response为空的数据）
    - result_labeled : 保存经过人类标注的qa 数据 turingflag = True
    - qa_clear_data: 保存清空response的qa数据 
- data_bot: 保存机器生成response的qa数据 
- test: 保存 result_labeled 和 data的混合数据


`data_old_house_descrip 是保存的 community 旧版本format的数据`