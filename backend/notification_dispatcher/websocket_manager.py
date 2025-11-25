"""
WebSocket Manager for Real-Time Push Notifications

Manages WebSocket connections and Redis caching for persistent notifications.
"""
from flask_sock import Sock
import json
import redis
import threading
from collections import defaultdict

class WebSocketManager:
    """Manages WebSocket connections and notification distribution"""
    
    def __init__(self, app, redis_host='localhost', redis_port=6379):
        """
        Initialize WebSocket manager
        
        Args:
            app: Flask application
            redis_host: Redis server host
            redis_port: Redis server port
        """
        self.sock = Sock(app)
        self.connections = defaultdict(list)  # user_id -> list of websocket connections
        self.lock = threading.Lock()
        
        # Initialize Redis client
        try:
            self.redis_client = redis.Redis(
                host=redis_host, 
                port=redis_port, 
                decode_responses=True,
                socket_connect_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            print(f"[WebSocket] Connected to Redis at {redis_host}:{redis_port}")
            self.redis_available = True
        except Exception as e:
            print(f"[WebSocket] Redis connection failed: {e}")
            print(f"[WebSocket] Running without Redis (notifications won't persist)")
            self.redis_client = None
            self.redis_available = False
        
        # Register WebSocket route
        @self.sock.route('/ws/notifications/<user_id>')
        def notifications_websocket(ws, user_id):
            self.handle_connection(ws, user_id)
    
    def handle_connection(self, ws, user_id):
        """Handle new WebSocket connection from a user"""
        print(f"[WebSocket] User {user_id} connected")
        
        # Add connection to the pool
        with self.lock:
            self.connections[user_id].append(ws)
        
        try:
            # Send cached notifications on connect
            cached = self.get_cached_notifications(user_id, limit=10)
            if cached:
                ws.send(json.dumps({
                    'type': 'cached',
                    'count': len(cached),
                    'notifications': cached
                }))
                print(f"[WebSocket] Sent {len(cached)} cached notifications to {user_id}")
            
            # Keep connection alive and handle messages
            while True:
                try:
                    data = ws.receive(timeout=60)
                    if data:
                        # Handle client messages (ping/pong, etc.)
                        msg = json.loads(data) if data else {}
                        if msg.get('type') == 'ping':
                            ws.send(json.dumps({'type': 'pong'}))
                except Exception as e:
                    # Timeout or connection closed
                    break
        
        except Exception as e:
            print(f"[WebSocket] Connection error for {user_id}: {e}")
        
        finally:
            # Remove connection from pool
            with self.lock:
                if user_id in self.connections and ws in self.connections[user_id]:
                    self.connections[user_id].remove(ws)
                    if not self.connections[user_id]:
                        del self.connections[user_id]
            print(f"[WebSocket] User {user_id} disconnected")
    
    def push_notification(self, user_id, notification):
        """
        Push notification to user via WebSocket and cache in Redis
        
        Args:
            user_id: User ID to send notification to
            notification: Notification data dict
        """
        # 1. Cache in Redis first (persistent storage)
        if self.redis_available:
            self.cache_notification(user_id, notification)
        
        # 2. Push to active WebSocket connections (real-time delivery)
        with self.lock:
            if user_id in self.connections:
                message = json.dumps({
                    'type': 'notification',
                    'data': notification
                })
                
                dead_connections = []
                for ws in self.connections[user_id]:
                    try:
                        ws.send(message)
                        print(f"[WebSocket] Pushed notification to {user_id} (real-time)")
                    except Exception as e:
                        print(f"[WebSocket] Failed to push to {user_id}: {e}")
                        dead_connections.append(ws)
                
                # Clean up dead connections
                for ws in dead_connections:
                    self.connections[user_id].remove(ws)
                
                return True
            else:
                print(f"[WebSocket] User {user_id} not connected (cached for later)")
                return False
    
    def cache_notification(self, user_id, notification):
        """
        Cache notification in Redis for persistence
        
        Args:
            user_id: User ID
            notification: Notification data dict
        """
        if not self.redis_available:
            return
        
        try:
            key = f"notifications:{user_id}"
            # Store as JSON string in list
            self.redis_client.lpush(key, json.dumps(notification))
            # Keep last 100 notifications
            self.redis_client.ltrim(key, 0, 99)
            # Set expiry to 7 days
            self.redis_client.expire(key, 86400 * 7)
            print(f"[Redis] Cached notification for {user_id}")
        except Exception as e:
            print(f"[Redis] Error caching notification: {e}")
    
    def get_cached_notifications(self, user_id, limit=50):
        """
        Get cached notifications from Redis
        
        Args:
            user_id: User ID
            limit: Maximum number of notifications to return
            
        Returns:
            List of notification dicts
        """
        if not self.redis_available:
            return []
        
        try:
            key = f"notifications:{user_id}"
            cached = self.redis_client.lrange(key, 0, limit - 1)
            return [json.loads(n) for n in cached]
        except Exception as e:
            print(f"[Redis] Error fetching cached notifications: {e}")
            return []
    
    def get_connection_count(self):
        """Get number of active WebSocket connections"""
        with self.lock:
            return sum(len(conns) for conns in self.connections.values())
    
    def get_connected_users(self):
        """Get list of user IDs with active connections"""
        with self.lock:
            return list(self.connections.keys())

