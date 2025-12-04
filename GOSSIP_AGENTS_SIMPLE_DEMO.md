# Simple Guide: Viewing Three Gossip Agents Side-by-Side

This guide shows you how to view all three gossip agents simultaneously with clear, visible output.

---

## Step 1: Start All Services

```bash
cd deployment/docker
docker-compose up -d
```

**Wait 30 seconds** for all services to start.

---

## Step 2: Open 4 Terminal Windows Side-by-Side

### Terminal 1: Gossip Agent-1 (Port 5006)
```bash
docker logs gossip-agent-1 -f --tail 0
```

### Terminal 2: Gossip Agent-2 (Port 5007)
```bash
docker logs gossip-agent-2 -f --tail 0
```

### Terminal 3: Gossip Agent-3 (Port 5008)
```bash
docker logs gossip-agent-3 -f --tail 0
```

### Terminal 4: API Calls (Check States)
```bash
# Keep this terminal for running curl commands
```

---

## Step 3: Wait for Initialization (30 seconds)

Watch all three terminals. You should see:

**Terminal 1 (Gossip Agent-1):**
```
[Gossip Agent] Starting node gossip-1 on port 5006
[Gossip Agent] Initial peers: ['http://gossip-agent-2:5007', 'http://gossip-agent-3:5008']
[Gossip Agent] Started MCP monitoring
[Gossip Agent] Started gossip protocol
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-1
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-2
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-3
```

**Terminal 2 (Gossip Agent-2):**
```
[Gossip Agent] Starting node gossip-2 on port 5007
[Gossip Agent] Initial peers: ['http://gossip-agent-1:5006', 'http://gossip-agent-3:5008']
[Gossip Agent] Started MCP monitoring
[Gossip Agent] Started gossip protocol
```

**Terminal 3 (Gossip Agent-3):**
```
[Gossip Agent] Starting node gossip-3 on port 5008
[Gossip Agent] Initial peers: ['http://gossip-agent-1:5006', 'http://gossip-agent-2:5007']
[Gossip Agent] Started MCP monitoring
[Gossip Agent] Started gossip protocol
```

---

## Step 4: Watch Gossip Exchanges (Every 5 Seconds)

After 30 seconds, you'll see gossip exchanges happening:

**Terminal 1 (Gossip Agent-1):**
```
[Gossip] [GOSSIP] Gossiping with http://gossip-agent-2:5007
[Gossip] Merged from http://gossip-agent-2:5007: {'membership_updates': 0, 'popularity_updates': 0, 'new_events': 0}
[Gossip] [GOSSIP] Gossiping with http://gossip-agent-3:5008
[Gossip] Merged from http://gossip-agent-3:5008: {'membership_updates': 0, 'popularity_updates': 0, 'new_events': 0}
[Gossip Agent] [GOSSIP] Received gossip exchange from gossip-2: membership_updates=0, popularity_updates=0, new_events=0
[Gossip Agent] [GOSSIP] Received gossip exchange from gossip-3: membership_updates=0, popularity_updates=0, new_events=0
```

**Terminal 2 (Gossip Agent-2):**
```
[Gossip] [GOSSIP] Gossiping with http://gossip-agent-1:5006
[Gossip] Merged from http://gossip-agent-1:5006: {'membership_updates': 3, 'popularity_updates': 0, 'new_events': 0}
[Gossip] [GOSSIP] Gossiping with http://gossip-agent-3:5008
[Gossip Agent] [GOSSIP] Received gossip exchange from gossip-1: membership_updates=0, popularity_updates=0, new_events=0
[Gossip Agent] [GOSSIP] Received gossip exchange from gossip-3: membership_updates=0, popularity_updates=0, new_events=0
```

**Terminal 3 (Gossip Agent-3):**
```
[Gossip] [GOSSIP] Gossiping with http://gossip-agent-1:5006
[Gossip] Merged from http://gossip-agent-1:5006: {'membership_updates': 3, 'popularity_updates': 0, 'new_events': 0}
[Gossip] [GOSSIP] Gossiping with http://gossip-agent-2:5007
[Gossip Agent] [GOSSIP] Received gossip exchange from gossip-1: membership_updates=0, popularity_updates=0, new_events=0
[Gossip Agent] [GOSSIP] Received gossip exchange from gossip-2: membership_updates=0, popularity_updates=0, new_events=0
```

**Key Points:**
- ✅ All three agents are gossiping with each other
- ✅ Messages appear every 5 seconds
- ✅ You can see state being merged (membership_updates, popularity_updates)

---

## Step 5: Check State Synchronization (Terminal 4)

After waiting 30-60 seconds, check if all three agents have the same state:

### Check Gossip Agent-1 State:
```bash
curl -s http://localhost:5006/gossip/state | python -m json.tool | head -40
```

### Check Gossip Agent-2 State:
```bash
curl -s http://localhost:5007/gossip/state | python -m json.tool | head -40
```

### Check Gossip Agent-3 State:
```bash
curl -s http://localhost:5008/gossip/state | python -m json.tool | head -40
```

**Expected Output (All three should show similar membership):**

All three should show:
```json
{
  "node_id": "gossip-1",  // or gossip-2, gossip-3
  "membership": {
    "dispatcher-1": {
      "node_id": "dispatcher-1",
      "role": "dispatcher",
      "status": "alive",
      "last_seen": 1701432300.123
    },
    "dispatcher-2": {
      "node_id": "dispatcher-2",
      "role": "dispatcher",
      "status": "alive",
      "last_seen": 1701432300.456
    },
    "dispatcher-3": {
      "node_id": "dispatcher-3",
      "role": "dispatcher",
      "status": "alive",
      "last_seen": 1701432300.789
    }
  },
  "popularity": {},
  "recent_events": [],
  "version": 12,
  "timestamp": 1701432305.123
}
```

**Point out:**
- ✅ All three agents show the same 3 dispatcher nodes
- ✅ All show status "alive"
- ✅ This proves state synchronization through gossip

---

## Step 6: Compare Membership Counts (Quick Check)

In Terminal 4, run this to quickly compare:

```bash
echo "=== Membership Counts ==="
echo "Gossip Agent-1:"
curl -s http://localhost:5006/gossip/state | python -m json.tool | grep -c "dispatcher"
echo "Gossip Agent-2:"
curl -s http://localhost:5007/gossip/state | python -m json.tool | grep -c "dispatcher"
echo "Gossip Agent-3:"
curl -s http://localhost:5008/gossip/state | python -m json.tool | grep -c "dispatcher"
```

All three should show the same count (3 dispatchers).

---

## Step 7: View Statistics (Terminal 4)

Check gossip statistics to see activity:

```bash
echo "=== Gossip Agent-1 Stats ==="
curl -s http://localhost:5006/gossip/stats | python -m json.tool
echo ""
echo "=== Gossip Agent-2 Stats ==="
curl -s http://localhost:5007/gossip/stats | python -m json.tool
echo ""
echo "=== Gossip Agent-3 Stats ==="
curl -s http://localhost:5008/gossip/stats | python -m json.tool
```

**Expected Output:**
All three should show:
- `membership_size: 3` (same number of dispatchers)
- `rounds: X` (number of gossip rounds completed)
- `messages_sent: Y` (messages sent to peers)
- `messages_received: Z` (messages received from peers)

---

## Visual Layout for Recording

**Arrange your screen like this:**

```
┌─────────────────┬─────────────────┬─────────────────┐
│  Terminal 1     │  Terminal 2     │  Terminal 3     │
│  Gossip Agent-1 │  Gossip Agent-2 │  Gossip Agent-3 │
│  (Port 5006)    │  (Port 5007)    │  (Port 5008)    │
│                 │                 │                 │
│  [Logs showing] │  [Logs showing] │  [Logs showing] │
│  gossip         │  gossip          │  gossip          │
│  exchanges]     │  exchanges]      │  exchanges]      │
└─────────────────┴─────────────────┴─────────────────┘
┌─────────────────────────────────────────────────────┐
│  Terminal 4: API Calls                               │
│  curl commands to check state                        │
└─────────────────────────────────────────────────────┘
```

---

## Quick Summary

1. **Start services**: `docker-compose up -d`
2. **Open 3 terminals** for gossip agent logs
3. **Watch logs** - you'll see gossip exchanges every 5 seconds
4. **Check state** - use Terminal 4 to verify all three have same membership
5. **Record** - all three terminals show synchronized state

---

## Troubleshooting

### If you don't see gossip exchanges:

1. **Check if services are running:**
   ```bash
   docker ps | grep gossip-agent
   ```
   Should show all 3 gossip agents

2. **Check logs for errors:**
   ```bash
   docker logs gossip-agent-1 | tail -20
   docker logs gossip-agent-2 | tail -20
   docker logs gossip-agent-3 | tail -20
   ```

3. **Wait longer** - Gossip happens every 5 seconds, so wait 30+ seconds

4. **Verify peers are configured:**
   ```bash
   docker logs gossip-agent-1 | grep "Initial peers"
   docker logs gossip-agent-2 | grep "Initial peers"
   docker logs gossip-agent-3 | grep "Initial peers"
   ```

---

This simple guide gives you clear, visible output from all three gossip agents side-by-side!

