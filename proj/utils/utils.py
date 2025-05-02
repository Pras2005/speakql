import asyncio

async def run_with_timeout(func,*args,timeout_seconds =10,**kwargs):
    try:
        return await asyncio.wait_for(
                asyncio.to_thread(func,*args,**kwargs),
                timeout =timeout_seconds
                )
    except asyncio.TimeoutError:
        print(f"request timed out after{timeout_seconds}")
        return None
