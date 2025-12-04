"""
Unit Tests for Lamport Logical Clock Implementation
=====================================================

Tests the distributed timestamp ordering algorithm required for COEN 317.
"""

import pytest
import threading
import time
from backend.libs.timestamps import (
    LamportClock,
    create_timestamped_event,
    process_received_event,
    order_events
)


def test_lamport_clock_initialization():
    """Test that clock initializes correctly"""
    clock = LamportClock("node-1")
    assert clock.node_id == "node-1"
    assert clock.get_current() == 0


def test_lamport_clock_send_event():
    """Test that sending event increments clock"""
    clock = LamportClock("node-1")
    
    ts1 = clock.send_event()
    assert ts1["clock"] == 1
    assert ts1["node_id"] == "node-1"
    
    ts2 = clock.send_event()
    assert ts2["clock"] == 2
    assert ts2["node_id"] == "node-1"


def test_lamport_clock_receive_event():
    """Test that receiving event updates clock correctly"""
    clock = LamportClock("node-1")
    
    # Initial state
    assert clock.get_current() == 0
    
    # Receive event with timestamp 5
    received_ts = {"clock": 5, "node_id": "node-2"}
    new_clock = clock.receive_event(received_ts)
    
    # Clock should be max(0, 5) + 1 = 6
    assert new_clock == 6
    assert clock.get_current() == 6


def test_lamport_clock_receive_lower_timestamp():
    """Test receiving event with lower timestamp"""
    clock = LamportClock("node-1")
    
    # Send events to advance clock
    clock.send_event()  # clock = 1
    clock.send_event()  # clock = 2
    clock.send_event()  # clock = 3
    
    # Receive event with lower timestamp
    received_ts = {"clock": 1, "node_id": "node-2"}
    new_clock = clock.receive_event(received_ts)
    
    # Clock should be max(3, 1) + 1 = 4
    assert new_clock == 4


def test_lamport_clock_compare_timestamps():
    """Test comparing two Lamport timestamps"""
    clock = LamportClock("node-1")
    
    ts1 = {"clock": 1, "node_id": "node-1"}
    ts2 = {"clock": 2, "node_id": "node-2"}
    ts3 = {"clock": 2, "node_id": "node-3"}
    
    # ts1 happened before ts2
    assert clock.compare_timestamps(ts1, ts2) == -1
    
    # ts2 happened after ts1
    assert clock.compare_timestamps(ts2, ts1) == 1
    
    # ts2 and ts3 have same clock - use node_id for ordering
    result = clock.compare_timestamps(ts2, ts3)
    assert result != 0  # Should have deterministic order


def test_lamport_clock_thread_safety():
    """Test that clock is thread-safe"""
    clock = LamportClock("node-1")
    results = []
    
    def send_events(n):
        for _ in range(n):
            ts = clock.send_event()
            results.append(ts["clock"])
    
    # Create multiple threads
    threads = []
    for i in range(5):
        t = threading.Thread(target=send_events, args=(10,))
        threads.append(t)
        t.start()
    
    # Wait for all threads
    for t in threads:
        t.join()
    
    # Should have 50 timestamps (5 threads * 10 events)
    assert len(results) == 50
    
    # All timestamps should be unique
    assert len(set(results)) == 50
    
    # Final clock should be 50
    assert clock.get_current() == 50


def test_create_timestamped_event():
    """Test creating an event with timestamp"""
    event = {
        "event_id": "E1",
        "title": "Test Event",
        "topic": "hackathon"
    }
    
    timestamped = create_timestamped_event(event, "node-1")
    
    # Should have all original fields plus timestamp
    assert timestamped["event_id"] == "E1"
    assert timestamped["title"] == "Test Event"
    assert "lamport_timestamp" in timestamped
    assert timestamped["lamport_timestamp"]["node_id"] == "node-1"
    assert timestamped["lamport_timestamp"]["clock"] > 0


def test_process_received_event():
    """Test processing a received event"""
    event = {
        "event_id": "E1",
        "lamport_timestamp": {"clock": 10, "node_id": "node-2"}
    }
    
    processed = process_received_event(event, "node-1")
    
    # Should have processed_at_lamport field
    assert "processed_at_lamport" in processed
    assert processed["processed_at_lamport"] == 11  # max(0, 10) + 1


def test_order_events():
    """Test ordering events by Lamport timestamp"""
    events = [
        {
            "event_id": "E3",
            "lamport_timestamp": {"clock": 5, "node_id": "node-1"}
        },
        {
            "event_id": "E1",
            "lamport_timestamp": {"clock": 2, "node_id": "node-2"}
        },
        {
            "event_id": "E2",
            "lamport_timestamp": {"clock": 3, "node_id": "node-3"}
        }
    ]
    
    ordered = order_events(events)
    
    # Should be ordered by clock value
    assert ordered[0]["event_id"] == "E1"  # clock 2
    assert ordered[1]["event_id"] == "E2"  # clock 3
    assert ordered[2]["event_id"] == "E3"  # clock 5


def test_order_events_empty_list():
    """Test ordering empty list"""
    ordered = order_events([])
    assert ordered == []


def test_order_events_without_timestamps():
    """Test ordering events without timestamps (should use default)"""
    events = [
        {"event_id": "E1"},
        {"event_id": "E2"}
    ]
    
    ordered = order_events(events)
    assert len(ordered) == 2


def test_distributed_scenario():
    """
    Test a realistic distributed scenario:
    - Node 1 sends event A
    - Node 2 sends event B
    - Node 1 receives B, then sends event C
    - Node 2 receives A and C
    
    Should maintain causal ordering: A -> B -> C
    """
    clock1 = LamportClock("node-1")
    clock2 = LamportClock("node-2")
    
    # Node 1 sends event A
    ts_a = clock1.send_event()  # clock1 = 1
    assert ts_a["clock"] == 1
    
    # Node 2 sends event B (independent)
    ts_b = clock2.send_event()  # clock2 = 1
    assert ts_b["clock"] == 1
    
    # Node 1 receives B
    clock1.receive_event(ts_b)  # clock1 = max(1, 1) + 1 = 2
    
    # Node 1 sends event C (causally after B)
    ts_c = clock1.send_event()  # clock1 = 3
    assert ts_c["clock"] == 3
    
    # Node 2 receives A and C
    clock2.receive_event(ts_a)  # clock2 = max(1, 1) + 1 = 2
    clock2.receive_event(ts_c)  # clock2 = max(2, 3) + 1 = 4
    
    # Events should be ordered: A (1, node-1), B (1, node-2), C (3, node-1)
    events = [
        {"event_id": "A", "lamport_timestamp": ts_a},
        {"event_id": "C", "lamport_timestamp": ts_c},
        {"event_id": "B", "lamport_timestamp": ts_b}
    ]
    
    ordered = order_events(events)
    
    # A and B both have clock=1, so ordering by node_id
    # C has clock=3, so it should be last
    assert ordered[2]["event_id"] == "C"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])



