import openai

apis =[
    # "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",
    "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"]


import os

for api in apis:
    openai.api_key = api

    completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a poetic assistant, skilled in explaining complex programming concepts with creative flair."},
        {"role": "user", "content": "Compose a poem that explains the concept of recursion in programming."}
    
    ]
    )

    print(completion.choices[0].message,api)