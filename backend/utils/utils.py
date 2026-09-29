import asyncio
import inspect

async def run_with_timeout(func, *args, timeout_seconds=10, **kwargs):
    try:
        if inspect.iscoroutinefunction(func):
            return await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=timeout_seconds
            )
        else:
            return await asyncio.wait_for(
                asyncio.to_thread(func, *args, **kwargs),
                timeout=timeout_seconds
            )
    except asyncio.TimeoutError:
        print(f"Request timed out after {timeout_seconds} seconds")
        return None
