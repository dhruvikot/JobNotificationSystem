# Complete Failure Scenario Demo - Step by Step

This guide provides a complete, detailed demonstration of the MCP failure detection scenario with exact timing and expected outputs.

---

## Scenario Requirements

**What We're Demonstrating:**
- When a node crashes unexpectedly, MCP automatically detects the failure through missed heartbeats
- Node transitions: ALIVE → SUSPECT → DEAD without manual intervention

**System Setup:**
- Three dispatchers running and sending heartbeats
- All nodes in ALIVE status
- Dispatcher-2 selected as target for simulated crash

**Expected Behavior:**
- When dispatcher-2 is killed, heartbeats stop immediately
- Gossip agent detects first missed heartbeat after 5 seconds
- After 2 missed heartbeats (10 seconds), node marked SUSPECT
- After 5 missed heartbeats (25 seconds), node marked DEAD
- Remaining two dispatchers (dispatcher-1, dispatcher-3) continue operating
- No manual intervention required for detection

---

## Prerequisites

1. **Start all services:**
   ```bash
   cd deployment/docker
   docker-compose up -d
   ```

2. **Wait 30 seconds** for all services to initialize

3. **Verify all services are running:**
   ```bash
   docker ps | grep notification-dispatcher
   ```
   
   Should show 3 dispatcher containers:
   - notification-dispatcher-1
   - notification-dispatcher-2
   - notification-dispatcher-3

---

## Terminal Setup (5 Terminals)

Open 5 terminals side-by-side for the demo:

- **Terminal 1**: API calls and membership checks
- **Terminal 2**: Dispatcher-1 logs (will continue working)
- **Terminal 3**: Dispatcher-2 logs (will be crashed)
- **Terminal 4**: Dispatcher-3 logs (will continue working)
- **Terminal 5**: Gossip Agent logs (shows failure detection)

---

## STEP 1: Verify Initial State (All Nodes ALIVE)

### Terminal 1 - Check Initial Membership

```bash
curl http://localhost:5006/mcp/membership | python -m json.tool
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
      "host": "localhost",
      "port": 5004,
      "load": {
        "queue_len": 0,
        "cpu": 0.5
      }
    },
    "dispatcher-2": {
      "node_id": "dispatcher-2",
      "role": "dispatcher",
      "status": "alive",
      "last_seen": 1701432226.456,
      "host": "localhost",
      "port": 5014,
      "load": {
        "queue_len": 0,
        "cpu": 0.5
      }
    },
    "dispatcher-3": {
      "node_id": "dispatcher-3",
      "role": "dispatcher",
      "status": "alive",
      "last_seen": 1701432227.789,
      "host": "localhost",
      "port": 5024,
      "load": {
        "queue_len": 0,
        "cpu": 0.5
      }
    }
  }
}
```

**Point out:**
- ✅ All 3 dispatcher nodes are ALIVE
- ✅ All have recent `last_seen` timestamps
- ✅ We'll crash dispatcher-2 to demonstrate failure detection

---

## STEP 2: Start Monitoring All Terminals

### Terminal 2 - Dispatcher-1 Logs (Will Continue Working)

```bash
# Windows PowerShell
docker logs notification-dispatcher-1 -f --tail 0

# Linux/Mac
docker logs notification-dispatcher-1 -f --tail 0
```

**Expected Output (Before Crash):**
```
[Dispatcher] Registered with local MCP
[Dispatcher] Registered with gossip agent (MCP server)
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
```

### Terminal 3 - Dispatcher-2 Logs (Will Be Crashed)

```bash
# Windows PowerShell
docker logs notification-dispatcher-2 -f --tail 0

# Linux/Mac
docker logs notification-dispatcher-2 -f --tail 0
```

**Expected Output (Before Crash):**
```
[Dispatcher] Registered with local MCP
[Dispatcher] Registered with gossip agent (MCP server)
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
```

### Terminal 4 - Dispatcher-3 Logs (Will Continue Working)

```bash
# Windows PowerShell
docker logs notification-dispatcher-3 -f --tail 0

# Linux/Mac
docker logs notification-dispatcher-3 -f --tail 0
```

**Expected Output (Before Crash):**
```
[Dispatcher] Registered with local MCP
[Dispatcher] Registered with gossip agent (MCP server)
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
```

### Terminal 5 - Gossip Agent Logs (Shows Failure Detection)

```bash
# Windows PowerShell
docker logs gossip-agent -f --tail 0

# Linux/Mac
docker logs gossip-agent -f --tail 0
```

**Expected Output (Before Crash):**
```
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-1
127.0.0.1 - - [29/Nov/2025 13:16:56] "POST /mcp/heartbeat HTTP/1.1" 200 -
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-2
127.0.0.1 - - [29/Nov/2025 13:16:55] "POST /mcp/heartbeat HTTP/1.1" 200 -
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-3
127.0.0.1 - - [29/Nov/2025 13:16:59] "POST /mcp/heartbeat HTTP/1.1" 200 -
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-1
127.0.0.1 - - [29/Nov/2025 13:17:01] "POST /mcp/heartbeat HTTP/1.1" 200 -
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-2
127.0.0.1 - - [29/Nov/2025 13:17:00] "POST /mcp/heartbeat HTTP/1.1" 200 -
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-3
127.0.0.1 - - [29/Nov/2025 13:17:04] "POST /mcp/heartbeat HTTP/1.1" 200 -
```

**Point out:**
- ✅ All three dispatchers sending heartbeats every 5 seconds
- ✅ Gossip agent receiving heartbeats from all three
- ✅ HTTP 200 status codes indicate successful reception

**Wait for 2-3 heartbeats to show normal operation, then proceed.**

---

## STEP 3: Crash Dispatcher-2

### In Terminal 1 (or new terminal):

```bash
# Stop dispatcher-2 container (simulating crash)
docker stop notification-dispatcher-2
```

**Expected Output:**
```
notification-dispatcher-2
```

**Point out:**
- ✅ Dispatcher-2 container has been stopped
- ✅ This simulates an unexpected node crash
- ✅ Heartbeats from dispatcher-2 will stop immediately

**Immediately observe:**

- **Terminal 3 (Dispatcher-2)**: Log stream stops - no more heartbeat messages
- **Terminal 5 (Gossip Agent)**: Dispatcher-2 heartbeats stop appearing
- **Terminal 2 & 4**: Continue showing heartbeats (dispatcher-1 and dispatcher-3 still working)

---

## STEP 4: Monitor Failure Detection Timeline

### Timeline of Events

Watch **Terminal 5 (Gossip Agent)** and note the timeline:

| Time | Event | What You See |
|------|-------|--------------|
| **0s** | Dispatcher-2 stopped | Last heartbeat from dispatcher-2 appears |
| **5s** | First missed heartbeat | Only dispatcher-1 and dispatcher-3 heartbeats appear |
| **10s** | Second missed heartbeat | `[MCP] Node marked as SUSPECT: dispatcher-2` ⚠️ |
| **15s** | Third missed heartbeat | Still SUSPECT, dispatcher-1 and dispatcher-3 continue |
| **20s** | Fourth missed heartbeat | Still SUSPECT, dispatcher-1 and dispatcher-3 continue |
| **25s** | Fifth missed heartbeat | `[MCP] Node marked as DEAD: dispatcher-2` ❌ |
| **30s+** | Cleanup | `[MCP] Node removed: dispatcher-2` 🗑️ |

### Terminal 5 - Expected Output (After Crash)

**0-5 seconds:**
```
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-1
127.0.0.1 - - [29/Nov/2025 13:17:11] "POST /mcp/heartbeat HTTP/1.1" 200 -
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-3
127.0.0.1 - - [29/Nov/2025 13:17:09] "POST /mcp/heartbeat HTTP/1.1" 200 -
```
(Notice: No dispatcher-2 heartbeat)

**~10 seconds (2 missed heartbeats):**
```
[MCP] Node marked as SUSPECT: dispatcher-2
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-1
127.0.0.1 - - [29/Nov/2025 13:17:16] "POST /mcp/heartbeat HTTP/1.1" 200 -
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-3
127.0.0.1 - - [29/Nov/2025 13:17:14] "POST /mcp/heartbeat HTTP/1.1" 200 -
```

**~25 seconds (5 missed heartbeats):**
```
[MCP] Node marked as DEAD: dispatcher-2
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-1
127.0.0.1 - - [29/Nov/2025 13:17:26] "POST /mcp/heartbeat HTTP/1.1" 200 -
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-3
127.0.0.1 - - [29/Nov/2025 13:17:24] "POST /mcp/heartbeat HTTP/1.1" 200 -
```

**~30+ seconds (cleanup):**
```
[MCP] Node removed: dispatcher-2
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-1
127.0.0.1 - - [29/Nov/2025 13:17:31] "POST /mcp/heartbeat HTTP/1.1" 200 -
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-3
127.0.0.1 - - [29/Nov/2025 13:17:34] "POST /mcp/heartbeat HTTP/1.1" 200 -
```

**Point out:**
- ✅ Automatic detection - no manual intervention
- ✅ State transitions: ALIVE → SUSPECT (10s) → DEAD (25s) → REMOVED (30s+)
- ✅ Remaining nodes continue operating throughout

---

## STEP 5: Verify Remaining Nodes Continue Operating

### Terminal 2 (Dispatcher-1) - CONTINUES WORKING

**Expected Output (After Crash):**
```
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
```

✅ **Point out:** Dispatcher-1 continues sending heartbeats every 5 seconds - no interruption

### Terminal 3 (Dispatcher-2) - STOPPED

**Expected Output (After Crash):**
```
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
```
(No new messages - stopped)

❌ **Point out:** Dispatcher-2 stopped - no more heartbeats

### Terminal 4 (Dispatcher-3) - CONTINUES WORKING

**Expected Output (After Crash):**
```
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
```

✅ **Point out:** Dispatcher-3 continues sending heartbeats every 5 seconds - no interruption

---

## STEP 6: Check Membership Status at Different Stages

### Terminal 1 - Check Status After 10 Seconds (Should be SUSPECT)

```bash
# Wait 10 seconds after crash, then check
sleep 10
curl -s http://localhost:5006/mcp/membership | python -m json.tool | grep -A 8 "dispatcher-2"
```

**Expected Output:**
```json
"dispatcher-2": {
    "node_id": "dispatcher-2",
    "role": "dispatcher",
    "status": "suspect",  // ⚠️ Changed to SUSPECT
    "last_seen": 1701432226.456,  // Old timestamp (frozen)
    "host": "localhost",
    "port": 5014,
    "load": {
        "queue_len": 0,
        "cpu": 0.5
    }
}
```

**Point out:**
- ⚠️ Status changed from "alive" to "suspect"
- ⚠️ `last_seen` timestamp is old (frozen at crash time)
- ✅ This happened automatically after 2 missed heartbeats (10 seconds)

### Terminal 1 - Check Status After 25 Seconds (Should be DEAD)

```bash
# Wait 15 more seconds (total 25 seconds), then check
sleep 15
curl -s http://localhost:5006/mcp/membership | python -m json.tool | grep -A 8 "dispatcher-2"
```

**Expected Output:**
```json
"dispatcher-2": {
    "node_id": "dispatcher-2",
    "role": "dispatcher",
    "status": "dead",  // ❌ Changed to DEAD
    "last_seen": 1701432226.456,  // Still old timestamp
    "host": "localhost",
    "port": 5014,
    "load": {
        "queue_len": 0,
        "cpu": 0.5
    }
}
```

**Point out:**
- ❌ Status changed from "suspect" to "dead"
- ❌ `last_seen` timestamp still frozen
- ✅ This happened automatically after 5 missed heartbeats (25 seconds)

### Terminal 1 - Check Remaining Nodes (Still ALIVE)

```bash
curl -s http://localhost:5006/mcp/membership | python -m json.tool | grep -E "(dispatcher-1|dispatcher-3)" -A 8
```

**Expected Output:**
```json
"dispatcher-1": {
    "status": "alive",  // ✅ Still ALIVE
    "last_seen": 1701432300.123,  // Recent timestamp
    ...
},
"dispatcher-3": {
    "status": "alive",  // ✅ Still ALIVE
    "last_seen": 1701432300.456,  // Recent timestamp
    ...
}
```

**Point out:**
- ✅ Dispatcher-1 and dispatcher-3 remain ALIVE
- ✅ Both have recent `last_seen` timestamps (updating every 5 seconds)
- ✅ System continues to function despite dispatcher-2 failure

---

## STEP 7: Complete Side-by-Side View

**At this point (after 25+ seconds), you should have:**

### Terminal 1 (API):
```json
{
  "membership": {
    "dispatcher-1": {"status": "alive", "last_seen": 1701432300.123},
    "dispatcher-2": {"status": "dead", "last_seen": 1701432226.456},
    "dispatcher-3": {"status": "alive", "last_seen": 1701432300.456}
  }
}
```

### Terminal 2 (Dispatcher-1):
```
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
```
✅ **Working normally**

### Terminal 3 (Dispatcher-2):
```
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
```
(Stopped - no new messages)
❌ **Crashed**

### Terminal 4 (Dispatcher-3):
```
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
```
✅ **Working normally**

### Terminal 5 (Gossip Agent):
```
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-1
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-3
[MCP] Node marked as SUSPECT: dispatcher-2
[MCP] Node marked as DEAD: dispatcher-2
[MCP] Node removed: dispatcher-2
```
⚠️ **Shows automatic failure detection**

---

## Summary of What Was Demonstrated

✅ **Three dispatchers running and sending heartbeats** - All three showed heartbeat messages

✅ **All nodes in ALIVE status initially** - Verified via membership API

✅ **Dispatcher-2 selected and crashed** - `docker stop notification-dispatcher-2`

✅ **Heartbeats stopped immediately** - Terminal 3 stopped showing new messages

✅ **Gossip agent detected first missed heartbeat after 5 seconds** - Only dispatcher-1 and dispatcher-3 heartbeats appeared

✅ **After 2 missed heartbeats (10 seconds), node marked SUSPECT** - `[MCP] Node marked as SUSPECT: dispatcher-2`

✅ **After 5 missed heartbeats (25 seconds), node marked DEAD** - `[MCP] Node marked as DEAD: dispatcher-2`

✅ **Remaining two dispatchers continue operating** - Terminal 2 and Terminal 4 continued showing heartbeats

✅ **No manual intervention required** - Only action was `docker stop`, all detection was automatic

---

## Key Points to Emphasize

1. **Automatic Detection**: MCP monitoring thread runs every 2 seconds and automatically detects failures
2. **State Transitions**: ALIVE → SUSPECT (10s) → DEAD (25s) → REMOVED (30s+)
3. **Fault Tolerance**: Remaining nodes continue operating normally
4. **No Manual Intervention**: All detection and status changes happen automatically
5. **Timing**: Exact timing based on missed heartbeats (5s interval)

---

## Troubleshooting

### If SUSPECT doesn't appear after 10 seconds:

1. **Check MCP configuration:**
   - `heartbeat_timeout` should be 10 seconds (2 missed heartbeats at 5s interval)

2. **Verify dispatcher is actually stopped:**
   ```bash
   docker ps | grep notification-dispatcher-2
   ```
   Should show nothing

3. **Check gossip agent monitoring:**
   ```bash
   docker logs gossip-agent | grep -i "monitoring\|started"
   ```

### If DEAD doesn't appear after 25 seconds:

1. **Check MCP configuration:**
   - `suspect_timeout` should be 15 seconds (total 25s for 5 missed heartbeats)

2. **Wait longer** - DEAD happens at 25 seconds total (10s for SUSPECT + 15s more)

---

This complete guide shows the exact scenario with all three dispatchers visible side-by-side, demonstrating automatic failure detection without manual intervention.

