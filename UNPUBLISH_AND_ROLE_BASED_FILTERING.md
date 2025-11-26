# Unpublish Feature & Role-Based Event Filtering

## Overview

This document explains the new **unpublish** functionality and **role-based event filtering** that have been implemented to provide better control over event visibility.

## Key Features

### 1. **Publish Draft Events (Organizers/Admins Only)**

Organizers and admins can now publish draft events directly from the Events page. This provides:
- Quick one-click publishing
- Confirmation before sending notifications
- Instant visibility to students
- No need to navigate to edit forms

**How it works:**
- "📤 Publish Event" button appears on draft events
- Confirmation dialog warns about notifications
- Event status changes from `draft` → `published`
- All subscribed students receive notifications
- Event becomes visible to all students

### 2. **Unpublish Events (Organizers/Admins Only)**

Organizers and admins can unpublish events that have been previously published. This is useful for:
- Removing outdated events
- Hiding events that need corrections
- Managing event visibility dynamically

**How it works:**
- "📥 Unpublish" button appears on published events
- Only the event creator (organizer) or admins can unpublish
- Unpublished events return to "draft" status
- Once unpublished, students can no longer see the event
- Organizers can still see and edit draft events

### 3. **Role-Based Event Filtering**

Events are now filtered based on user role to ensure proper visibility:

| User Role | What They See |
|-----------|---------------|
| **Students** | Only **published** events |
| **Organizers** | All events (both **draft** and **published**) |
| **Admins** | All events (both **draft** and **published**) |

This ensures that:
- Students don't see incomplete or draft events
- Organizers can manage their drafts before making them public
- Clear separation between public and private content

---

## Implementation Details

### Backend Changes

#### 1. **Publisher Service** (`backend/publisher_service/app.py`)

**New Endpoint:**
```python
POST /events/<event_id>/unpublish
```

**Functionality:**
- Checks if user is the event owner or admin
- Verifies event is currently published
- Updates event status from `published` to `draft`
- Returns success confirmation

**Response:**
```json
{
  "success": true,
  "event_id": "evt_123",
  "message": "Event unpublished successfully"
}
```

#### 2. **API Gateway** (`backend/api_gateway/app.py`)

**New Endpoint:**
```python
POST /events/<event_id>/unpublish
@require_role('organizer', 'admin')
```

**Updated Endpoint:**
```python
GET /events
```
- Now checks user role from JWT token
- If user is a student (or unauthenticated), adds `status=published` filter
- Organizers and admins see all events without filtering

### Frontend Changes

#### 1. **Events API** (`frontend/web/src/api/api.js`)

**New API Method:**
```javascript
unpublishEvent: (eventId) => api.post(`/events/${eventId}/unpublish`)
```

#### 2. **Events Page** (`frontend/web/src/pages/Events.js`)

**New Features:**
- Imports `useAuth` to get current user role
- Shows status badges for both **Published** and **Draft** events
- Displays "📤 Publish Event" button for organizers on draft events
- Displays "📥 Unpublish" button for organizers on published events
- Confirmation dialogs before publishing/unpublishing
- Auto-refreshes event list after state change

**Status Badges:**
- ✅ **Published** - Green badge for published events
- 📝 **Draft** - Yellow badge for draft events (only visible to organizers/admins)

**Action Buttons:**
- **📤 Publish Event** button:
  - Only visible to organizers/admins
  - Only shown on draft events
  - Confirms before publishing and sending notifications
  
- **📥 Unpublish** button:
  - Only visible to organizers/admins
  - Only shown on published events
  - Confirms before hiding event from students

#### 3. **CSS Styling** (`frontend/web/src/pages/Events.css`)

**New Styles:**
```css
.badge-warning {
  background-color: #ffc107;
  color: #000;
}

.event-actions {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}
```

---

## User Experience

### For Students

**Before:**
- Could see all events including drafts
- Confusing to see incomplete events

**After:**
- Only see published, ready-to-view events
- Clean, curated event feed

### For Organizers/Admins

**Before:**
- Could only publish events from edit form
- No way to hide events after publishing
- No quick publish option

**After:**
- Can create draft events
- Can publish directly from Events page (quick action)
- Can unpublish if needed
- Can re-publish after making changes
- Full control over event lifecycle

---

## Event Lifecycle

```
1. CREATE
   ↓
2. DRAFT (visible only to organizers/admins)
   ↓
   | Click "📤 Publish Event" button
   ↓
3. PUBLISH → sends notifications to subscribers
   ↓
4. PUBLISHED (visible to all students)
   ↓
   | Click "📥 Unpublish" button (if needed)
   ↓
5. DRAFT (can edit and re-publish)
   ↓
   | Click "📤 Publish Event" again
   ↓
6. PUBLISHED (back to step 4)
```

---

## Security

### Authorization Checks

1. **Create Event**: Organizer or Admin role required
2. **Publish Event**: Must be event creator or admin
3. **Unpublish Event**: Must be event creator or admin
4. **View Drafts**: Organizer or Admin role required
5. **View Published**: Available to all users

### JWT Token Validation

- All authenticated endpoints verify JWT tokens
- User role extracted from token payload
- Invalid tokens treated as student role (most restrictive)

---

## Testing the Features

### Test Unpublish Functionality

1. **Login as Organizer:**
   ```
   Email: john.doe@university.edu
   Password: organizer123
   ```

2. **Create and publish an event**

3. **View the Events page** - you should see:
   - Published events with ✅ badge
   - Draft events with 📝 badge (if any)
   - "📤 Publish Event" button on draft events
   - "📥 Unpublish" button on published events

4. **Test Publishing a Draft:**
   - Create a new event (it starts as draft)
   - Go to Events page
   - Click "📤 Publish Event"
   - Confirm the dialog
   - Event status changes to "Published"
   - Subscribed students receive notifications

5. **Test Unpublishing:**
   - Click "📥 Unpublish" on a published event
   - Confirm the dialog
   - Event status changes to "Draft"
   - Students can no longer see it

### Test Role-Based Filtering

1. **Login as Student:**
   ```
   Email: alice.johnson@university.edu
   Password: student123
   ```

2. **View Events page:**
   - You should only see published events
   - No draft events visible
   - No unpublish buttons

3. **Login as Organizer:**
   ```
   Email: john.doe@university.edu
   Password: organizer123
   ```

4. **View Events page:**
   - You should see both draft and published events
   - "📤 Publish Event" buttons on your draft events
   - "📥 Unpublish" buttons on your published events

---

## Benefits

### 1. **Content Control**
- Organizers can prepare events as drafts
- Publish when ready
- Unpublish if changes needed

### 2. **Better UX for Students**
- Only see complete, relevant events
- No confusion from draft content

### 3. **Event Management**
- Full event lifecycle management
- Flexibility to correct mistakes
- Dynamic content visibility

### 4. **Security**
- Role-based access control
- Proper authorization checks
- JWT token validation

---

## API Reference

### Unpublish Event

**Endpoint:** `POST /events/<event_id>/unpublish`

**Authentication:** Required (Organizer or Admin)

**Request Headers:**
```
Authorization: Bearer <jwt_token>
```

**Success Response (200):**
```json
{
  "success": true,
  "event_id": "evt_abc123",
  "message": "Event unpublished successfully"
}
```

**Error Responses:**

- **401 Unauthorized:**
```json
{
  "error": "Authentication required"
}
```

- **403 Forbidden:**
```json
{
  "error": "Unauthorized to unpublish this event"
}
```

- **404 Not Found:**
```json
{
  "error": "Event not found"
}
```

- **400 Bad Request:**
```json
{
  "error": "Event is already unpublished"
}
```

### List Events

**Endpoint:** `GET /events?status=<status>&topic=<topic>`

**Authentication:** Optional (affects filtering)

**Query Parameters:**
- `status`: Filter by status (auto-set for students)
- `topic`: Filter by topic category
- `limit`: Max results (default: 50)

**Filtering Logic:**
- **Authenticated Students:** Auto-filters to `status=published`
- **Organizers/Admins:** No auto-filtering, see all events
- **Unauthenticated:** Treated as student, only see published

**Response:**
```json
{
  "events": [
    {
      "event_id": "evt_123",
      "title": "AI Hackathon",
      "status": "published",
      "topic": "hackathon.aiml",
      ...
    }
  ],
  "count": 10
}
```

---

## Summary

✅ **Students** see only **published events** (clean, curated feed)

✅ **Organizers** can:
- Create draft events
- Publish directly from Events page (quick action)
- Unpublish if changes needed
- Re-publish after editing
- See all their events (draft + published)
- Full lifecycle management

✅ **Better content control** for event management

✅ **Improved user experience** for all roles

This creates a proper **content moderation workflow** similar to platforms like Medium, WordPress, or other publishing systems!

