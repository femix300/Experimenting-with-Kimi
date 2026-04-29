"""
Resilience utilities for EdgeIQ:
- Retry decorator with exponential backoff
- Token bucket rate limiter
- Request queuing for burst scenarios
- Function invocation time monitoring
"""
import time
import functools
import threading
from collections import deque
from typing import Optional, Callable, Any
import logging

logger = logging.getLogger(__name__)


class TokenBucket:
    """Token bucket rate limiter for API calls."""

    def __init__(self, rate: float = 10, capacity: int = 20):
        """
        Args:
            rate: Tokens added per second
            capacity: Maximum bucket capacity
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self._lock = threading.Lock()

    def acquire(self, tokens: int = 1, block: bool = True, timeout: Optional[float] = None) -> bool:
        """Acquire tokens. Returns True if acquired, False otherwise."""
        start = time.time()
        while True:
            with self._lock:
                now = time.time()
                elapsed = now - self.last_update
                self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
                self.last_update = now

                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True

            if not block:
                return False

            if timeout and (time.time() - start) > timeout:
                return False

            time.sleep(0.05)


class RequestQueue:
    """Simple request queue for burst management."""

    def __init__(self, max_concurrent: int = 5, max_queue_size: int = 100):
        self.max_concurrent = max_concurrent
        self.max_queue_size = max_queue_size
        self.active = 0
        self.queue: deque = deque()
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)

    def submit(self, fn: Callable, *args, **kwargs) -> Any:
        """Submit a function for execution. Blocks if queue is full."""
        with self._lock:
            if len(self.queue) >= self.max_queue_size:
                raise Exception("Request queue is full")
            self.queue.append((fn, args, kwargs))
            self._condition.notify()

        with self._lock:
            while self.active >= self.max_concurrent:
                self._condition.wait(timeout=30)

        with self._lock:
            if self.queue:
                self.active += 1
                fn, args, kwargs = self.queue.popleft()

        try:
            return fn(*args, **kwargs)
        finally:
            with self._lock:
                self.active -= 1
                self._condition.notify()


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 10.0,
                       exceptions: tuple = (Exception,)):
    """Retry decorator with exponential backoff."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        logger.warning(f"Retry {attempt + 1}/{max_retries} for {func.__name__}: {e}. Waiting {delay}s")
                        time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator


def monitor_execution(max_duration: float = 15.0):
    """Monitor function execution time. Alert if exceeds threshold."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start
                if duration > max_duration:
                    logger.warning(f"SLOW FUNCTION: {func.__name__} took {duration:.1f}s (threshold: {max_duration}s)")
                else:
                    logger.info(f"Function {func.__name__} completed in {duration:.1f}s")
                return result
            except Exception as e:
                duration = time.time() - start
                logger.error(f"Function {func.__name__} failed after {duration:.1f}s: {e}")
                raise
        return wrapper
    return decorator


# Global rate limiter for Bayse API (10 requests per second)
bayse_rate_limiter = TokenBucket(rate=10, capacity=20)

# Global request queue for burst management
bayse_request_queue = RequestQueue(max_concurrent=5, max_queue_size=100)
