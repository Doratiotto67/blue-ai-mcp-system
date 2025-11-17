import traceback, sys, asyncio, os
sys.path.append('/app')
from app import get_imports

async def main():
    try:
        r = await get_imports('react')
        print('ok', len(str(r)))
    except Exception as e:
        traceback.print_exc()

asyncio.run(main())