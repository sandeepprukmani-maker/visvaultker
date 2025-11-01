import asyncio
from functools import wraps
from typing import List, Callable, Any
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=10)

def run_in_executor(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, lambda: func(*args, **kwargs))
    return wrapper

async def run_sync_in_async(func: Callable, *args, **kwargs) -> Any:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, lambda: func(*args, **kwargs))
