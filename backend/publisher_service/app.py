"""
Publisher Service

Manages events and publishes them to RabbitMQ with publisher-side filtering.
Uses AWS DynamoDB for event storage and AWS S3 for media files.

Key Features:
- Event CRUD operations
- Publisher-side filtering (reduces network traffic)
- Popularity-based priority assignment
- Integration with RabbitMQ topic exchange
- Bully leader election for coordinated tasks

Endpoints:
- POST /events - Create new event
- PUT /events/<event_id> - Update event
- GET /events - List events
- GET /events/<event_id> - Get single event
- POST /events/<event_id>/publish - Publish event to subscribers
- POST /events/<event_id>/unpublish - Unpublish event
- GET /election/status - Get election status
- POST /election/message - Handle election messages
- POST /election/heartbeat - Handle leader heartbeat
- GET /health - Health check
"""

import os
import sys
import time
import json
import threading
from decimal import Decimal
import boto3
import pika
import requests
from botocore.exceptions import ClientError
from flask import Flask, request, jsonify
from flask_cors import CORS

# Add libs to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from libs.filtering import get_subscribers_for_event, build_notification_payload
from libs.popularity import increment_topic, get_priority
from libs.timestamps import get_lamport_clock, create_timestamped_event
from libs.leader_election import BullyElection

app = Flask(__name__)
CORS(app)

# Configuration
NODE_ID = os.getenv('NODE_ID', f'publisher-{int(time.time())}')
NODE_URL = os.getenv('NODE_URL', 'http://localhost:5003')
PEER_NODES = os.getenv('PEER_NODES', '').split(',') if os.getenv('PEER_NODES') else []
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
EVENTS_TABLE = os.getenv('EVENTS_TABLE', 'Events')
S3_BUCKET = os.getenv('EVENT_MEDIA_BUCKET', 'event-media-bucket')
SUBSCRIPTION_SERVICE_URL = os.getenv('SUBSCRIPTION_SERVICE_URL', 'http://localhost:5002')
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', '5672'))
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'guest')
RABBITMQ_EXCHANGE = os.getenv('RABBITMQ_EXCHANGE', 'events.topic')
PORT = int(os.getenv('PORT', '5003'))

# Initialize AWS services
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
events_table = dynamodb.Table(EVENTS_TABLE)
s3_client = boto3.client('s3', region_name=AWS_REGION)

# Initialize Leader Election
election = None  # Initialized after Flask app starts

print(f"[Publisher] Starting node {NODE_ID} on port {PORT}")
print(f"[Publisher] Node URL: {NODE_URL}")
print(f"[Publisher] Peer nodes: {PEER_NODES if PEER_NODES else 'None (single node mode)'}")
print(f"[Publisher] Using DynamoDB table: {EVENTS_TABLE}")
print(f"[Publisher] RabbitMQ: {RABBITMQ_HOST}:{RABBITMQ_PORT}")


# ============================================================================
# Helper Functions
# ============================================================================

def decimal_to_number(obj):
    """
    Convert DynamoDB Decimal objects to int or float for JSON serialization.
    
    Args:
        obj: Object that may contain Decimal values
        
    Returns:
        Object with Decimals converted to int/float
    """
    if isinstance(obj, list):
        return [decimal_to_number(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: decimal_to_number(value) for key, value in obj.items()}
    elif isinstance(obj, Decimal):
        # Convert to int if no decimal places, otherwise float
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    else:
        return obj


# ============================================================================
# RabbitMQ Connection
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
        print(f"[Publisher] Failed to connect to RabbitMQ: {e}")
        return None


def publish_to_rabbitmq(routing_key: str, message: dict):
    """
    Publish message to RabbitMQ topic exchange.
    
    Args:
        routing_key: Topic routing key (e.g., 'hackathon.aiml')
        message: Message payload as dict
    """
    connection = None
    try:
        connection = get_rabbitmq_connection()
        if not connection:
            print("[Publisher] RabbitMQ connection failed, skipping publish", flush=True)
            return False
        
        channel = connection.channel()
        
        # Declare topic exchange
        channel.exchange_declare(
            exchange=RABBITMQ_EXCHANGE,
            exchange_type='topic',
            durable=True
        )
        
        # Publish message
        # Convert Decimal objects to int/float for JSON serialization
        message_clean = decimal_to_number(message)
        channel.basic_publish(
            exchange=RABBITMQ_EXCHANGE,
            routing_key=routing_key,
            body=json.dumps(message_clean),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
                content_type='application/json',
                priority=_get_priority_int(message.get('priority', 'medium'))
            )
        )
        
        print(f"[Publisher] Published message to {routing_key}", flush=True)
        return True
    
    except Exception as e:
        print(f"[Publisher] Error publishing to RabbitMQ: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        if connection and not connection.is_closed:
            connection.close()


def _get_priority_int(priority_str: str) -> int:
    """Convert priority string to integer (0-9)"""
    mapping = {'low': 3, 'medium': 5, 'high': 8}
    return mapping.get(priority_str, 5)


# ============================================================================
# Helper Functions
# ============================================================================

def get_user_from_token(request_obj):
    """Extract user info from request"""
    user_id = request_obj.headers.get('X-User-ID', '')
    role = request_obj.headers.get('X-User-Role', 'student')
    
    if not user_id:
        return None, None, "Missing authentication"
    
    return user_id, role, None


def validate_event_data(data):
    """Validate event creation data"""
    required_fields = ['title', 'topic', 'start_time']
    
    for field in required_fields:
        if field not in data or not data[field]:
            return False, f"Missing required field: {field}"
    
    # Validate topic format
    topic = data['topic']
    if '.' not in topic:
        return False, "Topic must be in format 'category.subcategory' (e.g., 'hackathon.aiml')"
    
    return True, None


def fetch_all_subscriptions():
    """Fetch all subscriptions from subscription service"""
    try:
        response = requests.get(
            f"{SUBSCRIPTION_SERVICE_URL}/subscriptions/all",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get('subscriptions', [])
        else:
            print(f"[Publisher] Error fetching subscriptions: {response.status_code}")
            return []
    
    except Exception as e:
        print(f"[Publisher] Failed to fetch subscriptions: {e}")
        return []


# ============================================================================
# API Endpoints
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'publisher-service',
        'node_id': NODE_ID,
        'is_leader': election.is_leader() if election else False
    }), 200


@app.route('/events', methods=['POST'])
def create_event():
    """
    Create a new event.
    
    Headers:
        X-User-ID: user_id
        X-User-Role: role
    
    Request body:
    {
        "title": "AI/ML Hackathon 2024",
        "description": "Join us for...",
        "topic": "hackathon.aiml",
        "start_time": 1734567890,
        "end_time": 1734654290,
        "location": "San Francisco, CA",
        "level": "beginner",  // optional
        "media_url": ""  // optional, S3 URL
    }
    
    Response:
    {
        "success": true,
        "event_id": "...",
        "event": {...}
    }
    """
    try:
        user_id, role, error = get_user_from_token(request)
        if error:
            return jsonify({'error': error}), 401
        
        # Check if user is organizer or admin
        if role not in ['organizer', 'admin']:
            return jsonify({'error': 'Only organizers and admins can create events'}), 403
        
        data = request.get_json()
        
        # Validate input
        is_valid, error_msg = validate_event_data(data)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        # Generate event ID
        event_id = f"E{int(time.time() * 1000)}"
        
        # Create event record
        event = {
            'event_id': event_id,
            'title': data['title'],
            'description': data.get('description', ''),
            'topic': data['topic'],
            'start_time': int(data['start_time']),
            'end_time': int(data.get('end_time', data['start_time'] + 3600)),
            'location': data.get('location', 'TBD'),
            'level': data.get('level', ''),
            'organizer_id': user_id,
            'media_url': data.get('media_url', ''),
            'popularity_score': 0,
            'status': 'draft',  # draft, published
            'created_at': int(time.time()),
            'updated_at': int(time.time())
        }
        
        # Save to DynamoDB
        events_table.put_item(Item=event)
        
        print(f"[Publisher] Created event: {event_id} ({event['title']})")
        
        return jsonify({
            'success': True,
            'event_id': event_id,
            'event': event
        }), 201
    
    except ClientError as e:
        print(f"[Publisher] DynamoDB error: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    
    except Exception as e:
        print(f"[Publisher] Error creating event: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/events/<event_id>', methods=['GET'])
def get_event(event_id):
    """
    Get a single event by ID.
    
    Response:
    {
        "event": {...}
    }
    """
    try:
        response = events_table.get_item(Key={'event_id': event_id})
        
        if 'Item' not in response:
            return jsonify({'error': 'Event not found'}), 404
        
        event = response['Item']
        
        # Increment view count (optional popularity tracking)
        increment_topic(event['topic'], amount=1)
        
        return jsonify({'event': event}), 200
    
    except ClientError as e:
        print(f"[Publisher] DynamoDB error: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    
    except Exception as e:
        print(f"[Publisher] Error getting event: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/events', methods=['GET'])
def list_events():
    """
    List all events (with optional filters).
    
    Query params:
        topic: Filter by topic
        status: Filter by status (draft, published)
        limit: Max number of events (default 50)
    
    Response:
    {
        "events": [...],
        "count": 10
    }
    """
    try:
        topic = request.args.get('topic')
        status = request.args.get('status')
        limit = int(request.args.get('limit', 50))
        
        # Scan with filters
        scan_kwargs = {'Limit': limit}
        filter_expressions = []
        expression_values = {}
        
        if topic:
            filter_expressions.append('topic = :topic')
            expression_values[':topic'] = topic
        
        if status:
            filter_expressions.append('#status = :status')
            expression_values[':status'] = status
            scan_kwargs['ExpressionAttributeNames'] = {'#status': 'status'}
        
        if filter_expressions:
            scan_kwargs['FilterExpression'] = ' AND '.join(filter_expressions)
            scan_kwargs['ExpressionAttributeValues'] = expression_values
        
        response = events_table.scan(**scan_kwargs)
        events = response['Items']
        
        # Sort by created_at descending
        events.sort(key=lambda x: x.get('created_at', 0), reverse=True)
        
        return jsonify({
            'events': events,
            'count': len(events)
        }), 200
    
    except ClientError as e:
        print(f"[Publisher] DynamoDB error: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    
    except Exception as e:
        print(f"[Publisher] Error listing events: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/events/<event_id>', methods=['PUT'])
def update_event(event_id):
    """
    Update an existing event.
    
    Headers:
        X-User-ID: user_id
        X-User-Role: role
    
    Request body: Same as create_event (partial updates allowed)
    """
    try:
        user_id, role, error = get_user_from_token(request)
        if error:
            return jsonify({'error': error}), 401
        
        # Get existing event
        response = events_table.get_item(Key={'event_id': event_id})
        
        if 'Item' not in response:
            return jsonify({'error': 'Event not found'}), 404
        
        event = response['Item']
        
        # Check permissions
        if event['organizer_id'] != user_id and role != 'admin':
            return jsonify({'error': 'Unauthorized to update this event'}), 403
        
        data = request.get_json()
        
        # Update fields
        update_expr = []
        expr_values = {}
        
        updatable_fields = ['title', 'description', 'topic', 'start_time', 'end_time', 
                           'location', 'level', 'media_url']
        
        for field in updatable_fields:
            if field in data:
                update_expr.append(f"{field} = :{field}")
                expr_values[f":{field}"] = data[field]
        
        if not update_expr:
            return jsonify({'error': 'No fields to update'}), 400
        
        update_expr.append("updated_at = :updated_at")
        expr_values[':updated_at'] = int(time.time())
        
        # Perform update
        events_table.update_item(
            Key={'event_id': event_id},
            UpdateExpression='SET ' + ', '.join(update_expr),
            ExpressionAttributeValues=expr_values
        )
        
        print(f"[Publisher] Updated event: {event_id}")
        
        # Fetch updated event
        response = events_table.get_item(Key={'event_id': event_id})
        updated_event = response['Item']
        
        return jsonify({
            'success': True,
            'event': updated_event
        }), 200
    
    except ClientError as e:
        print(f"[Publisher] DynamoDB error: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    
    except Exception as e:
        print(f"[Publisher] Error updating event: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/events/<event_id>/publish', methods=['POST'])
def publish_event(event_id):
    """
    Publish an event to subscribers with PUBLISHER-SIDE FILTERING.
    
    This is a key distributed systems optimization:
    1. Fetch all subscriptions
    2. Filter subscribers based on topic, location, level, etc.
    3. Only send notifications to matching subscribers
    4. Assign priority based on topic popularity
    5. Publish to RabbitMQ
    
    Headers:
        X-User-ID: user_id
        X-User-Role: role
    
    Response:
    {
        "success": true,
        "event_id": "...",
        "subscribers_count": 10,
        "priority": "high"
    }
    """
    try:
        user_id, role, error = get_user_from_token(request)
        if error:
            return jsonify({'error': error}), 401
        
        # Get event
        response = events_table.get_item(Key={'event_id': event_id})
        
        if 'Item' not in response:
            return jsonify({'error': 'Event not found'}), 404
        
        event = response['Item']
        
        # Check permissions
        if event['organizer_id'] != user_id and role != 'admin':
            return jsonify({'error': 'Unauthorized to publish this event'}), 403
        
        print(f"[Publisher] Publishing event {event_id}: {event['title']}", flush=True)
        
        # Step 1: Fetch all subscriptions
        all_subscriptions = fetch_all_subscriptions()
        print(f"[Publisher] Fetched {len(all_subscriptions)} total subscriptions")
        
        # Step 2: PUBLISHER-SIDE FILTERING
        # Filter subscriptions to find matching subscribers
        matching_subscribers = get_subscribers_for_event(event, all_subscriptions)
        print(f"[Publisher] After filtering: {len(matching_subscribers)} matching subscribers")
        
        if not matching_subscribers:
            return jsonify({
                'success': True,
                'message': 'Event published but no matching subscribers',
                'subscribers_count': 0
            }), 200
        
        # Step 3: Increment topic popularity
        increment_topic(event['topic'], amount=1)
        
        # Step 4: Get priority based on popularity
        priority = get_priority(event['topic'])
        print(f"[Publisher] Topic {event['topic']} priority: {priority}")
        
        # Step 5: Build notification payload with Lamport timestamp
        notification_payload = build_notification_payload(
            event=event,
            subscribers=matching_subscribers,
            priority=priority
        )
        
        # Add Lamport timestamp for distributed ordering
        node_id = os.getenv('HOSTNAME', 'publisher-service')
        timestamped_payload = create_timestamped_event(notification_payload, node_id)
        notification_payload = timestamped_payload
        
        # Add timestamp
        notification_payload['timestamp'] = int(time.time())
        
        # Step 6: Publish to RabbitMQ
        routing_key = event['topic']
        success = publish_to_rabbitmq(routing_key, notification_payload)
        
        if not success:
            return jsonify({
                'error': 'Failed to publish to message queue',
                'subscribers_count': len(matching_subscribers)
            }), 500
        
        # Step 7: Update event status
        events_table.update_item(
            Key={'event_id': event_id},
            UpdateExpression='SET #status = :status, updated_at = :updated_at',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'published',
                ':updated_at': int(time.time())
            }
        )
        
        print(f"[Publisher] Successfully published event {event_id} to {len(matching_subscribers)} subscribers")
        
        return jsonify({
            'success': True,
            'event_id': event_id,
            'subscribers_count': len(matching_subscribers),
            'priority': priority,
            'message': f'Event published to {len(matching_subscribers)} subscribers'
        }), 200
    
    except ClientError as e:
        print(f"[Publisher] DynamoDB error: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    
    except Exception as e:
        print(f"[Publisher] Error publishing event: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/events/<event_id>/unpublish', methods=['POST'])
def unpublish_event(event_id):
    """
    Unpublish an event (change status from published to draft).
    
    Only organizers and admins can unpublish events.
    This removes the event from public view for students.
    
    Headers:
        X-User-ID: user_id
        X-User-Role: role
    
    Response:
    {
        "success": true,
        "event_id": "...",
        "message": "Event unpublished"
    }
    """
    try:
        user_id, role, error = get_user_from_token(request)
        if error:
            return jsonify({'error': error}), 401
        
        # Get event
        response = events_table.get_item(Key={'event_id': event_id})
        
        if 'Item' not in response:
            return jsonify({'error': 'Event not found'}), 404
        
        event = response['Item']
        
        # Check permissions
        if event['organizer_id'] != user_id and role != 'admin':
            return jsonify({'error': 'Unauthorized to unpublish this event'}), 403
        
        # Check if already draft
        if event.get('status') == 'draft':
            return jsonify({'error': 'Event is already unpublished'}), 400
        
        print(f"[Publisher] Unpublishing event {event_id}: {event['title']}")
        
        # Update event status to draft
        events_table.update_item(
            Key={'event_id': event_id},
            UpdateExpression='SET #status = :status, updated_at = :updated_at',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'draft',
                ':updated_at': int(time.time())
            }
        )
        
        print(f"[Publisher] Successfully unpublished event {event_id}")
        
        return jsonify({
            'success': True,
            'event_id': event_id,
            'message': 'Event unpublished successfully'
        }), 200
    
    except ClientError as e:
        print(f"[Publisher] DynamoDB error: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    
    except Exception as e:
        print(f"[Publisher] Error unpublishing event: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# Leader Election Endpoints
# ============================================================================

@app.route('/election/status', methods=['GET'])
def election_status():
    """Get election status"""
    if not election:
        return jsonify({'error': 'Election not initialized'}), 500
    
    try:
        return jsonify({
            'node_id': NODE_ID,
            'is_leader': election.is_leader(),
            'current_leader': election.get_leader(),
            'state': election.state.value
        }), 200
    except Exception as e:
        print(f"[Publisher] Error getting election status: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/election/message', methods=['POST'])
def handle_election_message():
    """Handle election protocol messages (ELECTION, COORDINATOR)"""
    if not election:
        return jsonify({'error': 'Election not initialized'}), 500
    
    try:
        data = request.get_json()
        msg_type = data.get('type')
        from_node = data.get('from_node')
        
        if msg_type == 'ELECTION':
            # Received election message
            should_respond = election.handle_election_message(from_node)
            return jsonify({'success': True, 'responded': should_respond}), 200
        
        elif msg_type == 'COORDINATOR':
            # Received coordinator announcement
            leader_id = data.get('leader_id')
            leader_url = data.get('leader_url')
            election.handle_coordinator_message(leader_id, leader_url)
            return jsonify({'success': True}), 200
        
        return jsonify({'error': 'Unknown message type'}), 400
    
    except Exception as e:
        print(f"[Publisher] Error handling election message: {e}")
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
        print(f"[Publisher] Error handling heartbeat: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# Leader Election Initialization
# ============================================================================

def on_become_leader():
    """Called when this node becomes the leader"""
    print(f"[Publisher] 🏆 Node {NODE_ID} became the LEADER")
    # Leader can perform exclusive tasks here


def on_lose_leadership():
    """Called when this node loses leadership"""
    print(f"[Publisher] ⚠️  Node {NODE_ID} lost leadership")


def start_election():
    """Initialize leader election"""
    global election
    
    if not PEER_NODES or all(not node.strip() for node in PEER_NODES):
        print("[Publisher] Running in single-node mode (no leader election)")
        return
    
    # Parse peer nodes
    peers = {}
    for peer_url in PEER_NODES:
        peer_url = peer_url.strip()
        if peer_url:
            # Extract node_id from URL (e.g., publisher-service-2 from http://publisher-service-2:5013)
            peer_id = peer_url.split('//')[1].split(':')[0]
            peers[peer_id] = peer_url
    
    print(f"[Publisher] Initializing leader election with peers: {peers}")
    
    # Initialize Bully Election
    all_nodes = {NODE_ID: NODE_URL}
    all_nodes.update(peers)
    
    election = BullyElection(
        node_id=NODE_ID,
        node_url=NODE_URL,
        all_nodes=all_nodes
    )
    
    election.on_become_leader = on_become_leader
    election.on_lose_leadership = on_lose_leadership
    
    election.start()
    
    print("[Publisher] Leader election initialized")


# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    # Start leader election in background
    if PEER_NODES:
        threading.Thread(target=start_election, daemon=True).start()
    
    app.run(host='0.0.0.0', port=PORT, debug=os.getenv('FLASK_ENV') == 'development')

