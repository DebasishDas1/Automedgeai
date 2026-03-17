import time
import hashlib
import threading
from typing import Any, Optional

class InMemoryCache:
    def __init__(self):
        self._cache = {}
        self._lock = threading.Lock()

    def _get_key(self, prefix: str, data: Any) -> str:
        # Simple hash-based key
        serialized = str(data).encode()
        return f"{prefix}:{hashlib.md5(serialized).hexdigest()}"

    def get(self, prefix: str, data: Any) -> Optional[Any]:
        key = self._get_key(prefix, data)
        with self._lock:
            if key in self._cache:
                val, expiry = self._cache[key]
                if expiry is None or expiry > time.time():
                    return val
                del self._cache[key]
        return None

    def set(self, prefix: str, data: Any, value: Any, ttl: int = 3600):
        key = self._get_key(prefix, data)
        expiry = time.time() + ttl if ttl else None
        with self._lock:
            self._cache[key] = (value, expiry)
            # Basic cleanup of expired items on set
            if len(self._cache) > 1000:
                now = time.time()
                self._cache = {k: v for k, v in self._cache.items() if v[1] is None or v[1] > now}

cache = InMemoryCache()
