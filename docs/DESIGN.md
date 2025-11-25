# Design Document: Distributed Job Events Notifier

## 1. Introduction

### 1.1 Purpose

This document describes the detailed design of the Distributed Job Events Notifier system, built as a coursework project for **COEN 317 – Distributed Systems**. The system demonstrates core distributed systems concepts including membership protocols, gossip dissemination, leader election, and distributed coordination.

### 1.2 Scope

The system enables:
- Publishers (organizers, companies) to create and publish events
- Subscribers (students, professionals) to receive notifications via multiple channels
- A robust distributed backend that handles failures, scales horizontally, and maintains consistency

### 1.3 Distributed Systems Requirements

This project explicitly addresses the following requirements:

1. **Membership & Coordination Protocol (MCP)**: Track node health and membership
2. **Gossip Protocol**: Disseminate state across the cluster
3. **Leader Election**: Bully algorithm for coordination tasks
4. **Publisher-Side Filtering**: Optimize network usage
5. **Popularity-Based Routing**: Priority assignment
6. **Heterogeneity**: Multiple technologies and protocols
7. **Openness**: Standard APIs and extensibility
8. **Security**: Authentication and authorization
9. **Failure Handling**: Fault tolerance and recovery
10. **Concurrency**: Simultaneous operations
11. **QoS**: Quality of service guarantees
12. **Scalability**: Horizontal scaling
13. **Transparency**: Location, migration, replication, concurrency, failure

## 2. System Design Goals

### 2.1 Functional Goals

- Allow users to register, login, and manage subscriptions
- Enable organizers to create and publish events
- Deliver notifications through multiple channels (in-app, email, SMS)
- Support topic hierarchies and wildcard subscriptions
- Filter notifications based on user preferences

### 2.2 Non-Functional Goals

- **Availability**: 99.9% uptime
- **Latency**: < 1 second for API requests, < 5 seconds for notification delivery
- **Throughput**: Support 10,000+ users, 1,000+ events
- **Scalability**: Horizontal scaling to handle increased load
- **Fault Tolerance**: Survive single node failures
- **Consistency**: Eventual consistency for gossip, strong consistency for critical data

## 3. Distributed Algorithms Design

### 3.1 Membership & Coordination Protocol (MCP)

#### 3.1.1 Design Rationale

MCP provides a soft-state membership view of the cluster. Unlike Kubernetes' pod discovery (which tells us *what pods exist*), MCP tells us *which pods are healthy and responsive*.

#### 3.1.2 State Machine

```
Node States:
┌────────┐
│  ALIVE │  ◄─── Normal operation, heartbeats received
└───┬────┘
    │ Heartbeat timeout (10s)
    ▼
┌─────────┐
│ SUSPECT │  ◄─── Possible failure, grace period
└───┬─────┘
    │ Additional timeout (5s)
    ▼
┌────────┐
│  DEAD  │  ◄─── Confirmed failure, trigger election
└────────┘
```

#### 3.1.3 Data Structures

```python
class NodeInfo:
    node_id: str          # Unique identifier
    role: str             # "dispatcher", "gossip", etc.
    status: str           # "alive", "suspect", "dead"
    last_seen: float      # Unix timestamp
    host: str             # Hostname
    port: int             # Port number
    load: Dict            # Current load metrics
```

#### 3.1.4 Operations

**JOIN**:
- New node registers with MCP
- MCP adds to membership table
- Gossip agents propagate to cluster

**HEARTBEAT**:
- Nodes send every 5 seconds
- Includes current load metrics
- Resets timeout and transitions from SUSPECT → ALIVE

**LEAVE**:
- Graceful shutdown
- Node sends explicit leave message
- Immediate removal from membership

**FAILURE DETECTION**:
- Background thread checks timeouts every 2 seconds
- ALIVE → SUSPECT after 10s without heartbeat
- SUSPECT → DEAD after additional 5s
- Callbacks notify interested parties (e.g., leader election)

#### 3.1.5 Why MCP is Needed

While Kubernetes tells us about pod lifecycle, MCP provides:
- **Application-level health**: A pod can be "Running" in K8s but hung/slow
- **Custom metrics**: Queue lengths, processing rates
- **Coordination**: Who should be elected leader?
- **Distributed state**: Gossip can disseminate this to all nodes

### 3.2 Gossip Protocol

#### 3.2.1 Algorithm: Push-Pull Epidemic Gossip

```
Every GOSSIP_INTERVAL (5 seconds):
  1. Select FANOUT (3) random peers
  2. For each peer:
     a. PUSH: Send our state to peer
     b. PULL: Receive peer's state
     c. MERGE: Combine states using conflict resolution
```

#### 3.2.2 State Gossiped

```python
class GossipState:
    membership: Dict[node_id -> NodeInfo]
    popularity: Dict[topic -> {count, last_updated}]
    recent_events: List[event_id]
    version: int          # Incremented on each update
    timestamp: float      # When this state was created
```

#### 3.2.3 Conflict Resolution

**Rule**: Most recent wins

```python
def merge_nodes(local_node, remote_node):
    if remote_node.last_seen > local_node.last_seen:
        return remote_node  # Remote is fresher
    else:
        return local_node
```

For popularity:
```python
def merge_popularity(local_pop, remote_pop):
    if remote_pop.last_updated > local_pop.last_updated:
        return remote_pop
    elif remote_pop.last_updated == local_pop.last_updated:
        # Same timestamp: take max count (eventual consistency)
        return max(local_pop.count, remote_pop.count)
    else:
        return local_pop
```

#### 3.2.4 Convergence Analysis

- **Fanout = 3**: Each round, state spreads to 3 peers
- **Round 1**: 1 → 3 nodes
- **Round 2**: 3 → 9 nodes
- **Round 3**: 9 → 27 nodes
- **Expected rounds to full propagation**: O(log N)

For N = 10 nodes, full propagation in ~3-4 rounds = 15-20 seconds

### 3.3 Leader Election (Bully Algorithm)

#### 3.3.1 Why Application-Level Election?

**Important Distinction**:
- **Kubernetes leader election**: Used for K8s control plane (scheduler, controller-manager)
- **Our application leader election**: Used for distributed application tasks

Just as databases (etcd, Cassandra) run their own consensus protocols on K8s, our application runs its own election for application-specific coordination.

#### 3.3.2 Node ID Assignment

Nodes are ordered lexicographically by ID:
```
dispatcher-1 < dispatcher-2 < dispatcher-3
```

Highest ID = Highest priority

#### 3.3.3 Election Algorithm

```
When to start election:
- On startup (if no known leader)
- On leader failure detected (via MCP)

Steps:
1. Node X detects no leader
2. X sends ELECTION to all nodes with ID > X
3. If any node responds:
   - X waits for COORDINATOR message
   - If timeout: restart election
4. If no node responds:
   - X declares itself leader
   - X broadcasts COORDINATOR to all nodes
5. All nodes accept COORDINATOR with highest ID
```

#### 3.3.4 Example Scenario

```
Initial: Dispatcher-1, Dispatcher-2 (LEADER), Dispatcher-3

Event: Dispatcher-2 crashes

Dispatcher-1:
  t=0: Detects leader timeout (no heartbeats)
  t=1: Sends ELECTION to Disp-2, Disp-3
  t=2: Disp-3 responds
  t=3: Waits for COORDINATOR

Dispatcher-3:
  t=2: Receives ELECTION from Disp-1
  t=2: Responds to Disp-1
  t=3: Starts own election
  t=4: Sends ELECTION to Disp-2
  t=5: No response (Disp-2 is down)
  t=6: Declares self LEADER
  t=7: Broadcasts COORDINATOR

Result: Dispatcher-3 is new leader
```

#### 3.3.5 Leader Responsibilities

**Only the leader performs**:
1. **Periodic cleanup**: Delete old notifications/events
2. **Aggregation**: Save popularity metrics to DynamoDB
3. **Global monitoring**: Optional health checks

**All nodes perform**:
- Message consumption from RabbitMQ
- Notification delivery
- Heartbeat sending

### 3.4 Publisher-Side Filtering

#### 3.4.1 Problem Statement

**Naive approach**: Publisher sends N messages (one per subscriber)
- High network overhead
- RabbitMQ queue depth = N
- Each dispatcher processes duplicate filtering

**Our approach**: Publisher sends 1 message with filtered subscriber list
- Low network overhead
- RabbitMQ queue depth = 1
- Dispatcher directly sends to subscribers

#### 3.4.2 Algorithm

```python
def publish_event(event_id):
    # 1. Fetch event
    event = dynamodb.get_item(event_id)
    
    # 2. Fetch ALL subscriptions
    all_subs = subscription_service.get_all()
    
    # 3. Filter subscribers
    matching = []
    for sub in all_subs:
        # Topic match (with wildcards)
        if not matches_topic(event.topic, sub.topic):
            continue
        
        # Location filter
        if sub.filters.locations:
            if event.location not in sub.filters.locations:
                continue
        
        # Level filter
        if sub.filters.levels:
            if event.level not in sub.filters.levels:
                continue
        
        matching.append({
            'user_id': sub.user_id,
            'channels': sub.channels
        })
    
    # 4. Increment popularity
    popularity.increment(event.topic)
    
    # 5. Get priority
    priority = popularity.get_priority(event.topic)
    
    # 6. Build payload
    payload = {
        'event_id': event.event_id,
        'title': event.title,
        'topic': event.topic,
        'subscriber_ids': [m['user_id'] for m in matching],
        'channels': list(set([c for m in matching for c in m['channels']])),
        'priority': priority,
        'timestamp': time.time()
    }
    
    # 7. Publish once to RabbitMQ
    rabbitmq.publish('events.topic', event.topic, payload)
```

#### 3.4.3 Performance Analysis

**Assumptions**:
- 10,000 subscribers
- 1,000 subscriptions per topic (after filtering)
- Event published to topic

**Naive approach**:
- Network: 10,000 messages × 1 KB = 10 MB
- RabbitMQ: 10,000 queue items
- Dispatcher: 10,000 × filter() + 10,000 × deliver()

**Our approach**:
- Network: 1 message × 5 KB = 5 KB  (2000x reduction!)
- RabbitMQ: 1 queue item
- Dispatcher: 1,000 × deliver()

**Winner**: Our approach by 1000x-2000x

### 3.5 Popularity-Based Routing

#### 3.5.1 Design

Track topic access counts and assign priority:
```
Priority Thresholds:
- count < 10:     LOW priority
- count < 50:     MEDIUM priority
- count >= 100:   HIGH priority
```

#### 3.5.2 Implementation

**Increment**:
```python
def increment_topic(topic: str):
    # Atomic increment in DynamoDB
    dynamodb.update_item(
        Key={'topic': topic},
        UpdateExpression='ADD count :inc SET last_updated = :ts',
        ExpressionAttributeValues={
            ':inc': 1,
            ':ts': time.time()
        }
    )
```

**Get Priority**:
```python
def get_priority(topic: str) -> str:
    count = get_count(topic)
    if count >= 100:
        return 'high'
    elif count >= 50:
        return 'medium'
    else:
        return 'low'
```

#### 3.5.3 Priority Handling

**RabbitMQ**:
- Messages published with priority (0-9)
- Consumers process high-priority first

**Dispatcher**:
- Optional: maintain separate in-memory queues per priority
- Process high → medium → low

---

### 3.6 Lamport Logical Clocks (Distributed Timestamps)

#### 3.6.1 Design Rationale

**Problem**: In a distributed system without synchronized physical clocks, how do we determine the causal order of events?

**Solution**: Lamport logical clocks provide a mechanism to order events in a distributed system based on causality, not physical time.

**Why Required for COEN 317**:
- Satisfies "Timestamps" requirement (#7) from the distributed algorithms list
- Essential for maintaining causal consistency in event notifications
- Enables proper ordering of notifications when displayed to users
- Helps debug distributed system behavior

#### 3.6.2 Algorithm

**Lamport Clock Rules**:
1. Each node maintains a local counter (initially 0)
2. On internal event: increment counter
3. On send: increment counter, attach to message
4. On receive: counter = max(local, received) + 1

**Properties**:
- If event A causally precedes event B, then timestamp(A) < timestamp(B)
- Concurrent events may have same timestamp (resolved by node ID)
- Provides partial ordering (causal order), not total ordering

#### 3.6.3 Implementation

```python
class LamportClock:
    def __init__(self, node_id: str):
        self.node_id = node_id
        self._counter = 0
        self._lock = threading.Lock()
    
    def send_event(self) -> dict:
        """Called when publishing an event"""
        with self._lock:
            self._counter += 1
            return {
                "clock": self._counter,
                "node_id": self.node_id
            }
    
    def receive_event(self, received_timestamp: dict) -> int:
        """Called when receiving an event"""
        with self._lock:
            received_clock = received_timestamp.get("clock", 0)
            self._counter = max(self._counter, received_clock) + 1
            return self._counter
```

#### 3.6.4 Usage in System

**1. Publisher Service (Send)**:
```python
# When publishing event to RabbitMQ
node_id = os.getenv('HOSTNAME', 'publisher-service')
clock = get_lamport_clock(node_id)

# Add timestamp to event
notification_payload['lamport_timestamp'] = clock.send_event()

# Publish to RabbitMQ
rabbitmq.publish(notification_payload)
```

**2. Notification Dispatcher (Receive)**:
```python
# When consuming from RabbitMQ
message = rabbitmq.consume()

# Update local clock
clock = get_lamport_clock(NODE_ID)
if 'lamport_timestamp' in message:
    local_time = clock.receive_event(message['lamport_timestamp'])
    message['processed_at_lamport'] = local_time

# Store notification
notification['lamport_timestamp'] = message['lamport_timestamp']
```

**3. Notification Ordering (Display)**:
```python
# When user fetches notifications
def get_user_notifications(user_id: str):
    notifications = fetch_notifications(user_id)
    
    # Order by Lamport timestamp (causal order)
    ordered = sorted(
        notifications,
        key=lambda n: (
            n['lamport_timestamp']['clock'],
            n['lamport_timestamp']['node_id']
        )
    )
    return ordered
```

#### 3.6.5 Example Scenario

```
Scenario: Two publishers simultaneously publish events

Publisher A (node-a):
  t=0: clock=0
  t=1: Publish Event E1 → clock=1, timestamp=(1, node-a)

Publisher B (node-b):
  t=0: clock=0
  t=1: Publish Event E2 → clock=1, timestamp=(1, node-b)

Dispatcher (node-d):
  t=0: clock=0
  t=2: Receives E1 → clock = max(0, 1) + 1 = 2
  t=3: Receives E2 → clock = max(2, 1) + 1 = 3
  t=4: Processes later events...

User Views Notifications:
  - System shows: E1 (1, node-a), E2 (1, node-b)
  - Ordered by: clock value, then node_id
  - E1 appears before E2 (deterministic ordering)
```

#### 3.6.6 Causal Ordering Example

```
Scenario: Publisher A creates event, Publisher B reacts to it

Publisher A:
  t=1: Publishes "Hackathon Announced" → TS=(1, node-a)

Publisher B:
  t=2: Receives "Hackathon Announced" → clock = max(0, 1) + 1 = 2
  t=3: Publishes "Registration Open" → TS=(3, node-b)

Dispatcher:
  Receives both events
  Orders them: (1, node-a) < (3, node-b)
  
User sees correct order:
  1. "Hackathon Announced" (happened first)
  2. "Registration Open" (happened after)
```

#### 3.6.7 Comparison with Physical Timestamps

| Feature | Lamport Clock | Physical Clock |
|---------|--------------|----------------|
| **Synchronization** | Not required | Required (NTP) |
| **Causal Order** | Guaranteed | Not guaranteed |
| **Total Order** | Partial (+ node ID) | Total |
| **Clock Drift** | N/A | Problematic |
| **Implementation** | Simple counter | System clock |
| **Best For** | Distributed causality | Absolute time |

**Why We Use Lamport for This System**:
- ✅ No clock synchronization needed
- ✅ Guarantees causal consistency
- ✅ Lightweight (just an integer)
- ✅ Works across different time zones
- ✅ Required algorithm for COEN 317

#### 3.6.8 Limitations and Trade-offs

**Limitations**:
1. **Concurrent events**: Cannot determine absolute order
   - Events with same timestamp are concurrent
   - Use node ID for deterministic tie-breaking

2. **Storage overhead**: Each event carries timestamp
   - Solution: Minimal (2 integers: clock + node_id)

3. **Not human-readable**: Cannot convert to wall-clock time
   - Solution: Store both Lamport timestamp (ordering) and physical timestamp (display)

**Trade-offs**:
- **Pro**: Causally consistent ordering without clock sync
- **Pro**: Simple to implement and understand
- **Con**: Doesn't provide absolute time information
- **Con**: Requires all events to include timestamps

#### 3.6.9 Testing

**Unit Tests** (`backend/tests/test_timestamps.py`):
1. Clock initialization
2. Send event increments clock
3. Receive event updates clock correctly
4. Thread-safety (concurrent access)
5. Event ordering
6. Causal scenario simulation

**Integration Tests**:
1. Publisher sends timestamped events
2. Dispatcher receives and orders events
3. User API returns causally ordered notifications
4. Multiple publishers with concurrent events

---

## 4. Data Consistency Model

### 4.1 Strong Consistency

**Where**: DynamoDB for critical data
- User credentials
- Event details
- Subscription records

**Why**: Cannot tolerate inconsistency

### 4.2 Eventual Consistency

**Where**: Gossip protocol for soft state
- Membership information
- Popularity metrics
- Recent events list

**Why**: High availability > strict consistency

### 4.3 At-Least-Once Delivery

**Where**: RabbitMQ notifications
- Message persistence
- Manual acknowledgments
- Redelivery on failure

**Why**: Better to deliver twice than lose a notification

## 5. Fault Tolerance

### 5.1 Failure Scenarios

| Failure               | Detection           | Recovery               |
|-----------------------|---------------------|------------------------|
| Node crash            | MCP timeout         | K8s restarts pod       |
| Network partition     | Gossip divergence   | Heal on reconnect      |
| Leader failure        | Heartbeat timeout   | Bully election         |
| RabbitMQ down         | Connection error    | Retry with backoff     |
| DynamoDB throttle     | ClientError         | Exponential backoff    |

### 5.2 Split-Brain Prevention

**Problem**: Network partition causes multiple leaders

**Solution**: 
- Bully algorithm is deterministic (highest ID wins)
- When partition heals, nodes compare IDs
- Lower-ID "leaders" step down immediately

### 5.3 Data Loss Prevention

- **RabbitMQ**: Durable queues + persistent messages
- **DynamoDB**: Automatic replication across 3 AZs
- **S3**: 99.999999999% durability

## 6. Scalability Analysis

### 6.1 Bottlenecks

1. **Publisher Service**: Must query all subscriptions
   - **Solution**: Cache subscriptions, refresh every 30s
   
2. **RabbitMQ**: Single point of congestion
   - **Solution**: RabbitMQ clustering (3 nodes)
   
3. **DynamoDB**: Throttling on high traffic
   - **Solution**: Auto-scaling, eventual consistency where possible

### 6.2 Horizontal Scaling

All services scale horizontally except:
- **RabbitMQ**: Cluster with replication
- **Gossip Agents**: Fixed at 3-5 nodes (typical for gossip)

## 7. Security Design

### 7.1 Threat Model

**Threats**:
- Unauthorized access to events
- Data leakage (user emails, phone numbers)
- Message tampering
- Denial of service

**Mitigations**:
- JWT authentication (prevents unauthorized access)
- HTTPS/TLS (prevents eavesdropping)
- RBAC (role-based access control)
- Rate limiting (prevents DoS)
- AWS IAM (service-level security)

### 7.2 JWT Structure

```json
{
  "user_id": "U123",
  "email": "john@example.com",
  "role": "student",
  "exp": 1734567890,
  "iat": 1734481490
}
```

Signed with HS256 and secret key. Verified by API Gateway on each request.

## 8. Performance Optimization

### 8.1 Caching Strategy

```
Component          | Cache            | TTL
------------------------------------------------
Subscriptions      | In-memory dict   | 30s
Popularity         | In-memory dict   | 60s
Topics list        | In-memory list   | 300s
```

### 8.2 Database Optimization

- **GSI on email**: Fast user lookup
- **GSI on topic**: Fast subscription queries
- **Batch operations**: Reduce round-trips

### 8.3 Network Optimization

- **Keep-Alive**: Reuse HTTP connections
- **Compression**: Gzip response bodies
- **CDN**: Serve frontend via CloudFront (optional)

## 9. Testing Strategy

### 9.1 Unit Tests

- Test each distributed algorithm in isolation
- Mock external dependencies (DynamoDB, RabbitMQ)

### 9.2 Integration Tests

- Test service-to-service communication
- Use Localstack for AWS services

### 9.3 Distributed Systems Tests

**Failure tests**:
- Kill leader, verify new election
- Partition network, verify gossip recovery
- Crash dispatcher, verify message redelivery

**Performance tests**:
- Publish 1000 events/minute
- 10,000 concurrent users
- Measure latency p50, p95, p99

## 10. Trade-Offs & Design Decisions

### Decision 1: Publisher-Side vs Consumer-Side Filtering

**Choice**: Publisher-side

**Rationale**: 
- Reduces network traffic 1000x
- Simplifies dispatcher logic
- Slightly increases publisher complexity (acceptable)

### Decision 2: Bully vs Raft for Leader Election

**Choice**: Bully

**Rationale**:
- Simpler implementation
- Suitable for small clusters (< 10 nodes)
- Raft would be better for larger, critical systems

### Decision 3: Push-Pull vs Pure Push Gossip

**Choice**: Push-Pull

**Rationale**:
- Faster convergence (2x speedup)
- Better resilience to message loss
- Minimal overhead (responses already needed)

### Decision 4: DynamoDB vs Self-Hosted DB

**Choice**: DynamoDB

**Rationale**:
- Managed service (less operational overhead)
- Auto-scaling
- Multi-AZ replication built-in
- Project requirement

## 11. Future Improvements

1. **WebSockets**: Real-time push instead of polling
2. **Raft Consensus**: Replace Bully for production robustness
3. **Observability**: Prometheus + Grafana dashboards
4. **Chaos Engineering**: Automated failure injection tests
5. **Multi-Region**: Geographic distribution for lower latency

## 12. Conclusion

This design demonstrates a production-quality distributed system implementing key concepts from COEN 317:
- Membership protocols (MCP)
- Epidemic dissemination (Gossip)
- Distributed coordination (Leader Election)
- System optimizations (Publisher-Side Filtering, Popularity Routing)
- Cloud-native architecture (Kubernetes, AWS)

The system is scalable, fault-tolerant, and ready for real-world deployment.

