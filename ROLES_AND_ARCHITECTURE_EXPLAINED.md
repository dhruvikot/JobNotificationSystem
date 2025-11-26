# 👥 User Roles vs 🖥️ Cluster Nodes - Complete Explanation

## PART 1: User Roles (Application Level)

### 📚 **What is a "Publisher"?**

In this system, **"Publisher" = "Organizer" or "Admin"**

There are **3 user roles** (NOT nodes):

| Role | Description | What They Can Do |
|------|-------------|------------------|
| **Student** 👨‍🎓 | Regular user | ✓ Subscribe to topics<br>✓ Receive notifications<br>✓ View events<br>✗ Cannot create events |
| **Organizer** 📢 | Event publisher | ✓ **Create events**<br>✓ **Publish events**<br>✓ Subscribe & receive notifications<br>✓ Everything students can do |
| **Admin** 👑 | System administrator | ✓ All organizer permissions<br>✓ Can modify any event<br>✓ Full system access |

---

### 🔑 **Publisher/Organizer Credentials (Seeded)**

From `scripts/seed-data.py`:

```python
SAMPLE_USERS = [
    {
        "name": "Alice Student",
        "email": "alice@student.com",        # ← STUDENT
        "password": "password123",
        "role": "student"
    },
    {
        "name": "Bob Developer",
        "email": "bob@student.com",          # ← STUDENT
        "password": "password123",
        "role": "student"
    },
    {
        "name": "Charlie Organizer",
        "email": "charlie@organizer.com",    # ← PUBLISHER/ORGANIZER ⭐
        "password": "password123",
        "role": "organizer"
    },
    {
        "name": "Diana Admin",
        "email": "diana@admin.com",          # ← ADMIN ⭐
        "password": "password123",
        "role": "admin"
    }
]
```

**To test as a publisher, login as:**
- **Email:** `charlie@organizer.com`
- **Password:** `password123`

OR

- **Email:** `diana@admin.com`
- **Password:** `password123`

---

### 🖥️ **Dashboard Differences by Role**

#### **Student Dashboard:**
```
┌─────────────────────────────────────┐
│  Welcome, Alice Student!            │
├─────────────────────────────────────┤
│  📬 Subscriptions  │  📅 Events     │
│  📍 Notifications  │  🔔 Alerts     │
├─────────────────────────────────────┤
│  Navigation:                         │
│  • Dashboard                         │
│  • Subscriptions                     │
│  • Events (view only)                │
│  • Notifications                     │
└─────────────────────────────────────┘
```

#### **Organizer/Admin Dashboard:**
```
┌─────────────────────────────────────┐
│  Welcome, Charlie Organizer!        │
├─────────────────────────────────────┤
│  📬 Subscriptions  │  📅 Events     │
│  📍 Notifications  │  🔔 Alerts     │
├─────────────────────────────────────┤
│  Navigation:                         │
│  • Dashboard                         │
│  • Subscriptions                     │
│  • Events (view)                     │
│  • Create Event ⭐ (EXTRA OPTION)    │
│  • Notifications                     │
└─────────────────────────────────────┘
```

**Key Difference:** Only organizers/admins see **"Create Event"** button!

From `frontend/web/src/components/Navbar.js` (line 28-29):
```javascript
{user && (user.role === 'organizer' || user.role === 'admin') && (
  <Link to="/events/create" className="navbar-link">Create Event</Link>
)}
```

---

## PART 2: Cluster Nodes (Infrastructure Level)

### 🖥️ **What are the "3 Nodes"?**

**IMPORTANT:** These are **NOT user roles**. These are **physical/virtual servers** in your Kubernetes cluster!

```
┌─────────────────────────────────────────────────────────┐
│           AWS EKS CLUSTER (if deployed)                 │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Node 1     │  │   Node 2     │  │   Node 3     │ │
│  │ EC2 t3.medium│  │ EC2 t3.medium│  │ EC2 t3.medium│ │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤ │
│  │ Containers:  │  │ Containers:  │  │ Containers:  │ │
│  │ • API Gtwy   │  │ • Dispatcher │  │ • Dispatcher │ │
│  │ • Auth Svc   │  │ • Publisher  │  │ • Gossip     │ │
│  │ • RabbitMQ   │  │ • Sub Service│  │ • Frontend   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                          │
│  All nodes run MULTIPLE microservices as containers     │
└─────────────────────────────────────────────────────────┘
```

---

### 📊 **3 Nodes Configuration**

From `deployment/k8s/README.md` (line 74-82):

```bash
eksctl create cluster \
    --name distributed-events-cluster \
    --region us-east-1 \
    --nodegroup-name standard-workers \
    --node-type t3.medium \          # Each node: 2 vCPU, 4GB RAM
    --nodes 3 \                      # ← 3 WORKER NODES
    --nodes-min 2 \                  # Auto-scale down to 2
    --nodes-max 5                    # Auto-scale up to 5
```

**What this means:**
- 3 AWS EC2 instances (servers)
- Each runs Docker containers
- Kubernetes distributes your microservices across them
- NOT related to user roles!

---

### 🔄 **How Microservices Distribute Across Nodes**

From `deployment/k8s/notification-dispatcher.yaml` (line 11):

```yaml
spec:
  replicas: 3  # Create 3 instances of Notification Dispatcher
```

**Example distribution (Kubernetes decides automatically):**

```
NODE 1                    NODE 2                    NODE 3
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│ Dispatcher-1 │ ←──┐    │ Dispatcher-2 │         │ Dispatcher-3 │
│ (Leader) 👑  │    │    │ (Follower)   │         │ (Follower)   │
├──────────────┤    │    ├──────────────┤         ├──────────────┤
│ API Gateway  │    │    │ Publisher    │         │ Gossip Agent │
├──────────────┤    │    ├──────────────┤         ├──────────────┤
│ Auth Service │    │    │ Sub Service  │         │ Frontend     │
├──────────────┤    │    ├──────────────┤         ├──────────────┤
│ RabbitMQ     │    │    │ Redis        │         │ ...          │
└──────────────┘    │    └──────────────┘         └──────────────┘
                    │
                    └── Leader Election happens BETWEEN these 3
                        Dispatcher replicas (Bully Algorithm)
```

---

### 🎯 **Leader Election Across 3 Dispatcher Replicas**

**Key Point:** The 3 "nodes" for leader election are **NOT EC2 nodes**, they are **3 instances of Notification Dispatcher**!

```
Notification Dispatcher Replicas:
┌─────────────────────────────────────────────────┐
│                                                  │
│  Dispatcher-1 (ID: dispatcher-1) ──┐            │
│  ↓ Running on Node 1                │            │
│                                     │            │
│  Dispatcher-2 (ID: dispatcher-2) ──┼─→ Bully    │
│  ↓ Running on Node 2                │   Election│
│                                     │            │
│  Dispatcher-3 (ID: dispatcher-3) ──┘            │
│  ↓ Running on Node 3                             │
│                                                  │
│  Result: Highest ID becomes leader 👑           │
└─────────────────────────────────────────────────┘
```

**Your Bully Algorithm runs at APPLICATION LEVEL:**
- 3 dispatcher containers communicate
- They elect a leader (highest ID)
- Leader performs exclusive tasks (cleanup, aggregation)
- If leader fails, re-election happens automatically

---

## 🎬 **Complete Architecture: Putting It All Together**

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER ROLES (Application)                     │
│                                                                   │
│   👨‍🎓 Students         📢 Organizers         👑 Admins           │
│   alice@student.com   charlie@organizer.com  diana@admin.com    │
│   (View & Subscribe)  (Create & Publish)     (Full Access)       │
│                                                                   │
│                           ↓ Login via                            │
│                                                                   │
│                      React Frontend                              │
└────────────────────────────┬────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    KUBERNETES CLUSTER (3 Nodes)                  │
│                                                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐│
│  │  EC2 Node 1     │  │  EC2 Node 2     │  │  EC2 Node 3     ││
│  │  (t3.medium)    │  │  (t3.medium)    │  │  (t3.medium)    ││
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤│
│  │ 🐳 Containers:  │  │ 🐳 Containers:  │  │ 🐳 Containers:  ││
│  │                 │  │                 │  │                 ││
│  │ API Gateway     │  │ Dispatcher-2    │  │ Dispatcher-3    ││
│  │ Auth Service    │  │ Publisher       │  │ Gossip Agent    ││
│  │ Dispatcher-1 👑 │  │ Subscription    │  │ Frontend        ││
│  │ RabbitMQ        │  │ Redis           │  │ ...             ││
│  └─────────────────┘  └─────────────────┘  └─────────────────┘│
│                                                                   │
│  ↑ Leader Election between 3 Dispatcher replicas ↑             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        AWS SERVICES                              │
│   • DynamoDB (User data, Events, Subscriptions, Popularity)     │
│   • S3 (Event media storage)                                     │
│   • SNS (Email/SMS notifications)                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧪 **Testing Both Concepts**

### **Test 1: User Roles (Different Dashboards)**

**Step 1:** Login as Student
```
http://localhost:3000
Email: alice@student.com
Password: password123

Result: Dashboard WITHOUT "Create Event" button
```

**Step 2:** Logout and Login as Organizer
```
Email: charlie@organizer.com
Password: password123

Result: Dashboard WITH "Create Event" button ⭐
```

**Step 3:** Create an Event (only works as organizer)
```
Click "Create Event"
Fill in event details
Click "Create & Publish"
```

**Step 4:** Login as Student again
```
Check "Notifications" page
See the event notification appear! 🔔
```

---

### **Test 2: Cluster Nodes (Leader Election)**

**Currently (Docker Compose):**
```bash
# Check running containers
docker ps

# You have 1 dispatcher replica
# To test multi-node, you'd scale:
docker-compose up -d --scale notification-dispatcher=3

# Check which is leader
curl http://localhost:5004/election/status
```

**On Kubernetes (if deployed):**
```bash
# Check dispatcher pods (3 replicas)
kubectl get pods -n distributed-events -l app=notification-dispatcher

# Check which is leader
kubectl exec -it dispatcher-1 -- curl localhost:5004/election/status
kubectl exec -it dispatcher-2 -- curl localhost:5004/election/status
kubectl exec -it dispatcher-3 -- curl localhost:5004/election/status

# One will show: "is_leader": true 👑
```

---

## 📝 **Summary**

### **User Roles (Application Level):**
- **3 roles:** Student, Organizer (Publisher), Admin
- **Different permissions:** Only organizers/admins create events
- **Different UI:** Organizers see "Create Event" button
- **Test credentials:** charlie@organizer.com / password123

### **Cluster Nodes (Infrastructure Level):**
- **3 EC2 servers:** Physical machines running containers
- **Multiple replicas:** 3 instances of Notification Dispatcher
- **Leader election:** Bully algorithm between dispatcher replicas
- **Not related to user roles:** Infrastructure vs application layer

### **Key Distinction:**
```
USER ROLES          ≠          CLUSTER NODES
(Who uses system)              (Where system runs)
3 types of users               3 physical servers
alice, charlie, diana          Node-1, Node-2, Node-3
```

---

## 🎓 **For Your Presentation:**

"Our system has **two independent layers**:

1. **Application Layer:** 3 user roles (student, organizer, admin) with different permissions. Organizers publish events; students subscribe and receive notifications.

2. **Infrastructure Layer:** Designed for 3-node Kubernetes cluster where microservices are distributed. Our custom Bully Leader Election algorithm coordinates between 3 Notification Dispatcher replicas for fault tolerance.

These layers are independent - user roles don't determine node assignment. Kubernetes handles container orchestration, while our distributed algorithms handle application-level coordination."

---

**Questions? Ask me!** 🚀

