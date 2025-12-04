"""
Unit Tests for Membership & Coordination Protocol (MCP)

Tests the core functionality of the MCP including:
- Node registration (JOIN)
- Heartbeat updates
- Failure detection (alive -> suspect -> dead)
- Node removal (LEAVE)
- Membership snapshots
"""

import unittest
import time
from backend.libs.mcp import MembershipProtocol, NodeInfo, NodeStatus


class TestMCP(unittest.TestCase):
    """Test cases for MCP"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mcp = MembershipProtocol(
            heartbeat_timeout=2,  # Shorter for testing
            suspect_timeout=1,
            cleanup_interval=5
        )
        
        self.node1 = NodeInfo(
            node_id="node-1",
            role="dispatcher",
            status=NodeStatus.ALIVE.value,
            last_seen=time.time(),
            host="localhost",
            port=5004
        )
        
        self.node2 = NodeInfo(
            node_id="node-2",
            role="dispatcher",
            status=NodeStatus.ALIVE.value,
            last_seen=time.time(),
            host="localhost",
            port=5005
        )
    
    def test_register_node(self):
        """Test node registration (JOIN)"""
        result = self.mcp.register_node(self.node1)
        
        self.assertTrue(result)
        self.assertIn("node-1", self.mcp.members)
        self.assertEqual(self.mcp.members["node-1"].status, NodeStatus.ALIVE.value)
    
    def test_update_heartbeat(self):
        """Test heartbeat update"""
        # Register node first
        self.mcp.register_node(self.node1)
        
        # Update heartbeat
        time.sleep(0.5)
        result = self.mcp.update_heartbeat("node-1", {"queue_len": 5, "cpu": 0.5})
        
        self.assertTrue(result)
        self.assertEqual(self.mcp.members["node-1"].load["queue_len"], 5)
    
    def test_heartbeat_unknown_node(self):
        """Test heartbeat for non-existent node"""
        result = self.mcp.update_heartbeat("unknown-node")
        self.assertFalse(result)
    
    def test_membership_snapshot(self):
        """Test getting membership snapshot"""
        self.mcp.register_node(self.node1)
        self.mcp.register_node(self.node2)
        
        snapshot = self.mcp.get_membership_snapshot()
        
        self.assertEqual(len(snapshot), 2)
        self.assertIn("node-1", snapshot)
        self.assertIn("node-2", snapshot)
    
    def test_get_alive_nodes(self):
        """Test getting alive nodes"""
        self.mcp.register_node(self.node1)
        self.mcp.register_node(self.node2)
        
        alive_nodes = self.mcp.get_alive_nodes()
        self.assertEqual(len(alive_nodes), 2)
        
        # Test role filter
        alive_dispatchers = self.mcp.get_alive_nodes(role="dispatcher")
        self.assertEqual(len(alive_dispatchers), 2)
    
    def test_mark_suspect(self):
        """Test marking node as suspect"""
        self.mcp.register_node(self.node1)
        
        result = self.mcp.mark_suspect("node-1")
        
        self.assertTrue(result)
        self.assertEqual(self.mcp.members["node-1"].status, NodeStatus.SUSPECT.value)
    
    def test_mark_dead(self):
        """Test marking node as dead"""
        self.mcp.register_node(self.node1)
        
        result = self.mcp.mark_dead("node-1")
        
        self.assertTrue(result)
        self.assertEqual(self.mcp.members["node-1"].status, NodeStatus.DEAD.value)
    
    def test_remove_node(self):
        """Test node removal (LEAVE)"""
        self.mcp.register_node(self.node1)
        
        result = self.mcp.remove_node("node-1")
        
        self.assertTrue(result)
        self.assertNotIn("node-1", self.mcp.members)
    
    def test_failure_detection_to_suspect(self):
        """Test automatic transition from ALIVE to SUSPECT"""
        self.mcp.register_node(self.node1)
        self.mcp.start_monitoring()
        
        # Wait for heartbeat timeout
        time.sleep(2.5)
        
        # Check if node became suspect
        self.assertEqual(self.mcp.members["node-1"].status, NodeStatus.SUSPECT.value)
        
        self.mcp.stop_monitoring()
    
    def test_recovery_from_suspect(self):
        """Test node recovery from SUSPECT state"""
        self.mcp.register_node(self.node1)
        self.mcp.mark_suspect("node-1")
        
        # Send heartbeat to recover
        self.mcp.update_heartbeat("node-1")
        
        self.assertEqual(self.mcp.members["node-1"].status, NodeStatus.ALIVE.value)
    
    def test_merge_membership(self):
        """Test merging remote membership data"""
        self.mcp.register_node(self.node1)
        
        # Simulate remote membership with fresher data
        remote_membership = {
            "node-1": {
                "node_id": "node-1",
                "role": "dispatcher",
                "status": "alive",
                "last_seen": time.time() + 10,  # Fresher
                "host": "localhost",
                "port": 5004,
                "load": {"queue_len": 10}
            },
            "node-3": {  # New node
                "node_id": "node-3",
                "role": "gossip",
                "status": "alive",
                "last_seen": time.time(),
                "host": "localhost",
                "port": 5006,
                "load": None
            }
        }
        
        self.mcp.merge_membership(remote_membership)
        
        # Check that node-1 was updated with fresher data
        self.assertEqual(self.mcp.members["node-1"].load["queue_len"], 10)
        
        # Check that node-3 was added
        self.assertIn("node-3", self.mcp.members)
    
    def tearDown(self):
        """Clean up after tests"""
        if hasattr(self, 'mcp'):
            self.mcp.stop_monitoring()


if __name__ == '__main__':
    unittest.main()



