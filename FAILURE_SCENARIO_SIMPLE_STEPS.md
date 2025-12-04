# Failure Scenario Demo - Simple Steps

## What You'll See
- 3 dispatcher nodes running and sending heartbeats
- One dispatcher crashes
- MCP automatically detects the failure (SUSPECT → DEAD)
- Other 2 dispatchers continue working

---

## Step 1: Start Services

```bash
cd deployment/docker
docker-compose up -d
```

**Wait 30 seconds** for services to start.

---

## Step 2: Open 4 Terminal Windows Side-by-Side

### Terminal 1 - Dispatcher 1 (Will Keep Working)
```bash
docker logs notification-dispatcher-1 -f
```

### Terminal 2 - Dispatcher 2 (Will Be Crashed)
```bash
docker logs notification-dispatcher-2 -f
```

### Terminal 3 - Dispatcher 3 (Will Keep Working)
```bash
docker logs notification-dispatcher-3 -f
```

### Terminal 4 - Gossip Agent (Shows Failure Detection)
```bash
docker logs gossip-agent-1 -f
```

---

## Step 3: Verify All Are Running (Wait 30 seconds)

Watch all 4 terminals. You should see:

**Terminal 1, 2, 3 (All Dispatchers):**
```
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
```
*(Messages appear every 5 seconds)*

**Terminal 4 (Gossip Agent):**
```
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-1
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-2
[Gossip Agent] [HEARTBEAT] Received heartbeat from dispatcher-3
```
*(All 3 dispatchers sending heartbeats)*

---

## Step 4: Check Initial Status (Optional)

Open a **5th terminal** and run:

```bash
curl http://localhost:5006/mcp/membership | python -m json.tool
```

**You should see all 3 dispatchers with status "alive".**

---

## Step 5: Crash Dispatcher-2

In a **new terminal** (or Terminal 5), run:

```bash
docker stop notification-dispatcher-2
```

**What happens immediately:**
- ✅ Terminal 2 (Dispatcher-2) stops showing new messages
- ✅ Terminal 4 (Gossip Agent) stops receiving dispatcher-2 heartbeats
- ✅ Terminal 1 & 3 continue showing heartbeats (still working)

---

## Step 6: Watch Failure Detection (Wait 30 seconds)

Watch **Terminal 4 (Gossip Agent)** - you'll see automatic failure detection:

### Timeline:

**~10 seconds (2 missed heartbeats):**
```
[MCP] Node marked as SUSPECT: dispatcher-2
```

**~25 seconds (5 missed heartbeats):**
```
[MCP] Node marked as DEAD: dispatcher-2
```

**~30+ seconds:**
```
[MCP] Node removed: dispatcher-2
```

**Meanwhile, Terminal 1 & 3 continue:**
```
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
```
*(Still working normally!)*

---

## Step 7: Verify Final Status

In Terminal 5, check membership again:

```bash
curl http://localhost:5006/mcp/membership | python -m json.tool
```

**You should see:**
- ✅ dispatcher-1: status "alive" (still working)
- ✅ dispatcher-2: status "dead" (crashed and detected)
- ✅ dispatcher-3: status "alive" (still working)

---

## Summary

### What This Shows:

✅ **3 dispatchers running** - All sending heartbeats initially

✅ **One crashes** - `docker stop notification-dispatcher-2`

✅ **Automatic detection** - MCP detects failure without manual intervention

✅ **State transitions** - ALIVE → SUSPECT (10s) → DEAD (25s)

✅ **Other nodes continue** - Dispatcher-1 and Dispatcher-3 keep working

✅ **No manual intervention** - Everything happens automatically

---

## Quick Commands Summary

```bash
# Start everything
docker-compose up -d

# Open 4 terminals:
docker logs notification-dispatcher-1 -f
docker logs notification-dispatcher-2 -f
docker logs notification-dispatcher-3 -f
docker logs gossip-agent-1 -f

# Crash dispatcher-2
docker stop notification-dispatcher-2

# Check status
curl http://localhost:5006/mcp/membership | python -m json.tool
```

---

## Troubleshooting

**Don't see SUSPECT/DEAD messages?**
- Wait longer (SUSPECT at 10s, DEAD at 25s)
- Check gossip agent logs: `docker logs gossip-agent-1 | tail -50`

**Want to restart?**
```bash
docker-compose restart notification-dispatcher-2
```

---

That's it! Simple 7-step process to demonstrate automatic failure detection.

