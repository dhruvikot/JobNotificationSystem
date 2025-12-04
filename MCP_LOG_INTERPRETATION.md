# Understanding MCP Logs - What You're Seeing

## HTTP Access Logs vs MCP Messages

When monitoring gossip agent logs, you'll see two types of messages:

### 1. HTTP Access Logs (What you're currently seeing)

These are Flask's default HTTP request logs:
```
172.18.0.7 - - [04/Dec/2025 02:53:55] "POST /mcp/heartbeat HTTP/1.1" 200 -
172.18.0.9 - - [04/Dec/2025 02:53:56] "POST /mcp/heartbeat HTTP/1.1" 200 -
172.18.0.11 - - [04/Dec/2025 02:53:56] "POST /mcp/heartbeat HTTP/1.1" 200 -
```

**What this means:**
- ✅ Heartbeats are being received successfully (200 status code)
- ✅ Three different IPs = three dispatcher nodes
- ✅ Timestamps show when heartbeats arrive
- ⚠️ These are HTTP logs, not MCP state change messages

### 2. MCP State Change Messages (What to look for)

These are printed by the MCP monitoring thread:
```
[MCP] Node marked as SUSPECT: dispatcher-2
[MCP] Node marked as DEAD: dispatcher-2
[MCP] Node recovered from suspect: dispatcher-2
```

**When these appear:**
- When monitoring thread detects missed heartbeats (runs every 2 seconds)
- When node transitions from ALIVE → SUSPECT → DEAD
- When node recovers (DEAD/SUSPECT → ALIVE)

---

## How to See Both Types of Logs

### Option 1: See All Logs (Recommended)

```bash
# Windows PowerShell
docker logs gossip-agent -f --tail 50

# Linux/Mac
docker logs gossip-agent -f --tail 50
```

This shows everything - HTTP logs AND MCP messages.

### Option 2: Filter for MCP Messages Only

```bash
# Windows PowerShell
docker logs gossip-agent -f --tail 0 | Select-String -Pattern "\[MCP\]"

# Linux/Mac
docker logs gossip-agent -f --tail 0 | grep "\[MCP\]"
```

### Option 3: See HTTP Logs + MCP Messages

```bash
# Windows PowerShell
docker logs gossip-agent -f --tail 0 | Select-String -Pattern "POST|\[MCP\]|SUSPECT|DEAD"

# Linux/Mac
docker logs gossip-agent -f --tail 0 | grep -E "POST|\[MCP\]|SUSPECT|DEAD"
```

---

## Interpreting Your Current Output

Your output shows:
```
172.18.0.7 - - [04/Dec/2025 02:53:55] "POST /mcp/heartbeat HTTP/1.1" 200 -
172.18.0.9 - - [04/Dec/2025 02:53:56] "POST /mcp/heartbeat HTTP/1.1" 200 -
172.18.0.11 - - [04/Dec/2025 02:53:56] "POST /mcp/heartbeat HTTP/1.1" 200 -
```

**This is GOOD!** It means:
- ✅ All 3 dispatchers are sending heartbeats
- ✅ Gossip agent is receiving them (200 = success)
- ✅ Heartbeats arrive concurrently (timestamps within 1 second)

**To see failure detection:**
1. Stop one dispatcher: `docker stop notification-dispatcher-2`
2. Wait 10-15 seconds
3. Check logs again - you should see:
   - One IP stops appearing in HTTP logs
   - MCP messages appear: `[MCP] Node marked as SUSPECT: dispatcher-2`

---

## What Happens During Failure Detection

### Timeline:

1. **0s**: Dispatcher-2 stopped
   - HTTP logs: One IP stops sending heartbeats
   - MCP: Still shows ALIVE (last heartbeat was recent)

2. **5s**: First missed heartbeat
   - HTTP logs: Only 2 IPs sending heartbeats
   - MCP: Still ALIVE (needs 2 missed = 10s)

3. **10s**: Second missed heartbeat
   - HTTP logs: Still only 2 IPs
   - **MCP: `[MCP] Node marked as SUSPECT: dispatcher-2`** ⚠️

4. **25s**: Fifth missed heartbeat
   - HTTP logs: Still only 2 IPs
   - **MCP: `[MCP] Node marked as DEAD: dispatcher-2`** ❌

---

## Commands to See Everything

### See All Logs (Best for Demo)

```bash
# Windows PowerShell
docker logs gossip-agent -f --tail 100

# Linux/Mac
docker logs gossip-agent -f --tail 100
```

### See Only MCP State Changes

```bash
# Windows PowerShell
docker logs gossip-agent -f --tail 0 | Select-String -Pattern "\[MCP\].*SUSPECT|\[MCP\].*DEAD|\[MCP\].*recovered"

# Linux/Mac
docker logs gossip-agent -f --tail 0 | grep -E "\[MCP\].*SUSPECT|\[MCP\].*DEAD|\[MCP\].*recovered"
```

### See Heartbeat Reception + State Changes

```bash
# Windows PowerShell
docker logs gossip-agent -f --tail 0 | Select-String -Pattern "POST.*heartbeat|\[MCP\].*SUSPECT|\[MCP\].*DEAD"

# Linux/Mac
docker logs gossip-agent -f --tail 0 | grep -E "POST.*heartbeat|\[MCP\].*SUSPECT|\[MCP\].*DEAD"
```

---

## For Your Demo

**What to show:**

1. **Before crash:** Show HTTP logs with 3 IPs sending heartbeats
   ```
   172.18.0.7 - - [...] "POST /mcp/heartbeat HTTP/1.1" 200 -
   172.18.0.9 - - [...] "POST /mcp/heartbeat HTTP/1.1" 200 -
   172.18.0.11 - - [...] "POST /mcp/heartbeat HTTP/1.1" 200 -
   ```

2. **After crash:** Show HTTP logs with only 2 IPs
   ```
   172.18.0.7 - - [...] "POST /mcp/heartbeat HTTP/1.1" 200 -
   172.18.0.11 - - [...] "POST /mcp/heartbeat HTTP/1.1" 200 -
   ```
   (One IP missing = dispatcher-2 stopped)

3. **After 10 seconds:** Show MCP message
   ```
   [MCP] Node marked as SUSPECT: dispatcher-2
   ```

4. **After 25 seconds:** Show MCP message
   ```
   [MCP] Node marked as DEAD: dispatcher-2
   ```

5. **Check membership API:** Show status changed
   ```bash
   curl -s http://localhost:5006/mcp/membership | python -m json.tool | grep -A 8 "dispatcher-2"
   ```
   Shows: `"status": "dead"`

---

## Summary

- ✅ **HTTP logs (200 status)** = Heartbeats being received successfully
- ✅ **Missing IP in HTTP logs** = Node stopped sending heartbeats
- ✅ **`[MCP] Node marked as SUSPECT`** = Failure detected (after 10s)
- ✅ **`[MCP] Node marked as DEAD`** = Node declared dead (after 25s)
- ✅ **Check membership API** = See final status (ALIVE/SUSPECT/DEAD)

Your current output is correct - it shows the system is working! The MCP state change messages will appear when failures are detected.

