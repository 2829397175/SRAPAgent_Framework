
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

tenant_infos={
    "Oliver":{
        "role":"You are Oliver, and the people living with you include your wife, your child, who is about to start elementary school. Your wife takes care of the child at home and handles the purchase of daily necessities, while you are responsible for working at a company in the city center to earn money and support the family."
    }
}

import re    
def seach_house(house_index):
    choose_housing_idx= re.search("([0-9]+)",str(house_index),re.I | re.M)
    if choose_housing_idx is not None:
        choose_housing_idx = choose_housing_idx.group(1)
    house_info=house_infos.get("house_{}".format(choose_housing_idx),
                           False)
    if house_info:
        return house_info.get("feature")
    else:
        return "no useful information"
    
    
def search_tenant(name):
    role_info=tenant_infos.get(name,False)
    if role_info:
        return role_info.get("role")
    else:
        return "no useful information"

    
tools = [
    Tool(
        name = "Search_House",
        func=seach_house,
        description="Help you get information of houses."
    ),
    Tool(
        name = "Search_Tenant",
        func=search_tenant,
        description="Help you get information of yourself.")
    ]

tools = [   ]

# Set up the base template
template = """
You are Oliver, and the people living with you include your wife, your child, who is about to start elementary school. Your wife takes care of the child at home and handles the purchase of daily necessities, while you are responsible for working at a company in the city center to earn money and support the family.
You're planning to choose one house.
There are {num_houses} houses available. The infomation of these houses are listed as follows:
{houses} 

- If you have decided which house to choose, you must conclude this public housing rental process!!

Use the following format:

Task: the task you need to accomplish.
Thought: (Your views on given houses)
Action: Choose
Final Answer: My choice is house (the index of house.) 


These were previous tasks you completed:

Begin!

Task: {input}
{agent_scratchpad}"""

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
        regex = r"Action\s*\d*\s*:(.*?)\nAction\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)"
        match = re.search(regex, llm_output, re.DOTALL)
        if not match:
            raise ValueError(f"Could not parse LLM output: `{llm_output}`")
        action = match.group(1).strip()
        action_input = match.group(2)
        # Return the action and action input
        return AgentAction(tool=action, tool_input=action_input.strip(" ").strip('"'), log=llm_output)
    
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
        intermediate_steps = kwargs.pop("intermediate_steps")
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += action.log
            thoughts += f"\nObservation: {observation}\nThought: "
        # Set the agent_scratchpad variable to that value
        kwargs["agent_scratchpad"] = thoughts
        # Create a tools variable from the list of tools provided
        
        kwargs["num_houses"] = len(house_infos)
        houses_str = [
            "house {index} has {feature}".format(index=house_idx,
                                                 feature=house_info.get("feature"))
            for house_idx,house_info in house_infos.items()
        ]
        houses_str="\n".join(houses_str)
        kwargs["houses"] = houses_str
        formatted = self.template.format(**kwargs)
        return [HumanMessage(content=formatted)]

# LLM chain consisting of the LLM and a prompt
prompt = CustomPromptTemplate(
    template=template,
    tools=tools,
    # This omits the `agent_scratchpad`, `tools`, and `tool_names` variables because those are generated dynamically
    # This includes the `intermediate_steps` variable because that is needed
    input_variables=["input", "intermediate_steps"]
)
OPENAI_API_KEY = "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"
llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, temperature=0)
llm_chain = LLMChain(llm=llm, prompt=prompt)

tool_names = [tool.name for tool in tools]
agent = LLMSingleActionAgent(
    llm_chain=llm_chain, 
    output_parser=output_parser,
    stop=["\nObservation:"], 
    allowed_tools=tool_names
)


agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True)
agent_executor.run("Choose one house.")