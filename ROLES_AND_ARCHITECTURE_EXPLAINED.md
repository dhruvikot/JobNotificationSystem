# 👥 User Roles vs 🖥️ Cluster Nodes - Complete Explanation

## PART 1: User Roles (Application Level)

### 📚 **What is a "Publisher"?**

In this system, **"Publisher" = "Organizer" or "Admin"**

There are **3 user roles** (NOT nodes):

| Role | Description | What They Can Do |
|------|-------------|------------------|
| **Student** 👨‍🎓 | Regular user | ✓ Subscribe to topics<br>✓ Receive notifications<br>✓ View **published events only**<br>✗ Cannot create events<br>✗ Cannot see draft events |
| **Organizer** 📢 | Event publisher | ✓ **Create events**<br>✓ **Publish events**<br>✓ **Unpublish events**<br>✓ View draft + published events<br>✓ Subscribe & receive notifications |
| **Admin** 👑 | System administrator | ✓ All organizer permissions<br>✓ **Create user accounts (Admin Panel)**<br>✓ Can modify any event<br>✓ Full system access |

---

### 🔑 **Publisher/Organizer Credentials (Seeded)**

From `scripts/seed-data.py`:

```python
SAMPLE_USERS = [
    {
        "name": "Alice Johnson",
        "email": "alice.johnson@university.edu",   # ← STUDENT
        "password": "student123",
        "role": "student"
    },
    {
        "name": "Bob Smith",
        "email": "bob.smith@university.edu",       # ← STUDENT
        "password": "student123",
        "role": "student"
    },
    {
        "name": "John Doe",
        "email": "john.doe@university.edu",        # ← PUBLISHER/ORGANIZER ⭐
        "password": "organizer123",
        "role": "organizer"
    },
    {
        "name": "System Admin",
        "email": "admin@system.com",               # ← ADMIN ⭐
        "password": "admin123",
        "role": "admin"
    }
]
```

**To test as a publisher, login as:**
- **Email:** `john.doe@university.edu`
- **Password:** `organizer123`

**To test as admin (with user management), login as:**
- **Email:** `admin@system.com`
- **Password:** `admin123`

**To test as student, login as:**
- **Email:** `alice.johnson@university.edu`
- **Password:** `student123`

---

### 🖥️ **Dashboard Differences by Role**

#### **Student Dashboard:**
```
┌─────────────────────────────────────┐
│  Welcome, Alice Johnson!            │
├─────────────────────────────────────┤
│  📬 Subscriptions  │  📅 Events     │
│  📍 Notifications  │  🔔 Alerts     │
├─────────────────────────────────────┤
│  Navigation:                         │
│  • Dashboard                         │
│  • Subscriptions                     │
│  • Events (published only)           │
│  • Notifications                     │
└─────────────────────────────────────┘
```

#### **Organizer Dashboard:**
```
┌─────────────────────────────────────┐
│  Welcome, John Doe!                 │
├─────────────────────────────────────┤
│  📬 Subscriptions  │  📅 Events     │
│  📍 Notifications  │  🔔 Alerts     │
├─────────────────────────────────────┤
│  Navigation:                         │
│  • Dashboard                         │
│  • Subscriptions                     │
│  • Events (draft + published)        │
│  • Create Event ⭐ (EXTRA OPTION)    │
│  • Notifications                     │
├─────────────────────────────────────┤
│  Event Actions:                      │
│  • 📤 Publish (draft events)         │
│  • 📥 Unpublish (published events)   │
└─────────────────────────────────────┘
```

#### **Admin Dashboard:**
```
┌─────────────────────────────────────┐
│  Welcome, System Admin!             │
├─────────────────────────────────────┤
│  📬 Subscriptions  │  📅 Events     │
│  📍 Notifications  │  🔔 Alerts     │
├─────────────────────────────────────┤
│  Navigation:                         │
│  • Dashboard                         │
│  • Subscriptions                     │
│  • Events (all)                      │
│  • Create Event                      │
│  • Notifications                     │
│  • Admin Panel 👑 (EXTRA OPTION)     │
├─────────────────────────────────────┤
│  Admin Powers:                       │
│  • ➕ Create Publishers/Organizers   │
│  • ➕ Create Students                │
│  • ➕ Create Admins                  │
└─────────────────────────────────────┘
```

**Key Differences:** 
- Students: See **published events only**, no creation ability
- Organizers: See **all events**, can create, publish, unpublish
- Admins: See **everything**, plus **Admin Panel** for user management

From `frontend/web/src/components/Navbar.js`:
```javascript
{user && (user.role === 'organizer' || user.role === 'admin') && (
  <Link to="/events/create" className="navbar-link">Create Event</Link>
)}

{user && user.role === 'admin' && (
  <Link to="/admin" className="navbar-link navbar-link-admin">Admin Panel</Link>
)}
```

---

## PART 2: Cluster Nodes (Infrastructure Level)

### 🖥️ **What are the "3 Nodes"?**

**IMPORTANT:** These are **NOT user roles**. These are **container replicas** running your microservices!

**Current Implementation (Docker Compose):**

```
┌─────────────────────────────────────────────────────────────────────┐
│              3-NODE DISTRIBUTED ARCHITECTURE                         │
│                                                                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │
│  │  Publisher-1     │  │  Publisher-2     │  │  Publisher-3     │ │
│  │  Port: 5003      │  │  Port: 5013      │  │  Port: 5023      │ │
│  │  ID: publisher-1 │  │  ID: publisher-2 │  │  ID: publisher-3 │ │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘ │
│           │                     │                      │            │
│           └─────────────────────┼──────────────────────┘            │
│                      Bully Leader Election                           │
│                      (publisher-2 is LEADER 👑)                      │
│                                                                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │
│  │ Dispatcher-1     │  │ Dispatcher-2     │  │ Dispatcher-3     │ │
│  │ Port: 5004       │  │ Port: 5014       │  │ Port: 5024       │ │
│  │ ID: dispatcher-1 │  │ ID: dispatcher-2 │  │ ID: dispatcher-3 │ │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘ │
│           │                     │                      │            │
│           └─────────────────────┼──────────────────────┘            │
│                      Bully Leader Election                           │
│                      + Gossip Protocol + MCP                         │
│                      (dispatcher-1 is LEADER 👑)                     │
│                                                                       │
│  All nodes communicate via HTTP for leader election                 │
│  All nodes consume from shared RabbitMQ                             │
│  All nodes use shared Redis for caching                             │
└─────────────────────────────────────────────────────────────────────┘
```

---

### 📊 **3+3 Node Configuration (Docker Compose)**

From `deployment/docker/docker-compose.yml`:

#### **Publisher Service - 3 Replicas:**

```yaml
publisher-service-1:
  container_name: publisher-service-1
  ports: ["5003:5003"]
  environment:
    NODE_ID: publisher-1
    NODE_URL: http://publisher-service-1:5003
    PEER_NODES: http://publisher-service-2:5013,http://publisher-service-3:5023

publisher-service-2:
  container_name: publisher-service-2
  ports: ["5013:5013"]
  environment:
    NODE_ID: publisher-2
    NODE_URL: http://publisher-service-2:5013
    PEER_NODES: http://publisher-service-1:5003,http://publisher-service-3:5023

publisher-service-3:
  container_name: publisher-service-3
  ports: ["5023:5023"]
  environment:
    NODE_ID: publisher-3
    NODE_URL: http://publisher-service-3:5023
    PEER_NODES: http://publisher-service-1:5003,http://publisher-service-2:5013
```

#### **Notification Dispatcher - 3 Replicas:**

```yaml
notification-dispatcher-1:
  container_name: notification-dispatcher-1
  ports: ["5004:5004"]
  environment:
    NODE_ID: dispatcher-1
    NODE_URL: http://notification-dispatcher-1:5004
    PEER_NODES: http://notification-dispatcher-2:5014,http://notification-dispatcher-3:5024

notification-dispatcher-2:
  container_name: notification-dispatcher-2
  ports: ["5014:5014"]
  environment:
    NODE_ID: dispatcher-2
    NODE_URL: http://notification-dispatcher-2:5014
    PEER_NODES: http://notification-dispatcher-1:5004,http://notification-dispatcher-3:5024

notification-dispatcher-3:
  container_name: notification-dispatcher-3
  ports: ["5024:5024"]
  environment:
    NODE_ID: dispatcher-3
    NODE_URL: http://notification-dispatcher-3:5024
    PEER_NODES: http://notification-dispatcher-1:5004,http://notification-dispatcher-2:5014
```

**What this means:**
- 6 container instances total (3 publishers + 3 dispatchers)
- Each has unique NODE_ID and PORT
- Each knows about its peers via PEER_NODES
- Leader election runs independently for each service type
- NOT related to user roles!

---

### 🔄 **How Services Distribute Across Containers**

**Complete Architecture:**

```
API Gateway (5000)
    ↓
┌───┴────────┬──────────┐
│            │          │
Pub-1 (5003) Pub-2 (5013) Pub-3 (5023)  ← Publisher Cluster
│            │          │                  Leader: publisher-2 👑
└────────────┼──────────┘
             ↓
         RabbitMQ (5672)
             ↓
┌────────────┼──────────┐
│            │          │
Dis-1 (5004) Dis-2 (5014) Dis-3 (5024)  ← Dispatcher Cluster
│            │          │                  Leader: dispatcher-1 👑
│            │          │                  + Gossip Protocol
│            │          │                  + MCP Membership
└────────────┼──────────┘
             ↓
    Redis (6379) + AWS SNS
```

---

### 🎯 **Leader Election - 2 Independent Clusters**

**Key Point:** We have **TWO independent leader elections**:
1. **Publisher Cluster** (3 replicas)
2. **Dispatcher Cluster** (3 replicas)

#### **Publisher Cluster:**
```
Publisher Leader Election:
┌──────────────────────────────────────────────┐
│                                               │
│  publisher-1 (ID: publisher-1) ──┐           │
│  ↓ Port 5003                      │           │
│                                   │           │
│  publisher-2 (ID: publisher-2) ──┼─→ Bully   │
│  ↓ Port 5013 (LEADER 👑)         │   Election│
│                                   │           │
│  publisher-3 (ID: publisher-3) ──┘           │
│  ↓ Port 5023                                  │
│                                               │
│  Result: publisher-2 is LEADER               │
│  Coordinates event publishing                │
└──────────────────────────────────────────────┘
```

#### **Dispatcher Cluster:**
```
Dispatcher Leader Election:
┌──────────────────────────────────────────────┐
│                                               │
│  dispatcher-1 (ID: dispatcher-1) ──┐         │
│  ↓ Port 5004 (LEADER 👑)            │         │
│                                     │         │
│  dispatcher-2 (ID: dispatcher-2) ──┼─→ Bully │
│  ↓ Port 5014                        │   Election│
│                                     │   + Gossip│
│  dispatcher-3 (ID: dispatcher-3) ──┘   + MCP  │
│  ↓ Port 5024                                  │
│                                               │
│  Result: dispatcher-1 is LEADER              │
│  Performs cleanup, aggregation tasks         │
└──────────────────────────────────────────────┘
```

**Your Bully Algorithm runs at APPLICATION LEVEL:**
- Containers communicate via HTTP
- They elect a leader (highest ID wins in Bully)
- Leader performs exclusive tasks
- If leader fails, re-election happens automatically (5-10 seconds)
- **NOT using Kubernetes native leader election**

---

## 🎬 **Complete Architecture: Putting It All Together**

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER ROLES (Application)                     │
│                                                                   │
│   👨‍🎓 Students            📢 Organizers          👑 Admins        │
│   alice.johnson@...      john.doe@...           admin@system.com │
│   (View published)       (Create & Publish)     (User Management)│
│   password: student123   password: organizer123 password: admin123│
│                                                                   │
│                           ↓ Login via                            │
│                                                                   │
│                      React Frontend (Port 3000)                  │
│                      ↓ Connects to WebSocket                     │
│                      ↓ Real-time Push Notifications              │
└────────────────────────────┬────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  DOCKER DISTRIBUTED ARCHITECTURE                 │
│                                                                   │
│  API Gateway (5000)                                              │
│        ↓                                                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐│
│  │  Publisher-1    │  │  Publisher-2 👑 │  │  Publisher-3    ││
│  │  Port: 5003     │  │  Port: 5013     │  │  Port: 5023     ││
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘│
│           └───────────────┬─────────────────────────┘          │
│                     Bully Election                              │
│                           ↓                                     │
│                     RabbitMQ (5672)                             │
│                           ↓                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐│
│  │  Dispatcher-1 👑│  │  Dispatcher-2   │  │  Dispatcher-3   ││
│  │  Port: 5004     │  │  Port: 5014     │  │  Port: 5024     ││
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘│
│           └───────────────┬─────────────────────────┘          │
│                     Bully Election                              │
│                     + Gossip Protocol                           │
│                     + MCP Membership                            │
│                           ↓                                     │
│         Redis (6379) ← WebSocket Notifications                 │
│                                                                   │
│  Supporting Services:                                            │
│  • Auth Service (5001)                                          │
│  • Subscription Service (5002)                                  │
│  • Gossip Agent (5006)                                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        AWS SERVICES                              │
│   • DynamoDB (Users, Events, Subscriptions, Popularity)        │
│   • S3 (Event media storage)                                     │
│   • SNS (Email/SMS notifications)                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧪 **Testing Both Concepts**

### **Test 1: User Roles (Different Dashboards)**

#### **As Student:**
```bash
# Login
http://localhost:3000
Email: alice.johnson@university.edu
Password: student123

✓ Dashboard WITHOUT "Create Event" button
✓ Events page shows ONLY published events (no drafts)
✓ No Admin Panel link
✓ Can subscribe to topics
✓ Receives real-time notifications via WebSocket
```

#### **As Organizer:**
```bash
# Login
Email: john.doe@university.edu
Password: organizer123

✓ Dashboard WITH "Create Event" button ⭐
✓ Events page shows draft + published events
✓ Can click "📤 Publish Event" on drafts
✓ Can click "📥 Unpublish" on published events
✓ No Admin Panel (not an admin)
```

#### **As Admin:**
```bash
# Login
Email: admin@system.com
Password: admin123

✓ All organizer features
✓ Admin Panel link visible (purple gradient) ⭐
✓ Can create new users (publishers/students/admins)
✓ Full system access
```

**Test Creating Event (organizer only):**
```bash
1. Login as john.doe@university.edu
2. Click "Create Event"
3. Fill details:
   - Title: "AI Hackathon 2025"
   - Topic: hackathon.aiml
   - Description: "Build the future"
4. Click "Create Event" (saves as DRAFT)
5. Go to Events page
6. See event with "📝 Draft" badge
7. Click "📤 Publish Event"
8. Confirm → Event published
9. Check as student → Event now visible! 🎉
```

---

### **Test 2: Leader Election & Fault Tolerance**

#### **Check Cluster Status:**
```powershell
# View all running containers
docker ps --format "table {{.Names}}\t{{.Status}}"

# Should show:
# publisher-service-1         Up
# publisher-service-2         Up
# publisher-service-3         Up
# notification-dispatcher-1   Up
# notification-dispatcher-2   Up
# notification-dispatcher-3   Up
```

#### **Check Publisher Leader:**
```powershell
# Check publisher-1 election status
Invoke-WebRequest -Uri "http://localhost:5003/election/status" -UseBasicParsing

# Check publisher-2 (likely leader)
Invoke-WebRequest -Uri "http://localhost:5013/election/status" -UseBasicParsing

# Response:
# {
#   "node_id": "publisher-2",
#   "is_leader": true,        ← This one is LEADER! 👑
#   "current_leader": "publisher-2",
#   "state": "LEADER"
# }
```

#### **Check Dispatcher Leader:**
```powershell
# Check dispatcher-1
Invoke-WebRequest -Uri "http://localhost:5004/election/status" -UseBasicParsing

# Response:
# {
#   "node_id": "dispatcher-1",
#   "is_leader": true,         ← This one is LEADER! 👑
#   "current_leader": "dispatcher-1",
#   "state": "LEADER"
# }
```

#### **Test Fault Tolerance (Simulate Node Failure):**
```powershell
# 1. Stop a node (simulate crash)
docker stop publisher-service-3

# 2. Check remaining nodes (5-10 seconds for election)
docker logs publisher-service-2 | Select-String "Election|Leader"

# Expected log output:
# [Election] Node notification-dispatcher-3 didn't respond
# [Election] Timeout waiting for COORDINATOR, restarting election
# [Election] *** Node publisher-2 is now LEADER ***

# 3. Verify system still works
Invoke-WebRequest -Uri "http://localhost:5003/health" -UseBasicParsing
# Status: healthy ✓

# 4. Restart the node (recovery)
docker start publisher-service-3

# Node automatically rejoins cluster and participates in next election!
```

#### **View Election Logs:**
```powershell
# Publisher election activity
docker logs publisher-service-2 | Select-String "Election|Leader|LEADER"

# Expected output:
# [Election] Initialized Bully Election for node publisher-2
# [Election] Node publisher-2 starting election
# [Election] Sending ELECTION to 2 higher nodes
# [Election] *** Node publisher-2 is now LEADER ***
# [Publisher] 🏆 Node publisher-2 became the LEADER

# Dispatcher election activity
docker logs notification-dispatcher-1 | Select-String "Election|Leader|LEADER"

# Expected output:
# [Election] Initialized Bully Election for node dispatcher-1
# [Dispatcher] *** Node dispatcher-1 became LEADER ***
# [Election] Accepted dispatcher-3 as leader
# [Dispatcher] *** Node dispatcher-1 lost leadership ***
# [Dispatcher] *** Node dispatcher-1 became LEADER ***
```

---

### **Test 3: Admin User Management**

```bash
# 1. Login as Admin
http://localhost:3000
Email: admin@system.com
Password: admin123

# 2. Click purple "Admin Panel" button in nav

# 3. Create a new publisher
Fill form:
  Name: Jane Publisher
  Email: jane@university.edu
  Password: publisher123
  Role: Organizer/Publisher
  
Click "Create Organizer Account"

# 4. Logout and login as new publisher
Email: jane@university.edu
Password: publisher123

# 5. Verify can create events! ✓
```

---

## 📝 **Summary**

### **User Roles (Application Level):**
- **3 roles:** Student, Organizer (Publisher), Admin
- **Different permissions:** 
  - Students: View published events only
  - Organizers: Create, publish, unpublish events
  - Admins: User management + all organizer powers
- **Different UI:** 
  - Students: No creation buttons
  - Organizers: "Create Event", "Publish", "Unpublish" buttons
  - Admins: "Admin Panel" button (purple)
- **Test credentials:** 
  - Student: `alice.johnson@university.edu` / `student123`
  - Organizer: `john.doe@university.edu` / `organizer123`
  - Admin: `admin@system.com` / `admin123`

### **Cluster Nodes (Infrastructure Level):**
- **6 container replicas:** 3 publishers + 3 dispatchers
- **2 independent leader elections:** 
  - Publisher cluster (coordinates event publishing)
  - Dispatcher cluster (coordinates notification dispatch)
- **Bully algorithm:** Application-level, not K8s native
- **Fault tolerance:** Cluster survives with N-1 nodes
- **Automatic failover:** 5-10 seconds for re-election
- **Not related to user roles:** Infrastructure vs application layer

### **Key Distinction:**
```
USER ROLES            ≠            CLUSTER NODES
(Who uses system)                  (Where system runs)
3 types of users                   6 container replicas
alice, john, admin                 pub-1, pub-2, pub-3
                                   dis-1, dis-2, dis-3

Application Layer     ≠            Infrastructure Layer
Role-based access                  Distributed coordination
```

---

## 🎓 **For Your Presentation:**

"Our system has **two independent layers**:

1. **Application Layer:** 3 user roles with different permissions:
   - **Students** see published events and subscribe to topics
   - **Organizers** create, publish, and unpublish events
   - **Admins** manage users through a dedicated Admin Panel
   
   Students only see published events (role-based filtering), while organizers see all events including drafts.

2. **Infrastructure Layer:** 3-node distributed architecture:
   - **3 Publisher Service replicas** with Bully Leader Election
   - **3 Dispatcher Service replicas** with Bully Election + Gossip + MCP
   - **Custom distributed algorithms** (not using K8s native features)
   - **Fault tolerance** - cluster continues with 2/3 nodes
   - **Automatic failover** - re-election in 5-10 seconds
   
   Each service type runs its own leader election independently for coordinated task execution.

3. **Real-time Features:**
   - WebSocket connections for instant notifications
   - Redis for persistent caching
   - Browser push notifications

**Tested Features:**
- ✅ Leader election working (Bully algorithm)
- ✅ Fault tolerance validated (survived node crash)
- ✅ Role-based access control (students vs organizers)
- ✅ Real-time notifications (WebSocket + Redis)
- ✅ Admin user management (create publishers/students)

These layers are independent - user roles don't determine node assignment. The distributed algorithms handle application-level coordination while Docker manages container orchestration."

---

## 📚 **Additional Resources**

- **3-Node Implementation Guide:** `3_NODE_DISTRIBUTED_IMPLEMENTATION.md`
- **Test Results:** `TEST_RESULTS_3_NODE_ARCHITECTURE.md`
- **Admin User Management:** `ADMIN_USER_MANAGEMENT.md`
- **Publisher Workflow:** `UNPUBLISH_AND_ROLE_BASED_FILTERING.md`
- **Quick Start:** `QUICK_START_CHECKLIST.md`

---

**Questions? The system is fully functional and tested!** 🚀
