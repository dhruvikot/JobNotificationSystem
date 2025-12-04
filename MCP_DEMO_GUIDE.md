# MCP Test Scenarios - Live Demo Guide

This guide shows you how to demonstrate the MCP scenarios using the actual running services. All output will come from Docker logs and API calls - no test scripts needed.

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
   docker ps
   ```
   
   Should show:
   - `gossip-agent` (port 5006)
   - `notification-dispatcher-1` (port 5004)
   - `notification-dispatcher-2` (port 5014)
   - `notification-dispatcher-3` (port 5024)

---

## SCENARIO 1: MCP Membership Protocol Operational Success

### Objective
Demonstrate that MCP tracks health and status of multiple distributed nodes through periodic heartbeat messages.

### Step-by-Step Demo

#### Step 1: Show Gossip Agent is Running

**Open Terminal 1** (for API calls):

```bash
# Check gossip agent health
curl http://localhost:5006/health
```

**Expected Output:**
```json
{
  "status": "healthy",
  "service": "gossip-agent",
  "node_id": "gossip-1"
}
```

#### Step 2: Check Initial Membership State

**In Terminal 1:**

```bash
# Get current membership
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
- ✅ All 3 dispatcher nodes are registered
- ✅ All show status "alive"
- ✅ Each has unique node_id, host, and port
- ✅ Load metrics (queue_len, cpu) are present

#### Step 3: Monitor Dispatcher Heartbeats (Live)

**Open Terminal 2** (for dispatcher-1 logs):

```bash
# Watch dispatcher-1 heartbeat logs
docker logs notification-dispatcher-1 -f | grep -i "heartbeat\|mcp\|registered"
```

**Open Terminal 3** (for dispatcher-2 logs):

```bash
# Watch dispatcher-2 heartbeat logs
docker logs notification-dispatcher-2 -f | grep -i "heartbeat\|mcp\|registered"
```

**Open Terminal 4** (for dispatcher-3 logs):

```bash
# Watch dispatcher-3 heartbeat logs
docker logs notification-dispatcher-3 -f | grep -i "heartbeat\|mcp\|registered"
```

**Expected Output (Terminal 2, 3, 4):**

Every 5 seconds, you'll see:
```
[Dispatcher] Sent heartbeat to gossip agent: {'queue_len': 0, 'cpu': 0.5}
```

**Point out:**
- ✅ Each dispatcher sends heartbeat every 5 seconds
- ✅ Heartbeats include load metrics (queue_len, cpu)
- ✅ All three dispatchers operate independently

#### Step 4: Monitor Gossip Agent Receiving Heartbeats

**Open Terminal 5** (for gossip agent logs):

```bash
# Watch gossip agent receiving heartbeats
docker logs gossip-agent -f | grep -i "heartbeat\|mcp\|registered"
```

**Expected Output:**

You'll see periodic messages showing heartbeats being received:
```
[MCP] Heartbeat from dispatcher-1
[MCP] Heartbeat from dispatcher-2
[MCP] Heartbeat from dispatcher-3
```

#### Step 5: Monitor Membership Changes in Real-Time

**In Terminal 1** (run this command to watch membership):

```bash
# Watch membership every 2 seconds
watch -n 2 'curl -s http://localhost:5006/mcp/membership | python -m json.tool | grep -A 10 "dispatcher"'
```

**Or manually check every 5 seconds:**

```bash
# Check 1
curl -s http://localhost:5006/mcp/membership | python -m json.tool | grep -A 5 "dispatcher-1"
sleep 5

# Check 2
curl -s http://localhost:5006/mcp/membership | python -m json.tool | grep -A 5 "dispatcher-1"
sleep 5

# Check 3
curl -s http://localhost:5006/mcp/membership | python -m json.tool | grep -A 5 "dispatcher-1"
```

**Point out:**
- ✅ `last_seen` timestamp updates every ~5 seconds
- ✅ Status remains "alive" for all nodes
- ✅ Load metrics are updated with each heartbeat

#### Step 6: Show All Nodes Remain ALIVE

**In Terminal 1:**

```bash
# Get final membership status
curl http://localhost:5006/mcp/membership | python -m json.tool
```

**Point out:**
- ✅ All 3 nodes still show status "alive"
- ✅ All have recent `last_seen` timestamps
- ✅ Load metrics are being transmitted

#### Step 7: Show Heartbeat Intervals

**In Terminal 1** (check timestamps):

```bash
# Get timestamps
curl -s http://localhost:5006/mcp/membership | python -m json.tool | grep "last_seen"
```

Wait 5 seconds, then:

```bash
# Get timestamps again
curl -s http://localhost:5006/mcp/membership | python -m json.tool | grep "last_seen"
```

**Point out:**
- ✅ Timestamps increase by approximately 5 seconds
- ✅ This proves heartbeats are being sent regularly

---

## SCENARIO 2: Distributed Cluster Concurrent Operation

### Objective
Demonstrate that multiple dispatcher processes run concurrently without conflicts, sending heartbeats in parallel.

### Step-by-Step Demo

#### Step 1: Verify All Three Dispatchers Are Running

**In Terminal 1:**

```bash
# Check all dispatcher containers
docker ps | grep notification-dispatcher
```

**Expected Output:**
```
CONTAINER ID   IMAGE                    STATUS         PORTS                    NAMES
abc123def456   ...notification-dispatcher   Up 2 minutes   0.0.0.0:5004->5004/tcp   notification-dispatcher-1
def456ghi789   ...notification-dispatcher   Up 2 minutes   0.0.0.0:5014->5014/tcp   notification-dispatcher-2
ghi789jkl012   ...notification-dispatcher   Up 2 minutes   0.0.0.0:5024->5024/tcp   notification-dispatcher-3
```

**Point out:**
- ✅ Three separate containers running
- ✅ Each on different ports (5004, 5014, 5024)
- ✅ No port conflicts

#### Step 2: Show Independent Registration

**In Terminal 1:**

```bash
# Get membership showing all three nodes
curl http://localhost:5006/mcp/membership | python -m json.tool
```

**Point out:**
- ✅ Each node has unique `node_id` (dispatcher-1, dispatcher-2, dispatcher-3)
- ✅ Each has different `port` (5004, 5014, 5024)
- ✅ All registered independently with gossip agent

#### Step 3: Demonstrate Concurrent Heartbeats

**Open Terminal 2, 3, 4** (side by side):

**Terminal 2:**
```bash
docker logs notification-dispatcher-1 -f --tail 0 | grep "Sent heartbeat"
```

**Terminal 3:**
```bash
docker logs notification-dispatcher-2 -f --tail 0 | grep "Sent heartbeat"
```

**Terminal 4:**
```bash
docker logs notification-dispatcher-3 -f --tail 0 | grep "Sent heartbeat"
```

**Watch for 30 seconds**

**Point out:**
- ✅ All three terminals show heartbeat messages
- ✅ Messages appear at nearly the same time (within 1 second)
- ✅ This proves parallel/concurrent operation

#### Step 4: Show Concurrent Timestamps

**In Terminal 1** (run multiple times quickly):

```bash
# Check 1
echo "=== Check 1 ===" && date && curl -s http://localhost:5006/mcp/membership | python -m json.tool | grep -E "(dispatcher-|last_seen)" | head -6

sleep 1

# Check 2
echo "=== Check 2 ===" && date && curl -s http://localhost:5006/mcp/membership | python -m json.tool | grep -E "(dispatcher-|last_seen)" | head -6

sleep 1

# Check 3
echo "=== Check 3 ===" && date && curl -s http://localhost:5006/mcp/membership | python -m json.tool | grep -E "(dispatcher-|last_seen)" | head -6
```

**Expected Output:**
```
=== Check 1 ===
Fri Dec  1 14:23:45 PST 2023
        "dispatcher-1": {
            "last_seen": 1701432225.123,
        "dispatcher-2": {
            "last_seen": 1701432225.456,
        "dispatcher-3": {
            "last_seen": 1701432225.789,
=== Check 2 ===
Fri Dec  1 14:23:46 PST 2023
        "dispatcher-1": {
            "last_seen": 1701432225.123,
        "dispatcher-2": {
            "last_seen": 1701432225.456,
        "dispatcher-3": {
            "last_seen": 1701432225.789,
=== Check 3 ===
Fri Dec  1 14:23:47 PST 2023
        "dispatcher-1": {
            "last_seen": 1701432230.234,
        "dispatcher-2": {
            "last_seen": 1701432230.567,
        "dispatcher-3": {
            "last_seen": 1701432230.890,
```

**Point out:**
- ✅ All three `last_seen` timestamps are very close together (within 1 second)
- ✅ This proves heartbeats are sent concurrently, not sequentially
- ✅ Timestamps update together (all change at same time)

#### Step 5: Show Cluster Stability

**In Terminal 1:**

```bash
# Monitor membership for 30 seconds
for i in {1..6}; do
  echo "=== Check $i at $(date) ==="
  curl -s http://localhost:5006/mcp/membership | python -m json.tool | grep -E "(dispatcher-|status)" | head -6
  echo
  sleep 5
done
```

**Expected Output:**
```
=== Check 1 at Fri Dec  1 14:24:00 PST 2023 ===
        "dispatcher-1": {
            "status": "alive",
        "dispatcher-2": {
            "status": "alive",
        "dispatcher-3": {
            "status": "alive",
=== Check 2 at Fri Dec  1 14:24:05 PST 2023 ===
        "dispatcher-1": {
            "status": "alive",
        "dispatcher-2": {
            "status": "alive",
        "dispatcher-3": {
            "status": "alive",
...
```

**Point out:**
- ✅ All nodes remain "alive" throughout monitoring
- ✅ No false failures detected
- ✅ Cluster is stable

#### Step 6: Show Independent Operation

**In Terminal 1:**

```bash
# Get detailed info for each node
curl -s http://localhost:5006/mcp/membership | python -m json.tool | grep -A 8 "dispatcher-1"
echo "---"
curl -s http://localhost:5006/mcp/membership | python -m json.tool | grep -A 8 "dispatcher-2"
echo "---"
curl -s http://localhost:5006/mcp/membership | python -m json.tool | grep -A 8 "dispatcher-3"
```

**Point out:**
- ✅ Each node has independent `node_id`, `host`, `port`
- ✅ Each has its own `last_seen` timestamp
- ✅ Each has its own `load` metrics
- ✅ MCP tracks them as separate, independent nodes

---

## Quick Reference Commands

### Check Membership
```bash
curl http://localhost:5006/mcp/membership | python -m json.tool
```

### Watch Dispatcher Logs
```bash
# Dispatcher 1
docker logs notification-dispatcher-1 -f | grep -i "heartbeat\|mcp"

# Dispatcher 2
docker logs notification-dispatcher-2 -f | grep -i "heartbeat\|mcp"

# Dispatcher 3
docker logs notification-dispatcher-3 -f | grep -i "heartbeat\|mcp"
```

### Watch Gossip Agent Logs
```bash
docker logs gossip-agent -f | grep -i "heartbeat\|mcp"
```

### Monitor Membership Changes
```bash
watch -n 2 'curl -s http://localhost:5006/mcp/membership | python -m json.tool'
```

### Get Only Dispatcher Nodes
```bash
curl http://localhost:5006/mcp/nodes/dispatcher | python -m json.tool
```

---

## What to Point Out During Demo

### Scenario 1:
1. ✅ Three dispatcher nodes registered with gossip agent
2. ✅ Each dispatcher sends heartbeat every 5 seconds
3. ✅ Gossip agent receives and logs all heartbeats
4. ✅ MCP API returns status showing all 3 nodes as "alive"
5. ✅ Load metrics (CPU, queue length) transmitted with heartbeats
6. ✅ Heartbeat intervals are consistent (~5 seconds)

### Scenario 2:
1. ✅ Three processes start successfully without port conflicts
2. ✅ Each process independently registers with gossip agent
3. ✅ All three send heartbeats concurrently (timestamps within 1 second)
4. ✅ MCP tracks all three as separate, independent nodes
5. ✅ Cluster remains stable with all nodes ALIVE (no false failures)
6. ✅ Heartbeat timestamps show sub-second differences (proving parallel operation)

---

## Troubleshooting

### If dispatcher nodes don't appear:

1. **Check if services are running:**
   ```bash
   docker ps | grep notification-dispatcher
   ```

2. **Check dispatcher logs for errors:**
   ```bash
   docker logs notification-dispatcher-1
   docker logs notification-dispatcher-2
   docker logs notification-dispatcher-3
   ```

3. **Check if dispatchers can reach gossip agent:**
   ```bash
   docker exec notification-dispatcher-1 curl http://gossip-agent:5006/health
   ```

### If heartbeats aren't showing:

1. **Check dispatcher logs:**
   ```bash
   docker logs notification-dispatcher-1 | tail -50
   ```

2. **Look for "Sent heartbeat" messages**

3. **Check gossip agent logs:**
   ```bash
   docker logs gossip-agent | tail -50
   ```

---

## Recording Tips

1. **Use multiple terminal windows** side-by-side to show:
   - Terminal 1: API calls (curl commands)
   - Terminal 2-4: Dispatcher logs (one per dispatcher)
   - Terminal 5: Gossip agent logs

2. **Run commands slowly** so viewers can see the output

3. **Point out timestamps** - show how they update every 5 seconds

4. **Highlight concurrent behavior** - show all three dispatchers sending heartbeats at nearly the same time

5. **Show the JSON output** - demonstrate the structure of the membership data

---

This guide uses only Docker logs and curl commands - no Python scripts needed. All output comes directly from the running services!

