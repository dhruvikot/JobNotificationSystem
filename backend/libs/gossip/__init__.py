"""
Gossip Protocol Implementation

This module implements a push-pull gossip protocol for disseminating
state information across the distributed system.

Key Features:
- Periodic gossip rounds with random peer selection
- State merging for membership, popularity, and events
- Eventual consistency through epidemic-style propagation
- Version vectors for conflict resolution
"""

import time
import random
import threading
import requests
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict


@dataclass
class GossipState:
    """Complete state that can be gossiped"""
    membership: Dict[str, Dict]  # From MCP
    popularity: Dict[str, Dict]  # Topic popularity data
    recent_events: List[str]  # Recent event IDs
    version: int  # Version number for this state
    timestamp: float  # When this state was created
    
    def to_dict(self):
        return asdict(self)


class GossipProtocol:
    """
    Implements epidemic-style gossip for state dissemination.
    
    The gossip protocol enables eventual consistency across all nodes
    by periodically exchanging state with random peers.
    
    This is a PUSH-PULL gossip:
    - PUSH: Send your state to peer
    - PULL: Receive peer's state and merge
    """
    
    def __init__(self, 
                 node_id: str,
                 gossip_interval: int = 5,
                 fanout: int = 3,
                 peer_list: Optional[List[str]] = None):
        """
        Args:
            node_id: Unique ID of this node
            gossip_interval: Seconds between gossip rounds
            fanout: Number of random peers to gossip with per round
            peer_list: Initial list of peer URLs
        """
        self.node_id = node_id
        self.gossip_interval = gossip_interval
        self.fanout = fanout
        self.peers: Set[str] = set(peer_list or [])
        
        # Local state
        self.membership_data: Dict[str, Dict] = {}
        self.popularity_data: Dict[str, Dict] = {}
        self.recent_events: List[str] = []
        self.version = 0
        self.lock = threading.RLock()
        
        # Gossip control
        self._running = False
        self._gossip_thread = None
        
        # Statistics
        self.stats = {
            'rounds': 0,
            'messages_sent': 0,
            'messages_received': 0,
            'merge_conflicts': 0
        }
    
    def update_membership(self, membership: Dict[str, Dict]):
        """
        Update local membership state (typically from MCP).
        
        Args:
            membership: Current membership snapshot
        """
        with self.lock:
            self.membership_data = membership.copy()
            self.version += 1
    
    def update_popularity(self, popularity: Dict[str, Dict]):
        """
        Update local popularity state.
        
        Args:
            popularity: Current topic popularity data
        """
        with self.lock:
            self.popularity_data = popularity.copy()
            self.version += 1
    
    def add_recent_event(self, event_id: str, max_events: int = 100):
        """
        Add an event to recent events list.
        
        Args:
            event_id: Event ID to track
            max_events: Maximum number of events to keep
        """
        with self.lock:
            if event_id not in self.recent_events:
                self.recent_events.insert(0, event_id)
                if len(self.recent_events) > max_events:
                    self.recent_events = self.recent_events[:max_events]
                self.version += 1
    
    def add_peer(self, peer_url: str):
        """
        Add a peer to gossip with.
        
        Args:
            peer_url: Base URL of peer (e.g., http://gossip-2:5000)
        """
        with self.lock:
            self.peers.add(peer_url)
    
    def remove_peer(self, peer_url: str):
        """
        Remove a peer from gossip list.
        
        Args:
            peer_url: Base URL of peer to remove
        """
        with self.lock:
            self.peers.discard(peer_url)
    
    def get_state_snapshot(self) -> GossipState:
        """
        Get current state snapshot for gossiping.
        
        Returns:
            GossipState object with current state
        """
        with self.lock:
            return GossipState(
                membership=self.membership_data.copy(),
                popularity=self.popularity_data.copy(),
                recent_events=self.recent_events.copy(),
                version=self.version,
                timestamp=time.time()
            )
    
    def merge_remote_state(self, remote_state: Dict) -> Dict[str, int]:
        """
        Merge remote gossip state with local state.
        
        Uses timestamps and version numbers to resolve conflicts.
        
        Args:
            remote_state: State received from peer
            
        Returns:
            Dictionary with merge statistics
        """
        stats = {
            'membership_updates': 0,
            'popularity_updates': 0,
            'new_events': 0
        }
        
        with self.lock:
            # Merge membership
            remote_membership = remote_state.get('membership', {})
            for node_id, remote_node in remote_membership.items():
                if node_id not in self.membership_data:
                    # New node discovered
                    self.membership_data[node_id] = remote_node
                    stats['membership_updates'] += 1
                else:
                    # Merge based on last_seen timestamp
                    local_last_seen = self.membership_data[node_id].get('last_seen', 0)
                    remote_last_seen = remote_node.get('last_seen', 0)
                    
                    if remote_last_seen > local_last_seen:
                        self.membership_data[node_id] = remote_node
                        stats['membership_updates'] += 1
            
            # Merge popularity
            remote_popularity = remote_state.get('popularity', {})
            for topic, remote_pop in remote_popularity.items():
                if topic not in self.popularity_data:
                    self.popularity_data[topic] = remote_pop
                    stats['popularity_updates'] += 1
                else:
                    # Merge based on last_updated timestamp
                    local_updated = self.popularity_data[topic].get('last_updated', 0)
                    remote_updated = remote_pop.get('last_updated', 0)
                    
                    if remote_updated > local_updated:
                        self.popularity_data[topic] = remote_pop
                        stats['popularity_updates'] += 1
                    elif remote_updated == local_updated:
                        # Same timestamp: sum the counts (eventual consistency)
                        local_count = self.popularity_data[topic].get('count', 0)
                        remote_count = remote_pop.get('count', 0)
                        if remote_count > local_count:
                            self.popularity_data[topic]['count'] = remote_count
                            stats['popularity_updates'] += 1
            
            # Merge recent events
            remote_events = remote_state.get('recent_events', [])
            for event_id in remote_events:
                if event_id not in self.recent_events:
                    self.recent_events.append(event_id)
                    stats['new_events'] += 1
            
            # Keep only most recent events
            if len(self.recent_events) > 100:
                self.recent_events = self.recent_events[:100]
            
            self.version += 1
        
        return stats
    
    def start_gossip(self):
        """Start background gossip thread"""
        if self._running:
            return
        
        self._running = True
        self._gossip_thread = threading.Thread(target=self._gossip_loop, daemon=True)
        self._gossip_thread.start()
        print(f"[Gossip] Node {self.node_id} started gossip protocol")
    
    def stop_gossip(self):
        """Stop background gossip thread"""
        self._running = False
        if self._gossip_thread:
            self._gossip_thread.join(timeout=5)
        print(f"[Gossip] Node {self.node_id} stopped gossip protocol")
    
    def _gossip_loop(self):
        """Background loop for periodic gossip rounds"""
        while self._running:
            try:
                self._perform_gossip_round()
                time.sleep(self.gossip_interval)
            except Exception as e:
                print(f"[Gossip] Error in gossip loop: {e}")
    
    def _perform_gossip_round(self):
        """
        Perform one round of gossip with random peers.
        
        This is the core gossip algorithm:
        1. Select k random peers (fanout)
        2. Send our state to each peer (PUSH)
        3. Receive their state (PULL)
        4. Merge their state with ours
        """
        with self.lock:
            if not self.peers:
                return
            
            # Select random peers
            available_peers = list(self.peers)
            selected_peers = random.sample(
                available_peers, 
                min(self.fanout, len(available_peers))
            )
        
        self.stats['rounds'] += 1
        local_state = self.get_state_snapshot()
        
        for peer_url in selected_peers:
            try:
                self._gossip_with_peer(peer_url, local_state)
            except Exception as e:
                print(f"[Gossip] Failed to gossip with {peer_url}: {e}")
    
    def _gossip_with_peer(self, peer_url: str, local_state: GossipState):
        """
        Exchange state with a specific peer.
        
        Args:
            peer_url: Base URL of peer
            local_state: Our current state to send
        """
        try:
            # PUSH our state to peer
            response = requests.post(
                f"{peer_url}/gossip/exchange",
                json=local_state.to_dict(),
                timeout=3
            )
            
            if response.status_code == 200:
                self.stats['messages_sent'] += 1
                
                # PULL peer's state from response
                peer_state = response.json()
                self.stats['messages_received'] += 1
                
                # Merge peer's state
                merge_stats = self.merge_remote_state(peer_state)
                
                if sum(merge_stats.values()) > 0:
                    print(f"[Gossip] Merged from {peer_url}: {merge_stats}")
        
        except requests.exceptions.RequestException as e:
            # Peer might be down, skip silently
            pass
    
    def get_statistics(self) -> Dict:
        """
        Get gossip protocol statistics.
        
        Returns:
            Dictionary with protocol statistics
        """
        with self.lock:
            return {
                **self.stats,
                'peers': len(self.peers),
                'version': self.version,
                'membership_size': len(self.membership_data),
                'popularity_topics': len(self.popularity_data),
                'recent_events_count': len(self.recent_events)
            }


def create_gossip_protocol(node_id: str, 
                          peers: Optional[List[str]] = None,
                          **kwargs) -> GossipProtocol:
    """
    Factory function to create a gossip protocol instance.
    
    Args:
        node_id: Unique ID for this node
        peers: List of peer URLs
        **kwargs: Additional configuration options
        
    Returns:
        Configured GossipProtocol instance
    """
    return GossipProtocol(node_id=node_id, peer_list=peers, **kwargs)


