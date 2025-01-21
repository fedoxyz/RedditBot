from functools import wraps
import threading
from typing import List, Any, Callable
from logger import logger
import time

def thread_safe(f: Callable) -> Callable:
    """
    Decorator to make a method thread-safe using a lock.
    Each instance will have its own lock.
    """
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, '_locks'):
            self._locks = {}
        if f.__name__ not in self._locks:
            self._locks[f.__name__] = threading.Lock()
            
        with self._locks[f.__name__]:
            return f(self, *args, **kwargs)
    return wrapper

def with_retry(max_retries: int = 3, delay: float = 1.0) -> Callable:
    """
    Decorator to add retry functionality to methods.
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(f"Attempt {attempt + 1} failed for {f.__name__}: {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))
            
            logger.error(f"All {max_retries} attempts failed for {f.__name__}")
            raise last_exception
        return wrapper
    return decorator

def run_in_threads(objects: List[Any], method, synchronize: bool = False, *args, **kwargs):
    """
    Run a method on multiple objects in parallel.
    Returns list of successful objects.
    """
    if not isinstance(objects, list):
        objects = [objects]
        
    threads = []
    successful = []
    failed = []
    thread_lock = threading.Lock()
    barrier = threading.Barrier(len(objects)) if synchronize else None
    
    def thread_func(obj):
        try:
            if isinstance(method, str):
                # Get method by name and run it
                method_to_call = getattr(obj, method)
                method_to_call(*args, **kwargs)
            else:
                # Direct callable
                method(obj, *args, **kwargs)
            
            with thread_lock:
                successful.append(obj)
                
            if synchronize and barrier:
                try:
                    barrier.wait(timeout=30)  # Add timeout to prevent hanging
                except threading.BrokenBarrierError:
                    pass  # Ignore barrier errors to allow continued execution
                
        except Exception as e:
            logger.error(f"Error in thread for {getattr(obj, 'username', 'unknown')}: {str(e)}")
            with thread_lock:
                failed.append(obj)
    
    # Start all threads without delay between them
    for obj in objects:
        thread = threading.Thread(target=thread_func, args=(obj,))
        thread.start()
        threads.append(thread)
    
    # Wait for completion if synchronized
    if synchronize:
        for thread in threads:
            thread.join(timeout=30)  # Add timeout to prevent hanging
    
    return successful
