import asyncio


async def p(x):
    print(x)

async def say(what, when):
    await asyncio.gather(*[p(what)for i in range(when)])


loop = asyncio.get_event_loop()
loop.run_until_complete(say('hello world', 3))
print("1")
loop.close()
print("2")
