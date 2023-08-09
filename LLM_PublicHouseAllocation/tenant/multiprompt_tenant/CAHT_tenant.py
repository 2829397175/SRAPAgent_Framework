from langchain.base_language import BaseLanguageModel
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from typing import Dict
from LLM_PublicHouseAllocation.memory import ActionHistoryMemory
from LLM_PublicHouseAllocation.output_parser import OutputParseError

import re
import LLM_PublicHouseAllocation.map as map
from LLM_PublicHouseAllocation.tenant.multiprompt_tenant.base import BaseMultiPromptTenant
from LLM_PublicHouseAllocation.tenant.multiprompt_tenant import multiprompt_tenant_registry as MultiPromptTenantRegistry




@MultiPromptTenantRegistry.register("CAHT")
class CAHTTenant(BaseMultiPromptTenant):
    id: int
    name: str
    role_description: str  # 角色描述，里面主要是描述agent不变的信息
    memory: ActionHistoryMemory
    choose_times: int = 0  # 剩余选择次数
    max_choose_time: int = 3  # 最大选择次数
    available: bool = True  # 是否选择过房子
    max_retry: int = 6  # 访问api
    max_jug_time : int = 3 # 错误结果的retry次数
    workplace: str  # 用来记录工作点的中文名
    # 这个是为了更改llm_chain
    llm: BaseLanguageModel
    prompt: Dict

    def __init__(self, agentrule ,**kwargs):
        super().__init__(agentrule=agentrule, **kwargs)

    # 更新tenant剩余次数
    def update_times(self, chose=False):
        if chose:
            self.available = False
        else:
            self.choose_times += 1
            if (self.choose_times >= self.max_choose_time):
                self.available = False

    # community_infos表示所有的社区名和社区位置的list，forum_data表示论坛所有的信息
    def collect_information(self, community_infos, forum_data):
        collect_info={}
        for community_info in community_infos:
            collect_info[community_info["community_name"]]={}
            collect_info[community_info["community_name"]]["comment_summary"] = self.produce_forum_summary(community_info["community_name"],
                                                                           self.agentrule.read_forum(forum_data,
                                                                                                   community_info[
                                                                                                       "community_name"]))
            collect_info[community_info["community_name"]]["get_shortest_commute_time"] = map.baidumap.get_shortest_commute_time(self.workplace,
                                                                                                 community_info[
                                                                                                     "location"])
        return collect_info
    def summary_collect_info(self,community_infos,collect_info):
        community_infoss = community_infos.copy()
        for community in community_infoss:
            if community["community_name"] in collect_info:
                community["comment_summary"] = collect_info[community["community_name"]]["comment_summary"]
                community["get_shortest_commute_time"] = collect_info[community["community_name"]]["get_shortest_commute_time"]
        return community_infoss

    def community_str(self,curcommunity_list,furcommunity_list):
        len_curcommunity= len(curcommunity_list)
        len_furcommunity = len(furcommunity_list)
        template = """\
                                {community_id}. {community_name} is located at {en_location}. The rent for this community is {value_inch} dollars per square meter. {get_shortest_commute_time_str}.\
                                In this community, {description}. {nearby_info}.My comment after watching the community forum is that {comment_summary}.\
                            """
        housetype_template = """
                                        The {housetype} in this community is a {living_room} apartment, with an area of about {size}, the monthly rent  is about {cost} dollars, and there are still {remain_number} houses.
                                     """
        curcommunity_description = ""
        furcommunity_description = ""
        for community_info in curcommunity_list:
            curcommunity_description += template.format(community_id=community_info["community_id"],
                                                     community_name=community_info["community_name"],
                                                     en_location=community_info["en_location"],
                                                     value_inch=community_info["value_inch"],
                                                     description=community_info["description"],
                                                     get_shortest_commute_time_str=community_info[
                                                         "get_shortest_commute_time"],
                                                     nearby_info=community_info["nearby_info"],
                                                     comment_summary=community_info["comment_summary"]
                                                     )
            house_types = ['small_house', 'middle_house', 'large_house']
            house_typs=[]
            for house_type in house_types:
                if house_type in community_info:
                    curcommunity_description += housetype_template.format(housetype=house_type,
                                                                       living_room=community_info[house_type][
                                                                           "living_room"],
                                                                       size=community_info[house_type]["size"],
                                                                       cost=community_info[house_type]["cost"],
                                                                       remain_number=community_info[house_type][
                                                                           "remain_number"]
                                                                       )
                    house_typs.append(house_type)
            house_type_describe_prompt = "There are {num_house_type} room types in this community,including {house_type}. The infomation of room types are listed as follows:\n{room_type}"
            house_type_describe=house_type_describe_prompt.format(num_house_type=len(house_typs),house_type=",".join(house_typs),room_type=curcommunity_description)
            house_type_describe += "\n"

        curcommunitys_describe_prompt = "There are {num_communitys} communities available. The infomation of these communitys are listed as follows:\n{communitys}"
        curstr = curcommunitys_describe_prompt.format(num_communitys=len_curcommunity,
                                                                      communitys=curcommunity_description)

        for furcommunity_info in furcommunity_list:
            furcommunity_description += template.format(community_id=furcommunity_info["community_id"],
                                                     community_name=furcommunity_info["community_name"],
                                                     en_location=furcommunity_info["en_location"],
                                                     value_inch=furcommunity_info["value_inch"],
                                                     description=furcommunity_info["description"],
                                                     get_shortest_commute_time_str=furcommunity_info[
                                                         "get_shortest_commute_time"],
                                                     nearby_info=furcommunity_info["nearby_info"],
                                                     comment_summary=furcommunity_info["comment_summary"]
                                                     )
            house_types = ['small_house', 'middle_house', 'large_house']
            house_typs = []
            for house_type in house_types:
                if house_type in furcommunity_info:
                    furcommunity_description += housetype_template.format(housetype=house_type,
                                                                       living_room=furcommunity_info[house_type][
                                                                           "living_room"],
                                                                       size=furcommunity_info[house_type]["size"],
                                                                       cost=furcommunity_info[house_type]["cost"],
                                                                       remain_number=furcommunity_info[house_type][
                                                                           "remain_number"]
                                                                       )
                    house_typs.append(house_type)
            house_type_describe_prompt = "There are {num_house_type} room types in this community,including {house_type}. The infomation of room types are listed as follows:\n{room_type}"
            house_type_describe = house_type_describe_prompt.format(num_house_type=len(house_typs),
                                                                    house_type=",".join(house_typs),
                                                                    room_type=furcommunity_description)
            house_type_describe += "\n"


        furcommunitys_describe_prompt = "There are {num_communitys} communities that will be released in the future . The infomation of these communitys are listed as follows:\n{communitys}"
        furstr = furcommunitys_describe_prompt.format(num_communitys=len_furcommunity,
                                                                      communitys=furcommunity_description)
        return curstr,furstr
    # 选择小区户型，输入
    def choose_community(self, house_info, house_future_info):
        house_info, house_future_info=self.community_str(house_info, house_future_info)
        choose_state,community_name, house_type, reason=False,"","","I don't think any of these communities or house types are right for me"
        for i in range(self.max_retry):
            try:
                response = self.chain(self.prompt['choose_community']).run(role_description=self.role_description,
                                                                           choose_num=self.choose_times,
                                                                           house_info=house_info,
                                                                           house_future_info=house_future_info,
                                                                           )
                if response == "" or response.isspace():
                    continue
                parse_bool,choose_state,community_name, house_type, reason=self.choose_community_extract_info(response)
                if not parse_bool:
                    response=self.chain(self.prompt['correct_choose_community']).run(response=response)
                    parse_bool,choose_state,community_name, house_type, reason=self.choose_community_extract_info(response)
                if response != "" and (not response.isspace()) and parse_bool==True :
                    break
            except OutputParseError as e:
                print(e)
                print("Retrying...")
                continue
        if response is None:
            raise ValueError(f"{self.name} failed to generate valid response.")
        return choose_state,community_name, house_type, reason

    # 选择房子
    def choose_house(self, availablehouse_info):
        house_info_description = self.agentrule.read_house_list(availablehouse_info)
        choose_state,house_id, reason=False,"","I don't think any of these  \houses are right for me"
        for i in range(self.max_retry):
            try:
                response = self.chain(self.prompt['choose_house']).run(role_description=self.role_description,
                                                                       house_info=house_info_description)
                if response=="" or response.isspace():
                    continue
                parse_bool,choose_state,house_id, reason=self.choose_house_extract_info(response)
                if not parse_bool:
                    response=self.chain(self.prompt['correct_choose_house']).run(response=response)
                    parse_bool,choose_state,house_id, reason=self.choose_house_extract_info(response)
                if response != "" and (not response.isspace()):
                    break
            except OutputParseError as e:
                print(e)
                print("Retrying...")
                continue
        if response is None:
            raise ValueError(f"{self.name} failed to generate valid response.")
        return choose_state,house_id, reason

    # 产生评论
    def produce_comment(self, community_description, house_description, potential_information_house):
        for i in range(self.max_retry):
            try:
                response = self.chain(self.prompt['comment']).run(role_description=self.role_description,
                                                                  community_description=community_description,
                                                                  house_description=house_description,
                                                                  potential_information_house=potential_information_house)
               # print("produce_comment: " + response)
                if response != "" and (not response.isspace()):
                    break
            except OutputParseError as e:
                print(e)
                print("Retrying...")
                continue
        if response is None:
            raise ValueError(f"{self.name} failed to generate valid response.")
        return response.replace("\n","").strip()

    # 对论坛评论生成总结
    def produce_forum_summary(self, community_name, forum_info):
        forum_info=forum_info.strip()
        if forum_info == "":
            return "Community " + community_name + " has no comments ."


        for i in range(self.max_retry):
            try:
                response = self.chain(self.prompt['forum']).run(role_description=self.role_description,
                                                                community_name=community_name,
                                                                forum_comments=forum_info
                                                                )
                if response != "" and (not response.isspace()):
                    break
            except OutputParseError as e:
                print(e)
                print("Retrying...")
                continue
        if response is None:
            raise ValueError(f"{self.name} failed to generate valid response.")
        return response.replace("\n","").strip()

    # 第一个bool是判断是否解析成功，第二个是判断是否选择
    def choose_community_extract_info(self, input_string):
        input_string = input_string.strip()
        community_name = ''
        house_type = ''
        reason = ''

        # Define the patterns for the two expected formats
        choose_pattern = r".*?Action: Choose\s*Result:\s*'?.*?My choice is (?:the )?\[?((?:large|middle|small)\s?\w+)\]? in (?:the )?\[?(\w+)\]?.*?'?\s*Reason: (.+)$"
        not_choose_pattern = r".*?Action: Not Choose\s*Result: (.+)\s*Reason：(.+)$"

        # Try to match the input_string with the first format
        match = re.search(choose_pattern, input_string, re.MULTILINE | re.IGNORECASE)
        if match:
            house_type = match.group(1).replace(" ", "_")  # replace the space with an underscore
            community_name = match.group(2)
            reason = match.group(3)
            return True, True, community_name, house_type, reason

        # Try to match the input_string with the second format
        match = re.search(not_choose_pattern, input_string, re.MULTILINE | re.IGNORECASE)
        if match:
            reason = match.group(2)
            return True, False, community_name, house_type, reason

        # If the input_string does not match any of the expected formats
        return False, False, community_name, house_type, reason

    #第一个bool是判断是否解析成功，第二个是判断是否选择
    def choose_house_extract_info(self,input_string):
        input_string = input_string.strip()
        house_id = ''
        reason = ''

        # Define the patterns for the two expected formats
        choose_pattern = r".*?Action: Choose\s*Result:\s*'?.*My choice is(?: the)? house\s?_?(\d+).*'?\s*Reason: (.+)$"
        not_choose_pattern = r".*?Action: Not Choose\s*Result: (.+)\s*Reason：(.+)$"

        # Try to match the input_string with the first format
        match = re.search(choose_pattern, input_string, re.MULTILINE | re.IGNORECASE)
        if match:
            house_id = 'house_' + match.group(1)
            reason = match.group(2)
            return True, True, house_id, reason

        # Try to match the input_string with the second format
        match = re.search(not_choose_pattern, input_string, re.MULTILINE | re.IGNORECASE)
        if match:
            reason = match.group(2)
            return True, False, house_id, reason
        return False, False, house_id, reason

    def chain(self, prompt: PromptTemplate, verbose: bool = False) -> LLMChain:
            return LLMChain(
                llm=self.llm, prompt=prompt, verbose=verbose
            )

    def choose(self,forum_manager, system, log_round):

        community_list = system.community_manager.get_available_community_info()

        community_available_description = "There are {available_community_num} communities that have not been allocated yet.The infomation of these communitys are listed as follows:\n{communitys}"
        community_available_description_template = " {id}.There are {sum_remain_house} houses in {community_name}."
        housetype_available_description_template = "There are {remain_house} houses of {house_type}."
        communitys = ""
        id = 1
        for community in community_list:
            communitys_str = community_available_description_template.format(id=1, sum_remain_house=community[
                "sum_remain_num"], community_name=community["community_name"])
            communitys += communitys_str
            id += 1
            for housetype, housetype_att in list(community.items()):
                if isinstance(housetype_att, dict) and 'remain_number' in housetype_att:
                    house_str = housetype_available_description_template.format(
                        remain_house=housetype_att["remain_number"], house_type=housetype)
                    communitys += house_str
            communitys += "\n"
        log_round["community_available_description"] = community_available_description.format(
            available_community_num=len(community_list), communitys=communitys)

        collect_info = self.collect_information(community_list, forum_manager.data)


        # forum_conclusion
        forum_conclusion = ""
        forum_info_template = "The summary of comments for {community_name} is that {summary}.\n"
        for community_name, community_attr in list(collect_info.items()):
            forum_conclusion += forum_info_template.format(community_name=community_name,
                                                           summary=community_attr["comment_summary"])
        log_round["forum_conclusion"] = forum_conclusion

        #
        community_infoss = self.summary_collect_info(community_list, collect_info)
        cur_info, fur_info = system.community_manager.split(community_infoss)
        jug_community_housetype_state=False
        for i in range(self.max_jug_time):
            choose_community_state, choose_community_name, choose_house_type, choose_community_thought = self.choose_community(
                cur_info, fur_info)
            if choose_community_state==False and choose_community_name=="" and choose_house_type=="":
                break
            jug_community_housetype_state=system.community_manager.jug_community_housetype_valid(choose_community_name,choose_house_type)
            if jug_community_housetype_state:
                break
        if jug_community_housetype_state==False:
            choose_community_state, choose_community_name, choose_house_type, choose_community_thought=False,"","","I don't think any of these communities or house types are right for me"



        log_round["choose_community_id"] = choose_community_name
        log_round["choose_house_type"] = choose_house_type
        log_round["choose_community_reason"] = choose_community_thought
        log_round["choose_house_type_reason"] = "None"

        # 这里只改housemanager中的available标签
        if (choose_community_state):

            housedic = system.house_manager.get_available_houses(choose_community_name, choose_house_type)

            house_info_description = "{house_id}: The house is a {house_type} with an area of {house_area} square meters and a monthly rent of {rent_money} yuan." \
                                     "It {balcony} a balcony and {elevator} an elevator. " \
                                     "It's on the {floor}th floor. Its description is that {description}"
            housedes_list = []
            for house_id, house_info in housedic.items():
                h = house_info_description.format(house_id=house_id,
                                                  house_type=house_info["house_type"],
                                                  house_area=house_info["house_area"],
                                                  rent_money=house_info["rent_money"],
                                                  balcony=house_info["balcony"],
                                                  elevator=house_info["elevator"],
                                                  floor=house_info["floor"],
                                                  description=house_info["description"],
                                                  )
                housedes_list.append(h.replace("\n", ""))
            log_round["house_available_description"] = housedes_list

            jug_house_state = False
            for i in range(self.max_jug_time):
                choose_house_state, choose_house_id, choose_house_thought = self.choose_house(housedic)
                if choose_house_state==False and choose_house_id=="":
                    break
                jug_house_state = system.house_manager.jug_house_valid(choose_house_id)
                if jug_house_state:
                    break
            if jug_house_state == False:
                choose_house_state, choose_house_id, choose_house_thought = False, "", "I don't think any of these houses are right for me"
            log_round["choose_house_id"] = choose_house_id
            log_round["choose_house_reason"] = choose_house_thought

            if choose_house_state:
                community_description = system.community_manager.update_remain_num(choose_community_name,
                                                                                      choose_house_id)

                house_description, house_potential_information_house = system.house_manager.set_chosed_house(
                    choose_house_id)

                comment = self.produce_comment(community_description, house_description,
                                                 house_potential_information_house)

                log_round["choose_house_state"] = True
                log_round["produce_comment"] = comment

                forum_manager.add_comment(self.name, choose_community_name, comment)
                self.update_times(chose=True)
                return True
            else:
                self.update_times()

                log_round["choose_house_state"] = False
                log_round["produce_comment"] = "None"
                return False
        else:
            log_round["choose_house_state"] = False
            log_round["house_available_description"] = []
            log_round["choose_house_id"] = ""
            log_round["choose_house_reason"] = "I don't think any of these communities or houses are right for me"

            self.update_times()
            return False



    def update_memory(self, response):
        pass

    def reset(self):
        pass
