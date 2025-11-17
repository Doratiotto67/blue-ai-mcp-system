import sys
import os
import asyncio

sys.path.append('.')
sys.path.append('agents/common')

from llm_router import LLMRouter, Message

async def test_glm():
    router = LLMRouter()
    print('OPENROUTER_API_KEY configured:', bool(os.environ.get('OPENROUTER_API_KEY', '')))
    try:
        resp = await router.call_glm46(
            messages=[
                Message(role='system', content='Você é um assistente de código.'),
                Message(role='user', content='Escreva uma função Python que soma uma lista de números.')
            ],
            temperature=0.1,
            max_tokens=256
        )
        print('GLM-4.6 response length:', len(resp))
        print('GLM-4.6 snippet:', resp[:300].replace('\n', ' '))
    except Exception as e:
        print('GLM-4.6 error:', type(e).__name__, str(e)[:500])


async def main():
    mode = os.environ.get('LLM_TEST_MODE', 'glm')
    if mode in ('glm', 'both'):
        await test_glm()
    # modo 'gemini' não é suportado

if __name__ == '__main__':
    asyncio.run(main())