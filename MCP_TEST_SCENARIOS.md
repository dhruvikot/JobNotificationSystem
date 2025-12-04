# MCP Test Scenarios - Replication Guide

This document provides step-by-step instructions to replicate the MCP (Membership & Coordination Protocol) test scenarios.

## Prerequisites

1. **All services running via Docker Compose:**
   ```bash
   cd deployment/docker
   docker-compose up -d
   ```

2. **Verify services are running:**
   ```bash
   docker ps
   ```
   
   Should show:
   - `gossip-agent` (port 5006)
   - `notification-dispatcher-1` (port 5004)
   - `notification-dispatcher-2` (port 5014)
   - `notification-dispatcher-3` (port 5024)

3. **Install Python dependencies:**
   ```bash
   pip install requests
   ```

---

## Scenario 1: MCP Membership Protocol Operational Success

### Objective
Demonstrate that MCP can track the health and status of multiple distributed nodes through periodic heartbeat messages.

### Expected Configuration
- **Gossip Agent (MCP server)**: Running on port 5006
- **Three dispatcher nodes**: Running on ports 5004, 5014, 5024
- **Heartbeat interval**: Every 5 seconds
- **Failure detection**:
  - SUSPECT after 2 missed heartbeats (10 seconds)
  - DEAD after 5 missed heartbeats (25 seconds total)

### Test Steps

1. **Start all services:**
   ```bash
   cd deployment/docker
   docker-compose up -d
   ```

2. **Wait for services to initialize (30 seconds)**

3. **Run the test script:**
   ```bash
   python scripts/test-mcp-scenario1.py
   ```

4. **Expected Output:**
   ```
   ✅ Gossip Agent is running
   ✅ Found 3 dispatcher nodes
   ✅ All 3 dispatcher nodes are ALIVE
   ✅ Heartbeats are being sent at regular intervals (~5 seconds)
   ✅ SCENARIO 1 PASSED
   ```

5. **Manual Verification:**
   
   **Check membership status:**
   ```bash
   curl http://localhost:5006/mcp/membership | python -m json.tool
   ```
   
   Should show all 3 dispatcher nodes with status "alive"
   
   **Check dispatcher logs:**
   ```bash
   docker logs notification-dispatcher-1 | grep -i heartbeat
   docker logs notification-dispatcher-2 | grep -i heartbeat
   docker logs notification-dispatcher-3 | grep -i heartbeat
   ```
   
   Should show periodic heartbeat messages every 5 seconds

### Expected Behavior

- ✅ All three dispatchers register with gossip agent upon startup
- ✅ Each dispatcher sends heartbeat every 5 seconds to gossip agent
- ✅ Gossip agent receives and logs all heartbeats
- ✅ MCP API returns status showing all 3 nodes as "alive"
- ✅ Load metrics (CPU, queue length) transmitted with heartbeats

### Distributed Properties Demonstrated

- **Fault Tolerance**: Continuous heartbeat monitoring enables detection of failed nodes
- **Concurrency**: Three nodes transmit heartbeats independently in parallel without conflicts

---

## Scenario 2: Distributed Cluster Concurrent Operation

### Objective
Demonstrate that multiple independent dispatcher processes can run simultaneously as a coordinated cluster, each operating on different ports without conflicts.

### Expected Configuration
- **Three dispatcher nodes**: Running on ports 5004, 5014, 5024
- **All connect to**: Same gossip agent endpoint (port 5006)
- **Operation**: Concurrent, not sequential

### Test Steps

1. **Start all services:**
   ```bash
   cd deployment/docker
   docker-compose up -d
   ```

2. **Wait for services to initialize (30 seconds)**

3. **Run the test script:**
   ```bash
   python scripts/test-mcp-scenario2.py
   ```

4. **Expected Output:**
   ```
   ✅ Found 3 dispatcher nodes
   ✅ Heartbeats are concurrent (max difference: <1.0s)
   ✅ Cluster is stable: All 3 nodes are ALIVE
   ✅ SCENARIO 2 PASSED
   ```

5. **Manual Verification:**
   
   **Check concurrent heartbeats:**
   ```bash
   # Monitor membership for 30 seconds
   watch -n 2 'curl -s http://localhost:5006/mcp/membership | python -m json.tool | grep -A 5 "dispatcher"'
   ```
   
   Heartbeat timestamps should show sub-second differences (proving parallel operation)

### Expected Behavior

- ✅ Three processes start successfully without port conflicts
- ✅ Each process independently registers with gossip agent
- ✅ All three send heartbeats concurrently (not sequentially)
- ✅ MCP tracks all three as separate, independent nodes
- ✅ Cluster remains stable with all nodes ALIVE (no false failures)
- ✅ Heartbeat timestamps show sub-second differences (proving parallel operation)

### Distributed Properties Demonstrated

- **Scalability**: Distributed deployment across multiple ports; adding nodes requires only unique configuration
- **Concurrency**: True parallel operation confirmed by near-simultaneous heartbeat timestamps
- **Fault Isolation**: Each node operates independently; one node's state doesn't affect others

---

## Manual Testing Commands

### Check Gossip Agent Health
```bash
curl http://localhost:5006/health
```

### Get MCP Membership Status
```bash
curl http://localhost:5006/mcp/membership | python -m json.tool
```

### Get Dispatcher Nodes Only
```bash
curl http://localhost:5006/mcp/nodes/dispatcher | python -m json.tool
```

### Monitor Heartbeats in Real-Time
```bash
# Watch membership changes every 2 seconds
watch -n 2 'curl -s http://localhost:5006/mcp/membership | python -m json.tool'
```

### Check Dispatcher Logs
```bash
# Dispatcher 1
docker logs notification-dispatcher-1 -f | grep -i "heartbeat\|mcp"

# Dispatcher 2
docker logs notification-dispatcher-2 -f | grep -i "heartbeat\|mcp"

# Dispatcher 3
docker logs notification-dispatcher-3 -f | grep -i "heartbeat\|mcp"
```

### Check Gossip Agent Logs
```bash
docker logs gossip-agent -f | grep -i "heartbeat\|mcp"
```

---

## Troubleshooting

### Issue: No dispatcher nodes found

**Solution:**
1. Check if dispatcher services are running:
   ```bash
   docker ps | grep notification-dispatcher
   ```

2. Check dispatcher logs for errors:
   ```bash
   docker logs notification-dispatcher-1
   ```

3. Verify environment variables in docker-compose.yml:
   - `GOSSIP_AGENT_URL` should be set to `http://gossip-agent:5006`

### Issue: Heartbeats not being sent

**Solution:**
1. Check if dispatcher can reach gossip agent:
   ```bash
   docker exec notification-dispatcher-1 curl http://gossip-agent:5006/health
   ```

2. Check dispatcher logs for heartbeat errors:
   ```bash
   docker logs notification-dispatcher-1 | grep -i "heartbeat\|error"
   ```

### Issue: Nodes showing as SUSPECT or DEAD

**Solution:**
1. Check if heartbeats are actually being sent:
   ```bash
   docker logs notification-dispatcher-1 | grep "Sent heartbeat"
   ```

2. Check MCP timeout configuration:
   - Default: heartbeat_timeout=10 seconds (2 missed heartbeats)
   - If heartbeats are sent every 5 seconds, 2 missed = 10 seconds = SUSPECT

3. Verify network connectivity between dispatchers and gossip agent

### Issue: Heartbeats not concurrent

**Solution:**
1. Check if all three dispatchers are running:
   ```bash
   docker ps | grep notification-dispatcher
   ```

2. Verify each dispatcher has unique NODE_ID:
   - notification-dispatcher-1: NODE_ID=dispatcher-1
   - notification-dispatcher-2: NODE_ID=dispatcher-2
   - notification-dispatcher-3: NODE_ID=dispatcher-3

3. Check system load - if system is overloaded, heartbeats may be delayed

---

## Expected Test Results

### Scenario 1 Results
```
✅ SCENARIO 1 PASSED

All requirements met:
  ✅ Three dispatcher nodes registered with gossip agent
  ✅ Each dispatcher sends heartbeats every ~5 seconds
  ✅ Gossip agent receives and logs all heartbeats
  ✅ MCP API returns status showing all 3 nodes as 'alive'
  ✅ Load metrics (CPU, queue length) transmitted with heartbeats
```

### Scenario 2 Results
```
✅ SCENARIO 2 PASSED

All requirements met:
  ✅ Three processes start successfully without port conflicts
  ✅ Each process independently registers with gossip agent
  ✅ All three send heartbeats concurrently (not sequentially)
  ✅ MCP tracks all three as separate, independent nodes
  ✅ Cluster remains stable with all nodes ALIVE (no false failures)
  ✅ Heartbeat timestamps show sub-second differences (proving parallel operation)
```

---

## Notes

- **Heartbeat Interval**: Dispatchers send heartbeats every 5 seconds
- **Failure Detection**: 
  - SUSPECT after 10 seconds (2 missed heartbeats)
  - DEAD after 25 seconds (5 missed heartbeats total)
- **MCP Configuration**: Can be adjusted in `backend/libs/mcp/__init__.py`
- **Gossip Agent**: Acts as centralized MCP server on port 5006
- **Dispatcher Nodes**: Each has unique NODE_ID and PORT

