import asyncio
import structlog
from typing import Callable, Any
from concurrent.futures import ThreadPoolExecutor

logger = structlog.get_logger(__name__)

class ToolExecutor:
    # Class-level thread pool for sync tools to prevent thread explosion per-request
    _pool = ThreadPoolExecutor(max_workers=32)

    @classmethod
    async def execute(
        cls, 
        tool_name: str, 
        func: Callable, 
        *args, 
        timeout: float = 12.0, 
        **kwargs
    ) -> Any:
        # Request-local tracking for isolation
        log = logger.bind(tool=tool_name)
        
        try:
            if asyncio.iscoroutinefunction(func):
                # Async tool: just wait for it
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
            else:
                # Sync tool: offload to the shared thread pool to avoid blocking the event loop
                loop = asyncio.get_running_loop()
                return await asyncio.wait_for(
                    loop.run_in_executor(cls._pool, lambda: func(*args, **kwargs)),
                    timeout=timeout
                )
        except Exception as e:
            log.error("tool_execution_failed", error=str(e))
            return {"error": str(e), "success": False}

tool_executor = ToolExecutor()
