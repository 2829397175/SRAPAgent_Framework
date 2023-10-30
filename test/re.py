# text = """Thought: I should compare all the options to make a wise decision.
# Acquaintance: James Anderson
# Output: Hi James, let's compare all the houses in the community_2 together and discuss the pros and cons before making the final decision. 

# Thought: I need to tell Emma the truth.
# Acquaintance: Emma Davis
# Output: Hi Emma, I think the houses in community_2 offer the best options for us and our family. Let's patiently research the area and talk to people in the know before making a decision.
# """

import re

import requests

requests.get()
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
regex = r"Rating\s*\d*\s*:(.*?)Reason\s*\d*\s*:(.*)\n"
llm = """Rating:
house_18: 7
house_19: 8

Reason:
Both house_18 and house_19 are priced similarly and have similar square footage, orientation (NS), and the presence of an elevator. However, house_19 stands out with a slightly higher rating due to its location on the 15th floor, which offers better views and potentially more natural light. Additionally, house_19 is described as having a well-designed layout for efficient use of space, which adds to its appeal. Both houses enjoy a favorable south-facing orientation and offer good green views of the community, making them suitable for comfortable living."""
llm +="\n"

output = re.search(regex,llm,re.I|re.S)

rating = output.group(1).strip()
reason = output.group(2).strip()

rating = rating.split("\n")
rating =  [rating_one.split(":") for rating_one in rating]

for rating_one in rating:
    rating_one[1] = re.search("([0-9]+)",str(rating_one[1]),re.I | re.M).groups()[0]
    rating_one[1] = int(rating_one[1])