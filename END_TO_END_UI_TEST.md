# End-to-End UI Test - Publisher & Subscriber

## What You'll Test
- Publisher (Organizer) creates an event
- Subscriber (Student) subscribes to event categories
- Publisher publishes the event
- Subscriber receives notification (in-app + push notification)

---

## Step 1: Start All Services

```bash
cd deployment/docker
docker-compose up -d
```

**Wait 30 seconds** for all services to start.

**Verify services are running:**
```bash
docker ps | findstr -E "api-gateway|frontend|publisher|dispatcher"

docker ps | findstr /R "api-gateway frontend publisher dispatcher"

```

---

## Step 2: Access the Application

Open your web browser and go to:

```
http://localhost:3000
```

You should see the **Login/Register** page.

---

## Step 3: Login as Publisher (Organizer)

### Use Organizer Account:
- **Email:** `charlie@organizer.com`
- **Password:** `password123`

**Steps:**
1. Click **"Login"** or go to login page
2. Enter email: `charlie@organizer.com`
3. Enter password: `password123`
4. Click **"Login"** button

**You should see:**
- ✅ Dashboard with "Create Event" option
- ✅ Organizer role visible

---

## Step 4: Create an Event (Publisher)

1. Click **"Create Event"** button (or navigate to Create Event page)

2. Fill in event details:
   - **Event Title:** `Tech Conference 2025`
   - **Description:** `Join us for the biggest tech conference of the year`
   - **Category:** Select a category (e.g., `Technology`, `Hackathon`, etc.)
   - **Date:** Select a future date
   - **Location:** `San Francisco, CA`
   - **Image:** (Optional) Upload an image

3. Click **"Create Event"** button

**You should see:**
- ✅ Success message: "Event created successfully"
- ✅ Event appears in your events list

**Note the Event ID** (you'll need it for publishing).

---

## Step 5: Publish the Event

1. Find your created event in the events list
2. Click **"Publish"** button (or navigate to event details and click Publish)

**What happens:**
- ✅ Event is published to RabbitMQ
- ✅ Publisher-side filtering finds matching subscribers
- ✅ Notification dispatcher receives the event
- ✅ Subscribers will receive notifications

**You should see:**
- ✅ Success message: "Event published successfully"
- ✅ Event status changes to "Published"

---

## Step 6: Open New Browser Window (Subscriber)

**Open a new browser window or use Incognito/Private mode** to login as a student.

---

## Step 7: Register/Login as Subscriber (Student)

### Option A: Register New Student

1. Click **"Register"** button
2. Fill in details:
   - **Name:** `Test Student`
   - **Email:** `student@test.com`
   - **Password:** `password123`
   - **Role:** Select **"Student"**
3. Click **"Register"** button

### Option B: Use Existing Student Account

**Use these credentials:**
- **Email:** `alice@student.com`
- **Password:** `password123`

**Steps:**
1. Click **"Login"**
2. Enter email: `alice@student.com`
3. Enter password: `password123`
4. Click **"Login"** button

**You should see:**
- ✅ Dashboard with "Subscriptions" option
- ✅ Student role visible

---

## Step 8: Subscribe to Event Categories

1. Click **"Subscriptions"** (or navigate to Subscriptions page)

2. **Subscribe to categories:**
   - Find the category you used when creating the event (e.g., `Technology`)
   - Click **"Subscribe"** button next to that category

**You should see:**
- ✅ Success message: "Subscribed successfully"
- ✅ Category shows as "Subscribed"

**Important:** Make sure you subscribe to the **same category** as the event you created!

---

## Step 9: Allow Browser Notifications

**When you login as student, browser will ask for notification permission:**

1. Click **"Allow"** or **"Yes"** when browser asks for notification permission
2. This enables push notifications

**If you missed it:**
- Check browser address bar for notification icon
- Or go to browser settings → Site settings → Notifications → Allow

---

## Step 10: Publisher Publishes Event Again (If Needed)

**If you already published before subscribing:**
- Go back to Publisher window (Organizer)
- Find your event
- Click **"Publish"** again (or create a new event and publish it)

**This ensures the subscriber receives the notification.**

---

## Step 11: Watch for Notification (Subscriber)

**In the Student browser window:**

### Check In-App Notifications:

1. Click **"Notifications"** (or navigate to Notifications page)

**You should see:**
- ✅ New notification appears
- ✅ Notification shows event details:
   - Event title: `Tech Conference 2025`
   - Event description
   - Event date/location
   - Timestamp

### Check Push Notification:

**You should also see:**
- ✅ Desktop push notification popup (if browser notifications enabled)
- ✅ Notification appears in system notification area
- ✅ Notification shows event title and details

---

## Step 12: Verify Notification Details

**Click on the notification** (in-app or push notification):

**You should see:**
- ✅ Full event details
- ✅ Event description
- ✅ Event date and location
- ✅ Event image (if uploaded)

---

## Step 13: Test Multiple Subscriptions

**As Student:**
1. Subscribe to multiple categories
2. Go back to Publisher window

**As Publisher:**
1. Create events in different categories
2. Publish each event

**As Student:**
1. Check notifications
2. You should receive notifications for all subscribed categories

---

## Step 14: Test Real-Time Updates

**Open WebSocket connection (automatic):**

1. Check browser Developer Tools (F12)
2. Go to **Console** tab
3. Look for WebSocket connection messages:
   ```
   WebSocket connected
   Received notification: {...}
   ```

**This shows real-time notification delivery via WebSocket.**

---

## Complete Test Flow Summary

```
1. Start Services → docker-compose up -d
2. Login as Organizer → charlie@organizer.com / password123
3. Create Event → Fill form, click Create
4. Publish Event → Click Publish button
5. Open New Browser → Login as Student
6. Subscribe to Category → Click Subscribe
7. Allow Notifications → Click Allow in browser
8. Publisher Publishes → Go back, click Publish
9. Student Receives → Check Notifications page + Push notification
10. Verify Details → Click notification, see full event
```

---

## Troubleshooting

### No Notifications Received?

1. **Check Subscriptions:**
   - Make sure student subscribed to the same category as event
   - Go to Subscriptions page and verify

2. **Check Event Category:**
   - Verify event category matches subscription
   - Create new event with matching category

3. **Check Browser Notifications:**
   - Verify notifications are allowed in browser
   - Check browser settings → Site settings → Notifications

4. **Check Services:**
   ```bash
   docker logs notification-dispatcher-1 | tail -20
   docker logs publisher-service-1 | tail -20
   ```

5. **Check WebSocket:**
   - Open browser Developer Tools (F12)
   - Check Console for WebSocket errors
   - Check Network tab for WebSocket connection

### Event Not Publishing?

1. **Check Publisher Logs:**
   ```bash
   docker logs publisher-service-1 | tail -20
   ```

2. **Check RabbitMQ:**
   ```bash
   docker logs rabbitmq | tail -20
   ```

3. **Check API Gateway:**
   ```bash
   docker logs api-gateway | tail -20
   ```

### Can't Login?

1. **Check Auth Service:**
   ```bash
   docker logs auth-service | tail -20
   ```

2. **Try Different Account:**
   - Use seed data accounts (see seed-data.py)
   - Or register new account

3. **Check Database:**
   - Verify DynamoDB is running
   - Check if users exist in database

---

## Expected Results

### Publisher (Organizer):
- ✅ Can create events
- ✅ Can publish events
- ✅ Events appear in events list
- ✅ Published events show "Published" status

### Subscriber (Student):
- ✅ Can subscribe to categories
- ✅ Subscriptions appear in subscriptions list
- ✅ Receives in-app notifications
- ✅ Receives push notifications (desktop)
- ✅ Notifications show event details
- ✅ Can click notifications to see full event

### System:
- ✅ Events published to RabbitMQ
- ✅ Publisher-side filtering works
- ✅ Notification dispatcher receives events
- ✅ WebSocket delivers real-time notifications
- ✅ Redis stores persistent notifications
- ✅ All services working together

---

## Quick Test Checklist

- [ ] Services started (`docker-compose up -d`)
- [ ] Frontend accessible (`http://localhost:3000`)
- [ ] Login as Organizer (charlie@organizer.com)
- [ ] Create event with category
- [ ] Publish event
- [ ] Open new browser window
- [ ] Login as Student (alice@student.com)
- [ ] Subscribe to matching category
- [ ] Allow browser notifications
- [ ] Publisher publishes event again
- [ ] Student receives in-app notification
- [ ] Student receives push notification
- [ ] Notification shows correct event details

---

## Additional Test Scenarios

### Test 1: Multiple Subscribers
- Register multiple students
- All subscribe to same category
- Publisher publishes event
- All students receive notification

### Test 2: Multiple Categories
- Student subscribes to multiple categories
- Publisher creates events in different categories
- Student receives notifications for all subscribed categories

### Test 3: Real-Time Updates
- Keep notifications page open
- Publisher publishes new event
- Notification appears immediately (WebSocket)

### Test 4: Notification Persistence
- Receive notification
- Refresh page
- Notification still appears (stored in Redis)

---

That's it! Complete end-to-end test from publisher to subscriber on the UI.

