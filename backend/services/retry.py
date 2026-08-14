import asyncio
import logging
from typing import Callable, TypeVar, Any

logger = logging.getLogger(__name__)
T = TypeVar("T")


async def with_exponential_retry(
    coro_func: Callable[..., Any],
    *args,
    max_retries: int = 3,
    initial_delay: float = 0.5,
    backoff_factor: float = 2.0,
    **kwargs
) -> Any:
    delay = initial_delay
    last_exception = None
    for attempt in range(1, max_retries + 1):
        try:
            return await coro_func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            logger.warning(f"Operation failed on attempt {attempt}/{max_retries}: {str(e)}")
            if attempt == max_retries:
                raise last_exception
            await asyncio.sleep(delay)
            delay *= backoff_factor
