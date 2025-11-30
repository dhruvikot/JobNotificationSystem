"""
Membership & Coordination Protocol (MCP) Implementation

This module implements a distributed membership protocol for tracking
the health and status of nodes in the distributed system.

Key Features:
- Node registration (JOIN)
- Heartbeat monitoring
- Failure detection (alive -> suspect -> dead transitions)
- Integration with gossip for state dissemination
"""

import time
import threading
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum


class NodeStatus(Enum):
    """Node health status states"""
    ALIVE = "alive"
    SUSPECT = "suspect"
    DEAD = "dead"


@dataclass
class NodeInfo:
    """Information about a node in the cluster"""
    node_id: str
    role: str  # "dispatcher", "publisher", "gossip", etc.
    status: str
    last_seen: float
    host: str = ""
    port: int = 0
    load: Optional[Dict] = None
    
    def to_dict(self):
        return asdict(self)


class MembershipProtocol:
    """
    Manages cluster membership state and failure detection.
    
    This is a soft-state membership system that relies on:
    1. Periodic heartbeats from nodes
    2. Gossip protocol for state dissemination
    3. Timeout-based failure detection
    """
    
    def __init__(self, 
                 heartbeat_timeout: int = 30,
                 suspect_timeout: int = 15,
                 cleanup_interval: int = 60):
        """
        Args:
            heartbeat_timeout: Seconds before marking node as suspect
            suspect_timeout: Seconds in suspect state before marking dead
            cleanup_interval: Seconds between cleanup cycles
        """
        self.members: Dict[str, NodeInfo] = {}
        self.lock = threading.RLock()
        self.heartbeat_timeout = heartbeat_timeout
        self.suspect_timeout = suspect_timeout
        self.cleanup_interval = cleanup_interval
        self.callbacks = {
            'on_node_join': [],
            'on_node_suspect': [],
            'on_node_dead': [],
            'on_node_recover': []
        }
        self._running = False
        self._monitor_thread = None
    
    def register_node(self, node_info: NodeInfo) -> bool:
        """
        Register a new node or update existing node (JOIN event).
        
        Args:
            node_info: Information about the joining node
            
        Returns:
            True if registration successful
        """
        with self.lock:
            node_id = node_info.node_id
            is_new = node_id not in self.members
            
            if is_new:
                print(f"[MCP] New node joining: {node_id} (role: {node_info.role})")
                self._trigger_callbacks('on_node_join', node_info)
            else:
                old_status = self.members[node_id].status
                if old_status != NodeStatus.ALIVE.value and node_info.status == NodeStatus.ALIVE.value:
                    print(f"[MCP] Node recovered: {node_id}")
                    self._trigger_callbacks('on_node_recover', node_info)
            
            node_info.last_seen = time.time()
            node_info.status = NodeStatus.ALIVE.value
            self.members[node_id] = node_info
            return True
    
    def update_heartbeat(self, node_id: str, metrics: Optional[Dict] = None) -> bool:
        """
        Update heartbeat timestamp and optional metrics for a node.
        
        Args:
            node_id: ID of the node sending heartbeat
            metrics: Optional metrics (queue_len, cpu, memory, etc.)
            
        Returns:
            True if update successful, False if node not registered
        """
        with self.lock:
            if node_id not in self.members:
                print(f"[MCP] Heartbeat from unknown node: {node_id}")
                return False
            
            node = self.members[node_id]
            node.last_seen = time.time()
            
            # Recover from suspect or dead state if heartbeat received
            if node.status == NodeStatus.SUSPECT.value:
                print(f"[MCP] Node state change: {node_id} (suspect -> alive) - recovered via heartbeat")
                node.status = NodeStatus.ALIVE.value
                self._trigger_callbacks('on_node_recover', node)
            elif node.status == NodeStatus.DEAD.value:
                print(f"[MCP] Node state change: {node_id} (dead -> alive) - recovered via heartbeat")
                node.status = NodeStatus.ALIVE.value
                self._trigger_callbacks('on_node_recover', node)
            
            if metrics:
                node.load = metrics
            
            return True
    
    def get_membership_snapshot(self) -> Dict[str, Dict]:
        """
        Get current membership state snapshot.
        
        Returns:
            Dictionary mapping node_id to node information
        """
        with self.lock:
            return {
                node_id: node.to_dict() 
                for node_id, node in self.members.items()
            }
    
    def get_alive_nodes(self, role: Optional[str] = None) -> List[NodeInfo]:
        """
        Get list of alive nodes, optionally filtered by role.
        
        Args:
            role: Optional role filter
            
        Returns:
            List of alive NodeInfo objects
        """
        with self.lock:
            nodes = [
                node for node in self.members.values()
                if node.status == NodeStatus.ALIVE.value
            ]
            
            if role:
                nodes = [n for n in nodes if n.role == role]
            
            return nodes
    
    def mark_suspect(self, node_id: str) -> bool:
        """
        Mark a node as suspect (first stage of failure).
        
        Args:
            node_id: ID of the suspect node
            
        Returns:
            True if marked, False if node not found
        """
        with self.lock:
            if node_id not in self.members:
                return False
            
            node = self.members[node_id]
            if node.status != NodeStatus.SUSPECT.value:
                previous_status = node.status
                node.status = NodeStatus.SUSPECT.value
                time_since_seen = time.time() - node.last_seen
                print(f"[MCP] Node state change: {node_id} ({previous_status} -> suspect), last_seen {time_since_seen:.1f}s ago")
                self._trigger_callbacks('on_node_suspect', node)
            
            return True
    
    def mark_dead(self, node_id: str) -> bool:
        """
        Mark a node as dead (final stage of failure).
        
        Args:
            node_id: ID of the dead node
            
        Returns:
            True if marked, False if node not found
        """
        with self.lock:
            if node_id not in self.members:
                return False
            
            node = self.members[node_id]
            if node.status != NodeStatus.DEAD.value:
                previous_status = node.status
                node.status = NodeStatus.DEAD.value
                time_since_seen = time.time() - node.last_seen
                print(f"[MCP] Node state change: {node_id} ({previous_status} -> dead), last_seen {time_since_seen:.1f}s ago")
                self._trigger_callbacks('on_node_dead', node)
            
            return True
            
            return True
    
    def remove_node(self, node_id: str) -> bool:
        """
        Completely remove a node from membership (LEAVE event).
        
        Args:
            node_id: ID of the node to remove
            
        Returns:
            True if removed, False if not found
        """
        with self.lock:
            if node_id in self.members:
                print(f"[MCP] Node removed: {node_id}")
                del self.members[node_id]
                return True
            return False
    
    def merge_membership(self, remote_membership: Dict[str, Dict]):
        """
        Merge remote membership state (used by gossip protocol).
        
        Uses last_seen timestamp to resolve conflicts.
        Skips dead nodes that are too old (beyond cleanup_interval).
        
        Args:
            remote_membership: Membership state from another node
        """
        now = time.time()
        
        with self.lock:
            for node_id, remote_data in remote_membership.items():
                remote_last_seen = remote_data.get('last_seen', 0)
                remote_status = remote_data.get('status', '')
                time_since_seen = now - remote_last_seen
                
                # Skip dead nodes that are too old - don't re-add cleaned up nodes
                if remote_status == NodeStatus.DEAD.value and time_since_seen > self.cleanup_interval:
                    continue
                
                # Skip nodes that haven't been seen recently (stale data)
                if time_since_seen > (self.heartbeat_timeout + self.suspect_timeout + self.cleanup_interval):
                    continue
                
                if node_id not in self.members:
                    # New node learned via gossip
                    node_info = NodeInfo(**remote_data)
                    self.members[node_id] = node_info
                else:
                    # Merge based on freshness
                    local_node = self.members[node_id]
                    
                    if remote_last_seen > local_node.last_seen:
                        # Remote state is fresher - update last_seen
                        local_node.last_seen = remote_last_seen
                        
                        # If remote is alive and recent, mark local as alive too
                        if remote_status == NodeStatus.ALIVE.value and time_since_seen < self.heartbeat_timeout:
                            if local_node.status != NodeStatus.ALIVE.value:
                                print(f"[MCP] Node recovered via gossip: {node_id}")
                                local_node.status = NodeStatus.ALIVE.value
                                self._trigger_callbacks('on_node_recover', local_node)
                        
                        # Update load metrics if present
                        if remote_data.get('load'):
                            local_node.load = remote_data['load']
    
    def register_callback(self, event: str, callback):
        """
        Register a callback for membership events.
        
        Events: 'on_node_join', 'on_node_suspect', 'on_node_dead', 'on_node_recover'
        
        Args:
            event: Event name
            callback: Function to call (receives NodeInfo)
        """
        if event in self.callbacks:
            self.callbacks[event].append(callback)
    
    def _trigger_callbacks(self, event: str, node_info: NodeInfo):
        """Trigger all callbacks registered for an event"""
        for callback in self.callbacks.get(event, []):
            try:
                callback(node_info)
            except Exception as e:
                print(f"[MCP] Error in callback for {event}: {e}")
    
    def start_monitoring(self):
        """Start background thread for failure detection"""
        if self._running:
            return
        
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        print("[MCP] Started failure detection monitoring")
    
    def stop_monitoring(self):
        """Stop background monitoring thread"""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        print("[MCP] Stopped failure detection monitoring")
    
    def _monitor_loop(self):
        """Background loop for detecting failures"""
        while self._running:
            try:
                self._check_failures()
                time.sleep(2)  # Check every 2 seconds
            except Exception as e:
                print(f"[MCP] Error in monitor loop: {e}")
    
    def _check_failures(self):
        """Check for failed nodes based on heartbeat timeouts"""
        now = time.time()
        
        with self.lock:
            for node_id, node in list(self.members.items()):
                time_since_seen = now - node.last_seen
                
                if node.status == NodeStatus.ALIVE.value:
                    if time_since_seen > self.heartbeat_timeout:
                        self.mark_suspect(node_id)
                
                elif node.status == NodeStatus.SUSPECT.value:
                    if time_since_seen > (self.heartbeat_timeout + self.suspect_timeout):
                        self.mark_dead(node_id)
                
                elif node.status == NodeStatus.DEAD.value:
                    # Optional: remove dead nodes after extended period
                    if time_since_seen > self.cleanup_interval:
                        self.remove_node(node_id)


# Global instance (can be imported by services)
_mcp_instance = None


def get_mcp() -> MembershipProtocol:
    """Get or create global MCP instance"""
    global _mcp_instance
    if _mcp_instance is None:
        _mcp_instance = MembershipProtocol()
    return _mcp_instance


