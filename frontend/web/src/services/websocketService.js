/**
 * WebSocket Service for Real-Time Push Notifications
 * 
 * Manages WebSocket connection to notification dispatcher
 * and provides real-time notification delivery + browser notifications
 */

class WebSocketService {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.listeners = [];
    this.pingInterval = null;
    this.userId = null;
    this.isConnected = false;
  }

  /**
   * Connect to WebSocket server
   * @param {string} userId - User ID for personalized connection
   */
  connect(userId) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log('[WebSocket] Already connected');
      return;
    }

    this.userId = userId;
    const wsUrl = `ws://localhost:5004/ws/notifications/${userId}`;
    
    console.log(`[WebSocket] Connecting to ${wsUrl}`);
    
    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('[WebSocket] Connected successfully');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        
        // Send ping every 30 seconds to keep connection alive
        this.pingInterval = setInterval(() => {
          if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000);
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('[WebSocket] Message received:', data.type);
          
          if (data.type === 'notification') {
            // New real-time notification
            console.log('[WebSocket] New notification:', data.data);
            this.notifyListeners(data.data);
            this.showBrowserNotification(data.data);
            
          } else if (data.type === 'cached') {
            // Cached notifications received on connect
            console.log(`[WebSocket] Received ${data.count} cached notifications`);
            
          } else if (data.type === 'pong') {
            // Pong response to ping (keep-alive)
            // console.log('[WebSocket] Pong received');
          }
        } catch (err) {
          console.error('[WebSocket] Error parsing message:', err);
        }
      };

      this.ws.onerror = (error) => {
        console.error('[WebSocket] Connection error:', error);
        this.isConnected = false;
      };

      this.ws.onclose = (event) => {
        console.log('[WebSocket] Connection closed', event.code, event.reason);
        this.isConnected = false;
        
        if (this.pingInterval) {
          clearInterval(this.pingInterval);
          this.pingInterval = null;
        }
        
        // Attempt reconnect with exponential backoff
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
          console.log(`[WebSocket] Reconnecting in ${delay/1000}s (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
          
          setTimeout(() => {
            if (this.userId) {
              this.connect(this.userId);
            }
          }, delay);
        } else {
          console.log('[WebSocket] Max reconnect attempts reached');
        }
      };

    } catch (error) {
      console.error('[WebSocket] Connection failed:', error);
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect() {
    console.log('[WebSocket] Disconnecting');
    this.userId = null;
    
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    this.isConnected = false;
    this.reconnectAttempts = 0;
  }

  /**
   * Subscribe to notification events
   * @param {Function} callback - Callback function to receive notifications
   */
  subscribe(callback) {
    this.listeners.push(callback);
    console.log('[WebSocket] Listener subscribed, total:', this.listeners.length);
  }

  /**
   * Unsubscribe from notification events
   * @param {Function} callback - Callback function to remove
   */
  unsubscribe(callback) {
    this.listeners = this.listeners.filter(cb => cb !== callback);
    console.log('[WebSocket] Listener unsubscribed, remaining:', this.listeners.length);
  }

  /**
   * Notify all listeners of new notification
   * @param {Object} notification - Notification data
   */
  notifyListeners(notification) {
    this.listeners.forEach(callback => {
      try {
        callback(notification);
      } catch (err) {
        console.error('[WebSocket] Error in listener callback:', err);
      }
    });
  }

  /**
   * Show browser notification (desktop push notification)
   * @param {Object} notification - Notification data
   */
  showBrowserNotification(notification) {
    // Check if browser supports notifications
    if (!('Notification' in window)) {
      console.log('[WebSocket] Browser does not support notifications');
      return;
    }

    // Request permission if needed
    if (Notification.permission === 'default') {
      Notification.requestPermission().then(permission => {
        console.log('[WebSocket] Notification permission:', permission);
        if (permission === 'granted') {
          this.createNotification(notification);
        }
      });
    } else if (Notification.permission === 'granted') {
      this.createNotification(notification);
    }
  }

  /**
   * Create and display browser notification
   * @param {Object} notification - Notification data
   */
  createNotification(notification) {
    try {
      const title = notification.title || 'New Notification';
      const options = {
        body: notification.description || 'You have a new notification',
        icon: '/logo192.png',
        badge: '/logo192.png',
        tag: notification.event_id || `notif-${Date.now()}`,
        requireInteraction: false,
        silent: false
      };

      const browserNotif = new Notification(title, options);

      browserNotif.onclick = () => {
        window.focus();
        // Navigate to notifications page
        window.location.href = '/notifications';
        browserNotif.close();
      };

      // Auto-close after 5 seconds
      setTimeout(() => browserNotif.close(), 5000);
      
      console.log('[WebSocket] Browser notification shown');
    } catch (err) {
      console.error('[WebSocket] Error showing notification:', err);
    }
  }

  /**
   * Request notification permission
   */
  async requestNotificationPermission() {
    if (!('Notification' in window)) {
      console.log('[WebSocket] Notifications not supported');
      return false;
    }

    if (Notification.permission === 'granted') {
      return true;
    }

    const permission = await Notification.requestPermission();
    console.log('[WebSocket] Notification permission:', permission);
    return permission === 'granted';
  }

  /**
   * Get connection status
   * @returns {boolean} True if connected
   */
  getConnectionStatus() {
    return this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN;
  }
}

// Export singleton instance
const websocketService = new WebSocketService();
export default websocketService;

