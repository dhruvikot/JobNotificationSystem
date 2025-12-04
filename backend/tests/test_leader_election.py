"""
Unit Tests for Leader Election (Bully Algorithm)

Tests the leader election implementation including:
- Node ID ordering
- Election triggering
- Coordinator broadcasting
- Leader failure handling
"""

import unittest
import time
from backend.libs.leader_election import BullyElection, ElectionState


class TestLeaderElection(unittest.TestCase):
    """Test cases for Bully Leader Election"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.election1 = BullyElection(
            node_id="dispatcher-1",
            node_url="http://localhost:5004",
            all_nodes={},
            election_timeout=1.0,
            heartbeat_interval=0.5
        )
        
        self.election2 = BullyElection(
            node_id="dispatcher-2",
            node_url="http://localhost:5005",
            all_nodes={},
            election_timeout=1.0,
            heartbeat_interval=0.5
        )
        
        self.election3 = BullyElection(
            node_id="dispatcher-3",
            node_url="http://localhost:5006",
            all_nodes={},
            election_timeout=1.0,
            heartbeat_interval=0.5
        )
    
    def test_initialization(self):
        """Test election initialization"""
        self.assertEqual(self.election1.node_id, "dispatcher-1")
        self.assertEqual(self.election1.state, ElectionState.IDLE)
        self.assertIsNone(self.election1.current_leader)
    
    def test_is_leader(self):
        """Test is_leader check"""
        self.assertFalse(self.election1.is_leader())
        
        # Manually set as leader
        self.election1.state = ElectionState.LEADER
        self.assertTrue(self.election1.is_leader())
    
    def test_get_leader(self):
        """Test getting current leader"""
        self.assertIsNone(self.election1.get_leader())
        
        self.election1.current_leader = "dispatcher-2"
        self.assertEqual(self.election1.get_leader(), "dispatcher-2")
    
    def test_add_node(self):
        """Test adding nodes to cluster"""
        self.election1.add_node("dispatcher-2", "http://localhost:5005")
        
        self.assertIn("dispatcher-2", self.election1.all_nodes)
        self.assertEqual(self.election1.all_nodes["dispatcher-2"], "http://localhost:5005")
    
    def test_remove_node(self):
        """Test removing nodes from cluster"""
        self.election1.add_node("dispatcher-2", "http://localhost:5005")
        self.election1.remove_node("dispatcher-2")
        
        self.assertNotIn("dispatcher-2", self.election1.all_nodes)
    
    def test_get_higher_nodes(self):
        """Test getting nodes with higher IDs"""
        self.election1.add_node("dispatcher-2", "http://localhost:5005")
        self.election1.add_node("dispatcher-3", "http://localhost:5006")
        
        higher_nodes = self.election1._get_higher_nodes()
        
        # dispatcher-1 should see dispatcher-2 and dispatcher-3 as higher
        self.assertEqual(len(higher_nodes), 2)
        self.assertIn("dispatcher-2", higher_nodes)
        self.assertIn("dispatcher-3", higher_nodes)
    
    def test_highest_node_becomes_leader(self):
        """Test that node with highest ID becomes leader when no higher nodes exist"""
        # dispatcher-3 is highest
        # If it starts election, it should become leader
        
        self.election3._become_leader()
        
        self.assertTrue(self.election3.is_leader())
        self.assertEqual(self.election3.current_leader, "dispatcher-3")
    
    def test_handle_election_message_higher_id(self):
        """Test handling ELECTION message when we have higher ID"""
        # dispatcher-2 receives ELECTION from dispatcher-1
        should_respond = self.election2.handle_election_message("dispatcher-1")
        
        # Should respond because dispatcher-2 > dispatcher-1
        self.assertTrue(should_respond)
    
    def test_handle_election_message_lower_id(self):
        """Test handling ELECTION message when we have lower ID"""
        # dispatcher-1 receives ELECTION from dispatcher-2
        should_respond = self.election1.handle_election_message("dispatcher-2")
        
        # Should not respond because dispatcher-1 < dispatcher-2
        self.assertFalse(should_respond)
    
    def test_handle_coordinator_message(self):
        """Test handling COORDINATOR message"""
        self.election1.handle_coordinator_message("dispatcher-3", "http://localhost:5006")
        
        self.assertEqual(self.election1.current_leader, "dispatcher-3")
        self.assertEqual(self.election1.state, ElectionState.FOLLOWER)
    
    def test_handle_coordinator_self(self):
        """Test handling COORDINATOR message from self"""
        self.election2.handle_coordinator_message("dispatcher-2", "http://localhost:5005")
        
        self.assertEqual(self.election2.current_leader, "dispatcher-2")
        self.assertEqual(self.election2.state, ElectionState.LEADER)
    
    def test_handle_heartbeat(self):
        """Test handling leader heartbeat"""
        self.election1.current_leader = "dispatcher-2"
        old_timestamp = self.election1.last_leader_heartbeat
        
        time.sleep(0.1)
        self.election1.handle_heartbeat("dispatcher-2")
        
        self.assertGreater(self.election1.last_leader_heartbeat, old_timestamp)
    
    def test_callbacks(self):
        """Test election callbacks"""
        become_leader_called = [False]
        lose_leadership_called = [False]
        
        def on_become_leader():
            become_leader_called[0] = True
        
        def on_lose_leadership():
            lose_leadership_called[0] = True
        
        self.election1.on_become_leader = on_become_leader
        self.election1.on_lose_leadership = on_lose_leadership
        
        # Trigger become leader
        self.election1._become_leader()
        self.assertTrue(become_leader_called[0])
        
        # Trigger lose leadership
        self.election1.handle_coordinator_message("dispatcher-2", "http://localhost:5005")
        self.assertTrue(lose_leadership_called[0])
    
    def tearDown(self):
        """Clean up after tests"""
        for election in [self.election1, self.election2, self.election3]:
            if hasattr(election, 'stop'):
                election.stop()


if __name__ == '__main__':
    unittest.main()



