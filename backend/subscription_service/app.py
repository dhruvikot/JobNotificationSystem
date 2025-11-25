"""
Subscription Service

Manages user topic subscriptions and notification preferences.
Uses AWS DynamoDB for storage.

Endpoints:
- GET /subscriptions - Get user's subscriptions
- POST /subscriptions - Create new subscription
- DELETE /subscriptions/<topic> - Delete subscription
- GET /subscriptions/topics - Get all available topics
- GET /health - Health check
"""

import os
import time
import boto3
from botocore.exceptions import ClientError
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configuration
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
SUBSCRIPTIONS_TABLE = os.getenv('SUBSCRIPTIONS_TABLE', 'Subscriptions')
PORT = int(os.getenv('PORT', '5002'))

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
subscriptions_table = dynamodb.Table(SUBSCRIPTIONS_TABLE)

print(f"[Subscription Service] Starting on port {PORT}")
print(f"[Subscription Service] Using DynamoDB table: {SUBSCRIPTIONS_TABLE}")


# ============================================================================
# Predefined Topics (can be extended)
# ============================================================================

AVAILABLE_TOPICS = [
    # Hackathons
    {'topic': 'hackathon.aiml', 'name': 'AI/ML Hackathons', 'category': 'hackathon'},
    {'topic': 'hackathon.web', 'name': 'Web Development Hackathons', 'category': 'hackathon'},
    {'topic': 'hackathon.mobile', 'name': 'Mobile Development Hackathons', 'category': 'hackathon'},
    {'topic': 'hackathon.blockchain', 'name': 'Blockchain Hackathons', 'category': 'hackathon'},
    {'topic': 'hackathon.*', 'name': 'All Hackathons', 'category': 'hackathon'},
    
    # Jobs
    {'topic': 'jobs.internship', 'name': 'Internship Opportunities', 'category': 'jobs'},
    {'topic': 'jobs.fulltime', 'name': 'Full-Time Jobs', 'category': 'jobs'},
    {'topic': 'jobs.swe', 'name': 'Software Engineering Jobs', 'category': 'jobs'},
    {'topic': 'jobs.datascience', 'name': 'Data Science Jobs', 'category': 'jobs'},
    {'topic': 'jobs.*', 'name': 'All Job Opportunities', 'category': 'jobs'},
    
    # Career Fairs
    {'topic': 'careerfair.tech', 'name': 'Tech Career Fairs', 'category': 'careerfair'},
    {'topic': 'careerfair.business', 'name': 'Business Career Fairs', 'category': 'careerfair'},
    {'topic': 'careerfair.*', 'name': 'All Career Fairs', 'category': 'careerfair'},
    
    # Workshops
    {'topic': 'workshop.technical', 'name': 'Technical Workshops', 'category': 'workshop'},
    {'topic': 'workshop.leadership', 'name': 'Leadership Workshops', 'category': 'workshop'},
    {'topic': 'workshop.career', 'name': 'Career Development Workshops', 'category': 'workshop'},
    {'topic': 'workshop.*', 'name': 'All Workshops', 'category': 'workshop'},
    
    # Meetups
    {'topic': 'meetup.networking', 'name': 'Networking Meetups', 'category': 'meetup'},
    {'topic': 'meetup.tech', 'name': 'Tech Meetups', 'category': 'meetup'},
    {'topic': 'meetup.*', 'name': 'All Meetups', 'category': 'meetup'},
]


# ============================================================================
# Helper Functions
# ============================================================================

def get_user_from_token(request_obj):
    """Extract user_id from JWT token in Authorization header"""
    # In production, this should verify the JWT
    # For now, we'll accept a simple user_id in the header
    auth_header = request_obj.headers.get('Authorization', '')
    
    if auth_header.startswith('Bearer '):
        # Extract user_id from token (simplified - should decode JWT)
        # For demo, we can accept user_id directly in X-User-ID header
        pass
    
    # Fallback: use X-User-ID header
    user_id = request_obj.headers.get('X-User-ID', '')
    
    if not user_id:
        return None, "Missing authentication"
    
    return user_id, None


def validate_subscription_data(data):
    """Validate subscription request data"""
    if not data:
        return False, "No data provided"
    
    if 'topic' not in data:
        return False, "Missing 'topic' field"
    
    topic = data['topic']
    
    # Validate topic exists
    valid_topics = [t['topic'] for t in AVAILABLE_TOPICS]
    if topic not in valid_topics:
        return False, f"Invalid topic. Choose from: {', '.join(valid_topics)}"
    
    # Validate channels
    channels = data.get('channels', ['app'])
    valid_channels = ['app', 'email', 'sms']
    
    if not isinstance(channels, list):
        return False, "Channels must be a list"
    
    for channel in channels:
        if channel not in valid_channels:
            return False, f"Invalid channel: {channel}. Valid channels: {', '.join(valid_channels)}"
    
    return True, None


# ============================================================================
# API Endpoints
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'subscription-service'
    }), 200


@app.route('/subscriptions/topics', methods=['GET'])
def get_topics():
    """
    Get all available topics.
    
    Response:
    {
        "topics": [
            {"topic": "...", "name": "...", "category": "..."},
            ...
        ]
    }
    """
    return jsonify({'topics': AVAILABLE_TOPICS}), 200


@app.route('/subscriptions', methods=['GET'])
def get_subscriptions():
    """
    Get all subscriptions for the authenticated user.
    
    Headers:
        X-User-ID: user_id
    
    Response:
    {
        "subscriptions": [
            {
                "user_id": "...",
                "topic": "...",
                "channels": ["app", "email"],
                "filters": {...},
                "created_at": 1234567890
            },
            ...
        ]
    }
    """
    try:
        user_id, error = get_user_from_token(request)
        if error:
            return jsonify({'error': error}), 401
        
        # Query subscriptions for this user
        response = subscriptions_table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('user_id').eq(user_id)
        )
        
        subscriptions = response['Items']
        
        return jsonify({'subscriptions': subscriptions}), 200
    
    except ClientError as e:
        print(f"[Subscription] DynamoDB error: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    
    except Exception as e:
        print(f"[Subscription] Error getting subscriptions: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/subscriptions', methods=['POST'])
def create_subscription():
    """
    Create a new subscription.
    
    Headers:
        X-User-ID: user_id
    
    Request body:
    {
        "topic": "hackathon.aiml",
        "channels": ["app", "email", "sms"],  // optional, default ["app"]
        "filters": {  // optional
            "locations": ["San Francisco", "Remote"],
            "levels": ["beginner", "intermediate"]
        }
    }
    
    Response:
    {
        "success": true,
        "subscription": {...}
    }
    """
    try:
        user_id, error = get_user_from_token(request)
        if error:
            return jsonify({'error': error}), 401
        
        data = request.get_json()
        
        # Validate input
        is_valid, error_msg = validate_subscription_data(data)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        topic = data['topic']
        channels = data.get('channels', ['app'])
        filters = data.get('filters', {})
        
        # Check if subscription already exists
        try:
            existing = subscriptions_table.get_item(
                Key={'user_id': user_id, 'topic': topic}
            )
            
            if 'Item' in existing:
                # Update existing subscription
                subscriptions_table.update_item(
                    Key={'user_id': user_id, 'topic': topic},
                    UpdateExpression='SET channels = :c, filters = :f, updated_at = :u',
                    ExpressionAttributeValues={
                        ':c': channels,
                        ':f': filters,
                        ':u': int(time.time())
                    }
                )
                
                return jsonify({
                    'success': True,
                    'message': 'Subscription updated',
                    'subscription': {
                        'user_id': user_id,
                        'topic': topic,
                        'channels': channels,
                        'filters': filters
                    }
                }), 200
        
        except ClientError:
            pass  # Item doesn't exist, create new
        
        # Create new subscription
        subscription = {
            'user_id': user_id,
            'topic': topic,
            'channels': channels,
            'filters': filters,
            'created_at': int(time.time()),
            'updated_at': int(time.time())
        }
        
        subscriptions_table.put_item(Item=subscription)
        
        print(f"[Subscription] Created: {user_id} -> {topic}")
        
        return jsonify({
            'success': True,
            'subscription': subscription
        }), 201
    
    except ClientError as e:
        print(f"[Subscription] DynamoDB error: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    
    except Exception as e:
        print(f"[Subscription] Error creating subscription: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/subscriptions/<topic>', methods=['DELETE'])
def delete_subscription(topic):
    """
    Delete a subscription.
    
    Headers:
        X-User-ID: user_id
    
    Response:
    {
        "success": true,
        "message": "Subscription deleted"
    }
    """
    try:
        user_id, error = get_user_from_token(request)
        if error:
            return jsonify({'error': error}), 401
        
        # Delete subscription
        subscriptions_table.delete_item(
            Key={'user_id': user_id, 'topic': topic}
        )
        
        print(f"[Subscription] Deleted: {user_id} -> {topic}")
        
        return jsonify({
            'success': True,
            'message': 'Subscription deleted'
        }), 200
    
    except ClientError as e:
        print(f"[Subscription] DynamoDB error: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    
    except Exception as e:
        print(f"[Subscription] Error deleting subscription: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/subscriptions/topic/<topic>', methods=['GET'])
def get_subscribers_for_topic(topic):
    """
    Get all subscribers for a specific topic (used by publisher service).
    
    This is an internal endpoint used for publisher-side filtering.
    
    Response:
    {
        "subscribers": [
            {
                "user_id": "...",
                "channels": ["app", "email"],
                "filters": {...}
            },
            ...
        ]
    }
    """
    try:
        # This should have API key authentication in production
        
        # Query by topic using GSI (Global Secondary Index)
        # If GSI doesn't exist, fall back to scan
        try:
            response = subscriptions_table.query(
                IndexName='TopicIndex',
                KeyConditionExpression=boto3.dynamodb.conditions.Key('topic').eq(topic)
            )
            subscribers = response['Items']
        except ClientError:
            # Fallback to scan (less efficient)
            response = subscriptions_table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr('topic').eq(topic)
            )
            subscribers = response['Items']
        
        return jsonify({'subscribers': subscribers}), 200
    
    except ClientError as e:
        print(f"[Subscription] DynamoDB error: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    
    except Exception as e:
        print(f"[Subscription] Error getting subscribers: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/subscriptions/all', methods=['GET'])
def get_all_subscriptions():
    """
    Get ALL subscriptions (used by publisher service for filtering).
    
    This is an internal endpoint. In production, add authentication.
    
    Response:
    {
        "subscriptions": [...]
    }
    """
    try:
        # Scan entire table (use pagination for large datasets)
        response = subscriptions_table.scan()
        subscriptions = response['Items']
        
        # Handle pagination if needed
        while 'LastEvaluatedKey' in response:
            response = subscriptions_table.scan(
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            subscriptions.extend(response['Items'])
        
        return jsonify({'subscriptions': subscriptions}), 200
    
    except ClientError as e:
        print(f"[Subscription] DynamoDB error: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    
    except Exception as e:
        print(f"[Subscription] Error getting all subscriptions: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=os.getenv('FLASK_ENV') == 'development')


