"""Thread-safety tests for LRUCache concurrent access patterns."""

import threading
from sigflow.cache.lru import LRUCache


def test_lru_thread_safety():
    """Verify LRUCache is safe for concurrent access from multiple threads.
    
    Tests that:
    - No data corruption occurs during concurrent set/get operations
    - Values retrieved match values stored
    - Eviction doesn't cause race conditions or KeyError exceptions
    - Cache remains consistent under concurrent load
    """
    cache = LRUCache(50)
    errors = []
    
    def worker(thread_id):
        """Worker thread that performs concurrent cache operations."""
        try:
            for i in range(200):
                key = f"t{thread_id}_k{i}"
                value = f"v{thread_id}_{i}"
                
                # Concurrent set operations
                cache.set(key, value)
                
                # Concurrent get operations
                retrieved = cache.get(key)
                if retrieved != value:
                    errors.append(
                        f"Thread {thread_id}: Data mismatch for {key}. "
                        f"Expected {value}, got {retrieved}"
                    )
                
                # Also test getting other keys (cache hits/misses)
                other_key = f"t{(thread_id + 1) % 5}_k{i}"
                cache.get(other_key)
                
        except Exception as exc:
            errors.append(f"Thread {thread_id}: {type(exc).__name__}: {exc}")
    
    # Launch 10 concurrent threads
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # Verify no errors occurred
    assert not errors, f"Thread safety violations:\n" + "\n".join(errors)


def test_lru_concurrent_len():
    """Verify __len__() is thread-safe during concurrent modifications."""
    cache = LRUCache(100)
    lengths = []
    
    def reader():
        """Continuously read cache length."""
        for _ in range(100):
            lengths.append(cache.__len__())
    
    def writer():
        """Continuously modify cache."""
        for i in range(100):
            cache.set(f"key_{i}", f"value_{i}")
    
    threads = [
        *[threading.Thread(target=reader) for _ in range(3)],
        *[threading.Thread(target=writer) for _ in range(3)],
    ]
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # All length reads should have succeeded without error
    assert len(lengths) == 300


def test_lru_eviction_race():
    """Test that eviction under concurrent load doesn't cause corruption."""
    cache = LRUCache(10)  # Small capacity to force evictions
    errors = []
    
    def aggressive_writer(thread_id):
        """Aggressively write to trigger evictions."""
        try:
            for i in range(500):
                cache.set(f"t{thread_id}_k{i}", i)
        except Exception as exc:
            errors.append(f"Thread {thread_id} write error: {exc}")
    
    def aggressive_reader(thread_id):
        """Aggressively read during eviction."""
        try:
            for i in range(500):
                cache.get(f"t{(thread_id - 1) % 5}_k{i}")
        except Exception as exc:
            errors.append(f"Thread {thread_id} read error: {exc}")
    
    threads = [
        *[threading.Thread(target=aggressive_writer, args=(i,)) for i in range(5)],
        *[threading.Thread(target=aggressive_reader, args=(i,)) for i in range(5)],
    ]
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # Should complete without crashes or data corruption
    assert not errors, f"Eviction race condition:\n" + "\n".join(errors)
