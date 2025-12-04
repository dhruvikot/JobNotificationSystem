# Recovery Scenario Demo - Simple Steps

## What You'll See
- Dispatcher-2 is removed/stopped (DEAD status)
- New Dispatcher-2 starts up
- Automatically rejoins cluster and gets ALIVE status
- Cluster capacity restored to 100% (3/3 nodes)

---

## Step 1: Start from Previous Failure State

**Option A: If you already ran the failure scenario:**
- Dispatcher-2 should already be stopped
- Skip to Step 2

**Option B: If starting fresh:**
```bash
cd deployment/docker
docker-compose up -d
```
Wait 30 seconds, then stop dispatcher-2:
```bash
docker stop notification-dispatcher-2
```
Wait 30 seconds for it to be marked DEAD.

---

## Step 2: Open 4 Terminal Windows Side-by-Side

### Terminal 1 - Dispatcher 1 (Still Working)
```bash
docker logs notification-dispatcher-1 -f
```

### Terminal 2 - Dispatcher 2 (Will Restart)
```bash
docker logs notification-dispatcher-2 -f
```
*(This will be empty/stopped initially)*

### Terminal 3 - Dispatcher 3 (Still Working)
```bash
docker logs notification-dispatcher-3 -f
```

### Terminal 4 - Gossip Agent (Shows Recovery)
```bash
docker logs gossip-agent-1 -f
```

---

## Step 3: Verify Current State (Dispatcher-2 is DEAD)

In a **5th terminal**, check membership:

```bash
curl http://localhost:5006/mcp/membership | python -m json.tool
```

**You should see:**
- ✅ dispatcher-1: status "alive"
- ❌ dispatcher-2: status "dead" (or not present if removed)
- ✅ dispatcher-3: status "alive"

**Terminal 4 (Gossip Agent) should show:**
```
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-1
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-3
```
*(Only 2 dispatchers sending heartbeats)*

---

## Step 4: Restart Dispatcher-2 (Recovery)

In Terminal 5, restart dispatcher-2:

```bash
docker start notification-dispatcher-2
```

**OR if it was removed completely:**

```bash
cd deployment/docker
docker-compose up -d notification-dispatcher-2
```

---

## Step 5: Watch Automatic Recovery (Within 1 Second!)

**Watch Terminal 2 (Dispatcher-2)** - you'll see it start:

```
[Dispatcher] Starting node dispatcher-2 on port 5014
[Dispatcher] Registered with local MCP
[Dispatcher] Registered with gossip agent (MCP server)
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
```

**Watch Terminal 4 (Gossip Agent)** - you'll see recovery:

```
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-2
[MCP] Node registered: dispatcher-2
[MCP] Node status changed: dispatcher-2 -> ALIVE
```

**This happens within 1 second of first heartbeat!**

---

## Step 6: Verify Recovery (Check Membership)

In Terminal 5, check membership again:

```bash
curl http://localhost:5006/mcp/membership | python -m json.tool
```

**You should now see:**
- ✅ dispatcher-1: status "alive"
- ✅ dispatcher-2: status "alive" (RECOVERED!)
- ✅ dispatcher-3: status "alive"

**All 3 dispatchers are ALIVE - cluster capacity restored to 100%!**

---

## Step 7: Verify All Dispatchers Are Working

**Watch all 3 dispatcher terminals:**

**Terminal 1 (Dispatcher-1):**
```
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
```

**Terminal 2 (Dispatcher-2 - RECOVERED):**
```
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
```

**Terminal 3 (Dispatcher-3):**
```
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
```

**Terminal 4 (Gossip Agent) shows all 3:**
```
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-1
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-2
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-3
```

---

## Summary

### What This Shows:

✅ **Dispatcher-2 was DEAD** - From previous failure scenario

✅ **New node starts** - `docker start notification-dispatcher-2`

✅ **Automatic rejoin** - Node automatically registers with gossip agent

✅ **ALIVE status** - Gets ALIVE status within 1 second of first heartbeat

✅ **No manual configuration** - Everything happens automatically

✅ **Cluster restored** - Capacity back to 100% (3/3 nodes)

✅ **All nodes operational** - All 3 dispatchers sending heartbeats

---

## Quick Commands Summary

```bash
# Start from failure state (dispatcher-2 stopped)
docker stop notification-dispatcher-2

# Open 4 terminals:
docker logs notification-dispatcher-1 -f
docker logs notification-dispatcher-2 -f
docker logs notification-dispatcher-3 -f
docker logs gossip-agent-1 -f

# Check current state (should show dispatcher-2 as DEAD)
curl http://localhost:5006/mcp/membership | python -m json.tool

# Restart dispatcher-2 (recovery)
docker start notification-dispatcher-2

# Verify recovery (should show all 3 as ALIVE)
curl http://localhost:5006/mcp/membership | python -m json.tool
```

---

## Timeline

| Time | Event | What You See |
|------|-------|--------------|
| **0s** | Dispatcher-2 stopped | Status: DEAD |
| **0s** | `docker start` command | Dispatcher-2 container starts |
| **<1s** | First heartbeat sent | Terminal 2 shows heartbeat message |
| **<1s** | Gossip agent receives heartbeat | Terminal 4 shows heartbeat received |
| **<1s** | Status changes to ALIVE | Terminal 4 shows "Node status changed -> ALIVE" |
| **5s** | Second heartbeat | All 3 dispatchers sending heartbeats |
| **10s** | Cluster stable | All 3 nodes ALIVE, capacity 100% |

---

## Troubleshooting

**Dispatcher-2 doesn't restart?**
```bash
# Check if container exists
docker ps -a | findstr notification-dispatcher-2

# If not found, recreate it
cd deployment/docker
docker-compose up -d notification-dispatcher-2
```

**Don't see ALIVE status immediately?**
- Check gossip agent logs: `docker logs gossip-agent-1 | tail -20`
- Wait a few seconds (should happen within 1 second, but check logs)

**Want to test recovery again?**
```bash
# Stop dispatcher-2
docker stop notification-dispatcher-2

# Wait 30 seconds for DEAD status

# Restart it
docker start notification-dispatcher-2

# Watch recovery happen!
```

---

## Complete Demo Flow

**To demonstrate both scenarios together:**

1. **Failure Scenario:**
   - Start all services
   - Stop dispatcher-2
   - Watch it go ALIVE → SUSPECT → DEAD

2. **Recovery Scenario:**
   - Restart dispatcher-2
   - Watch it automatically rejoin
   - Status changes DEAD → ALIVE
   - Cluster restored to 3/3 nodes

**This shows the complete MCP cycle:**
- ALIVE → SUSPECT → DEAD → REMOVED (Failure)
- REMOVED → ALIVE (Recovery)

---

That's it! Simple steps to demonstrate automatic node recovery and rejoin.

