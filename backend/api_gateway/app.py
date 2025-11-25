"""
API Gateway

Single entry point for all client requests. Routes requests to internal
microservices and handles authentication/authorization.

Key Features:
- JWT validation for protected routes
- Request routing to internal services
- Centralized error handling
- Rate limiting (optional)
- CORS handling

Endpoints:
- POST /auth/register -> Auth Service
- POST /auth/login -> Auth Service
- GET /subscriptions -> Subscription Service
- POST /subscriptions -> Subscription Service
- DELETE /subscriptions/<topic> -> Subscription Service
- GET /subscriptions/topics -> Subscription Service
- POST /events -> Publisher Service
- GET /events -> Publisher Service
- GET /events/<event_id> -> Publisher Service
- PUT /events/<event_id> -> Publisher Service
- POST /events/<event_id>/publish -> Publisher Service
- GET /notifications/<user_id> -> Notification Dispatcher
- GET /health -> Health check
"""

import os
import jwt
import requests
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from functools import wraps

app = Flask(__name__)
CORS(app, origins='*', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

# Configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
PORT = int(os.getenv('PORT', '5000'))

# Internal service URLs
AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://localhost:5001')
SUBSCRIPTION_SERVICE_URL = os.getenv('SUBSCRIPTION_SERVICE_URL', 'http://localhost:5002')
PUBLISHER_SERVICE_URL = os.getenv('PUBLISHER_SERVICE_URL', 'http://localhost:5003')
DISPATCHER_SERVICE_URL = os.getenv('DISPATCHER_SERVICE_URL', 'http://localhost:5004')

print(f"[API Gateway] Starting on port {PORT}")
print(f"[API Gateway] Auth Service: {AUTH_SERVICE_URL}")
print(f"[API Gateway] Subscription Service: {SUBSCRIPTION_SERVICE_URL}")
print(f"[API Gateway] Publisher Service: {PUBLISHER_SERVICE_URL}")
print(f"[API Gateway] Dispatcher Service: {DISPATCHER_SERVICE_URL}")


# ============================================================================
# Authentication Middleware
# ============================================================================

def extract_token():
    """Extract JWT token from Authorization header"""
    auth_header = request.headers.get('Authorization', '')
    
    if auth_header.startswith('Bearer '):
        return auth_header.split(' ')[1]
    
    return None


def verify_token(token):
    """
    Verify JWT token and return payload.
    
    Returns: (payload, error)
    """
    if not token:
        return None, "Missing token"
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload, None
    
    except jwt.ExpiredSignatureError:
        return None, "Token expired"
    
    except jwt.InvalidTokenError:
        return None, "Invalid token"


def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = extract_token()
        payload, error = verify_token(token)
        
        if error:
            return jsonify({'error': error}), 401
        
        # Attach user info to request
        request.user_id = payload['user_id']
        request.user_email = payload['email']
        request.user_role = payload['role']
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_role(*allowed_roles):
    """Decorator to require specific role(s)"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = extract_token()
            payload, error = verify_token(token)
            
            if error:
                return jsonify({'error': error}), 401
            
            if payload['role'] not in allowed_roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            # Attach user info to request
            request.user_id = payload['user_id']
            request.user_email = payload['email']
            request.user_role = payload['role']
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


# ============================================================================
# Helper Functions
# ============================================================================

def forward_request(service_url, path, method='GET', **kwargs):
    """
    Forward request to internal service.
    
    Args:
        service_url: Base URL of service
        path: Path to append
        method: HTTP method
        **kwargs: Additional arguments for requests
    
    Returns:
        (response_data, status_code)
    """
    url = f"{service_url}{path}"
    
    try:
        # Forward request
        if method == 'GET':
            response = requests.get(url, timeout=10, **kwargs)
        elif method == 'POST':
            response = requests.post(url, timeout=10, **kwargs)
        elif method == 'PUT':
            response = requests.put(url, timeout=10, **kwargs)
        elif method == 'DELETE':
            response = requests.delete(url, timeout=10, **kwargs)
        else:
            return {'error': 'Unsupported method'}, 400
        
        # Return response
        try:
            return response.json(), response.status_code
        except:
            return {'error': 'Invalid response from service'}, 500
    
    except requests.exceptions.Timeout:
        return {'error': 'Service timeout'}, 504
    
    except requests.exceptions.ConnectionError:
        return {'error': 'Service unavailable'}, 503
    
    except Exception as e:
        print(f"[API Gateway] Error forwarding request: {e}")
        return {'error': 'Internal gateway error'}, 500


def add_user_headers(headers_dict):
    """Add user info to headers for forwarding to internal services"""
    if hasattr(request, 'user_id'):
        headers_dict['X-User-ID'] = request.user_id
        headers_dict['X-User-Email'] = request.user_email
        headers_dict['X-User-Role'] = request.user_role
    
    return headers_dict


# ============================================================================
# Health Check
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Gateway health check"""
    # Check connectivity to all services
    services_status = {}
    
    for name, url in [
        ('auth', AUTH_SERVICE_URL),
        ('subscription', SUBSCRIPTION_SERVICE_URL),
        ('publisher', PUBLISHER_SERVICE_URL),
        ('dispatcher', DISPATCHER_SERVICE_URL)
    ]:
        try:
            resp = requests.get(f"{url}/health", timeout=2)
            services_status[name] = 'healthy' if resp.status_code == 200 else 'unhealthy'
        except:
            services_status[name] = 'unavailable'
    
    overall_healthy = all(status == 'healthy' for status in services_status.values())
    
    return jsonify({
        'status': 'healthy' if overall_healthy else 'degraded',
        'service': 'api-gateway',
        'services': services_status
    }), 200 if overall_healthy else 503


# ============================================================================
# Auth Endpoints
# ============================================================================

@app.route('/auth/register', methods=['POST'])
def register():
    """Forward registration to auth service"""
    data, status = forward_request(
        AUTH_SERVICE_URL,
        '/register',
        method='POST',
        json=request.get_json()
    )
    return jsonify(data), status


@app.route('/auth/login', methods=['POST'])
def login():
    """Forward login to auth service"""
    data, status = forward_request(
        AUTH_SERVICE_URL,
        '/login',
        method='POST',
        json=request.get_json()
    )
    return jsonify(data), status


@app.route('/auth/user/<user_id>', methods=['GET'])
@require_auth
def get_user(user_id):
    """Forward get user to auth service"""
    headers = {'Authorization': request.headers.get('Authorization')}
    
    data, status = forward_request(
        AUTH_SERVICE_URL,
        f'/user/{user_id}',
        method='GET',
        headers=headers
    )
    return jsonify(data), status


# ============================================================================
# Subscription Endpoints
# ============================================================================

@app.route('/subscriptions/topics', methods=['GET'])
def get_topics():
    """Get available topics (public)"""
    data, status = forward_request(
        SUBSCRIPTION_SERVICE_URL,
        '/subscriptions/topics',
        method='GET'
    )
    return jsonify(data), status


@app.route('/subscriptions', methods=['GET'])
@require_auth
def get_subscriptions():
    """Get user's subscriptions"""
    headers = add_user_headers({})
    
    data, status = forward_request(
        SUBSCRIPTION_SERVICE_URL,
        '/subscriptions',
        method='GET',
        headers=headers
    )
    return jsonify(data), status


@app.route('/subscriptions', methods=['POST'])
@require_auth
def create_subscription():
    """Create new subscription"""
    headers = add_user_headers({})
    
    data, status = forward_request(
        SUBSCRIPTION_SERVICE_URL,
        '/subscriptions',
        method='POST',
        json=request.get_json(),
        headers=headers
    )
    return jsonify(data), status


@app.route('/subscriptions/<topic>', methods=['DELETE'])
@require_auth
def delete_subscription(topic):
    """Delete subscription"""
    headers = add_user_headers({})
    
    data, status = forward_request(
        SUBSCRIPTION_SERVICE_URL,
        f'/subscriptions/{topic}',
        method='DELETE',
        headers=headers
    )
    return jsonify(data), status


# ============================================================================
# Event/Publisher Endpoints
# ============================================================================

@app.route('/events', methods=['GET'])
def list_events():
    """List events (public)"""
    # Forward query params
    params = request.args.to_dict()
    
    data, status = forward_request(
        PUBLISHER_SERVICE_URL,
        '/events',
        method='GET',
        params=params
    )
    return jsonify(data), status


@app.route('/events/<event_id>', methods=['GET'])
def get_event(event_id):
    """Get single event (public)"""
    data, status = forward_request(
        PUBLISHER_SERVICE_URL,
        f'/events/{event_id}',
        method='GET'
    )
    return jsonify(data), status


@app.route('/events', methods=['POST'])
@require_role('organizer', 'admin')
def create_event():
    """Create event (organizers and admins only)"""
    headers = add_user_headers({})
    
    data, status = forward_request(
        PUBLISHER_SERVICE_URL,
        '/events',
        method='POST',
        json=request.get_json(),
        headers=headers
    )
    return jsonify(data), status


@app.route('/events/<event_id>', methods=['PUT'])
@require_role('organizer', 'admin')
def update_event(event_id):
    """Update event (organizers and admins only)"""
    headers = add_user_headers({})
    
    data, status = forward_request(
        PUBLISHER_SERVICE_URL,
        f'/events/{event_id}',
        method='PUT',
        json=request.get_json(),
        headers=headers
    )
    return jsonify(data), status


@app.route('/events/<event_id>/publish', methods=['POST'])
@require_role('organizer', 'admin')
def publish_event(event_id):
    """Publish event (organizers and admins only)"""
    headers = add_user_headers({})
    
    data, status = forward_request(
        PUBLISHER_SERVICE_URL,
        f'/events/{event_id}/publish',
        method='POST',
        headers=headers
    )
    return jsonify(data), status


# ============================================================================
# Notification Endpoints
# ============================================================================

@app.route('/notifications/<user_id>', methods=['GET'])
@require_auth
def get_notifications(user_id):
    """Get user's notifications"""
    # Ensure user can only get their own notifications
    if request.user_id != user_id and request.user_role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    params = request.args.to_dict()
    
    data, status = forward_request(
        DISPATCHER_SERVICE_URL,
        f'/notifications/{user_id}',
        method='GET',
        params=params
    )
    return jsonify(data), status


# ============================================================================
# System/Admin Endpoints (Optional)
# ============================================================================

@app.route('/system/membership', methods=['GET'])
@require_role('admin')
def get_membership():
    """Get MCP membership (admin only)"""
    data, status = forward_request(
        DISPATCHER_SERVICE_URL,
        '/mcp/membership',
        method='GET'
    )
    return jsonify(data), status


@app.route('/system/election', methods=['GET'])
@require_role('admin')
def get_election_status():
    """Get leader election status (admin only)"""
    data, status = forward_request(
        DISPATCHER_SERVICE_URL,
        '/election/status',
        method='GET'
    )
    return jsonify(data), status


# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=os.getenv('FLASK_ENV') == 'development')


