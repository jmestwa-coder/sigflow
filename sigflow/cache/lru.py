from collections import OrderedDict
from threading import Lock


class LRUCache:
    """Thread-safe Least-Recently-Used cache implementation.
    
    Uses a Lock to ensure all operations (get, set, len) are atomic and safe
    for concurrent access from multiple threads. The lock serializes access
    to the underlying OrderedDict to prevent data corruption, eviction races,
    and concurrent modification errors.
    
    Args:
        capacity: Maximum number of items to cache (must be > 0)
    """
    def __init__(self, capacity: int = 1024):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self._data = OrderedDict()
        self._lock = Lock()

    def get(self, key, default=None):
        with self._lock:
            if key not in self._data:
                return default
            self._data.move_to_end(key)
            return self._data[key]

    def set(self, key, value) -> None:
        with self._lock:
            self._data[key] = value
            self._data.move_to_end(key)
            while len(self._data) > self.capacity:
                self._data.popitem(last=False)

    def __len__(self):
        with self._lock:
            return len(self._data)
