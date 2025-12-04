# System Architecture

## Overview

The Distributed Job Events Notifier is built as a microservices-based, event-driven distributed system demonstrating key distributed systems concepts from COEN 317.

## Architecture Diagram

```
                         ┌──────────────────┐
                         │  Web Clients     │
                         │  (React SPA)     │
                         └────────┬─────────┘
                                  │
                                  │ HTTPS
                                  ▼
                         ┌────────────────────┐
                         │  Load Balancer     │
                         │  (AWS ALB/ELB)     │
                         └──────┬─────────────┘
                                │
                ┌───────────────┴────────────────┐
                │                                │
                ▼                                ▼
        ┌──────────────┐              ┌──────────────┐
        │ API Gateway  │              │ API Gateway  │
        │   Instance 1 │              │   Instance 2 │
        └──────┬───────┘              └──────┬───────┘
               │                             │
               └──────────┬──────────────────┘
                          │
         ┌────────────────┼────────────────┐
         │                │                │
         ▼                ▼                ▼
    ┌────────┐     ┌────────────┐   ┌──────────┐
    │  Auth  │     │Subscription│   │Publisher │
    │Service │     │  Service   │   │ Service  │
    └───┬────┘     └─────┬──────┘   └────┬─────┘
        │                │               │
        └────────┬───────┴───────┬───────┘
                 │               │
                 ▼               ▼
           ┌──────────────────────────┐
           │     AWS DynamoDB         │
           │  ┌─────────────────────┐ │
           │  │ Users               │ │
           │  │ Subscriptions       │ │
           │  │ Events              │ │
           │  │ TopicPopularity     │ │
           │  └─────────────────────┘ │
           └──────────────────────────┘
                         │
                         │
          ┌──────────────┴──────────────┐
          │                             │
          ▼                             ▼
    ┌────────────────┐          ┌─────────────┐
    │   AWS S3       │          │   AWS SNS   │
    │ (Event Media)  │          │(Email/SMS)  │
    └────────────────┘          └─────────────┘
                         
                         
        ┌─────────────────────────────────────┐
        │         RabbitMQ Cluster            │
        │  Topic Exchange: "events.topic"     │
        │                                     │
        │  Routing Keys:                      │
        │  - hackathon.aiml                   │
        │  - hackathon.web                    │
        │  - jobs.internship                  │
        │  - ...                              │
        └───────────┬─────────────────────────┘
                    │
        ┌───────────┴────────────┬─────────────┐
        │                        │             │
        ▼                        ▼             ▼
┌───────────────┐      ┌───────────────┐  ┌─────────────┐
│ Notification  │      │ Notification  │  │Notification │
│ Dispatcher 1  │◄────►│ Dispatcher 2  │◄►│Dispatcher 3 │
│               │      │               │  │             │
│ (Follower)    │      │   (LEADER)    │  │ (Follower)  │
└───────┬───────┘      └───────┬───────┘  └──────┬──────┘
        │                      │                  │
        └──────────────┬───────┴──────────────────┘
                       │
                       │ Heartbeats & State Updates
                       ▼
              ┌──────────────────┐
              │  Gossip Agents   │
              │  (3 instances)   │
              │                  │
              │  • MCP           │
              │  • Gossip        │
              │  • State Sync    │
              └──────────────────┘
```

## Component Details

### 1. API Gateway

**Purpose**: Single entry point for all client requests

**Responsibilities**:
- JWT token validation
- Request routing to internal services
- Rate limiting (optional)
- CORS handling

**Technology**: Flask, Python
**Scaling**: Horizontal (stateless)
**Port**: 5000

### 2. Auth Service

**Purpose**: User authentication and authorization

**Responsibilities**:
- User registration
- Login with JWT generation
- Token verification
- Password hashing (bcrypt)

**Data Store**: DynamoDB `Users` table
**Technology**: Flask, boto3
**Scaling**: Horizontal (stateless)
**Port**: 5001

### 3. Subscription Service

**Purpose**: Manage user topic subscriptions

**Responsibilities**:
- CRUD operations for subscriptions
- Topic listing and validation
- Channel management (app, email, SMS)
- Filter preferences (location, level)

**Data Store**: DynamoDB `Subscriptions` table
**Technology**: Flask, boto3
**Scaling**: Horizontal (stateless)
**Port**: 5002

### 4. Publisher Service

**Purpose**: Event management and publishing

**Responsibilities**:
- Event CRUD operations
- **Publisher-side filtering** (key optimization)
- Topic popularity tracking
- RabbitMQ message publishing
- S3 integration for media

**Data Store**: 
- DynamoDB `Events` table
- AWS S3 for media

**Technology**: Flask, boto3, pika (RabbitMQ client)
**Scaling**: Horizontal (stateless)
**Port**: 5003

**Key Algorithm - Publisher-Side Filtering**:

```python
def publish_event(event_id):
    1. Fetch event from DynamoDB
    2. Fetch ALL subscriptions from Subscription Service
    3. Filter subscriptions:
       - Match topic (with wildcard support)
       - Apply location filters
       - Apply level filters
    4. Build notification payload with filtered subscribers
    5. Increment topic popularity
    6. Get priority based on popularity
    7. Publish single message to RabbitMQ
```

This approach reduces:
- Network traffic (one message vs N messages)
- RabbitMQ queue overhead
- Dispatcher processing time

### 5. Notification Dispatcher

**Purpose**: Consume notifications and dispatch to users

**Responsibilities**:
- RabbitMQ message consumption
- In-app notification storage
- Email/SMS via AWS SNS
- **Leader election** (Bully algorithm)
- Leader-only tasks:
  - Periodic cleanup
  - Popularity aggregation to DynamoDB

**Technology**: Flask, boto3, pika
**Scaling**: Horizontal with leader election
**Port**: 5004

**Distributed Systems Features**:
- Participates in MCP (heartbeats)
- Runs Bully leader election
- Only leader performs certain tasks
- Automatic failover on leader failure

### 6. Gossip Agent

**Purpose**: State dissemination and membership tracking

**Responsibilities**:
- Implement MCP (Membership & Coordination Protocol)
- Run gossip protocol (push-pull)
- Track membership state
- Disseminate popularity data
- Failure detection

**Technology**: Flask
**Scaling**: Fixed 3 instances (typical for gossip)
**Port**: 5006

## Data Models

### DynamoDB Tables

#### Users
```
Primary Key: user_id (String)
GSI: EmailIndex on email
Attributes:
- user_id: String
- email: String
- name: String
- password_hash: String
- role: String (student, organizer, admin)
- phone: String
- created_at: Number (Unix timestamp)
- updated_at: Number
```

#### Subscriptions
```
Primary Key: user_id (Hash), topic (Range)
GSI: TopicIndex on topic
Attributes:
- user_id: String
- topic: String
- channels: List (app, email, sms)
- filters: Map (locations, levels)
- created_at: Number
- updated_at: Number
```

#### Events
```
Primary Key: event_id (String)
Attributes:
- event_id: String
- title: String
- description: String
- topic: String
- start_time: Number
- end_time: Number
- location: String
- level: String
- organizer_id: String
- media_url: String (S3 URL)
- popularity_score: Number
- status: String (draft, published)
- created_at: Number
- updated_at: Number
```

#### TopicPopularity
```
Primary Key: topic (String)
Attributes:
- topic: String
- count: Number
- last_updated: Number
```

## Message Flows

### Flow 1: User Registration

```
Client → API Gateway → Auth Service → DynamoDB (Users)
                                    ← 
       ← ← JWT Token ← ←
```

### Flow 2: Create Subscription

```
Client → API Gateway → Subscription Service → DynamoDB (Subscriptions)
       (with JWT)                           ←
                    ← Success ← ←
```

### Flow 3: Publish Event (Publisher-Side Filtering)

```
Organizer → API Gateway → Publisher Service
                          │
                          ├─► DynamoDB (Events) [Fetch event]
                          │
                          ├─► Subscription Service [Get all subscriptions]
                          │
                          ├─► Filter Subscribers (in-memory)
                          │   - Match topic
                          │   - Apply filters
                          │
                          ├─► Popularity Library
                          │   - Increment count
                          │   - Get priority
                          │
                          └─► RabbitMQ
                              - Single message
                              - Filtered subscriber IDs
                              - Priority set
                              
RabbitMQ → Notification Dispatcher
           │
           ├─► Process each subscriber
           │   - In-app: Store in memory
           │   - Email: AWS SNS
           │   - SMS: AWS SNS
           │
           └─► ACK to RabbitMQ
```

### Flow 4: Leader Election (Bully Algorithm)

```
Scenario: Dispatcher-2 (leader) fails

Dispatcher-1 detects leader timeout:
  1. Send ELECTION to higher-ID nodes (Disp-2, Disp-3)
  2. Wait for responses
  
Dispatcher-3 responds:
  1. Reply to Dispatcher-1
  2. Start own election
  3. Send ELECTION to Disp-2
  4. No response from Disp-2
  5. Declare self as leader
  6. Broadcast COORDINATOR to all

All nodes accept Dispatcher-3 as new leader
```

### Flow 5: Gossip Round

```
Every 5 seconds:

Gossip Agent 1:
  1. Select 3 random peers (Agents 2, 3, X)
  2. Build state snapshot:
     - Membership (from MCP)
     - Popularity data
     - Recent event IDs
  3. Send to each peer (POST /gossip/exchange)
  4. Receive peer's state in response
  5. Merge:
     - Use timestamps for conflict resolution
     - Update local state with fresher data
```

## Distributed Systems Properties

### Scalability

- **Horizontal Scaling**: All services are stateless (except RabbitMQ)
- **Load Balancing**: Kubernetes services distribute requests
- **Auto-scaling**: HPA scales based on CPU/memory

### Fault Tolerance

- **Leader Election**: Automatic failover for critical tasks
- **Gossip**: State recovery even if nodes fail
- **RabbitMQ**: Message persistence and redelivery
- **Kubernetes**: Health checks and pod restarts

### Consistency

- **Eventual Consistency**: Gossip protocol
- **Strong Consistency**: DynamoDB for critical data
- **At-Least-Once Delivery**: RabbitMQ with manual ACKs

### Performance Optimizations

1. **Publisher-Side Filtering**: Reduces network and processing overhead
2. **Priority Queues**: High-priority topics processed first
3. **Caching**: In-memory caches for popular data
4. **Connection Pooling**: Reuse database connections

## Network Communication

### Inter-Service Communication

- **Protocol**: HTTP/REST over TCP
- **Format**: JSON
- **Discovery**: Kubernetes DNS (service-name.namespace.svc.cluster.local)
- **Security**: Internal cluster network (no external exposure)

### Message Queue

- **Protocol**: AMQP
- **Pattern**: Topic-based pub/sub
- **Exchange**: `events.topic` (topic exchange)
- **Routing**: Hierarchical topics (e.g., `hackathon.aiml`)
- **Durability**: Persistent messages and queues

### Client Communication

- **Protocol**: HTTPS
- **Auth**: JWT Bearer tokens
- **Format**: JSON REST API

## Security Architecture

### Authentication Flow

```
1. User submits credentials
2. Auth Service validates against DynamoDB
3. Generate JWT with:
   - user_id
   - email
   - role
   - expiration (24 hours)
4. Client stores token
5. Token included in Authorization header
6. API Gateway validates JWT before routing
```

### Authorization

- **Role-Based Access Control (RBAC)**:
  - `student`: Subscribe, view events, get notifications
  - `organizer`: Create/update/publish events
  - `admin`: All permissions

### AWS Security

- **IAM Roles**: Service-level permissions via IRSA
- **Secrets Manager**: Sensitive configuration
- **VPC**: Network isolation
- **Security Groups**: Firewall rules

## Monitoring & Observability

### Health Checks

Each service exposes `/health` endpoint:
- Kubernetes liveness probes
- Kubernetes readiness probes
- Load balancer health checks

### Metrics (Recommended)

- Prometheus for metrics collection
- Grafana for visualization
- Key metrics:
  - Request rate
  - Error rate
  - Latency (p50, p95, p99)
  - Queue depth
  - Leader election events

### Logging

- Centralized logging via CloudWatch
- Structured JSON logs
- Log levels: DEBUG, INFO, WARN, ERROR

## Deployment Topology

### Development

- Docker Compose
- Single machine
- Minimal resources

### Production (AWS EKS)

- Kubernetes cluster with 3+ nodes
- Multi-AZ deployment
- Auto-scaling enabled
- Load balancers for external access

## Capacity Planning

### Estimated Resource Requirements

```
Service               | Replicas | CPU/Pod | Memory/Pod
--------------------------------------------------
API Gateway           | 2-10     | 200m    | 256Mi
Auth Service          | 2-5      | 200m    | 256Mi
Subscription Service  | 2-5      | 200m    | 256Mi
Publisher Service     | 2-5      | 250m    | 512Mi
Notification Dispatch | 3-10     | 250m    | 512Mi
Gossip Agent          | 3        | 200m    | 256Mi
RabbitMQ              | 1-3      | 500m    | 1Gi
Frontend              | 2-5      | 100m    | 128Mi
```

### DynamoDB Capacity

- Start with 5 RCU / 5 WCU per table
- Enable auto-scaling based on usage
- Monitor throttling and adjust

## Future Enhancements

1. **WebSockets**: Real-time push notifications
2. **Caching Layer**: Redis for session/data caching
3. **Service Mesh**: Istio for advanced traffic management
4. **Event Sourcing**: Audit trail and replay capability
5. **GraphQL**: Flexible API queries
6. **Multi-Region**: Global distribution



