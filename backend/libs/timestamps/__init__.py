"""
Lamport Logical Clock Implementation
=====================================

Provides distributed timestamp ordering for events in the pub/sub system.
Ensures causally related events are ordered correctly across distributed nodes.

Algorithm:
- Each node maintains a local counter
- On send: increment counter, attach to message
- On receive: update counter to max(local, received) + 1

This satisfies the requirement for distributed timestamp algorithms in COEN 317.
"""

import threading
from typing import Dict, Any


class LamportClock:
    """
    Thread-safe Lamport logical clock implementation.
    
    Usage:
        clock = LamportClock(node_id="dispatcher-1")
        
        # When sending event
        timestamp = clock.send_event()
        
        # When receiving event
        clock.receive_event(received_timestamp)
    """
    
    def __init__(self, node_id: str):
        """
        Initialize Lamport clock for a distributed node.
        
        Args:
            node_id: Unique identifier for this node (e.g., "dispatcher-1")
        """
        self.node_id = node_id
        self._counter = 0
        self._lock = threading.Lock()
    
    def send_event(self) -> Dict[str, Any]:
        """
        Called when sending/publishing an event.
        Increments local clock and returns timestamp.
        
        Returns:
            dict: Timestamp information with clock value and node_id
        """
        with self._lock:
            self._counter += 1
            return {
                "clock": self._counter,
                "node_id": self.node_id
            }
    
    def receive_event(self, received_timestamp: Dict[str, Any]) -> int:
        """
        Called when receiving an event from another node.
        Updates local clock based on Lamport algorithm.
        
        Args:
            received_timestamp: Timestamp dict from received message
        
        Returns:
            int: Updated local clock value
        """
        with self._lock:
            received_clock = received_timestamp.get("clock", 0)
            self._counter = max(self._counter, received_clock) + 1
            return self._counter
    
    def get_current(self) -> int:
        """
        Get current clock value without incrementing.
        
        Returns:
            int: Current local clock value
        """
        with self._lock:
            return self._counter
    
    def compare_timestamps(self, ts1: Dict[str, Any], ts2: Dict[str, Any]) -> int:
        """
        Compare two Lamport timestamps to determine causal ordering.
        
        Args:
            ts1: First timestamp
            ts2: Second timestamp
        
        Returns:
            -1 if ts1 < ts2 (ts1 happened before ts2)
             0 if concurrent (cannot determine order)
             1 if ts1 > ts2 (ts1 happened after ts2)
        """
        clock1 = ts1.get("clock", 0)
        clock2 = ts2.get("clock", 0)
        node1 = ts1.get("node_id")
        node2 = ts2.get("node_id")
        
        if clock1 < clock2:
            return -1
        elif clock1 > clock2:
            return 1
        else:
            # Same clock value - concurrent events or same node
            # Use node_id for tie-breaking (deterministic ordering)
            if node1 and node2 and node1 != node2:
                return -1 if node1 < node2 else 1
            return 0


# Global clock instance (singleton per process)
_global_clock = None
_clock_lock = threading.Lock()


def get_lamport_clock(node_id: str = None) -> LamportClock:
    """
    Get or create global Lamport clock instance for this process.
    
    Args:
        node_id: Node identifier (required on first call)
    
    Returns:
        LamportClock: Global clock instance
    """
    global _global_clock
    
    with _clock_lock:
        if _global_clock is None:
            if node_id is None:
                raise ValueError("node_id required for first clock initialization")
            _global_clock = LamportClock(node_id)
        return _global_clock


def create_timestamped_event(event_data: Dict[str, Any], node_id: str) -> Dict[str, Any]:
    """
    Utility function to add Lamport timestamp to an event.
    
    Args:
        event_data: Original event dictionary
        node_id: Current node identifier
    
    Returns:
        dict: Event with added lamport_timestamp field
    """
    clock = get_lamport_clock(node_id)
    timestamp = clock.send_event()
    
    return {
        **event_data,
        "lamport_timestamp": timestamp
    }


def process_received_event(event_data: Dict[str, Any], node_id: str) -> Dict[str, Any]:
    """
    Process a received event, updating local Lamport clock.
    
    Args:
        event_data: Received event dictionary
        node_id: Current node identifier
    
    Returns:
        dict: Processed event with updated local context
    """
    clock = get_lamport_clock(node_id)
    
    if "lamport_timestamp" in event_data:
        local_time = clock.receive_event(event_data["lamport_timestamp"])
        event_data["processed_at_lamport"] = local_time
    
    return event_data


def order_events(events: list) -> list:
    """
    Order a list of events by their Lamport timestamps.
    
    Args:
        events: List of event dictionaries with lamport_timestamp field
    
    Returns:
        list: Sorted events (causally ordered)
    """
    if not events:
        return []
    
    # Create a dummy clock for comparison
    dummy_clock = LamportClock("comparison")
    
    def sort_key(event):
        ts = event.get("lamport_timestamp", {"clock": 0, "node_id": ""})
        return (ts.get("clock", 0), ts.get("node_id", ""))
    
    return sorted(events, key=sort_key)


