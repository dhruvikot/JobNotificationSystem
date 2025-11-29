"""
Notification Dispatcher Service

Consumes event notifications from RabbitMQ and dispatches them through
various channels (in-app, email, SMS via AWS SNS).

Key Distributed Systems Features:
- Participates in MCP (Membership & Coordination Protocol)
- Implements Bully leader election
- Leader performs exclusive tasks (cleanup, aggregation)
- Integrates with gossip for state dissemination
- Provides priority-based message processing

Endpoints:
- POST /mcp/heartbeat - Send heartbeat to MCP
- GET /election/status - Get election status
- POST /election/message - Handle election messages
- POST /election/heartbeat - Handle leader heartbeat
- GET /notifications/<user_id> - Get notifications for user (in-app)
- GET /health - Health check
"""

import os
import sys
import time
import json
import threading
import traceback
import boto3
import pika
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from botocore.exceptions import ClientError
from collections import deque

# Add libs to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from libs.mcp import get_mcp, NodeInfo, NodeStatus
from libs.leader_election import BullyElection
from libs.popularity import get_tracker
from libs.timestamps import get_lamport_clock, process_received_event, order_events

# Import WebSocket manager
from websocket_manager import WebSocketManager

app = Flask(__name__)
CORS(app)

# Configuration
NODE_ID = os.getenv('NODE_ID', f'dispatcher-{int(time.time())}')
NODE_URL = os.getenv('NODE_URL', 'http://localhost:5004')
PEER_NODES = os.getenv('PEER_NODES', '').split(',') if os.getenv('PEER_NODES') else []
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
SNS_TOPIC_ARN = os.getenv('NOTIFICATIONS_SNS_TOPIC_ARN', '')
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', '5672'))
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'guest')
RABBITMQ_EXCHANGE = os.getenv('RABBITMQ_EXCHANGE', 'events.topic')
# Use a shared queue for load balancing across all dispatcher instances
RABBITMQ_QUEUE = os.getenv('RABBITMQ_QUEUE', 'dispatcher_queue')
PORT = int(os.getenv('PORT', '5004'))
GOSSIP_AGENT_URL = os.getenv('GOSSIP_AGENT_URL', 'http://localhost:5006')
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))

# Initialize AWS SNS
sns_client = boto3.client('sns', region_name=AWS_REGION)

# Initialize MCP and Leader Election
mcp = get_mcp()
election = None  # Initialized after discovering other nodes

# Initialize WebSocket Manager with Redis
ws_manager = WebSocketManager(app, redis_host=REDIS_HOST, redis_port=REDIS_PORT)

# In-memory notification storage (backup/fallback)
in_app_notifications = {}  # user_id -> deque of notifications
notifications_lock = threading.Lock()

print(f"[Dispatcher] Starting node {NODE_ID} on port {PORT}")
print(f"[Dispatcher] Node URL: {NODE_URL}")
print(f"[Dispatcher] Peer nodes: {PEER_NODES if PEER_NODES else 'None (single node mode)'}")
print(f"[Dispatcher] RabbitMQ: {RABBITMQ_HOST}:{RABBITMQ_PORT}")
print(f"[Dispatcher] Redis: {REDIS_HOST}:{REDIS_PORT}")
print(f"[Dispatcher] SNS Topic: {SNS_TOPIC_ARN or 'Not configured'}")


# ============================================================================
# In-App Notifications Storage
# ============================================================================

def add_in_app_notification(user_id: str, notification: dict):
    """Add notification and push via WebSocket"""
    # Push to WebSocket (real-time) + Redis (persistent)
    ws_manager.push_notification(user_id, notification)
    
    # Also keep in memory for backward compatibility
    with notifications_lock:
        if user_id not in in_app_notifications:
            in_app_notifications[user_id] = deque(maxlen=100)  # Keep last 100
        
        in_app_notifications[user_id].appendleft(notification)


def get_user_notifications(user_id: str, limit: int = 50):
    """Get notifications from Redis (persistent) or memory (fallback)"""
    # Try Redis first (persistent cache)
    if ws_manager.redis_available:
        cached = ws_manager.get_cached_notifications(user_id, limit)
        if cached:
            # Order by Lamport timestamp for causal ordering
            return order_events(cached)[:limit]
    
    # Fallback to memory
    with notifications_lock:
        if user_id not in in_app_notifications:
            return []
        
        # Order notifications by Lamport timestamp for causal ordering
        notifications = list(in_app_notifications[user_id])
        ordered = order_events(notifications)
        return ordered[:limit]


# ============================================================================
# AWS SNS Integration
# ============================================================================

def send_email_notification(email: str, subject: str, message: str):
    """Send email notification via AWS SNS"""
    try:
        if not SNS_TOPIC_ARN:
            print("[Dispatcher] SNS not configured, skipping email")
            return False
        
        response = sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=message,
            MessageAttributes={
                'email': {'DataType': 'String', 'StringValue': email}
            }
        )
        
        print(f"[Dispatcher] Sent email to {email}: {response['MessageId']}")
        return True
    
    except ClientError as e:
        print(f"[Dispatcher] SNS error sending email: {e}")
        return False


def send_sms_notification(phone: str, message: str):
    """Send SMS notification via AWS SNS"""
    try:
        if not phone.startswith('+'):
            print(f"[Dispatcher] Invalid phone number format: {phone}")
            return False
        
        response = sns_client.publish(
            PhoneNumber=phone,
            Message=message[:160]  # SMS limit
        )
        
        print(f"[Dispatcher] Sent SMS to {phone}: {response['MessageId']}")
        return True
    
    except ClientError as e:
        print(f"[Dispatcher] SNS error sending SMS: {e}")
        return False


# ============================================================================
# RabbitMQ Consumer
# ============================================================================

def get_rabbitmq_connection():
    """Create RabbitMQ connection"""
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )
        return pika.BlockingConnection(parameters)
    except Exception as e:
        print(f"[Dispatcher] Failed to connect to RabbitMQ: {e}")
        return None


def process_notification(message: dict):
    """
    Process a notification message from RabbitMQ.
    
    Message format:
    {
        "event_id": "...",
        "topic": "...",
        "title": "...",
        "description": "...",
        "subscriber_ids": ["U1", "U2", ...],
        "channels": ["app", "email", "sms"],
        "priority": "high",
        "timestamp": 1234567890,
        ...
    }
    """
    try:
        # Process Lamport timestamp for distributed ordering
        message = process_received_event(message, NODE_ID)
        
        event_id = message.get('event_id')
        title = message.get('title', 'New Event')
        description = message.get('description', '')
        subscriber_ids = message.get('subscriber_ids', [])
        channels = message.get('channels', ['app'])
        priority = message.get('priority', 'medium')
        lamport_ts = message.get('lamport_timestamp', {})
        
        print(f"[Dispatcher {NODE_ID}] Processing notification for event {event_id}")
        print(f"[Dispatcher {NODE_ID}] Lamport timestamp: {lamport_ts}")
        print(f"[Dispatcher {NODE_ID}] Channels: {channels}, Priority: {priority}, Subscribers: {len(subscriber_ids)}")
        
        # Create notification object with Lamport timestamp
        notification = {
            'event_id': event_id,
            'title': title,
            'description': description,
            'topic': message.get('topic'),
            'location': message.get('location'),
            'start_time': message.get('start_time'),
            'media_url': message.get('media_url'),
            'priority': priority,
            'timestamp': message.get('timestamp', int(time.time())),
            'lamport_timestamp': lamport_ts,  # For distributed ordering
            'read': False
        }
        
        # Process each channel
        for subscriber_id in subscriber_ids:
            if 'app' in channels:
                # In-app notification
                print(f"[Dispatcher {NODE_ID}] Adding in-app notification for user {subscriber_id}", flush=True)
                add_in_app_notification(subscriber_id, notification.copy())
                print(f"[Dispatcher {NODE_ID}] Notification added for user {subscriber_id}", flush=True)
            
            # Email and SMS would require user contact info
            # In production, fetch from Users table
            if 'email' in channels:
                # TODO: Fetch user email from DynamoDB
                # send_email_notification(user_email, title, description)
                print(f"[Dispatcher {NODE_ID}] Would send email to user {subscriber_id}", flush=True)
            
            if 'sms' in channels:
                # TODO: Fetch user phone from DynamoDB
                # send_sms_notification(user_phone, f"{title}: {description[:100]}")
                print(f"[Dispatcher {NODE_ID}] Would send SMS to user {subscriber_id}", flush=True)
        
        print(f"[Dispatcher {NODE_ID}] Completed processing notification for event {event_id}", flush=True)
        return True
    
    except Exception as e:
        print(f"[Dispatcher] Error processing notification: {e}")
        import traceback
        traceback.print_exc()
        return False


def rabbitmq_consumer_loop():
    """Background thread for consuming RabbitMQ messages"""
    print(f"[Dispatcher {NODE_ID}] Starting RabbitMQ consumer thread", flush=True)
    
    while True:
        connection = None
        try:
            print(f"[Dispatcher {NODE_ID}] Attempting to connect to RabbitMQ at {RABBITMQ_HOST}:{RABBITMQ_PORT}", flush=True)
            connection = get_rabbitmq_connection()
            if not connection:
                print(f"[Dispatcher {NODE_ID}] RabbitMQ not available, retrying in 5s...", flush=True)
                time.sleep(5)
                continue
            
            print(f"[Dispatcher {NODE_ID}] RabbitMQ connected successfully", flush=True)
            channel = connection.channel()
            
            # Declare exchange
            channel.exchange_declare(
                exchange=RABBITMQ_EXCHANGE,
                exchange_type='topic',
                durable=True
            )
            print(f"[Dispatcher {NODE_ID}] Exchange '{RABBITMQ_EXCHANGE}' declared", flush=True)
            
            # Declare queue
            channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
            print(f"[Dispatcher {NODE_ID}] Queue '{RABBITMQ_QUEUE}' declared", flush=True)
            
            # Bind to all topics (using wildcard)
            # In production, you might bind to specific topics per dispatcher
            channel.queue_bind(
                exchange=RABBITMQ_EXCHANGE,
                queue=RABBITMQ_QUEUE,
                routing_key='#'  # Subscribe to all topics
            )
            print(f"[Dispatcher {NODE_ID}] Queue bound to exchange with routing key '#'", flush=True)
            
            # Set QoS
            channel.basic_qos(prefetch_count=1)
            
            print(f"[Dispatcher {NODE_ID}] *** NOW CONSUMING from queue: {RABBITMQ_QUEUE} ***", flush=True)
            
            def callback(ch, method, properties, body):
                """Message callback"""
                try:
                    print(f"[Dispatcher {NODE_ID}] *** RECEIVED MESSAGE from RabbitMQ ***", flush=True)
                    message = json.loads(body)
                    print(f"[Dispatcher {NODE_ID}] Message: {json.dumps(message, indent=2)}", flush=True)
                    success = process_notification(message)
                    
                    if success:
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                        print(f"[Dispatcher {NODE_ID}] Message acknowledged", flush=True)
                    else:
                        # Reject and requeue
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                        print(f"[Dispatcher {NODE_ID}] Message rejected and requeued", flush=True)
                
                except Exception as e:
                    print(f"[Dispatcher {NODE_ID}] Error in callback: {e}", flush=True)
                    traceback.print_exc()
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            
            # Start consuming
            channel.basic_consume(queue=RABBITMQ_QUEUE, on_message_callback=callback)
            print(f"[Dispatcher {NODE_ID}] Starting to consume messages...", flush=True)
            channel.start_consuming()
        
        except Exception as e:
            print(f"[Dispatcher {NODE_ID}] RabbitMQ consumer error: {e}", flush=True)
            traceback.print_exc()
            time.sleep(5)
        
        finally:
            if connection and not connection.is_closed:
                try:
                    connection.close()
                    print(f"[Dispatcher {NODE_ID}] RabbitMQ connection closed", flush=True)
                except:
                    pass


# ============================================================================
# Leader-Only Tasks
# ============================================================================

def leader_task_loop():
    """Background tasks that only the leader performs"""
    print("[Dispatcher] Started leader task monitoring thread")
    
    while True:
        try:
            time.sleep(30)  # Run every 30 seconds
            
            if election and election.is_leader():
                print("[Dispatcher] Performing leader tasks...")
                
                # Task 1: Aggregate and save topic popularity to DynamoDB
                try:
                    tracker = get_tracker()
                    tracker.bulk_save_to_dynamodb()
                    print("[Dispatcher] Saved popularity data to DynamoDB")
                except Exception as e:
                    print(f"[Dispatcher] Error saving popularity: {e}")
                
                # Task 2: Cleanup old in-app notifications (optional)
                try:
                    cleanup_old_notifications()
                except Exception as e:
                    print(f"[Dispatcher] Error cleaning notifications: {e}")
                
                # Task 3: Report metrics to gossip agent (optional)
                try:
                    report_metrics_to_gossip()
                except Exception as e:
                    print(f"[Dispatcher] Error reporting metrics: {e}")
            
        except Exception as e:
            print(f"[Dispatcher] Error in leader task loop: {e}")


def cleanup_old_notifications():
    """Remove old notifications (leader-only task)"""
    cutoff_time = time.time() - (7 * 24 * 3600)  # 7 days ago
    
    with notifications_lock:
        for user_id, notifs in list(in_app_notifications.items()):
            # Remove old notifications
            filtered = deque(
                [n for n in notifs if n.get('timestamp', 0) > cutoff_time],
                maxlen=100
            )
            in_app_notifications[user_id] = filtered


def report_metrics_to_gossip():
    """Report metrics to gossip agent"""
    try:
        metrics = {
            'node_id': NODE_ID,
            'queue_length': len(in_app_notifications),
            'timestamp': int(time.time())
        }
        
        requests.post(
            f"{GOSSIP_AGENT_URL}/metrics",
            json=metrics,
            timeout=2
        )
    except Exception as e:
        print(f"[Dispatcher] Failed to report metrics: {e}")


# ============================================================================
# MCP Integration
# ============================================================================

def start_mcp_and_election():
    """Initialize MCP and leader election"""
    global election
    
    # Register this node with MCP
    node_info = NodeInfo(
        node_id=NODE_ID,
        role='dispatcher',
        status=NodeStatus.ALIVE.value,
        last_seen=time.time(),
        host='localhost',
        port=PORT,
        load={'queue_len': 0, 'cpu': 0.0}
    )
    
    mcp.register_node(node_info)
    mcp.start_monitoring()
    
    print("[Dispatcher] Registered with MCP")
    
    # Initialize leader election with peer nodes
    if not PEER_NODES or all(not node.strip() for node in PEER_NODES):
        print("[Dispatcher] Running in single-node mode (no leader election)")
        # Still initialize election with just this node
        all_dispatcher_nodes = {NODE_ID: NODE_URL}
    else:
        # Parse peer nodes
        all_dispatcher_nodes = {NODE_ID: NODE_URL}
        for peer_url in PEER_NODES:
            peer_url = peer_url.strip()
            if peer_url:
                # Extract node_id from URL (e.g., notification-dispatcher-2 from http://notification-dispatcher-2:5014)
                peer_id = peer_url.split('//')[1].split(':')[0]
                all_dispatcher_nodes[peer_id] = peer_url
        
        print(f"[Dispatcher] Initializing leader election with nodes: {all_dispatcher_nodes}")
    
    election = BullyElection(
        node_id=NODE_ID,
        node_url=NODE_URL,
        all_nodes=all_dispatcher_nodes
    )
    
    # Register callbacks
    election.on_become_leader = on_become_leader
    election.on_lose_leadership = on_lose_leadership
    
    election.start()
    
    print("[Dispatcher] Leader election initialized")


def on_become_leader():
    """Callback when this node becomes leader"""
    print(f"[Dispatcher] *** Node {NODE_ID} became LEADER ***")
    # Start leader-specific tasks


def on_lose_leadership():
    """Callback when this node loses leadership"""
    print(f"[Dispatcher] *** Node {NODE_ID} lost leadership ***")
    # Stop leader-specific tasks


def send_heartbeat_loop():
    """Send periodic heartbeats to MCP"""
    while True:
        try:
            time.sleep(5)
            
            metrics = {
                'queue_len': len(in_app_notifications),
                'cpu': 0.5  # Placeholder
            }
            
            mcp.update_heartbeat(NODE_ID, metrics)
        
        except Exception as e:
            print(f"[Dispatcher] Error sending heartbeat: {e}")


# ============================================================================
# API Endpoints
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'notification-dispatcher',
        'node_id': NODE_ID,
        'is_leader': election.is_leader() if election else False
    }), 200


@app.route('/election/status', methods=['GET'])
def election_status():
    """Get election status"""
    if not election:
        return jsonify({'error': 'Election not initialized'}), 500
    
    return jsonify({
        'node_id': NODE_ID,
        'is_leader': election.is_leader(),
        'current_leader': election.get_leader(),
        'state': election.state.value
    }), 200


@app.route('/election/message', methods=['POST'])
def handle_election_message():
    """Handle election protocol messages (ELECTION, COORDINATOR)"""
    if not election:
        return jsonify({'error': 'Election not initialized'}), 500
    
    try:
        data = request.get_json()
        msg_type = data.get('type')
        
        if msg_type == 'ELECTION':
            from_node = data.get('from_node')
            should_respond = election.handle_election_message(from_node)
            return jsonify({'respond': should_respond}), 200
        
        elif msg_type == 'COORDINATOR':
            leader_id = data.get('leader_id')
            leader_url = data.get('leader_url')
            election.handle_coordinator_message(leader_id, leader_url)
            return jsonify({'success': True}), 200
        
        else:
            return jsonify({'error': 'Unknown message type'}), 400
    
    except Exception as e:
        print(f"[Dispatcher] Error handling election message: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/election/heartbeat', methods=['POST'])
def handle_election_heartbeat():
    """Handle leader heartbeat"""
    if not election:
        return jsonify({'error': 'Election not initialized'}), 500
    
    try:
        data = request.get_json()
        leader_id = data.get('leader_id')
        election.handle_heartbeat(leader_id)
        return jsonify({'success': True}), 200
    
    except Exception as e:
        print(f"[Dispatcher] Error handling heartbeat: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/notifications/<user_id>', methods=['GET'])
def get_notifications(user_id):
    """
    Get in-app notifications for a user.
    
    Query params:
        limit: Max notifications to return (default 50)
    
    Response:
    {
        "notifications": [...]
    }
    """
    try:
        limit = int(request.args.get('limit', 50))
        notifications = get_user_notifications(user_id, limit)
        
        return jsonify({
            'notifications': notifications,
            'count': len(notifications)
        }), 200
    
    except Exception as e:
        print(f"[Dispatcher] Error getting notifications: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/mcp/membership', methods=['GET'])
def get_membership():
    """Get current MCP membership state"""
    membership = mcp.get_membership_snapshot()
    return jsonify({'membership': membership}), 200


# ============================================================================
# Startup
# ============================================================================

def start_background_threads():
    """Start all background threads"""
    # MCP and election
    threading.Thread(target=start_mcp_and_election, daemon=True).start()
    
    # Heartbeat sender
    threading.Thread(target=send_heartbeat_loop, daemon=True).start()
    
    # RabbitMQ consumer
    threading.Thread(target=rabbitmq_consumer_loop, daemon=True).start()
    
    # Leader tasks
    threading.Thread(target=leader_task_loop, daemon=True).start()
    
    print("[Dispatcher] All background threads started")


# Start background threads before Flask starts
start_background_threads()


# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)

