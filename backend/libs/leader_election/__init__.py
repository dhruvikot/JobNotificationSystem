"""
Leader Election - Bully Algorithm Implementation

This module implements application-level leader election using the Bully algorithm
for coordination among Notification Dispatcher nodes.

IMPORTANT NOTE ON KUBERNETES VS APPLICATION-LEVEL ELECTION:
===========================================================
This leader election is at the APPLICATION LEVEL and is used solely for
coordinating distributed tasks within our notification system (e.g., deciding
which dispatcher node performs periodic cleanup, aggregates popularity metrics).

This is SEPARATE from and INDEPENDENT of Kubernetes/EKS's own leader election
mechanisms used for cluster control plane operations. There is no conflict because:

1. K8s leader election: Manages K8s control plane (scheduler, controller manager)
2. Application leader election: Manages application-specific coordination tasks

Just as distributed databases (etcd, Cassandra) run their own consensus protocols
on top of K8s, our application runs its own election for application logic.

Algorithm Overview (Bully):
- Each node has a unique ID (numeric or lexicographic ordering)
- When a node detects no leader or leader failure:
  - It sends ELECTION messages to all nodes with higher IDs
  - If no higher node responds within timeout: declare self as leader
  - If a higher node responds: wait for its COORDINATOR message
- Highest-ID alive node becomes the leader
"""

import time
import threading
import requests
from typing import Optional, List, Callable, Dict
from enum import Enum


class ElectionState(Enum):
    """States in the election process"""
    IDLE = "idle"
    ELECTION_IN_PROGRESS = "election_in_progress"
    LEADER = "leader"
    FOLLOWER = "follower"


class BullyElection:
    """
    Implements Bully-style leader election for application coordination.
    
    The Bully algorithm ensures that the node with the highest ID
    becomes the leader, providing deterministic leadership.
    """
    
    def __init__(self,
                 node_id: str,
                 node_url: str,
                 all_nodes: Optional[Dict[str, str]] = None,
                 election_timeout: float = 5.0,
                 heartbeat_interval: float = 3.0):
        """
        Args:
            node_id: Unique ID of this node (must be comparable)
            node_url: URL where this node can be reached
            all_nodes: Dict mapping node_id -> url for all dispatcher nodes
            election_timeout: Seconds to wait for responses during election
            heartbeat_interval: Seconds between leader heartbeats
        """
        self.node_id = node_id
        self.node_url = node_url
        self.all_nodes: Dict[str, str] = all_nodes or {}
        self.election_timeout = election_timeout
        self.heartbeat_interval = heartbeat_interval
        
        # Election state
        self.state = ElectionState.IDLE
        self.current_leader: Optional[str] = None
        self.last_leader_heartbeat: float = 0
        self.lock = threading.RLock()
        
        # Callbacks
        self.on_become_leader: Optional[Callable] = None
        self.on_lose_leadership: Optional[Callable] = None
        self.on_leader_change: Optional[Callable] = None
        
        # Background threads
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._heartbeat_thread: Optional[threading.Thread] = None
        
        print(f"[Election] Initialized Bully Election for node {node_id}")
    
    def update_nodes(self, all_nodes: Dict[str, str]):
        """
        Update the list of all nodes in the cluster.
        
        Args:
            all_nodes: Dict mapping node_id -> url
        """
        with self.lock:
            self.all_nodes = all_nodes.copy()
            print(f"[Election] Updated node list: {list(self.all_nodes.keys())}")
    
    def add_node(self, node_id: str, node_url: str):
        """Add a single node to the cluster"""
        with self.lock:
            self.all_nodes[node_id] = node_url
    
    def remove_node(self, node_id: str):
        """Remove a node from the cluster (e.g., on failure)"""
        with self.lock:
            if node_id in self.all_nodes:
                del self.all_nodes[node_id]
                print(f"[Election] Removed node {node_id}")
                
                # If removed node was leader, start election
                if node_id == self.current_leader:
                    print(f"[Election] Leader {node_id} failed, starting election")
                    self.start_election()
    
    def is_leader(self) -> bool:
        """Check if this node is currently the leader"""
        with self.lock:
            return self.state == ElectionState.LEADER
    
    def get_leader(self) -> Optional[str]:
        """Get current leader node ID"""
        with self.lock:
            return self.current_leader
    
    def start_election(self):
        """
        Initiate leader election (Bully algorithm).
        
        Process:
        1. Send ELECTION to all higher-ID nodes
        2. Wait for responses
        3. If no response: declare self as leader
        4. If response received: wait for COORDINATOR from winner
        """
        with self.lock:
            if self.state == ElectionState.ELECTION_IN_PROGRESS:
                print("[Election] Election already in progress")
                return
            
            print(f"[Election] Node {self.node_id} starting election")
            self.state = ElectionState.ELECTION_IN_PROGRESS
        
        # Run election in background to avoid blocking
        threading.Thread(target=self._run_election, daemon=True).start()
    
    def _run_election(self):
        """Execute the election algorithm"""
        # Find nodes with higher IDs
        higher_nodes = self._get_higher_nodes()
        
        if not higher_nodes:
            # No higher nodes, I am the leader
            self._become_leader()
            return
        
        # Send ELECTION message to higher nodes
        print(f"[Election] Sending ELECTION to {len(higher_nodes)} higher nodes")
        responses = []
        
        for node_id, node_url in higher_nodes.items():
            try:
                response = requests.post(
                    f"{node_url}/election/message",
                    json={
                        "type": "ELECTION",
                        "from_node": self.node_id
                    },
                    timeout=2
                )
                if response.status_code == 200:
                    responses.append(node_id)
            except Exception as e:
                # Node didn't respond, assume it's dead
                print(f"[Election] Node {node_id} didn't respond: {e}")
        
        if not responses:
            # No higher node responded, I am the leader
            self._become_leader()
        else:
            # Higher node(s) responded, wait for COORDINATOR
            print(f"[Election] Waiting for COORDINATOR from higher nodes")
            self._wait_for_coordinator()
    
    def _become_leader(self):
        """Declare this node as the leader"""
        with self.lock:
            was_leader = self.state == ElectionState.LEADER
            self.state = ElectionState.LEADER
            self.current_leader = self.node_id
            self.last_leader_heartbeat = time.time()
        
        print(f"[Election] *** Node {self.node_id} is now LEADER ***")
        
        # Notify all other nodes
        self._broadcast_coordinator()
        
        # Trigger callback
        if not was_leader and self.on_become_leader:
            try:
                self.on_become_leader()
            except Exception as e:
                print(f"[Election] Error in on_become_leader callback: {e}")
    
    def _broadcast_coordinator(self):
        """Broadcast COORDINATOR message to all nodes"""
        all_nodes = self._get_all_other_nodes()
        
        for node_id, node_url in all_nodes.items():
            try:
                requests.post(
                    f"{node_url}/election/message",
                    json={
                        "type": "COORDINATOR",
                        "leader_id": self.node_id,
                        "leader_url": self.node_url
                    },
                    timeout=2
                )
            except Exception:
                pass  # Best effort
    
    def _wait_for_coordinator(self, timeout: Optional[float] = None):
        """Wait for COORDINATOR message from higher node"""
        if timeout is None:
            timeout = self.election_timeout
        
        deadline = time.time() + timeout
        
        while time.time() < deadline:
            with self.lock:
                if self.state != ElectionState.ELECTION_IN_PROGRESS:
                    # State changed (received COORDINATOR)
                    return
            time.sleep(0.5)
        
        # Timeout - no coordinator received, start new election
        print("[Election] Timeout waiting for COORDINATOR, restarting election")
        self.start_election()
    
    def handle_election_message(self, from_node: str) -> bool:
        """
        Handle incoming ELECTION message from another node.
        
        Args:
            from_node: Node ID that sent the message
            
        Returns:
            True if we respond (we have higher ID), False otherwise
        """
        with self.lock:
            if self.node_id > from_node:
                print(f"[Election] Received ELECTION from {from_node}, responding (I have higher ID)")
                # Start our own election
                threading.Thread(target=self.start_election, daemon=True).start()
                return True
            else:
                print(f"[Election] Received ELECTION from {from_node}, not responding (lower ID)")
                return False
    
    def handle_coordinator_message(self, leader_id: str, leader_url: str):
        """
        Handle incoming COORDINATOR message.
        
        Args:
            leader_id: ID of the new leader
            leader_url: URL of the new leader
        """
        with self.lock:
            old_leader = self.current_leader
            was_leader = self.state == ElectionState.LEADER
            
            self.current_leader = leader_id
            self.last_leader_heartbeat = time.time()
            
            if leader_id == self.node_id:
                self.state = ElectionState.LEADER
            else:
                self.state = ElectionState.FOLLOWER
            
            print(f"[Election] Accepted {leader_id} as leader")
            
            # Update node URL if needed
            if leader_id not in self.all_nodes:
                self.all_nodes[leader_id] = leader_url
            
            # Trigger callbacks
            if was_leader and leader_id != self.node_id and self.on_lose_leadership:
                try:
                    self.on_lose_leadership()
                except Exception as e:
                    print(f"[Election] Error in on_lose_leadership callback: {e}")
            
            if old_leader != leader_id and self.on_leader_change:
                try:
                    self.on_leader_change(leader_id)
                except Exception as e:
                    print(f"[Election] Error in on_leader_change callback: {e}")
    
    def handle_heartbeat(self, leader_id: str):
        """
        Handle leader heartbeat message.
        
        Args:
            leader_id: ID of the leader sending heartbeat
        """
        with self.lock:
            if leader_id == self.current_leader:
                self.last_leader_heartbeat = time.time()
    
    def _get_higher_nodes(self) -> Dict[str, str]:
        """Get all nodes with higher IDs than this node"""
        with self.lock:
            return {
                nid: url for nid, url in self.all_nodes.items()
                if nid > self.node_id
            }
    
    def _get_all_other_nodes(self) -> Dict[str, str]:
        """Get all nodes except this one"""
        with self.lock:
            return {
                nid: url for nid, url in self.all_nodes.items()
                if nid != self.node_id
            }
    
    def start(self):
        """Start background monitoring and heartbeat threads"""
        if self._running:
            return
        
        self._running = True
        
        # Start leader monitoring thread
        self._monitor_thread = threading.Thread(target=self._monitor_leader, daemon=True)
        self._monitor_thread.start()
        
        # Start heartbeat thread (for when we're leader)
        self._heartbeat_thread = threading.Thread(target=self._send_heartbeats, daemon=True)
        self._heartbeat_thread.start()
        
        print("[Election] Started election monitoring")
        
        # Initial election if no leader known
        if self.current_leader is None:
            self.start_election()
    
    def stop(self):
        """Stop background threads"""
        self._running = False
        print("[Election] Stopped election monitoring")
    
    def _monitor_leader(self):
        """Monitor leader health and trigger election if leader fails"""
        while self._running:
            try:
                time.sleep(2)
                
                with self.lock:
                    if self.current_leader is None:
                        continue
                    
                    if self.current_leader == self.node_id:
                        continue  # We are the leader
                    
                    time_since_heartbeat = time.time() - self.last_leader_heartbeat
                    
                    if time_since_heartbeat > (self.heartbeat_interval * 3):
                        print(f"[Election] Leader {self.current_leader} timeout, starting election")
                        self.current_leader = None
                        self.start_election()
            
            except Exception as e:
                print(f"[Election] Error in monitor loop: {e}")
    
    def _send_heartbeats(self):
        """Send periodic heartbeats when we're the leader"""
        while self._running:
            try:
                time.sleep(self.heartbeat_interval)
                
                if not self.is_leader():
                    continue
                
                # Send heartbeat to all followers
                all_nodes = self._get_all_other_nodes()
                for node_id, node_url in all_nodes.items():
                    try:
                        requests.post(
                            f"{node_url}/election/heartbeat",
                            json={"leader_id": self.node_id},
                            timeout=1
                        )
                    except Exception:
                        pass  # Best effort
            
            except Exception as e:
                print(f"[Election] Error in heartbeat loop: {e}")


