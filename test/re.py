# text = """Thought: I should compare all the options to make a wise decision.
# Acquaintance: James Anderson
# Output: Hi James, let's compare all the houses in the community_2 together and discuss the pros and cons before making the final decision. 

# Thought: I need to tell Emma the truth.
# Acquaintance: Emma Davis
# Output: Hi Emma, I think the houses in community_2 offer the best options for us and our family. Let's patiently research the area and talk to people in the know before making a decision.
# """

import re
# regex = r"Thought\s*\d*\s*:(.*?)\nAcquaintance\s*\d*\s*:(.*?)\nOutput\s*\d*\s*:(.*?)\n"
# match = re.search(regex, text, re.DOTALL)

# output_results=list(match.groups())

# matchs = re.findall(regex, text, re.DOTALL)
# return_values={"communication":[]} # 返回一个和各个熟人的交流结果

# for id_g in range(int(len(output_results)/3)):
#     communication={
#         "thought":output_results[id_g*3],
#         "acquaintance_names":output_results[id_g*3+1],
#         "output":output_results[id_g*3+2].strip(),
#     }

#     return_values["communication"].append(communication)


# text ="""Words to say to A: 23333"""

# output = re.sub('Words to say to .*?:','',text,flags=re.IGNORECASE)
# output
content = "My choice is S."
a =re.search(".*?choice.*?is (.*)",str(content),re.I | re.M)
li = [1,2,3]
while len(li)>0:
    print(li[0])
    li.pop(0)