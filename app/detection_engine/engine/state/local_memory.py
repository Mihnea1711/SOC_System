import time
from typing import Any, Optional, Dict

from .base import StateStore

class LocalMemoryStore(StateStore):
    """
    An implementation of StateStore using local memory via the cachetools library.
    
    Note: Since cachetools.TTLCache requires a fixed TTL at initialization, 
    we use a dictionary of caches to support different TTLs dynamically, 
    or we implement a custom wrapper. For simplicity and robustness in this SOC,
    we will use a single large TTLCache and manage the expiration manually 
    if a specific TTL is requested, or just rely on a default global TTL.
    
    For true per-key TTL in local memory, we wrap values with an expiry timestamp.
    """
    
    def __init__(self, maxsize: int = 10000):
        # We use a standard dict but wrap values with expiry times
        self._store: Dict[str, Dict[str, Any]] = {}
        self._maxsize = maxsize

    def _cleanup(self):
        """Removes expired keys to prevent memory leaks."""
        now = time.time()
        keys_to_delete = [k for k, v in self._store.items() if v['expires_at'] < now]
        for k in keys_to_delete:
            del self._store[k]
            
        # Enforce maxsize (crude FIFO eviction if too large)
        if len(self._store) > self._maxsize:
            # Delete oldest 10%
            sorted_keys = sorted(self._store.keys(), key=lambda k: self._store[k]['expires_at'])
            for k in sorted_keys[:int(self._maxsize * 0.1)]:
                if k in self._store:
                    del self._store[k]

    def get(self, key: str) -> Optional[Any]:
        self._cleanup()
        item = self._store.get(key)
        if item and item['expires_at'] > time.time():
            return item['value']
        return None

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        self._cleanup()
        self._store[key] = {
            'value': value,
            'expires_at': time.time() + ttl_seconds
        }

    def increment(self, key: str, amount: int = 1, ttl_seconds: int = 60) -> int:
        self._cleanup()
        item = self._store.get(key)
        now = time.time()
        
        if item and item['expires_at'] > now:
            # Key exists and is valid
            item['value'] += amount
            # Extend TTL
            item['expires_at'] = now + ttl_seconds
            return item['value']
        else:
            # Key doesn't exist or expired
            self._store[key] = {
                'value': amount,
                'expires_at': now + ttl_seconds
            }
            return amount

    def add_to_set(self, key: str, value: Any, ttl_seconds: int = 60) -> int:
        self._cleanup()
        item = self._store.get(key)
        now = time.time()
        
        if item and item['expires_at'] > now and isinstance(item['value'], set):
            item['value'].add(value)
            item['expires_at'] = now + ttl_seconds
            return len(item['value'])
        else:
            self._store[key] = {
                'value': {value},
                'expires_at': now + ttl_seconds
            }
            return 1

    def delete(self, key: str) -> None:
        if key in self._store:
            del self._store[key]
