
from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent, AgentOutputParser
from langchain.prompts import BaseChatPromptTemplate
from langchain import SerpAPIWrapper, LLMChain
from langchain.chat_models import ChatOpenAI
from typing import List, Union
from langchain.schema import AgentAction, AgentFinish, HumanMessage
import re
from getpass import getpass



house_infos={"house_1":
    {"feature": "a good layout with 1 bedroom, \
     1 living room, and 1 bathroom, featuring a square-shaped design and \
     excellent north-south ventilation. Secondly, the facilities are well-equipped, \
     with a subway station, bus stop, and large shopping mall conveniently located nearby."},
    "house_2":{"feature": "2 bedrooms and 1 bathroom. \
               It is located on the 9th floor and enjoys an \
               unobstructed cityscape view. It faces south, \
               providing ample sunlight and a comfortable, pleasant living environment. \
            The kitchen has a window, facilitating ventilation and odor dispersal. \
            There is also a window in the bathroom, allowing for the dissipation of any unpleasant odors. "} }

houses_types_global={"small_house":{
  "index":["house_3"],
  "mean_cost":8000,
  "mean_size":100
},
  "mid_house":{
  "index":["house_1","house_2"],
  "mean_cost":4000,
  "mean_size":65},
  "large_house":{
  "index":["house_4"],
  "mean_cost":3000,
  "mean_size":40}
}


community_global={
"community_1":{
  "location":"The community is located in the southeast corner of the city（所有小区位于同一个区，不存在跨区问题，location问题可以商讨）",
  "surroundings": "The friendhood offers a variety of amenities, including cafes, restaurants, schools,and parks, all within 2km.（简单描述周围环境，中立性描述，不带情感色彩）",
  "value_inch":20,
    **houses_types_global
}
}




tenant_infos={
    "Oliver":{
        "role":"You are Oliver, and the people living with you include your wife, your child, who is about to start elementary school. Your wife takes care of the child at home and handles the purchase of daily necessities, while you are responsible for working at a company in the city center to earn money and support the family."
    }
}


tools = [   ]

# Set up the base template
template = """
{role_description}

    You're planning to choose one house. In order to choose a house that satisfies you, you need to {input}. 

    {house_description}
    
    - If you made up your choice, respond in this format:
    Thought: ({thought_type})
    Action: Choose
    Action Input: My choice is ({choose_type}).
    
    - If you chose none of them, respond in this format:
    Thought: ({thought_type})
    Action: Choose
    Action Input: I choose none of these houses.
    

    - You must follow the following format with two fields "Action" and "Action Input" for your response in ANY case
    Thought: (your thought)
    Action: (an action name, it can be one of [Choose])
    Action Input: (argument for the action)

    Here is the thinking history
    {agent_scratchpad}

    Here is the conversation history
    {chat_history}"""
    
template = """
{role_description}

    You need to make some comments on the following objects:

    {house_description}
    
    - Respond in the following format:
    Thought: (Your thought on the objects)
    Action: Comment
    Action Input: (the comments of all the objects)
    
    Here is the history
    {agent_scratchpad}
    """
    
template = """
{role_description}

    Your goal is to rent one house. For now, You can take one action at a time, should be one of [{action_names}]
    
    - If you want to search house info from forum, respond in this format:
    Action: Search
    
    - If you want to publish house info on forum, respond in this format:
    Action: Publish
    
    - If you want to discuss with other people about house renting, respond in this format:
    Action: GroupDiscuss
    
    - If you want to do nothing, respond in this format:
    Action: Giveup
    
    Here is the history
    {agent_scratchpad}
    """
    
template = """
{role_description}

    Your goal is to rent one house. For now, You can take one action at a time, should be one of [{action_names}]
    
    You have access to the following tools:

    1. Search: search house info from forum
    2. Publish: publish house info on forum
    3. GroupDiscuss: discuss with other people about house renting
    4. Giveup: do nothing
    
    Give your response in the following format:

    Thought: you should always think about what to do
    Action: the action to take, should be one of [{action_names}]
    
    Here is the history
    {agent_scratchpad}"""
    
# template = """
# {role_description}

#     Your goal is to rent one house. For now, you want to discuss with some acquaintances.
    
#     Your acquaintances include:
#     Ross: friend
#     Julie: friend
#     Gloria: friend
#     Carol: friend
    
#     - Here's one example:
    
#     Your acquaintances include:
#     Jake: friend
#     Jane: friend
#     Bob: friend
#     Sarah: friend
    
#     Thought: I think house price is important, house_10000 is cheap
#     Action: GroupDiscuss
#     Friends: Jane, Jake, Bob
#     Action Input: house_10000 is cheap, we can consider this one
    
#     - Respond in this format:
#     Thought: you should always think about what to do
#     Action: GroupDiscuss
#     Friends: (friend names)
#     Action Input: (info you want to tell your friend)
    
#     Here is the history
#     {agent_scratchpad}
    
#     Respond:
#     """


class CustomOutputParser(AgentOutputParser):
    
    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        # Check if agent should finish
        if "Final Answer:" in llm_output:
            return AgentFinish(
                # Return values is generally always a dictionary with a single `output` key
                # It is not recommended to try anything else at the moment :)
                return_values={"output": llm_output.split("Final Answer:")[-1].strip()},
                log=llm_output,
            )
        # Parse out the action and action input
        # regex = r"Action\s*\d*\s*:(.*?)\nAction\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)"
        # match = re.search(regex, llm_output, re.DOTALL)
        # if not match:
        #     raise ValueError(f"Could not parse LLM output: `{llm_output}`")
        # action = match.group(1).strip()
        # action_input = match.group(2)
        # if action == "Choose":
        #     return AgentFinish(return_values={"output":action_input.strip(" ").strip('"')},
        #                        log=llm_output)
        # # Return the action and action input
        # return AgentAction(tool=action, tool_input=action_input.strip(" ").strip('"'), log=llm_output)
        
        # regex = r"Action\s*\d*\s*:(.*?)Friends\s*\d*\s*:(.*?)Action\s*\d*\s*Input\s*\d*\s*:(.*)"
        regex = r"Action\s*\d*\s*:(.*)"
        match = re.search(regex, llm_output, re.DOTALL)
        if not match:
            raise ValueError(f"Could not parse LLM output: `{llm_output}`")
        action = match.group(1).strip()

        # Return the action and action input
        return AgentAction(tool=action, tool_input="", log=llm_output)
    
output_parser = CustomOutputParser()

# Set up a prompt template
class CustomPromptTemplate(BaseChatPromptTemplate):
    # The template to use
    template: str
    # The list of tools available
    tools: List[Tool]
    
    

    
    def format_messages(self, **kwargs) -> str:
        # Get the intermediate steps (AgentAction, Observation tuples)
        # Format them in a particular way
        # intermediate_steps = kwargs.pop("intermediate_steps")
        # thoughts = ""
        # for action, observation in intermediate_steps:
        #     thoughts += action.log
        #     thoughts += f"\nObservation: {observation}\nThought: "
        # # Set the agent_scratchpad variable to that value
        # kwargs["agent_scratchpad"] = thoughts
        # Create a tools variable from the list of tools provided
        
        
        formatted = self.template.format(**kwargs)
        return [HumanMessage(content=formatted)]

# LLM chain consisting of the LLM and a prompt
prompt = CustomPromptTemplate(
    template=template,
    tools=tools,
    # This omits the `agent_scratchpad`, `tools`, and `tool_names` variables because those are generated dynamically
    # This includes the `intermediate_steps` variable because that is needed
    input_variables=[
                     "role_description",
                     "agent_scratchpad",
                    # "intermediate_steps",
                     "action_names",
                    #  "house_description",
                    #  "thought_type",
                    #  "choose_type",
                    #  "chat_history"
                    ]
)
OPENAI_API_KEY = "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"
llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY,
                 temperature=0)


llm_chain = LLMChain(llm=llm, prompt=prompt)


# llm_chain.run()

tool_names = [tool.name for tool in tools]
agent = LLMSingleActionAgent(
    llm_chain=llm_chain, 
    output_parser=output_parser,
    stop=["\nObservation:"], 
    allowed_tools=tool_names
)


agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True)
# agent_executor.run("Choose one house.")
input_arguments = {}

# input_arguments['input']  = 'You need to choose one type of house.'
# input_arguments['thought_type']  = 'your views on these house types.'
# input_arguments['choose_type'] = 'the index of house types'
# input_arguments['house_types'] = houses_types_global
# input_arguments['chat_history'] = ""
# input_arguments['role_description'] = "You are Oliver, and the people living with you include your wife, your child, who is about to start elementary school. Your wife takes care of the child at home and handles the purchase of daily necessities, while you are responsible for working at a company in the city center to earn money and support the family."


len_house = len(house_infos)
houses_str = [
    "house {index} has {feature}".format(index=house_idx,
                                            feature=house_info.get("feature"))
    for house_idx,house_info in house_infos.items()
]
houses_str="\n".join(houses_str)
houses_describe_prompt="There are {num_houses} houses available. The infomation of these houses are listed as follows:\n{houses} "
str_house_description = houses_describe_prompt.format(num_houses=len_house,
                                                    houses=houses_str)
        

# input_arguments['input']  = 'You need to choose one type of house.'
# input_arguments['thought_type']  = 'your views on these houses.'
# input_arguments['choose_type'] = 'the index of house'
# input_arguments['house_description'] = str_house_description
input_arguments['action_names'] = "Search, Publish, GroupDiscuss, Giveup"

# input_arguments['chat_history'] = ""
input_arguments['role_description'] = "You are Oliver, and the people living with you include your wife, your child, who is about to start elementary school. Your wife takes care of the child at home and handles the purchase of daily necessities, while you are responsible for working at a company in the city center to earn money and support the family."
input_arguments['agent_scratchpad'] = "Thought: I need to search some info.\nAction: Search\nObservation: I have searched some info on forum"
agent_executor.run(input_arguments)