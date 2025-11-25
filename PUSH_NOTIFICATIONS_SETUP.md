# 🔔 Real-Time Push Notifications Implementation Guide

## Current State ❌

**What's Missing:**
- ✗ Uses polling (frontend checks API every few seconds)
- ✗ Notifications stored in memory only (lost on restart)
- ✗ No desktop/browser push notifications
- ✗ No WebSocket for real-time updates

## Solution: 3-Level Push System ✅

### Level 1: WebSocket (Real-Time to Open Tabs) ⚡
### Level 2: Browser Push API (Desktop Notifications) 🔔  
### Level 3: Redis Caching (Persistent Storage) 💾

---

## Implementation

### 🔧 Step 1: Add Dependencies

**Update `backend/requirements.txt`:**
```python
# Add these lines:
flask-sock==0.7.0          # WebSocket support (already there)
redis==5.0.1               # Redis caching
```

**Install:**
```powershell
cd backend
pip install redis
```

### 🔧 Step 2: Add Redis to Docker Compose

**Update `deployment/docker/docker-compose.yml`:**

```yaml
services:
  # Add Redis service
  redis:
    image: redis:7-alpine
    container_name: redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - distributed-events-net
    command: redis-server --appendonly yes

  # Update notification-dispatcher
  notification-dispatcher:
    # ... existing config ...
    environment:
      # ... existing env vars ...
      REDIS_HOST: redis
      REDIS_PORT: 6379
    depends_on:
      - rabbitmq
      - gossip-agent
      - redis  # Add this

volumes:
  rabbitmq_data:
  redis_data:  # Add this
```

### 🔧 Step 3: Update Notification Dispatcher with WebSocket + Redis

**Create `backend/notification_dispatcher/websocket_manager.py`:**

```python
"""
WebSocket Manager for Real-Time Push Notifications
"""
from flask_sock import Sock
import json
import redis
import threading

class WebSocketManager:
    def __init__(self, app, redis_host='localhost', redis_port=6379):
        self.sock = Sock(app)
        self.redis_client = redis.Redis(
            host=redis_host, 
            port=redis_port, 
            decode_responses=True
        )
        self.connections = {}  # user_id -> list of websocket connections
        self.lock = threading.Lock()
        
        # Register WebSocket route
        @self.sock.route('/ws/notifications/<user_id>')
        def notifications_websocket(ws, user_id):
            self.handle_connection(ws, user_id)
    
    def handle_connection(self, ws, user_id):
        """Handle new WebSocket connection"""
        print(f"[WebSocket] User {user_id} connected")
        
        # Add connection
        with self.lock:
            if user_id not in self.connections:
                self.connections[user_id] = []
            self.connections[user_id].append(ws)
        
        try:
            # Send cached notifications on connect
            cached = self.get_cached_notifications(user_id)
            if cached:
                ws.send(json.dumps({
                    'type': 'cached',
                    'notifications': cached
                }))
            
            # Keep connection alive
            while True:
                data = ws.receive()
                if data:
                    # Handle ping/pong or client messages
                    ws.send(json.dumps({'type': 'pong'}))
        
        except Exception as e:
            print(f"[WebSocket] Connection closed for {user_id}: {e}")
        
        finally:
            # Remove connection
            with self.lock:
                if user_id in self.connections:
                    self.connections[user_id].remove(ws)
                    if not self.connections[user_id]:
                        del self.connections[user_id]
    
    def push_notification(self, user_id, notification):
        """Push notification to user's WebSocket connections + Redis cache"""
        # 1. Cache in Redis (persistent)
        self.cache_notification(user_id, notification)
        
        # 2. Push to active WebSocket connections (real-time)
        with self.lock:
            if user_id in self.connections:
                dead_connections = []
                for ws in self.connections[user_id]:
                    try:
                        ws.send(json.dumps({
                            'type': 'notification',
                            'data': notification
                        }))
                        print(f"[WebSocket] Pushed to {user_id}")
                    except Exception as e:
                        print(f"[WebSocket] Failed to push to {user_id}: {e}")
                        dead_connections.append(ws)
                
                # Clean up dead connections
                for ws in dead_connections:
                    self.connections[user_id].remove(ws)
    
    def cache_notification(self, user_id, notification):
        """Cache notification in Redis"""
        try:
            key = f"notifications:{user_id}"
            # Store as list with 100 item limit
            self.redis_client.lpush(key, json.dumps(notification))
            self.redis_client.ltrim(key, 0, 99)  # Keep last 100
            self.redis_client.expire(key, 86400 * 7)  # 7 days TTL
            print(f"[Redis] Cached notification for {user_id}")
        except Exception as e:
            print(f"[Redis] Error caching: {e}")
    
    def get_cached_notifications(self, user_id, limit=50):
        """Get cached notifications from Redis"""
        try:
            key = f"notifications:{user_id}"
            cached = self.redis_client.lrange(key, 0, limit - 1)
            return [json.loads(n) for n in cached]
        except Exception as e:
            print(f"[Redis] Error fetching: {e}")
            return []
```

**Update `backend/notification_dispatcher/app.py`:**

```python
# Add at top:
from websocket_manager import WebSocketManager

# After app initialization:
app = Flask(__name__)
CORS(app)

# Initialize WebSocket manager with Redis
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
ws_manager = WebSocketManager(app, REDIS_HOST, REDIS_PORT)

# Update add_in_app_notification function:
def add_in_app_notification(user_id: str, notification: dict):
    """Add notification and push via WebSocket"""
    try:
        # Push to WebSocket + Redis
        ws_manager.push_notification(user_id, notification)
        
        # Also keep in memory for backward compatibility
        with notifications_lock:
            if user_id not in in_app_notifications:
                in_app_notifications[user_id] = deque(maxlen=100)
            in_app_notifications[user_id].appendleft(notification)
        
        print(f"[Dispatcher] Added notification for {user_id} (pushed via WebSocket)")
    except Exception as e:
        print(f"[Dispatcher] Error adding notification: {e}")

# Update get_user_notifications to use Redis:
@app.route('/notifications/<user_id>', methods=['GET'])
def get_notifications(user_id):
    """Get notifications (from Redis cache)"""
    try:
        limit = int(request.args.get('limit', 50))
        
        # Get from Redis
        notifications = ws_manager.get_cached_notifications(user_id, limit)
        
        return jsonify({
            'user_id': user_id,
            'notifications': notifications,
            'count': len(notifications)
        }), 200
    
    except Exception as e:
        print(f"[Dispatcher] Error fetching notifications: {e}")
        return jsonify({'error': 'Internal server error'}), 500
```

### 🔧 Step 4: Update Frontend for WebSocket

**Create `frontend/web/src/services/websocketService.js`:**

```javascript
class WebSocketService {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.listeners = [];
  }

  connect(userId) {
    // WebSocket URL
    const wsUrl = `ws://localhost:5004/ws/notifications/${userId}`;
    
    console.log(`[WebSocket] Connecting to ${wsUrl}`);
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('[WebSocket] Connected');
      this.reconnectAttempts = 0;
      
      // Send ping every 30 seconds to keep alive
      this.pingInterval = setInterval(() => {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
          this.ws.send(JSON.stringify({ type: 'ping' }));
        }
      }, 30000);
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('[WebSocket] Message received:', data);
        
        if (data.type === 'notification') {
          // New real-time notification
          this.notifyListeners(data.data);
          
          // Show browser notification
          this.showBrowserNotification(data.data);
        } else if (data.type === 'cached') {
          // Cached notifications on connect
          console.log('[WebSocket] Received cached notifications:', data.notifications.length);
        }
      } catch (err) {
        console.error('[WebSocket] Error parsing message:', err);
      }
    };

    this.ws.onerror = (error) => {
      console.error('[WebSocket] Error:', error);
    };

    this.ws.onclose = () => {
      console.log('[WebSocket] Disconnected');
      clearInterval(this.pingInterval);
      
      // Attempt reconnect
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++;
        console.log(`[WebSocket] Reconnecting... (attempt ${this.reconnectAttempts})`);
        setTimeout(() => this.connect(userId), 3000);
      }
    };
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      clearInterval(this.pingInterval);
    }
  }

  // Subscribe to notifications
  subscribe(callback) {
    this.listeners.push(callback);
  }

  // Notify all listeners
  notifyListeners(notification) {
    this.listeners.forEach(callback => callback(notification));
  }

  // Show browser notification
  showBrowserNotification(notification) {
    // Request permission if needed
    if (Notification.permission === 'default') {
      Notification.requestPermission();
    }

    if (Notification.permission === 'granted') {
      const notif = new Notification(notification.title, {
        body: notification.description,
        icon: '/logo192.png',
        badge: '/logo192.png',
        tag: notification.event_id,
        requireInteraction: false
      });

      notif.onclick = () => {
        window.focus();
        window.location.href = '/notifications';
        notif.close();
      };

      // Auto-close after 5 seconds
      setTimeout(() => notif.close(), 5000);
    }
  }
}

export default new WebSocketService();
```

**Update `frontend/web/src/context/AuthContext.js`:**

```javascript
import websocketService from '../services/websocketService';

// In login function, after successful login:
const login = async (email, password) => {
  try {
    const response = await authAPI.login({ email, password });
    const userData = response.data;
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
    
    // Connect to WebSocket
    websocketService.connect(userData.user_id);
    
    return userData;
  } catch (err) {
    // ...
  }
};

// In logout function:
const logout = () => {
  websocketService.disconnect();
  setUser(null);
  localStorage.removeItem('user');
};
```

**Update `frontend/web/src/pages/Dashboard.js`:**

```javascript
import { useEffect, useState } from 'react';
import websocketService from '../services/websocketService';

function Dashboard() {
  const [recentNotifications, setRecentNotifications] = useState([]);

  useEffect(() => {
    // Subscribe to real-time notifications
    const handleNewNotification = (notification) => {
      setRecentNotifications(prev => [notification, ...prev].slice(0, 5));
      
      // Play sound or show toast
      console.log('New notification received:', notification);
    };

    websocketService.subscribe(handleNewNotification);

    // Load initial data
    loadDashboardData();
  }, [user]);

  // ... rest of component
}
```

---

## 🧪 Testing

### Test 1: WebSocket Connection
```javascript
// Open browser console on http://localhost:3000
// You should see:
// [WebSocket] Connecting to ws://localhost:5004/ws/notifications/U...
// [WebSocket] Connected
```

### Test 2: Real-Time Notification
```powershell
# Publish an event
$env:PYTHONIOENCODING='utf-8'
python scripts\seed-data.py

# Check browser - notification should appear instantly!
```

### Test 3: Browser Notification
```javascript
// First time, browser will ask permission:
// "localhost wants to show notifications" → Click Allow

// Next notification will show desktop popup
```

### Test 4: Redis Caching
```powershell
# Connect to Redis
docker exec -it redis redis-cli

# Check cached notifications
KEYS notifications:*
LRANGE notifications:U1234567890 0 10
```

---

## 📊 Architecture Flow

```
┌─────────────────────────────────────────────────────┐
│  1. Event Published                                  │
│     Publisher → RabbitMQ                            │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│  2. Dispatcher Receives & Processes                  │
│     RabbitMQ → Notification Dispatcher              │
└────────────────┬────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                  │
        ▼                  ▼
┌──────────────┐  ┌──────────────┐
│  3a. Cache   │  │  3b. Push    │
│  Redis Store │  │  WebSocket   │
│  (Persist)   │  │  (Real-Time) │
└──────────────┘  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │  4. Browser  │
                  │  Receives &  │
                  │  Shows Notif │
                  └──────────────┘
```

---

## 🎯 Benefits

✅ **Instant Notifications** - No polling, instant delivery via WebSocket  
✅ **Desktop Alerts** - Browser notifications even when tab is in background  
✅ **Persistent** - Redis caching survives server restarts  
✅ **Scalable** - Redis can be clustered for millions of users  
✅ **Offline Support** - Cached notifications available when reconnecting  

---

## 🚀 Next Steps

1. Follow this guide to implement WebSocket + Redis
2. Test with seed data
3. For production: Add Redis Cluster, WebSocket load balancing
4. Optional: Add mobile push (FCM/APNS) for native apps

---

## 💡 Quick Implementation (30 minutes)

**If you want to implement this NOW:**

1. Add Redis to docker-compose.yml (5 min)
2. Install redis library: `pip install redis` (1 min)
3. Copy websocket_manager.py to notification_dispatcher/ (5 min)
4. Update notification_dispatcher/app.py (10 min)
5. Copy websocketService.js to frontend (5 min)
6. Update AuthContext.js and Dashboard.js (4 min)

**Restart services:**
```powershell
cd deployment\docker
docker-compose up -d --build
```

**Test it:**
```powershell
# Login to web app
# Publish an event
# See instant notification! 🎉
```

