"""
Gossip Agent Service

Runs the gossip protocol to disseminate state information across
the distributed system.

Key Responsibilities:
- Maintain and gossip membership information from MCP
- Gossip topic popularity data
- Exchange recent event information
- Provide HTTP endpoints for gossip exchange
- Integrate with MCP for membership updates

Endpoints:
- POST /gossip/exchange - Exchange gossip state with peer
- POST /metrics - Receive metrics from other services
- GET /gossip/state - Get current gossip state
- GET /gossip/stats - Get gossip protocol statistics
- POST /mcp/join - Register node with MCP
- POST /mcp/heartbeat - Update node heartbeat
- POST /mcp/leave - Remove node from MCP
- GET /mcp/membership - Get membership snapshot
- GET /health - Health check
"""

import os
import sys
import time
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS

# Add libs to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from libs.mcp import get_mcp, NodeInfo, NodeStatus
from libs.gossip import create_gossip_protocol, GossipProtocol
from libs.popularity import get_tracker

app = Flask(__name__)
CORS(app)

# Configuration
NODE_ID = os.getenv('NODE_ID', f'gossip-{int(time.time())}')
PORT = int(os.getenv('PORT', '5006'))
GOSSIP_PEERS = os.getenv('GOSSIP_PEERS', '').split(',') if os.getenv('GOSSIP_PEERS') else []

# Initialize MCP
mcp = get_mcp()

# Initialize Gossip Protocol
gossip: GossipProtocol = create_gossip_protocol(
    node_id=NODE_ID,
    peers=[p.strip() for p in GOSSIP_PEERS if p.strip()],
    gossip_interval=5,
    fanout=3
)

# Popularity tracker
popularity_tracker = get_tracker()

print(f"[Gossip Agent] Starting node {NODE_ID} on port {PORT}")
print(f"[Gossip Agent] Initial peers: {GOSSIP_PEERS}")


# ============================================================================
# Background Synchronization
# ============================================================================

def sync_mcp_to_gossip():
    """Periodically sync MCP membership state to gossip protocol"""
    while True:
        try:
            time.sleep(3)
            
            # Get latest membership from MCP
            membership = mcp.get_membership_snapshot()
            
            # Update gossip state
            gossip.update_membership(membership)
        
        except Exception as e:
            print(f"[Gossip Agent] Error syncing MCP to gossip: {e}")


def sync_popularity_to_gossip():
    """Periodically sync popularity data to gossip protocol"""
    while True:
        try:
            time.sleep(5)
            
            # Get top topics from popularity tracker
            top_topics = popularity_tracker.get_top_topics(limit=50)
            
            # Convert to dict format for gossip
            popularity_data = {
                topic_info['topic']: {
                    'count': topic_info['count'],
                    'last_updated': topic_info.get('last_updated', int(time.time()))
                }
                for topic_info in top_topics
            }
            
            # Update gossip state
            gossip.update_popularity(popularity_data)
        
        except Exception as e:
            print(f"[Gossip Agent] Error syncing popularity to gossip: {e}")


def sync_gossip_to_popularity():
    """Periodically sync gossip popularity data back to popularity tracker"""
    while True:
        try:
            time.sleep(10)
            
            # Get popularity data from gossip
            popularity_data = gossip.popularity_data
            
            # Update local popularity tracker
            for topic, data in popularity_data.items():
                current_count = popularity_tracker.get_count(topic)
                remote_count = data.get('count', 0)
                
                # If remote has higher count, update local
                if remote_count > current_count:
                    diff = remote_count - current_count
                    popularity_tracker.increment_topic(topic, amount=diff)
        
        except Exception as e:
            print(f"[Gossip Agent] Error syncing gossip to popularity: {e}")


# ============================================================================
# API Endpoints - Gossip
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'gossip-agent',
        'node_id': NODE_ID
    }), 200


@app.route('/gossip/exchange', methods=['POST'])
def gossip_exchange():
    """
    Exchange gossip state with a peer (PUSH-PULL gossip).
    
    Request body: GossipState from peer
    Response: Our current GossipState
    
    This endpoint is called by other gossip nodes.
    """
    try:
        peer_state = request.get_json()
        
        if not peer_state:
            return jsonify({'error': 'No state provided'}), 400
        
        # Merge peer's state into ours
        merge_stats = gossip.merge_remote_state(peer_state)
        
        print(f"[Gossip Agent] Received gossip exchange: {merge_stats}")
        
        # Return our current state
        local_state = gossip.get_state_snapshot()
        
        return jsonify(local_state.to_dict()), 200
    
    except Exception as e:
        print(f"[Gossip Agent] Error in gossip exchange: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/gossip/state', methods=['GET'])
def get_gossip_state():
    """
    Get current gossip state.
    
    Response:
    {
        "membership": {...},
        "popularity": {...},
        "recent_events": [...],
        "version": 123,
        "timestamp": 1234567890
    }
    """
    try:
        state = gossip.get_state_snapshot()
        return jsonify(state.to_dict()), 200
    
    except Exception as e:
        print(f"[Gossip Agent] Error getting state: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/gossip/stats', methods=['GET'])
def get_gossip_stats():
    """
    Get gossip protocol statistics.
    
    Response:
    {
        "rounds": 100,
        "messages_sent": 300,
        "messages_received": 280,
        "peers": 5,
        "version": 123,
        "membership_size": 10,
        "popularity_topics": 20,
        "recent_events_count": 15
    }
    """
    try:
        stats = gossip.get_statistics()
        return jsonify(stats), 200
    
    except Exception as e:
        print(f"[Gossip Agent] Error getting stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/gossip/peers', methods=['POST'])
def add_peer():
    """
    Add a new peer to gossip with.
    
    Request body:
    {
        "peer_url": "http://gossip-2:5006"
    }
    """
    try:
        data = request.get_json()
        peer_url = data.get('peer_url')
        
        if not peer_url:
            return jsonify({'error': 'Missing peer_url'}), 400
        
        gossip.add_peer(peer_url)
        
        print(f"[Gossip Agent] Added peer: {peer_url}")
        
        return jsonify({
            'success': True,
            'message': f'Added peer {peer_url}'
        }), 200
    
    except Exception as e:
        print(f"[Gossip Agent] Error adding peer: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/gossip/peers/<path:peer_url>', methods=['DELETE'])
def remove_peer(peer_url):
    """Remove a peer from gossip list"""
    try:
        gossip.remove_peer(peer_url)
        
        print(f"[Gossip Agent] Removed peer: {peer_url}")
        
        return jsonify({
            'success': True,
            'message': f'Removed peer {peer_url}'
        }), 200
    
    except Exception as e:
        print(f"[Gossip Agent] Error removing peer: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# API Endpoints - MCP (Membership & Coordination Protocol)
# ============================================================================

@app.route('/mcp/join', methods=['POST'])
def mcp_join():
    """
    Register a node with MCP (JOIN event).
    
    Request body:
    {
        "node_id": "dispatcher-1",
        "role": "dispatcher",
        "host": "localhost",
        "port": 5004,
        "load": {"queue_len": 0, "cpu": 0.5}
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'node_id' not in data or 'role' not in data:
            return jsonify({'error': 'Missing required fields: node_id, role'}), 400
        
        node_info = NodeInfo(
            node_id=data['node_id'],
            role=data['role'],
            status=NodeStatus.ALIVE.value,
            last_seen=time.time(),
            host=data.get('host', ''),
            port=data.get('port', 0),
            load=data.get('load')
        )
        
        success = mcp.register_node(node_info)
        
        return jsonify({
            'success': success,
            'message': f"Node {data['node_id']} registered"
        }), 200
    
    except Exception as e:
        print(f"[Gossip Agent] Error in MCP join: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/mcp/heartbeat', methods=['POST'])
def mcp_heartbeat():
    """
    Update node heartbeat in MCP.
    
    Request body:
    {
        "node_id": "dispatcher-1",
        "metrics": {"queue_len": 5, "cpu": 0.7}
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'node_id' not in data:
            return jsonify({'error': 'Missing node_id'}), 400
        
        node_id = data['node_id']
        metrics = data.get('metrics')
        
        success = mcp.update_heartbeat(node_id, metrics)
        
        if not success:
            return jsonify({'error': 'Node not registered'}), 404
        
        return jsonify({'success': True}), 200
    
    except Exception as e:
        print(f"[Gossip Agent] Error in MCP heartbeat: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/mcp/leave', methods=['POST'])
def mcp_leave():
    """
    Remove a node from MCP (LEAVE event).
    
    Request body:
    {
        "node_id": "dispatcher-1"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'node_id' not in data:
            return jsonify({'error': 'Missing node_id'}), 400
        
        node_id = data['node_id']
        success = mcp.remove_node(node_id)
        
        return jsonify({
            'success': success,
            'message': f"Node {node_id} removed" if success else "Node not found"
        }), 200
    
    except Exception as e:
        print(f"[Gossip Agent] Error in MCP leave: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/mcp/membership', methods=['GET'])
def get_membership():
    """
    Get current MCP membership snapshot.
    
    Response:
    {
        "membership": {
            "node-1": {...},
            "node-2": {...}
        }
    }
    """
    try:
        membership = mcp.get_membership_snapshot()
        return jsonify({'membership': membership}), 200
    
    except Exception as e:
        print(f"[Gossip Agent] Error getting membership: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/mcp/nodes/<role>', methods=['GET'])
def get_nodes_by_role(role):
    """
    Get all alive nodes of a specific role.
    
    Response:
    {
        "nodes": [...]
    }
    """
    try:
        nodes = mcp.get_alive_nodes(role=role)
        nodes_dict = [node.to_dict() for node in nodes]
        
        return jsonify({
            'nodes': nodes_dict,
            'count': len(nodes_dict)
        }), 200
    
    except Exception as e:
        print(f"[Gossip Agent] Error getting nodes: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# API Endpoints - Metrics & Events
# ============================================================================

@app.route('/metrics', methods=['POST'])
def receive_metrics():
    """
    Receive metrics from other services.
    
    This can be used to track system-wide metrics via gossip.
    
    Request body:
    {
        "node_id": "...",
        "metrics": {...}
    }
    """
    try:
        data = request.get_json()
        
        # Store metrics (in production, aggregate and gossip)
        print(f"[Gossip Agent] Received metrics: {data}")
        
        return jsonify({'success': True}), 200
    
    except Exception as e:
        print(f"[Gossip Agent] Error receiving metrics: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/events/<event_id>', methods=['POST'])
def track_event():
    """
    Track a recent event for gossip dissemination.
    
    Request body:
    {
        "event_id": "E123"
    }
    """
    try:
        data = request.get_json()
        event_id = data.get('event_id')
        
        if not event_id:
            return jsonify({'error': 'Missing event_id'}), 400
        
        gossip.add_recent_event(event_id)
        
        return jsonify({'success': True}), 200
    
    except Exception as e:
        print(f"[Gossip Agent] Error tracking event: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# Startup & Background Threads
# ============================================================================

def start_background_tasks():
    """Start background threads"""
    # Start MCP monitoring
    mcp.start_monitoring()
    print("[Gossip Agent] Started MCP monitoring")
    
    # Start gossip protocol
    gossip.start_gossip()
    print("[Gossip Agent] Started gossip protocol")
    
    # Sync threads
    threading.Thread(target=sync_mcp_to_gossip, daemon=True).start()
    threading.Thread(target=sync_popularity_to_gossip, daemon=True).start()
    threading.Thread(target=sync_gossip_to_popularity, daemon=True).start()
    
    print("[Gossip Agent] Started sync threads")


# Start background tasks
start_background_tasks()


# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)


