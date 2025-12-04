# 🔔 Push Notification Troubleshooting Guide

## Why Push Notifications Might Not Work

### ✅ Checklist - Verify Each Step

1. **Browser Notification Permission**
   - Open browser console (F12)
   - Check: `Notification.permission` should be `"granted"`
   - If `"default"` or `"denied"`, you need to grant permission

2. **WebSocket Connection**
   - Open browser console (F12)
   - Look for: `[WebSocket] Connected successfully`
   - If not connected, check network tab for WebSocket errors

3. **User Subscription**
   - User must be subscribed to the topic that the event is published to
   - Example: If event topic is `hackathon.aiml`, user must subscribe to `hackathon.aiml` or `hackathon.*`

4. **User ID Match**
   - The `user_id` in the notification must match the logged-in user's `user_id`
   - Check browser console for WebSocket connection: `[WebSocket] Connecting to ws://localhost:5004/ws/notifications/{user_id}`

---

## 🔧 Step-by-Step Fix

### Step 1: Grant Browser Notification Permission

**Option A: Automatic (on login)**
- When you login, browser should ask for permission
- Click "Allow" when prompted

**Option B: Manual (if already denied)**
1. Open browser console (F12)
2. Run this command:
   ```javascript
   Notification.requestPermission().then(permission => {
     console.log('Permission:', permission);
   });
   ```
3. Click "Allow" in the browser prompt

**Option C: Browser Settings (Chrome/Edge)**
1. Click the lock icon in address bar
2. Find "Notifications"
3. Change to "Allow"
4. Refresh the page

### Step 2: Verify WebSocket Connection

1. Open browser console (F12)
2. Look for these messages:
   ```
   [Auth] Connecting WebSocket for user: U1234567890
   [WebSocket] Connecting to ws://localhost:5004/ws/notifications/U1234567890
   [WebSocket] Connected successfully
   ```

3. If you see connection errors:
   - Check if notification-dispatcher service is running: `docker ps`
   - Check if port 5004 is accessible
   - Check browser console for WebSocket errors

### Step 3: Verify User Subscription

1. Login as the student (dhruvi)
2. Go to Subscriptions page
3. Subscribe to the topic that matches the event
   - Example: If publisher publishes event with topic `hackathon.aiml`
   - Student must subscribe to: `hackathon.aiml` or `hackathon.*` or `hackathon.#`

4. Verify subscription was created:
   - Check Subscriptions page shows the topic
   - Or check DynamoDB Subscriptions table

### Step 4: Test the Flow

1. **As Student (dhruvi):**
   - Login
   - Grant notification permission (if prompted)
   - Subscribe to a topic (e.g., `hackathon.aiml`)
   - Keep browser open (don't close tab)

2. **As Publisher:**
   - Login as organizer
   - Create an event with topic `hackathon.aiml`
   - Click "Publish Event"

3. **Check Student Browser:**
   - Should see browser notification popup
   - Check console for: `[WebSocket] New notification:`
   - Check Notifications page for the notification

---

## 🐛 Common Issues & Solutions

### Issue 1: "Notification permission denied"

**Symptom:** No browser notification appears

**Solution:**
```javascript
// In browser console, reset permission:
Notification.requestPermission().then(permission => {
  console.log('New permission:', permission);
});
```

Or reset in browser settings (see Step 1 above).

### Issue 2: "WebSocket connection failed"

**Symptom:** Console shows `[WebSocket] Connection error`

**Solution:**
1. Check if notification-dispatcher is running:
   ```bash
   docker ps | grep notification-dispatcher
   ```

2. Check dispatcher logs:
   ```bash
   docker logs notification-dispatcher-1
   ```

3. Verify WebSocket URL is correct:
   - Should be: `ws://localhost:5004/ws/notifications/{user_id}`
   - Check `frontend/web/src/services/websocketService.js` line 30

### Issue 3: "Notifications appear in page but no browser popup"

**Symptom:** Notifications show in Notifications page, but no desktop notification

**Solution:**
- Browser permission is likely `"denied"` or `"default"`
- Follow Step 1 to grant permission
- Check console: `Notification.permission` should be `"granted"`

### Issue 4: "User not receiving notifications even though subscribed"

**Symptom:** User is subscribed but no notification received

**Check:**
1. Verify subscription topic matches event topic exactly
   - Event: `hackathon.aiml`
   - Subscription: `hackathon.aiml` ✅ OR `hackathon.*` ✅ OR `hackathon.#` ✅
   - Subscription: `hackathon.web` ❌ (won't match)

2. Check publisher-side filtering:
   - Publisher filters subscribers before sending
   - Check publisher logs: `docker logs publisher-service-1`
   - Should show: `After filtering: X matching subscribers`

3. Check notification dispatcher:
   - Check dispatcher logs: `docker logs notification-dispatcher-1`
   - Should show: `Processing notification for event {event_id}`

### Issue 5: "WebSocket connects but no notifications received"

**Symptom:** WebSocket connected but notifications don't arrive

**Check:**
1. Verify user_id matches:
   - WebSocket connects to: `/ws/notifications/{user_id}`
   - Notification sent to: `subscriber_ids` must include same `user_id`

2. Check RabbitMQ:
   - Verify message was published: Check RabbitMQ management UI (http://localhost:15672)
   - Check dispatcher consumed message: `docker logs notification-dispatcher-1`

3. Check Redis (if using):
   - Notifications are cached in Redis
   - Verify Redis is running: `docker ps | grep redis`

---

## 🧪 Debug Commands

### Check WebSocket Connection Status

In browser console:
```javascript
// Check if WebSocket is connected
websocketService.getConnectionStatus()

// Check notification permission
Notification.permission

// Manually request permission
websocketService.requestNotificationPermission()
```

### Check Backend Services

```bash
# Check all services are running
docker ps

# Check notification dispatcher logs
docker logs notification-dispatcher-1 -f

# Check publisher service logs
docker logs publisher-service-1 -f

# Check WebSocket connections
curl http://localhost:5004/health
```

### Check User Subscriptions

```bash
# Via API (replace {user_id} and {token})
curl -H "Authorization: Bearer {token}" \
  http://localhost:5000/subscriptions
```

---

## 📋 Quick Test Script

Run this in browser console after logging in as student:

```javascript
// 1. Check WebSocket connection
console.log('WebSocket connected:', websocketService.getConnectionStatus());

// 2. Check notification permission
console.log('Notification permission:', Notification.permission);

// 3. Request permission if needed
if (Notification.permission === 'default') {
  websocketService.requestNotificationPermission().then(granted => {
    console.log('Permission granted:', granted);
  });
}

// 4. Test notification (manual test)
if (Notification.permission === 'granted') {
  new Notification('Test Notification', {
    body: 'If you see this, notifications are working!',
    icon: '/logo192.png'
  });
}
```

---

## ✅ Expected Behavior

When everything works correctly:

1. **On Login:**
   - Browser asks for notification permission
   - WebSocket connects automatically
   - Console shows: `[WebSocket] Connected successfully`

2. **When Publisher Publishes Event:**
   - Student receives browser notification (desktop popup)
   - Notification appears in Notifications page
   - Console shows: `[WebSocket] New notification: {...}`

3. **Notification Content:**
   - Title: Event title
   - Body: Event description
   - Clicking notification opens Notifications page

---

## 🆘 Still Not Working?

1. **Check all services are running:**
   ```bash
   docker ps
   ```
   Should show: notification-dispatcher-1, publisher-service-1, rabbitmq, redis

2. **Check browser console for errors:**
   - Open F12 → Console tab
   - Look for red error messages
   - Share error messages for debugging

3. **Check backend logs:**
   ```bash
   docker logs notification-dispatcher-1 | tail -50
   docker logs publisher-service-1 | tail -50
   ```

4. **Verify user subscription:**
   - Login as student
   - Go to Subscriptions page
   - Ensure topic matches event topic

5. **Test with seed data:**
   - Use pre-seeded accounts: `alice@student.com` / `password123`
   - These accounts already have subscriptions set up

---

## 📝 Notes

- **Browser notifications only work on HTTPS or localhost** (security requirement)
- **Permission must be granted by user** (can't be auto-granted)
- **WebSocket must be connected** for real-time notifications
- **User must be subscribed** to the topic being published
- **Notifications are cached in Redis** for offline users



