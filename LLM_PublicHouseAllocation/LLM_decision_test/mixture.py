"""这个脚本将人类标注的内容 和 机器生成的内容进行混合
"""

import os
import json
import random

human_label_root = "LLM_PublicHouseAllocation/LLM_decision_test/data_label/result_labeled"
bot_root = "LLM_PublicHouseAllocation/LLM_decision_test/data_bot"

saving_QA = []

human_label_dirs = os.listdir(human_label_root)
for hl_dir in human_label_dirs:
    with open(os.path.join(human_label_root,hl_dir),'r',encoding = 'utf-8') as f:
        QA_result = json.load(f)
    saving_QA.extend(QA_result)
    
bot_dirs = os.listdir(bot_root)
for bot_dir in bot_dirs:
    with open(os.path.join(bot_root,bot_dir),'r',encoding = 'utf-8') as f:
        QA_result = json.load(f)
    for data in QA_result:
        data["humanjudge"]=False
    saving_QA.extend(QA_result)
    
for i in range(5):    
    random.shuffle(saving_QA)
with open("LLM_PublicHouseAllocation/LLM_decision_test/test/saving_QA.json", 'w', encoding='utf-8') as file:
    json.dump(saving_QA, file, indent=4,separators=(',', ':'),ensure_ascii=False)
    