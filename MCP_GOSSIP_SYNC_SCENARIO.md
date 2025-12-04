# Scenario 3: Gossip Protocol State Synchronization - Demo Guide

This guide demonstrates how the Gossip Protocol maintains consistent distributed state across all gossip agent nodes through periodic state exchanges, achieving eventual consistency.

---

## Scenario Requirements

**What We're Demonstrating:**
- The Gossip Protocol maintains consistent distributed state across all nodes through periodic state exchanges
- Achieving eventual consistency

**System Setup:**
- Each gossip agent maintaining a state repository consisting of:
  - Registered notification dispatcher nodes
  - Popularity stats
  - Recent events
- Three gossip agents participating in gossip exchanges
- Gossip interval configured to 5 seconds
- Push-pull gossip model for bidirectional state exchange

**Expected Behavior:**
- Gossip agent maintains complete membership information for all nodes
- All nodes have identical views of cluster membership
- State updates propagate through periodic gossip rounds
- Timestamps are recent (within gossip interval)
- No stale or missing data in synchronized state

---

## Prerequisites

1. **Start all services:**
   ```bash
   cd deployment/docker
   docker-compose up -d
   ```

2. **Wait 30 seconds** for all services to initialize

3. **Verify services are running:**
   ```bash
   docker ps | grep -E "gossip-agent|notification-dispatcher"
   ```
   
   Should show:
   - gossip-agent-1 (port 5006)
   - gossip-agent-2 (port 5007)
   - gossip-agent-3 (port 5008)
   - notification-dispatcher-1 (port 5004)
   - notification-dispatcher-2 (port 5014)
   - notification-dispatcher-3 (port 5024)

---

## Terminal Setup (6 Terminals)

Open 6 terminals side-by-side:

- **Terminal 1**: API calls (checking gossip agent states)
- **Terminal 2**: Gossip Agent-1 logs
- **Terminal 3**: Gossip Agent-2 logs
- **Terminal 4**: Gossip Agent-3 logs
- **Terminal 5**: Dispatcher-1 logs (showing registration)
- **Terminal 6**: Dispatcher-2 logs (showing registration)

---

## STEP 1: Verify All Services Are Running

### Terminal 1 - Check Services

```bash
docker ps | grep -E "gossip-agent|notification-dispatcher"
```

**Expected Output:**
```
CONTAINER ID   IMAGE                    STATUS         PORTS                    NAMES
abc123def456   ...gossip-agent           Up 2 minutes   0.0.0.0:5006->5006/tcp   gossip-agent-1
def456ghi789   ...gossip-agent           Up 2 minutes   0.0.0.0:5007->5007/tcp   gossip-agent-2
ghi789jkl012   ...gossip-agent           Up 2 minutes   0.0.0.0:5008->5008/tcp   gossip-agent-3
jkl012mno345   ...notification-dispatcher Up 2 minutes 0.0.0.0:5004->5004/tcp   notification-dispatcher-1
mno345pqr678   ...notification-dispatcher Up 2 minutes 0.0.0.0:5014->5014/tcp   notification-dispatcher-2
pqr678stu901   ...notification-dispatcher Up 2 minutes 0.0.0.0:5024->5024/tcp   notification-dispatcher-3
```

**Point out:**
- ✅ Three gossip agents running (ports 5006, 5007, 5008)
- ✅ Three dispatcher nodes running (ports 5004, 5014, 5024)

---

## STEP 2: Monitor Gossip Agent Logs

### Terminal 2 - Gossip Agent-1 Logs

```bash
# Windows PowerShell
docker logs gossip-agent-1 -f --tail 0

# Linux/Mac
docker logs gossip-agent-1 -f --tail 0
```

### Terminal 3 - Gossip Agent-2 Logs

```bash
# Windows PowerShell
docker logs gossip-agent-2 -f --tail 0

# Linux/Mac
docker logs gossip-agent-2 -f --tail 0
```

### Terminal 4 - Gossip Agent-3 Logs

```bash
# Windows PowerShell
docker logs gossip-agent-3 -f --tail 0

# Linux/Mac
docker logs gossip-agent-3 -f --tail 0
```

**Expected Output (all three terminals):**

**Terminal 2 (Gossip Agent-1):**
```
[Gossip Agent] Starting node gossip-1 on port 5006
[Gossip Agent] Initial peers: ['http://gossip-agent-2:5007', 'http://gossip-agent-3:5008']
[Gossip Agent] Started MCP monitoring
[Gossip Agent] Started gossip protocol
[Gossip Agent] Started sync threads
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-1
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-2
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-3
[Gossip Agent] [GOSSIP] Gossiping with http://gossip-agent-2:5007
[Gossip Agent] [GOSSIP] Gossiping with http://gossip-agent-3:5008
```

**Terminal 3 (Gossip Agent-2):**
```
[Gossip Agent] Starting node gossip-2 on port 5007
[Gossip Agent] Initial peers: ['http://gossip-agent-1:5006', 'http://gossip-agent-3:5008']
[Gossip Agent] Started MCP monitoring
[Gossip Agent] Started gossip protocol
[Gossip Agent] Started sync threads
[Gossip Agent] [GOSSIP] Received gossip exchange from gossip-1
[Gossip Agent] [GOSSIP] Gossiping with http://gossip-agent-1:5006
[Gossip Agent] [GOSSIP] Gossiping with http://gossip-agent-3:5008
```

**Terminal 4 (Gossip Agent-3):**
```
[Gossip Agent] Starting node gossip-3 on port 5008
[Gossip Agent] Initial peers: ['http://gossip-agent-1:5006', 'http://gossip-agent-2:5007']
[Gossip Agent] Started MCP monitoring
[Gossip Agent] Started gossip protocol
[Gossip Agent] Started sync threads
[Gossip Agent] [GOSSIP] Received gossip exchange from gossip-1
[Gossip Agent] [GOSSIP] Received gossip exchange from gossip-2
[Gossip Agent] [GOSSIP] Gossiping with http://gossip-agent-1:5006
[Gossip Agent] [GOSSIP] Gossiping with http://gossip-agent-2:5007
```

**Point out:**
- ✅ All three gossip agents started
- ✅ Each has the other two as peers
- ✅ Gossip protocol started on all three
- ✅ Gossip exchanges happening every 5 seconds

---

## STEP 3: Check Initial State of Each Gossip Agent

### Terminal 1 - Check Gossip Agent-1 State

```bash
curl http://localhost:5006/gossip/state | python -m json.tool
```

**Expected Output:**
```json
{
  "membership": {
    "dispatcher-1": {
      "node_id": "dispatcher-1",
      "role": "dispatcher",
      "status": "alive",
      "last_seen": 1701432225.123,
      ...
    },
    "dispatcher-2": {
      "node_id": "dispatcher-2",
      "role": "dispatcher",
      "status": "alive",
      "last_seen": 1701432226.456,
      ...
    },
    "dispatcher-3": {
      "node_id": "dispatcher-3",
      "role": "dispatcher",
      "status": "alive",
      "last_seen": 1701432227.789,
      ...
    }
  },
  "popularity": {
    "hackathon.aiml": {
      "count": 10,
      "last_updated": 1701432200
    },
    ...
  },
  "recent_events": [
    "E1234567890",
    "E1234567891",
    ...
  ],
  "version": 5,
  "timestamp": 1701432230.123
}
```

### Terminal 1 - Check Gossip Agent-2 State

```bash
curl http://localhost:5007/gossip/state | python -m json.tool
```

**Expected Output (initially may be empty or partial):**
```json
{
  "membership": {},
  "popularity": {},
  "recent_events": [],
  "version": 0,
  "timestamp": 1701432200.0
}
```

**Point out:**
- ⚠️ Gossip Agent-2 may not have membership data yet (if dispatchers only register with Agent-1)
- ✅ This is expected - state will synchronize through gossip

### Terminal 1 - Check Gossip Agent-3 State

```bash
curl http://localhost:5008/gossip/state | python -m json.tool
```

**Expected Output (initially may be empty or partial):**
```json
{
  "membership": {},
  "popularity": {},
  "recent_events": [],
  "version": 0,
  "timestamp": 1701432200.0
}
```

---

## STEP 4: Wait for Gossip Synchronization (30 seconds)

**Point out:**
- Gossip protocol runs every 5 seconds
- State synchronization takes a few gossip rounds
- Wait 30 seconds (6 gossip rounds) for state to propagate

**During this time, watch Terminal 2, 3, 4 for gossip exchange messages:**

**Terminal 2 (Gossip Agent-1):**
```
[Gossip Agent] [GOSSIP] Gossiping with http://gossip-agent-2:5007
[Gossip Agent] Received gossip exchange: {'membership_merged': 3, 'popularity_merged': 5}
[Gossip Agent] [GOSSIP] Gossiping with http://gossip-agent-3:5008
[Gossip Agent] Received gossip exchange: {'membership_merged': 3, 'popularity_merged': 5}
```

**Terminal 3 (Gossip Agent-2):**
```
[Gossip Agent] [GOSSIP] Received gossip exchange from gossip-1
[Gossip Agent] Received gossip exchange: {'membership_merged': 3, 'popularity_merged': 5}
[Gossip Agent] [GOSSIP] Gossiping with http://gossip-agent-3:5008
```

**Terminal 4 (Gossip Agent-3):**
```
[Gossip Agent] [GOSSIP] Received gossip exchange from gossip-1
[Gossip Agent] [GOSSIP] Received gossip exchange from gossip-2
[Gossip Agent] Received gossip exchange: {'membership_merged': 3, 'popularity_merged': 5}
```

**Point out:**
- ✅ Gossip exchanges happening every 5 seconds
- ✅ State being merged (membership_merged, popularity_merged)
- ✅ All three agents participating in gossip

---

## STEP 5: Verify Synchronized State (After 30 seconds)

### Terminal 1 - Check All Three Gossip Agents

```bash
echo "=== Gossip Agent-1 State ==="
curl -s http://localhost:5006/gossip/state | python -m json.tool | head -30
echo ""
echo "=== Gossip Agent-2 State ==="
curl -s http://localhost:5007/gossip/state | python -m json.tool | head -30
echo ""
echo "=== Gossip Agent-3 State ==="
curl -s http://localhost:5008/gossip/state | python -m json.tool | head -30
```

**Expected Output (All three should show similar membership):**

**Gossip Agent-1:**
```json
{
  "membership": {
    "dispatcher-1": {
      "node_id": "dispatcher-1",
      "status": "alive",
      "last_seen": 1701432300.123
    },
    "dispatcher-2": {
      "node_id": "dispatcher-2",
      "status": "alive",
      "last_seen": 1701432300.456
    },
    "dispatcher-3": {
      "node_id": "dispatcher-3",
      "status": "alive",
      "last_seen": 1701432300.789
    }
  },
  "version": 12,
  "timestamp": 1701432305.123
}
```

**Gossip Agent-2:**
```json
{
  "membership": {
    "dispatcher-1": {
      "node_id": "dispatcher-1",
      "status": "alive",
      "last_seen": 1701432300.123
    },
    "dispatcher-2": {
      "node_id": "dispatcher-2",
      "status": "alive",
      "last_seen": 1701432300.456
    },
    "dispatcher-3": {
      "node_id": "dispatcher-3",
      "status": "alive",
      "last_seen": 1701432300.789
    }
  },
  "version": 10,
  "timestamp": 1701432303.456
}
```

**Gossip Agent-3:**
```json
{
  "membership": {
    "dispatcher-1": {
      "node_id": "dispatcher-1",
      "status": "alive",
      "last_seen": 1701432300.123
    },
    "dispatcher-2": {
      "node_id": "dispatcher-2",
      "status": "alive",
      "last_seen": 1701432300.456
    },
    "dispatcher-3": {
      "node_id": "dispatcher-3",
      "status": "alive",
      "last_seen": 1701432300.789
    }
  },
  "version": 11,
  "timestamp": 1701432304.789
}
```

**Point out:**
- ✅ All three gossip agents have the same membership data
- ✅ All show the same 3 dispatcher nodes
- ✅ All show status "alive" with recent timestamps
- ✅ This proves state synchronization through gossip protocol

---

## STEP 6: Compare Membership Views Side-by-Side

### Terminal 1 - Extract and Compare Membership

```bash
echo "=== Membership Comparison ==="
echo ""
echo "Gossip Agent-1 Membership:"
curl -s http://localhost:5006/gossip/state | python -m json.tool | grep -A 5 "membership" | head -20
echo ""
echo "Gossip Agent-2 Membership:"
curl -s http://localhost:5007/gossip/state | python -m json.tool | grep -A 5 "membership" | head -20
echo ""
echo "Gossip Agent-3 Membership:"
curl -s http://localhost:5008/gossip/state | python -m json.tool | grep -A 5 "membership" | head -20
```

**Point out:**
- ✅ All three agents show identical membership
- ✅ Same node IDs (dispatcher-1, dispatcher-2, dispatcher-3)
- ✅ Same statuses (all "alive")
- ✅ Timestamps are recent (within gossip interval)

---

## STEP 7: Monitor Gossip Statistics

### Terminal 1 - Check Gossip Statistics for Each Agent

```bash
echo "=== Gossip Agent-1 Statistics ==="
curl -s http://localhost:5006/gossip/stats | python -m json.tool
echo ""
echo "=== Gossip Agent-2 Statistics ==="
curl -s http://localhost:5007/gossip/stats | python -m json.tool
echo ""
echo "=== Gossip Agent-3 Statistics ==="
curl -s http://localhost:5008/gossip/stats | python -m json.tool
```

**Expected Output:**

**Gossip Agent-1:**
```json
{
  "rounds": 12,
  "messages_sent": 24,
  "messages_received": 20,
  "peers": 2,
  "version": 12,
  "membership_size": 3,
  "popularity_topics": 5,
  "recent_events_count": 3
}
```

**Gossip Agent-2:**
```json
{
  "rounds": 10,
  "messages_sent": 20,
  "messages_received": 22,
  "peers": 2,
  "version": 10,
  "membership_size": 3,
  "popularity_topics": 5,
  "recent_events_count": 3
}
```

**Gossip Agent-3:**
```json
{
  "rounds": 11,
  "messages_sent": 22,
  "messages_received": 21,
  "peers": 2,
  "version": 11,
  "membership_size": 3,
  "popularity_topics": 5,
  "recent_events_count": 3
}
```

**Point out:**
- ✅ All three agents show `membership_size: 3` (same number of dispatchers)
- ✅ All show `popularity_topics: 5` (same popularity data)
- ✅ All show `recent_events_count: 3` (same events)
- ✅ Messages sent/received show active gossip exchanges
- ✅ This proves eventual consistency achieved

---

## STEP 8: Demonstrate State Update Propagation

### Terminal 1 - Trigger a State Update

Wait for a dispatcher to send a new heartbeat, then immediately check all three gossip agents:

```bash
# Check timestamps before update
echo "Before update:"
echo "Agent-1 timestamp:"
curl -s http://localhost:5006/gossip/state | python -m json.tool | grep "timestamp"
echo "Agent-2 timestamp:"
curl -s http://localhost:5007/gossip/state | python -m json.tool | grep "timestamp"
echo "Agent-3 timestamp:"
curl -s http://localhost:5008/gossip/state | python -m json.tool | grep "timestamp"

# Wait 10 seconds (2 gossip rounds)
sleep 10

# Check timestamps after gossip
echo ""
echo "After 10 seconds (2 gossip rounds):"
echo "Agent-1 timestamp:"
curl -s http://localhost:5006/gossip/state | python -m json.tool | grep "timestamp"
echo "Agent-2 timestamp:"
curl -s http://localhost:5007/gossip/state | python -m json.tool | grep "timestamp"
echo "Agent-3 timestamp:"
curl -s http://localhost:5008/gossip/state | python -m json.tool | grep "timestamp"
```

**Point out:**
- ✅ Timestamps update on all three agents
- ✅ State propagates through gossip rounds
- ✅ All agents eventually have the same state

---

## STEP 9: Verify No Stale Data

### Terminal 1 - Check for Stale Data

```bash
# Get current time
current_time=$(date +%s)
echo "Current time: $current_time"
echo ""

# Check last_seen timestamps for all dispatchers across all agents
echo "=== Checking for stale data ==="
echo ""
echo "Gossip Agent-1 - Dispatcher last_seen timestamps:"
curl -s http://localhost:5006/gossip/state | python -m json.tool | grep -A 2 "dispatcher" | grep "last_seen"
echo ""
echo "Gossip Agent-2 - Dispatcher last_seen timestamps:"
curl -s http://localhost:5007/gossip/state | python -m json.tool | grep -A 2 "dispatcher" | grep "last_seen"
echo ""
echo "Gossip Agent-3 - Dispatcher last_seen timestamps:"
curl -s http://localhost:5008/gossip/state | python -m json.tool | grep -A 2 "dispatcher" | grep "last_seen"
```

**Point out:**
- ✅ All timestamps are recent (within last 10 seconds)
- ✅ No stale data (old timestamps)
- ✅ All agents have synchronized, up-to-date state

---

## Summary of What Was Demonstrated

✅ **Three gossip agents running** - gossip-agent-1, gossip-agent-2, gossip-agent-3

✅ **Each gossip agent maintains state repository:**
   - Registered notification dispatcher nodes (all 3 dispatchers)
   - Popularity stats (synchronized)
   - Recent events (synchronized)

✅ **Gossip exchanges every 5 seconds** - Visible in logs

✅ **Push-pull gossip model** - Bidirectional state exchange

✅ **All nodes have identical views** - All three agents show same membership

✅ **State updates propagate** - Changes spread through gossip rounds

✅ **Timestamps are recent** - Within gossip interval (5 seconds)

✅ **No stale or missing data** - All agents have complete, synchronized state

---

## Key Points to Emphasize

1. **Eventual Consistency**: All three gossip agents eventually have the same state
2. **Automatic Synchronization**: No manual intervention required
3. **Periodic Gossip**: State exchanges happen every 5 seconds
4. **Bidirectional Exchange**: Push-pull model ensures both sides get updates
5. **Complete State**: Membership, popularity, and events all synchronized

---

## Troubleshooting

### If gossip agents don't show synchronized state:

1. **Wait longer** - Gossip takes a few rounds to synchronize (30+ seconds)

2. **Check gossip agent logs** for errors:
   ```bash
   docker logs gossip-agent-1 | tail -50
   docker logs gossip-agent-2 | tail -50
   docker logs gossip-agent-3 | tail -50
   ```

3. **Verify gossip peers are configured:**
   ```bash
   docker logs gossip-agent-1 | grep "Initial peers"
   docker logs gossip-agent-2 | grep "Initial peers"
   docker logs gossip-agent-3 | grep "Initial peers"
   ```

4. **Check network connectivity:**
   ```bash
   docker exec gossip-agent-1 curl http://gossip-agent-2:5007/health
   docker exec gossip-agent-1 curl http://gossip-agent-3:5008/health
   ```

---

This guide demonstrates complete state synchronization across three gossip agents using the gossip protocol!

