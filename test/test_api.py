import openai
from langchain.llms import OpenAI   
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os
import asyncio
from langchain.chat_models import ChatOpenAI

# apis =["sk-H3ENZsWqvSKnlb88A329FeEbCb6745D7A6E25eA71287E95d",
#     "sk-1TSrETkbF3yOSFeo51E36d199dF04038B6900314Aa475b5e",
#     "sk-LJQomCIuhDuqTu0EA9C634F05a0646F99f743204BeE9B2B7",
#     "sk-fc1wKOWUqic07eWN8159EcA20f0c40299a8e2552F34d2e3a",
#     "sk-Hsyu43W1aJROiSTH3eAe26F219E24992B47b098b00E324A2",
#     "sk-dCzZFatXAVVSW067D1333fC17b8f4c5e95076f9bA113805c"  ]
# api_base = os.environ.get("OPENAI_API_BASE","https://api.aiguoguo199.com/v1")

apis =[ "sk-UduOWZ3yEtC9mFxy52397cB469884a288f6dC565Fd33377d",
            "sk-amdLfnPdvaGhKQNO729a88A09aAd45C98b31D6Fb2c5a923f",
            "sk-IBDKadyW7ri8QTRJEdA4F5C9694d40138b5f0d1e43FcE52d"]

async def test_chain(apis):
    template="""
        Transfer the following context into Simplified Chinese:
        {english_text}
        
        Here's your translation:
    """  
    
    english_text = "hello"
    for api in apis:
        # llm = OpenAI(model_name = "text-davinci-003",
        #                 verbose = False,
        #                 temperature = 0.8,
        #                 openai_api_base=api_base,
        #                 openai_api_key= api)
        
        llm = ChatOpenAI(model_name="gpt-3.5-turbo-16k-0613",
                       verbose = False,
                       max_tokens = 500,
                       openai_api_key=api
                       )  
        input_variables=["english_text"]
        prompt = PromptTemplate(  
            input_variables=input_variables,  
            template=template,  
        )
        chain = LLMChain(llm=llm, prompt=prompt)
        chinese_text = await chain.arun(english_text=english_text)
        print(chinese_text.strip(),
              api)
    
def test_api(apis):


    for api in apis:
        openai.api_key = api
        # openai.api_base =api_base
        completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k-0613",
        messages=[
            {"role": "system", "content": "You are a poetic assistant, skilled in explaining complex programming concepts with creative flair."},
            {"role": "user", "content": "Compose a poem that explains the concept of recursion in programming."}
        
        ]
        )

        print(completion.choices[0].message,api)
        
def test_api_2():
    import requests

    url = 'http://23.224.131.195:5000/v1/chat/completions'
    header = {
        'Authorization': 'Bearer sk-VBGPQ5lsOj5ZjGPhk0vYD1yCyVjwc7',
        'Content-Type': 'application/json'
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": "你是谁",
        "stream": False
    }
    resp = requests.post(url, headers=header, json=data, stream=True)
    text = resp.json()
    print(text)



test_api(apis)
# asyncio.run(test_chain(apis))