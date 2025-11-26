"""
Authentication Service

Handles user registration, login, and JWT token management.
Uses AWS DynamoDB for user storage.

Endpoints:
- POST /register - Register new user
- POST /login - Authenticate and get JWT token
- GET /health - Health check
"""

import os
import time
import bcrypt
import jwt
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError

app = Flask(__name__)
CORS(app)

# Configuration from environment variables
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', '24'))
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
USERS_TABLE = os.getenv('USERS_TABLE', 'Users')
PORT = int(os.getenv('PORT', '5001'))

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
users_table = dynamodb.Table(USERS_TABLE)

print(f"[Auth Service] Starting on port {PORT}")
print(f"[Auth Service] Using DynamoDB table: {USERS_TABLE} in region {AWS_REGION}")


# ============================================================================
# Helper Functions
# ============================================================================

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def generate_jwt(user_id: str, email: str, role: str) -> str:
    """Generate JWT token for authenticated user"""
    payload = {
        'user_id': user_id,
        'email': email,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')


def validate_registration_data(data: dict) -> tuple:
    """
    Validate registration data.
    
    Returns: (is_valid, error_message)
    """
    required_fields = ['email', 'password', 'name']
    
    for field in required_fields:
        if field not in data or not data[field]:
            return False, f"Missing required field: {field}"
    
    email = data['email']
    password = data['password']
    
    # Basic email validation
    if '@' not in email or '.' not in email:
        return False, "Invalid email format"
    
    # Password strength
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    
    # Role validation
    role = data.get('role', 'student')
    valid_roles = ['student', 'organizer', 'admin']
    if role not in valid_roles:
        return False, f"Invalid role. Must be one of: {', '.join(valid_roles)}"
    
    return True, None


# ============================================================================
# API Endpoints
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'auth-service',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@app.route('/register', methods=['POST'])
def register():
    """
    Register a new user.
    
    Request body:
    {
        "email": "user@example.com",
        "password": "password123",
        "name": "John Doe",
        "phone": "+1234567890",  # optional
        "role": "student"  # or "organizer", "admin"
    }
    
    Response:
    {
        "success": true,
        "user_id": "...",
        "message": "User registered successfully"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate input
        is_valid, error_msg = validate_registration_data(data)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        name = data['name'].strip()
        phone = data.get('phone', '')
        role = data.get('role', 'student')
        
        # Check if user already exists
        try:
            response = users_table.query(
                IndexName='EmailIndex',
                KeyConditionExpression=boto3.dynamodb.conditions.Key('email').eq(email)
            )
            
            if response['Items']:
                return jsonify({'error': 'User with this email already exists'}), 409
        
        except ClientError as e:
            # If EmailIndex doesn't exist, do a scan (less efficient)
            print(f"[Auth] Warning: EmailIndex not found, using scan: {e}")
            response = users_table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr('email').eq(email)
            )
            if response['Items']:
                return jsonify({'error': 'User with this email already exists'}), 409
        
        # Generate user ID
        user_id = f"U{int(time.time() * 1000)}"
        
        # Hash password
        password_hash = hash_password(password)
        
        # Create user record
        user_item = {
            'user_id': user_id,
            'email': email,
            'name': name,
            'password_hash': password_hash,
            'role': role,
            'phone': phone,
            'created_at': int(time.time()),
            'updated_at': int(time.time())
        }
        
        # Save to DynamoDB
        users_table.put_item(Item=user_item)
        
        print(f"[Auth] Registered new user: {user_id} ({email})")
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'message': 'User registered successfully'
        }), 201
    
    except ClientError as e:
        print(f"[Auth] DynamoDB error: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    
    except Exception as e:
        print(f"[Auth] Registration error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/admin/create-user', methods=['POST'])
def admin_create_user():
    """
    Admin endpoint to create new users (especially publishers/organizers).
    
    Headers:
        X-User-ID: admin's user_id
        X-User-Role: admin
    
    Request body:
    {
        "email": "publisher@example.com",
        "password": "password123",
        "name": "John Doe",
        "phone": "+1234567890",  # optional
        "role": "organizer"  # or "student", "admin"
    }
    
    Response:
    {
        "success": true,
        "user_id": "...",
        "user": {...},
        "message": "User created successfully"
    }
    """
    try:
        # Check admin authorization
        user_role = request.headers.get('X-User-Role')
        if user_role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate input
        is_valid, error_msg = validate_registration_data(data)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        name = data['name'].strip()
        phone = data.get('phone', '')
        role = data.get('role', 'student')
        
        # Validate role
        if role not in ['student', 'organizer', 'admin']:
            return jsonify({'error': 'Invalid role. Must be student, organizer, or admin'}), 400
        
        # Check if user already exists
        try:
            response = users_table.query(
                IndexName='EmailIndex',
                KeyConditionExpression=boto3.dynamodb.conditions.Key('email').eq(email)
            )
            
            if response['Items']:
                return jsonify({'error': 'User with this email already exists'}), 409
        
        except ClientError as e:
            # If EmailIndex doesn't exist, do a scan (less efficient)
            print(f"[Auth] Warning: EmailIndex not found, using scan: {e}")
            response = users_table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr('email').eq(email)
            )
            if response['Items']:
                return jsonify({'error': 'User with this email already exists'}), 409
        
        # Generate user ID
        user_id = f"U{int(time.time() * 1000)}"
        
        # Hash password
        password_hash = hash_password(password)
        
        # Create user record
        user_item = {
            'user_id': user_id,
            'email': email,
            'name': name,
            'password_hash': password_hash,
            'role': role,
            'phone': phone,
            'created_at': int(time.time()),
            'updated_at': int(time.time())
        }
        
        # Save to DynamoDB
        users_table.put_item(Item=user_item)
        
        admin_id = request.headers.get('X-User-ID', 'unknown')
        print(f"[Auth] Admin {admin_id} created new user: {user_id} ({email}) with role {role}")
        
        # Return user data without password hash
        user_response = {
            'user_id': user_id,
            'email': email,
            'name': name,
            'role': role,
            'phone': phone,
            'created_at': user_item['created_at']
        }
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'user': user_response,
            'message': f'{role.capitalize()} account created successfully'
        }), 201
    
    except ClientError as e:
        print(f"[Auth] DynamoDB error: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    
    except Exception as e:
        print(f"[Auth] Admin create user error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/login', methods=['POST'])
def login():
    """
    Authenticate user and return JWT token.
    
    Request body:
    {
        "email": "user@example.com",
        "password": "password123"
    }
    
    Response:
    {
        "success": true,
        "token": "eyJ...",
        "user": {
            "user_id": "...",
            "email": "...",
            "name": "...",
            "role": "..."
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Find user by email
        try:
            response = users_table.query(
                IndexName='EmailIndex',
                KeyConditionExpression=boto3.dynamodb.conditions.Key('email').eq(email)
            )
            users = response['Items']
        except ClientError:
            # Fallback to scan if index doesn't exist
            response = users_table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr('email').eq(email)
            )
            users = response['Items']
        
        if not users:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        user = users[0]
        
        # Verify password
        if not verify_password(password, user['password_hash']):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Generate JWT token
        token = generate_jwt(user['user_id'], user['email'], user['role'])
        
        print(f"[Auth] User logged in: {user['user_id']} ({email})")
        
        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'user_id': user['user_id'],
                'email': user['email'],
                'name': user['name'],
                'role': user['role'],
                'phone': user.get('phone', '')
            }
        }), 200
    
    except ClientError as e:
        print(f"[Auth] DynamoDB error: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    
    except Exception as e:
        print(f"[Auth] Login error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/verify', methods=['POST'])
def verify_token():
    """
    Verify JWT token (used by other services).
    
    Request body:
    {
        "token": "eyJ..."
    }
    
    Response:
    {
        "valid": true,
        "user_id": "...",
        "email": "...",
        "role": "..."
    }
    """
    try:
        data = request.get_json()
        token = data.get('token', '')
        
        if not token:
            return jsonify({'valid': False, 'error': 'No token provided'}), 400
        
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            
            return jsonify({
                'valid': True,
                'user_id': payload['user_id'],
                'email': payload['email'],
                'role': payload['role']
            }), 200
        
        except jwt.ExpiredSignatureError:
            return jsonify({'valid': False, 'error': 'Token expired'}), 401
        
        except jwt.InvalidTokenError:
            return jsonify({'valid': False, 'error': 'Invalid token'}), 401
    
    except Exception as e:
        print(f"[Auth] Token verification error: {e}")
        return jsonify({'valid': False, 'error': 'Internal server error'}), 500


@app.route('/user/<user_id>', methods=['GET'])
def get_user(user_id):
    """
    Get user information (requires authentication).
    
    Headers:
        Authorization: Bearer <token>
    """
    try:
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization header'}), 401
        
        token = auth_header.split(' ')[1]
        
        # Verify token
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Check if requesting own data or admin
        if payload['user_id'] != user_id and payload['role'] != 'admin':
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get user from DynamoDB
        response = users_table.get_item(Key={'user_id': user_id})
        
        if 'Item' not in response:
            return jsonify({'error': 'User not found'}), 404
        
        user = response['Item']
        
        # Remove sensitive data
        user.pop('password_hash', None)
        
        return jsonify({'user': user}), 200
    
    except ClientError as e:
        print(f"[Auth] DynamoDB error: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    
    except Exception as e:
        print(f"[Auth] Get user error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=os.getenv('FLASK_ENV') == 'development')


