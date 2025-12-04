# Failure Scenario 1: Node Crash and Automatic Detection - Demo Guide

This guide demonstrates how MCP automatically detects node failures through missed heartbeats and transitions nodes from ALIVE → SUSPECT → DEAD.

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

   Should show 3 dispatcher containers running.

---

## Step-by-Step Failure Demo

### Terminal Setup

**Open 5 terminals side-by-side:**

- **Terminal 1**: API calls and membership checks
- **Terminal 2**: Dispatcher-1 logs (will continue working)
- **Terminal 3**: Dispatcher-2 logs (will be crashed)
- **Terminal 4**: Dispatcher-3 logs (will continue working)
- **Terminal 5**: Gossip Agent logs (shows failure detection)

---

### STEP 1: Verify Initial State (All Nodes ALIVE)

**In Terminal 1** (API calls):

```bash
# Check initial membership - all nodes should be ALIVE
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

### STEP 2: Monitor All Three Dispatchers (Before Crash)

**In Terminal 2** (Dispatcher-1 logs - will continue working):

```bash
# Windows PowerShell
docker logs notification-dispatcher-1 -f --tail 0

# Linux/Mac
docker logs notification-dispatcher-1 -f --tail 0
```

**In Terminal 3** (Dispatcher-2 logs - will be crashed):

```bash
# Windows PowerShell
docker logs notification-dispatcher-2 -f --tail 0

# Linux/Mac
docker logs notification-dispatcher-2 -f --tail 0
```

**In Terminal 4** (Dispatcher-3 logs - will continue working):

```bash
# Windows PowerShell
docker logs notification-dispatcher-3 -f --tail 0

# Linux/Mac
docker logs notification-dispatcher-3 -f --tail 0
```

**In Terminal 5** (Gossip Agent logs - shows failure detection):

```bash
# Windows PowerShell
docker logs gossip-agent -f --tail 0

# Linux/Mac
docker logs gossip-agent -f --tail 0
```

**Expected Output (all terminals showing normal operation):**

**Terminal 2 (Dispatcher-1):**
```
[Dispatcher] Registered with local MCP
[Dispatcher] Registered with gossip agent (MCP server)
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
```

**Terminal 3 (Dispatcher-2):**
```
[Dispatcher] Registered with local MCP
[Dispatcher] Registered with gossip agent (MCP server)
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
```

**Terminal 4 (Dispatcher-3):**
```
[Dispatcher] Registered with local MCP
[Dispatcher] Registered with gossip agent (MCP server)
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
```

**Terminal 5 (Gossip Agent):**
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
- ✅ All three dispatchers are sending heartbeats every 5 seconds
- ✅ Gossip agent is receiving heartbeats from all three
- ✅ This is normal operation before crash

**Wait for 2-3 heartbeats to show normal operation, then proceed to Step 3.**

---

### STEP 3: Crash Dispatcher-2

**Open a new terminal or use Terminal 1** (for stopping the container):

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
- ✅ This simulates a node crash
- ✅ Heartbeats from dispatcher-2 will stop immediately

**Immediately check Terminal 3 (Dispatcher-2):**
- You should see the log stream stop (no more heartbeat messages)
- The terminal will show the last message before stopping

**Check Terminal 5 (Gossip Agent):**
- You'll notice dispatcher-2 heartbeats stop appearing
- Only dispatcher-1 and dispatcher-3 heartbeats continue

---

### STEP 4: Observe Failure Detection in Real-Time

**Watch all terminals simultaneously to see the failure detection:**

**Terminal 2 (Dispatcher-1) - CONTINUES WORKING:**
```
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
```
✅ **Point out:** Dispatcher-1 continues sending heartbeats normally

**Terminal 3 (Dispatcher-2) - STOPPED:**
```
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
```
(No new messages after crash)
❌ **Point out:** Dispatcher-2 stopped - no more heartbeats

**Terminal 4 (Dispatcher-3) - CONTINUES WORKING:**
```
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
```
✅ **Point out:** Dispatcher-3 continues sending heartbeats normally

**Terminal 5 (Gossip Agent) - SHOWS FAILURE DETECTION:**

**Before crash (all 3 nodes):**
```
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-1
127.0.0.1 - - [29/Nov/2025 13:17:11] "POST /mcp/heartbeat HTTP/1.1" 200 -
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-2
127.0.0.1 - - [29/Nov/2025 13:17:00] "POST /mcp/heartbeat HTTP/1.1" 200 -
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-3
127.0.0.1 - - [29/Nov/2025 13:17:09] "POST /mcp/heartbeat HTTP/1.1" 200 -
```

**After crash (only 2 nodes, then failure detection):**
```
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-1
127.0.0.1 - - [29/Nov/2025 13:17:16] "POST /mcp/heartbeat HTTP/1.1" 200 -
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-3
127.0.0.1 - - [29/Nov/2025 13:17:14] "POST /mcp/heartbeat HTTP/1.1" 200 -
[MCP] Node marked as SUSPECT: dispatcher-2
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-1
127.0.0.1 - - [29/Nov/2025 13:17:21] "POST /mcp/heartbeat HTTP/1.1" 200 -
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-3
127.0.0.1 - - [29/Nov/2025 13:17:19] "POST /mcp/heartbeat HTTP/1.1" 200 -
[MCP] Node marked as DEAD: dispatcher-2
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-1
127.0.0.1 - - [29/Nov/2025 13:17:26] "POST /mcp/heartbeat HTTP/1.1" 200 -
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-3
127.0.0.1 - - [29/Nov/2025 13:17:24] "POST /mcp/heartbeat HTTP/1.1" 200 -
[MCP] Node removed: dispatcher-2
```

**Point out:**
- ✅ After crash: Only dispatcher-1 and dispatcher-3 heartbeats appear
- ⚠️ After ~10 seconds: `[MCP] Node marked as SUSPECT: dispatcher-2`
- ❌ After ~25 seconds: `[MCP] Node marked as DEAD: dispatcher-2`
- 🗑️ After cleanup: `[MCP] Node removed: dispatcher-2`

---

### STEP 5: Monitor Failure Detection (ALIVE → SUSPECT)

**In Terminal 1** (check membership every 5 seconds):

```bash
# Check 1: Immediately after crash (should still be ALIVE)
echo "=== Check 1: Immediately after crash ===" && date
curl -s http://localhost:5006/mcp/membership | python -m json.tool | grep -A 8 "dispatcher-2"
sleep 5

# Check 2: After 5 seconds (first missed heartbeat)
echo "=== Check 2: After 5 seconds (1 missed heartbeat) ===" && date
curl -s http://localhost:5006/mcp/membership | python -m json.tool | grep -A 8 "dispatcher-2"
sleep 5

# Check 3: After 10 seconds (2 missed heartbeats - should be SUSPECT)
echo "=== Check 3: After 10 seconds (2 missed heartbeats) ===" && date
curl -s http://localhost:5006/mcp/membership | python -m json.tool | grep -A 8 "dispatcher-2"
sleep 5

# Check 4: After 15 seconds
echo "=== Check 4: After 15 seconds ===" && date
curl -s http://localhost:5006/mcp/membership | python -m json.tool | grep -A 8 "dispatcher-2"
sleep 5

# Check 5: After 20 seconds
echo "=== Check 5: After 20 seconds ===" && date
curl -s http://localhost:5006/mcp/membership | python -m json.tool | grep -A 8 "dispatcher-2"
sleep 5

# Check 6: After 25 seconds (5 missed heartbeats - should be DEAD)
echo "=== Check 6: After 25 seconds (5 missed heartbeats) ===" && date
curl -s http://localhost:5006/mcp/membership | python -m json.tool | grep -A 8 "dispatcher-2"
```

**Expected Output Progression:**

**Check 1 (0 seconds):**
```json
"dispatcher-2": {
    "status": "alive",
    "last_seen": 1701432226.456,
    ...
}
```

**Check 2 (5 seconds):**
```json
"dispatcher-2": {
    "status": "alive",
    "last_seen": 1701432226.456,  // Same timestamp (no new heartbeat)
    ...
}
```

**Check 3 (10 seconds - 2 missed heartbeats):**
```json
"dispatcher-2": {
    "status": "suspect",  // ⚠️ Changed to SUSPECT
    "last_seen": 1701432226.456,
    ...
}
```

**Check 4 (15 seconds):**
```json
"dispatcher-2": {
    "status": "suspect",  // Still SUSPECT
    "last_seen": 1701432226.456,
    ...
}
```

**Check 5 (20 seconds):**
```json
"dispatcher-2": {
    "status": "suspect",  // Still SUSPECT
    "last_seen": 1701432226.456,
    ...
}
```

**Check 6 (25 seconds - 5 missed heartbeats):**
```json
"dispatcher-2": {
    "status": "dead",  // ❌ Changed to DEAD
    "last_seen": 1701432226.456,
    ...
}
```

**Point out:**
- ✅ Status transitions: ALIVE → SUSPECT → DEAD
- ✅ `last_seen` timestamp stops updating (frozen at crash time)
- ✅ Transition happens automatically (no manual intervention)

---

### STEP 5: Timeline of Failure Detection

**Watch Terminal 5 (Gossip Agent) and note the timeline:**

| Time | Event | What You See in Terminal 5 |
|------|-------|----------------------------|
| 0s | Dispatcher-2 stopped | Last heartbeat from dispatcher-2 |
| 5s | First missed heartbeat | Only dispatcher-1 and dispatcher-3 heartbeats |
| 10s | Second missed heartbeat | `[MCP] Node marked as SUSPECT: dispatcher-2` ⚠️ |
| 15s | Third missed heartbeat | Still SUSPECT, dispatcher-1 and dispatcher-3 continue |
| 20s | Fourth missed heartbeat | Still SUSPECT, dispatcher-1 and dispatcher-3 continue |
| 25s | Fifth missed heartbeat | `[MCP] Node marked as DEAD: dispatcher-2` ❌ |
| 30s+ | Cleanup | `[MCP] Node removed: dispatcher-2` 🗑️ |

**Point out:**
- ✅ Automatic detection - no manual intervention
- ✅ State transitions: ALIVE → SUSPECT → DEAD → REMOVED
- ✅ Remaining nodes continue operating throughout

---

### STEP 6: Verify Remaining Nodes Continue Operating

**In Terminal 1** (API calls):

```bash
# Check that dispatcher-1 and dispatcher-3 are still ALIVE
curl -s http://localhost:5006/mcp/membership | python -m json.tool | grep -E "(dispatcher-1|dispatcher-3)" -A 8
```

**Also observe Terminal 2 and Terminal 4:**
- Both continue showing heartbeat messages every 5 seconds
- No errors or interruptions

**Expected Output:**
```json
"dispatcher-1": {
    "node_id": "dispatcher-1",
    "role": "dispatcher",
    "status": "alive",  // ✅ Still ALIVE
    "last_seen": 1701432300.123,  // Recent timestamp
    ...
},
"dispatcher-3": {
    "node_id": "dispatcher-3",
    "role": "dispatcher",
    "status": "alive",  // ✅ Still ALIVE
    "last_seen": 1701432300.456,  // Recent timestamp
    ...
}
```

**Point out:**
- ✅ Dispatcher-1 and dispatcher-3 continue operating normally
- ✅ Both remain ALIVE
- ✅ Both continue sending heartbeats (timestamps are recent)
- ✅ System continues to function despite dispatcher-2 failure

---

### STEP 7: Show Side-by-Side Comparison

**At this point, you should have 5 terminals showing:**

**Terminal 1 (API):**
```json
{
  "membership": {
    "dispatcher-1": {"status": "alive", ...},
    "dispatcher-2": {"status": "dead", ...},
    "dispatcher-3": {"status": "alive", ...}
  }
}
```

**Terminal 2 (Dispatcher-1):**
```
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
```
✅ **Working normally**

**Terminal 3 (Dispatcher-2):**
```
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
```
(Stopped - no new messages)
❌ **Crashed**

**Terminal 4 (Dispatcher-3):**
```
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
```
✅ **Working normally**

**Terminal 5 (Gossip Agent):**
```
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-1
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-3
[MCP] Node marked as SUSPECT: dispatcher-2
[MCP] Node marked as DEAD: dispatcher-2
[MCP] Node removed: dispatcher-2
```
⚠️ **Shows failure detection**

**Point out:**
- ✅ Dispatcher-1 and dispatcher-3 continue operating (fault tolerance)
- ❌ Dispatcher-2 stopped (failure)
- ⚠️ Gossip agent automatically detected and marked the failure
- ✅ System continues to function despite node failure

---

### STEP 8: Show Complete Membership State

**In Terminal 1:**

```bash
# Get full membership state showing all nodes
curl http://localhost:5006/mcp/membership | python -m json.tool
```

**Expected Output:**
```json
{
  "membership": {
    "dispatcher-1": {
      "status": "alive",
      "last_seen": 1701432300.123,  // Recent
      ...
    },
    "dispatcher-2": {
      "status": "dead",  // ❌ DEAD
      "last_seen": 1701432226.456,  // Old (frozen at crash time)
      ...
    },
    "dispatcher-3": {
      "status": "alive",
      "last_seen": 1701432300.456,  // Recent
      ...
    }
  }
}
```

**Point out:**
- ✅ Dispatcher-1: ALIVE (recent timestamp)
- ❌ Dispatcher-2: DEAD (old timestamp, frozen)
- ✅ Dispatcher-3: ALIVE (recent timestamp)
- ✅ MCP correctly tracks all three states

---

### STEP 9: Verify No Manual Intervention Required

**In Terminal 1:**

```bash
# Show that we didn't need to manually mark the node as dead
echo "We only ran: docker stop notification-dispatcher-2"
echo "MCP automatically detected the failure and changed status:"
echo "  ALIVE → SUSPECT (after 2 missed heartbeats = 10 seconds)"
echo "  SUSPECT → DEAD (after 5 missed heartbeats = 25 seconds)"
```

**Point out:**
- ✅ Only action taken: `docker stop notification-dispatcher-2`
- ✅ MCP automatically detected failure
- ✅ MCP automatically changed status through SUSPECT to DEAD
- ✅ No manual intervention required

---

## Timeline Summary

| Time | Event | Status |
|------|-------|--------|
| 0s | Dispatcher-2 stopped | ALIVE (last heartbeat received) |
| 5s | First missed heartbeat | ALIVE (still) |
| 10s | Second missed heartbeat | **SUSPECT** ⚠️ |
| 15s | Third missed heartbeat | SUSPECT (still) |
| 20s | Fourth missed heartbeat | SUSPECT (still) |
| 25s | Fifth missed heartbeat | **DEAD** ❌ |

---

## Quick Reference Commands

### Terminal Setup (5 Terminals)

**Terminal 1 - API Calls:**
```bash
curl http://localhost:5006/mcp/membership | python -m json.tool
```

**Terminal 2 - Dispatcher-1 Logs:**
```bash
# Windows PowerShell
docker logs notification-dispatcher-1 -f --tail 0

# Linux/Mac
docker logs notification-dispatcher-1 -f --tail 0
```

**Terminal 3 - Dispatcher-2 Logs (will crash):**
```bash
# Windows PowerShell
docker logs notification-dispatcher-2 -f --tail 0

# Linux/Mac
docker logs notification-dispatcher-2 -f --tail 0
```

**Terminal 4 - Dispatcher-3 Logs:**
```bash
# Windows PowerShell
docker logs notification-dispatcher-3 -f --tail 0

# Linux/Mac
docker logs notification-dispatcher-3 -f --tail 0
```

**Terminal 5 - Gossip Agent Logs (shows failure detection):**
```bash
# Windows PowerShell
docker logs gossip-agent -f --tail 0

# Linux/Mac
docker logs gossip-agent -f --tail 0
```

### Other Useful Commands

**Check Only Dispatcher-2 Status:**
```bash
curl -s http://localhost:5006/mcp/membership | python -m json.tool | grep -A 8 "dispatcher-2"
```

**Stop Dispatcher (Simulate Crash):**
```bash
docker stop notification-dispatcher-2
```

**Restart Dispatcher (Recovery Demo):**
```bash
docker start notification-dispatcher-2
```

---

## Recovery Scenario (Optional)

To demonstrate recovery, restart the crashed node:

```bash
# Restart dispatcher-2
docker start notification-dispatcher-2

# Wait 5 seconds, then check status
sleep 5
curl -s http://localhost:5006/mcp/membership | python -m json.tool | grep -A 8 "dispatcher-2"
```

**Expected Output:**
```json
"dispatcher-2": {
    "status": "alive",  // ✅ Recovered to ALIVE
    "last_seen": 1701432400.789,  // New recent timestamp
    ...
}
```

**Point out:**
- ✅ Node automatically recovers to ALIVE when it starts sending heartbeats again
- ✅ No manual status change required

---

## What to Point Out During Demo

1. ✅ **Initial State**: All 3 nodes ALIVE and sending heartbeats
2. ✅ **Crash Simulation**: Only command needed is `docker stop`
3. ✅ **Automatic Detection**: MCP detects missed heartbeats automatically
4. ✅ **State Transitions**: ALIVE → SUSPECT (10s) → DEAD (25s)
5. ✅ **No Manual Intervention**: All detection and status changes are automatic
6. ✅ **Fault Tolerance**: Remaining nodes continue operating normally
7. ✅ **System Resilience**: Cluster continues to function despite node failure

---

## Troubleshooting

### If status doesn't change to SUSPECT:

1. **Check MCP timeout configuration:**
   - Default: `heartbeat_timeout=10` seconds (2 missed heartbeats)
   - Check gossip agent logs for timeout values

2. **Verify dispatcher is actually stopped:**
   ```bash
   docker ps | grep notification-dispatcher-2
   ```
   Should show nothing (container stopped)

3. **Check gossip agent is monitoring:**
   ```bash
   docker logs gossip-agent | grep -i "monitoring\|check"
   ```

### If status doesn't change to DEAD:

1. **Wait longer** - DEAD happens after 25 seconds (5 missed heartbeats)
2. **Check suspect_timeout** in MCP configuration (default: 5 seconds after SUSPECT)

### If remaining nodes also fail:

1. **Check if all containers are running:**
   ```bash
   docker ps | grep notification-dispatcher
   ```

2. **Check network connectivity:**
   ```bash
   docker exec notification-dispatcher-1 curl http://gossip-agent:5006/health
   ```

---

This guide demonstrates the complete failure detection process using only Docker commands and API calls - perfect for live demos!

