# Admin User Management Feature

## Overview

Administrators now have a dedicated **Admin Panel** where they can create new user accounts, including publishers/organizers, students, and other administrators. This provides centralized user management without requiring users to self-register.

---

## Key Features

### 1. **Admin-Only Access**
- Only users with `admin` role can access the Admin Panel
- Protected route with authorization checks
- Visible only to admins in navigation bar

### 2. **Create User Accounts**
Admins can create accounts for any role:
- **Publishers/Organizers**: Can create and manage events
- **Students**: Can subscribe and receive notifications
- **Administrators**: Full system access and user management

### 3. **User-Friendly Interface**
- Clean, intuitive form design
- Real-time validation
- Success/error feedback
- Role descriptions and guidance
- Auto-clearing form after successful creation

---

## How to Access

### For Admins

1. **Login as Admin:**
   ```
   Email: admin@system.com
   Password: admin123
   ```

2. **Navigate to Admin Panel:**
   - Look for the **"Admin Panel"** button in the navigation bar (purple gradient)
   - Or go directly to: `http://localhost:3000/admin`

### For Non-Admins

- The Admin Panel link will not appear in the navigation
- Direct URL access will show "Access Denied" message
- Role-based access control ensures security

---

## Creating a New User

### Step-by-Step Guide

1. **Navigate to Admin Panel** (visible only to admins)

2. **Fill in User Details:**
   - **Full Name** * (required)
   - **Email** * (required, must be unique)
   - **Password** * (required, min 6 characters)
   - **Phone** (optional)
   - **User Role** * (required):
     - Organizer/Publisher
     - Student
     - Administrator

3. **Review Role Description:**
   - Each role displays helper text explaining permissions
   - Role cards at bottom show detailed capabilities

4. **Submit Form:**
   - Click "Create [Role] Account" button
   - Success message appears with user details
   - Form automatically clears for next entry

5. **New User Can Login:**
   - User can immediately login with created credentials
   - Access level determined by assigned role

---

## User Roles Explained

### 📝 Organizer/Publisher

**Permissions:**
- Create and manage events
- Publish events to notify subscribers
- View event analytics
- Manage event lifecycle (draft/published)
- Unpublish events if needed

**Use Case:**
- Event organizers
- Career services staff
- Club leaders
- Department administrators

**Example Creation:**
```
Name: John Doe
Email: john.doe@university.edu
Password: organizer123
Role: Organizer/Publisher
```

### 👨‍🎓 Student

**Permissions:**
- Browse published events only
- Subscribe to topics of interest
- Receive real-time notifications
- View notification history
- Manage subscriptions

**Use Case:**
- Students seeking jobs/internships
- Students interested in hackathons
- Event attendees

**Example Creation:**
```
Name: Alice Johnson
Email: alice.johnson@university.edu
Password: student123
Role: Student
```

### 🔐 Administrator

**Permissions:**
- Create and manage user accounts
- Full access to all system features
- View system health and metrics
- Manage all events and subscriptions
- Override any restrictions

**Use Case:**
- System administrators
- IT staff
- Platform managers

**Example Creation:**
```
Name: System Admin
Email: admin@university.edu
Password: secureAdmin456
Role: Administrator
```

---

## Backend Implementation

### Auth Service Endpoint

**Endpoint:** `POST /admin/create-user`

**Authentication:** Required (Admin role only)

**Request Headers:**
```http
Authorization: Bearer <jwt_token>
X-User-ID: <admin_user_id>
X-User-Role: admin
```

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "password": "password123",
  "name": "New User",
  "phone": "+1234567890",
  "role": "organizer"
}
```

**Success Response (201):**
```json
{
  "success": true,
  "user_id": "U1732561234567",
  "user": {
    "user_id": "U1732561234567",
    "email": "newuser@example.com",
    "name": "New User",
    "role": "organizer",
    "phone": "+1234567890",
    "created_at": 1732561234
  },
  "message": "Organizer account created successfully"
}
```

**Error Responses:**

- **403 Forbidden:**
```json
{
  "error": "Admin access required"
}
```

- **409 Conflict:**
```json
{
  "error": "User with this email already exists"
}
```

- **400 Bad Request:**
```json
{
  "error": "Invalid role. Must be student, organizer, or admin"
}
```

### API Gateway Route

**Endpoint:** `POST /auth/admin/create-user`

**Middleware:** `@require_role('admin')`

Forwards request to Auth Service with proper headers.

---

## Frontend Implementation

### Admin Panel Component

**Location:** `frontend/web/src/pages/AdminPanel.js`

**Features:**
- Form validation (email format, password length)
- Role-based helper text
- Success/error messaging
- Loading states
- Auto-clearing form
- Role descriptions section

**Styling:** `frontend/web/src/pages/AdminPanel.css`

### Navigation Integration

**Component:** `frontend/web/src/components/Navbar.js`

**Conditional Rendering:**
```javascript
{user && user.role === 'admin' && (
  <Link to="/admin" className="navbar-link navbar-link-admin">
    Admin Panel
  </Link>
)}
```

**Styling:** Purple gradient background to stand out

### API Integration

**File:** `frontend/web/src/api/api.js`

```javascript
authAPI: {
  adminCreateUser: (data) => api.post('/auth/admin/create-user', data)
}
```

---

## Security Features

### 1. **Role-Based Access Control (RBAC)**
- Backend validates admin role in headers
- Frontend hides Admin Panel from non-admins
- Protected routes redirect unauthorized users

### 2. **Input Validation**
- Email format validation
- Password length requirements (min 6 chars)
- Required field validation
- Role whitelist (student, organizer, admin only)

### 3. **Duplicate Prevention**
- Email uniqueness check before creation
- DynamoDB conditional puts
- User-friendly error messages

### 4. **Audit Trail**
- Logs admin user ID who created the account
- Timestamps for user creation
- Server-side logging of all operations

---

## Use Cases

### Scenario 1: Onboarding Event Organizers

**Problem:** Career services needs to add 5 new event organizers for upcoming job fairs.

**Solution:**
1. Admin logs into Admin Panel
2. Creates 5 organizer accounts with university emails
3. Shares credentials with career services staff
4. Organizers can immediately start creating events

**Time Saved:** ~15 minutes vs. having each person self-register

### Scenario 2: Bulk Student Account Creation

**Problem:** Department wants to pre-create accounts for 100 students in a program.

**Solution:**
1. Admin uses Admin Panel to create accounts
2. Students receive credentials via email
3. Students login and subscribe to relevant topics
4. No registration friction for students

**Benefit:** Controlled onboarding, verified users

### Scenario 3: Adding New Administrators

**Problem:** New IT staff member needs admin access.

**Solution:**
1. Existing admin creates new admin account
2. New admin can immediately access Admin Panel
3. No need for complex permission escalation

**Security:** Existing admin controls who gets admin access

---

## Testing the Feature

### Test 1: Create Publisher Account

1. **Login as Admin:**
   ```
   Email: admin@system.com
   Password: admin123
   ```

2. **Go to Admin Panel**

3. **Fill form:**
   ```
   Name: Test Publisher
   Email: testpub@test.com
   Password: test123
   Role: Organizer/Publisher
   ```

4. **Click "Create Organizer Account"**

5. **Verify Success:**
   - Success message appears
   - Form clears

6. **Test Login:**
   - Logout
   - Login with new credentials
   - Should have organizer permissions

### Test 2: Verify Access Control

1. **Login as Student:**
   ```
   Email: alice.johnson@university.edu
   Password: student123
   ```

2. **Check Navigation:**
   - Admin Panel link should NOT appear

3. **Try Direct Access:**
   - Navigate to `/admin`
   - Should see "Access Denied" message

### Test 3: Duplicate Email Prevention

1. **Login as Admin**

2. **Create user with existing email**

3. **Verify Error:**
   - Should show "User with this email already exists"
   - Form data retained for correction

---

## Troubleshooting

### Issue: "Admin access required" error

**Cause:** User is not logged in as admin

**Solution:** 
- Verify logged in user has `admin` role
- Check JWT token is valid
- Logout and login again

### Issue: "User with this email already exists"

**Cause:** Email is already registered in system

**Solution:**
- Use different email address
- Check if user already exists in system
- Contact system admin to reset/delete existing account

### Issue: Admin Panel link not showing

**Cause:** User doesn't have admin role

**Solution:**
- Only admins can see Admin Panel link
- Verify user role in profile
- Contact existing admin to create admin account

---

## Benefits

### 1. **Centralized User Management**
- Admins control who joins the platform
- No open self-registration (if desired)
- Verified user accounts

### 2. **Streamlined Onboarding**
- Pre-create accounts for specific users
- Share credentials securely
- Immediate access without registration friction

### 3. **Better Security**
- Controlled access to publisher role
- Prevent unauthorized event creation
- Admin approval process

### 4. **Operational Efficiency**
- Bulk account creation
- Quick setup for new team members
- Reduced support requests

### 5. **Flexibility**
- Can create any role type
- Instant account activation
- No email verification required

---

## Future Enhancements

### Potential Features:

1. **Bulk User Import**
   - CSV file upload
   - Batch account creation
   - Email template for credentials

2. **User Management Dashboard**
   - List all users
   - Edit user details
   - Deactivate/delete users
   - Reset passwords

3. **Role Modification**
   - Change user roles
   - Temporary role upgrades
   - Permission management

4. **Audit Logs**
   - View who created which accounts
   - Track account modifications
   - Export audit reports

5. **Email Notifications**
   - Auto-send credentials to new users
   - Welcome email templates
   - Password reset links

---

## API Reference Summary

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/auth/admin/create-user` | POST | Admin | Create new user account |

### Required Headers
- `Authorization: Bearer <jwt_token>`
- `X-User-ID: <admin_user_id>` (auto-added by API gateway)
- `X-User-Role: admin` (auto-added by API gateway)

### Validation Rules
- Email: Valid format, unique
- Password: Minimum 6 characters
- Name: Required, non-empty
- Role: One of: `student`, `organizer`, `admin`
- Phone: Optional, any format

---

## Summary

✅ **Admins can now:**
- Create publisher/organizer accounts
- Create student accounts
- Create admin accounts
- Manage user onboarding centrally

✅ **Security ensured by:**
- Role-based access control
- Backend authorization checks
- Input validation
- Audit logging

✅ **User experience:**
- Clean, intuitive interface
- Clear role descriptions
- Real-time feedback
- Mobile-responsive design

This feature provides essential **user management capabilities** for platform administrators, enabling controlled growth and better operational control!

