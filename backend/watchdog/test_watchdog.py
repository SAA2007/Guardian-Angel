import os
import sys

def main():
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if root not in sys.path:
        sys.path.insert(0, root)

    from backend.watchdog.lock import PersistenceLock
    from backend.watchdog.disable_flow import DisableFlow

    print("--- Watchdog & Persistence Test ---")
    data_dir = os.path.join(root, "data")
    
    # Test lock
    lock = PersistenceLock(data_dir=data_dir)
    lock.set_mode("timed", 7)
    lock.start_lock()
    
    print(f"is_locked(): {lock.is_locked()} (should be True)")
    print(f"get_remaining_seconds(): {lock.get_remaining_seconds()} (should be ~604800)")
    
    lock.unlock()
    print(f"is_locked() after unlock: {lock.is_locked()} (should be False)")
    
    # Test disable flow
    flow = DisableFlow(lock=lock, stats_manager=None)
    result = flow.start()
    print(f"Disable flow state: {result.get('state')} (should be WAITING)")
    
    print("Watchdog/persistence test complete.")

if __name__ == "__main__":
    main()
