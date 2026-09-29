import asyncio
import inspect
import logging

logger = logging.getLogger(__name__)


async def run_with_timeout(func, *args, timeout_seconds=10, **kwargs):
    """
    Runs a sync or async function with a timeout.
    Returns None if the timeout is exceeded.
    """
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
        logger.warning("Request timed out after %s seconds", timeout_seconds)
        return None
