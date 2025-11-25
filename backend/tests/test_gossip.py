"""
Unit Tests for Gossip Protocol

Tests the gossip protocol implementation including:
- State updates
- State merging
- Conflict resolution
- Peer management
"""

import unittest
import time
from backend.libs.gossip import GossipProtocol, GossipState


class TestGossipProtocol(unittest.TestCase):
    """Test cases for Gossip Protocol"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.gossip = GossipProtocol(
            node_id="gossip-1",
            gossip_interval=10,  # Long interval for testing
            fanout=2
        )
    
    def test_initialization(self):
        """Test gossip protocol initialization"""
        self.assertEqual(self.gossip.node_id, "gossip-1")
        self.assertEqual(self.gossip.version, 0)
        self.assertEqual(len(self.gossip.membership_data), 0)
    
    def test_update_membership(self):
        """Test updating membership data"""
        membership = {
            "node-1": {"status": "alive", "last_seen": time.time()},
            "node-2": {"status": "alive", "last_seen": time.time()}
        }
        
        initial_version = self.gossip.version
        self.gossip.update_membership(membership)
        
        self.assertEqual(len(self.gossip.membership_data), 2)
        self.assertGreater(self.gossip.version, initial_version)
    
    def test_update_popularity(self):
        """Test updating popularity data"""
        popularity = {
            "hackathon.aiml": {"count": 100, "last_updated": time.time()},
            "jobs.internship": {"count": 50, "last_updated": time.time()}
        }
        
        initial_version = self.gossip.version
        self.gossip.update_popularity(popularity)
        
        self.assertEqual(len(self.gossip.popularity_data), 2)
        self.assertGreater(self.gossip.version, initial_version)
    
    def test_add_recent_event(self):
        """Test adding recent events"""
        self.gossip.add_recent_event("event-1")
        self.gossip.add_recent_event("event-2")
        
        self.assertIn("event-1", self.gossip.recent_events)
        self.assertIn("event-2", self.gossip.recent_events)
        self.assertEqual(len(self.gossip.recent_events), 2)
    
    def test_add_recent_event_no_duplicates(self):
        """Test that duplicate events are not added"""
        self.gossip.add_recent_event("event-1")
        self.gossip.add_recent_event("event-1")
        
        self.assertEqual(len(self.gossip.recent_events), 1)
    
    def test_add_recent_event_max_limit(self):
        """Test recent events list size limit"""
        for i in range(150):
            self.gossip.add_recent_event(f"event-{i}")
        
        # Should be capped at 100 (default max_events)
        self.assertEqual(len(self.gossip.recent_events), 100)
    
    def test_add_peer(self):
        """Test adding gossip peers"""
        self.gossip.add_peer("http://gossip-2:5006")
        self.gossip.add_peer("http://gossip-3:5006")
        
        self.assertEqual(len(self.gossip.peers), 2)
        self.assertIn("http://gossip-2:5006", self.gossip.peers)
    
    def test_remove_peer(self):
        """Test removing gossip peers"""
        self.gossip.add_peer("http://gossip-2:5006")
        self.gossip.remove_peer("http://gossip-2:5006")
        
        self.assertEqual(len(self.gossip.peers), 0)
    
    def test_get_state_snapshot(self):
        """Test getting state snapshot"""
        self.gossip.update_membership({"node-1": {"status": "alive"}})
        self.gossip.update_popularity({"topic-1": {"count": 10}})
        self.gossip.add_recent_event("event-1")
        
        snapshot = self.gossip.get_state_snapshot()
        
        self.assertIsInstance(snapshot, GossipState)
        self.assertEqual(len(snapshot.membership), 1)
        self.assertEqual(len(snapshot.popularity), 1)
        self.assertEqual(len(snapshot.recent_events), 1)
    
    def test_merge_remote_state_new_nodes(self):
        """Test merging remote state with new nodes"""
        remote_state = {
            "membership": {
                "node-1": {"status": "alive", "last_seen": time.time()}
            },
            "popularity": {},
            "recent_events": []
        }
        
        stats = self.gossip.merge_remote_state(remote_state)
        
        self.assertEqual(stats['membership_updates'], 1)
        self.assertIn("node-1", self.gossip.membership_data)
    
    def test_merge_remote_state_fresher_data(self):
        """Test merging with fresher remote data"""
        now = time.time()
        
        # Set local state
        self.gossip.membership_data = {
            "node-1": {"status": "suspect", "last_seen": now - 10}
        }
        
        # Remote has fresher data
        remote_state = {
            "membership": {
                "node-1": {"status": "alive", "last_seen": now}
            },
            "popularity": {},
            "recent_events": []
        }
        
        stats = self.gossip.merge_remote_state(remote_state)
        
        # Should update with fresher data
        self.assertEqual(stats['membership_updates'], 1)
        self.assertEqual(self.gossip.membership_data["node-1"]["status"], "alive")
    
    def test_merge_remote_state_stale_data(self):
        """Test that stale remote data is ignored"""
        now = time.time()
        
        # Set local state with fresh data
        self.gossip.membership_data = {
            "node-1": {"status": "alive", "last_seen": now}
        }
        
        # Remote has stale data
        remote_state = {
            "membership": {
                "node-1": {"status": "suspect", "last_seen": now - 10}
            },
            "popularity": {},
            "recent_events": []
        }
        
        stats = self.gossip.merge_remote_state(remote_state)
        
        # Should not update with stale data
        self.assertEqual(stats['membership_updates'], 0)
        self.assertEqual(self.gossip.membership_data["node-1"]["status"], "alive")
    
    def test_merge_remote_popularity(self):
        """Test merging popularity data"""
        remote_state = {
            "membership": {},
            "popularity": {
                "topic-1": {"count": 100, "last_updated": time.time()},
                "topic-2": {"count": 50, "last_updated": time.time()}
            },
            "recent_events": []
        }
        
        stats = self.gossip.merge_remote_state(remote_state)
        
        self.assertEqual(stats['popularity_updates'], 2)
        self.assertEqual(len(self.gossip.popularity_data), 2)
    
    def test_merge_recent_events(self):
        """Test merging recent events"""
        self.gossip.recent_events = ["event-1", "event-2"]
        
        remote_state = {
            "membership": {},
            "popularity": {},
            "recent_events": ["event-2", "event-3", "event-4"]
        }
        
        stats = self.gossip.merge_remote_state(remote_state)
        
        # Should add event-3 and event-4 (event-2 already exists)
        self.assertEqual(stats['new_events'], 2)
        self.assertIn("event-3", self.gossip.recent_events)
        self.assertIn("event-4", self.gossip.recent_events)
    
    def test_get_statistics(self):
        """Test getting gossip statistics"""
        self.gossip.update_membership({"node-1": {}})
        self.gossip.update_popularity({"topic-1": {}})
        self.gossip.add_peer("http://peer-1:5006")
        
        stats = self.gossip.get_statistics()
        
        self.assertIn('peers', stats)
        self.assertIn('version', stats)
        self.assertIn('membership_size', stats)
        self.assertEqual(stats['peers'], 1)
        self.assertEqual(stats['membership_size'], 1)
    
    def tearDown(self):
        """Clean up after tests"""
        if hasattr(self, 'gossip'):
            self.gossip.stop_gossip()


if __name__ == '__main__':
    unittest.main()


