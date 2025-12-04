# Leader Election Scenario Demo - Simple Steps

## What You'll See
- 3 publisher services with Bully leader election
- Publisher-3 is initial leader (highest ID)
- Publisher-3 crashes → Publisher-2 becomes new leader
- Publisher-3 restarts → Reclaims leadership
- Automatic re-election and recovery

---

## Step 1: Start Services

```bash
cd deployment/docker
docker-compose up -d
```

**Wait 30 seconds** for services to start.

---

## Step 2: Open 4 Terminal Windows Side-by-Side

### Terminal 1 - Publisher 1 (Follower)
```bash
docker logs publisher-service-1 -f
```

### Terminal 2 - Publisher 2 (Follower, then Leader)
```bash
docker logs publisher-service-2 -f
```

### Terminal 3 - Publisher 3 (Leader, then recovers)
```bash
docker logs publisher-service-3 -f
```

### Terminal 4 - Check Election Status
```bash
# Keep this terminal for checking election status
```

---

## Step 3: Verify Initial State (Normal Operation)

**Wait 30 seconds** for election to complete, then check status in Terminal 4:

```bash
# Check Publisher-1 status
curl http://localhost:5003/election/status | python -m json.tool

# Check Publisher-2 status
curl http://localhost:5013/election/status | python -m json.tool

# Check Publisher-3 status
curl http://localhost:5023/election/status | python -m json.tool
```

**Expected Output:**

**Publisher-1:**
```json
{
  "is_leader": false,
  "current_leader": "publisher-3",
  "state": "follower"
}
```

**Publisher-2:**
```json
{
  "is_leader": false,
  "current_leader": "publisher-3",
  "state": "follower"
}
```

**Publisher-3:**
```json
{
  "is_leader": true,
  "current_leader": "publisher-3",
  "state": "leader"
}
```

**Watch the terminals - you should see:**

**Terminal 1 (Publisher-1):**
```
[Publisher] Leader election initialized
[Publisher] ⚠️  Node publisher-1 lost leadership
```

**Terminal 2 (Publisher-2):**
```
[Publisher] Leader election initialized
[Publisher] ⚠️  Node publisher-2 lost leadership
```

**Terminal 3 (Publisher-3):**
```
[Publisher] Leader election initialized
[Publisher] 🏆 Node publisher-3 became the LEADER
```

**Point out:**
- ✅ Publisher-3 is LEADER (highest ID: publisher-3)
- ✅ Publisher-1 and Publisher-2 are FOLLOWERS
- ✅ Leader sends heartbeats every 3 seconds

---

## Step 4: Watch Normal Operation (30 seconds)

**Watch Terminal 3 (Publisher-3 - Leader):**
```
[Publisher] Sending leader heartbeat to followers
```

**Watch Terminal 1 & 2 (Followers):**
```
[Publisher] Received heartbeat from leader publisher-3
```

**This happens every 3 seconds** - showing normal leader operation.

---

## Step 5: Crash Publisher-3 (Leader Failure)

In Terminal 4, stop publisher-3:

```bash
docker stop publisher-service-3
```

**What happens immediately:**
- ✅ Terminal 3 (Publisher-3) stops showing new messages
- ✅ Terminal 1 & 2 stop receiving heartbeats from publisher-3

---

## Step 6: Watch Automatic Re-election (Wait 10 seconds)

**Watch Terminal 1 & 2** - you'll see automatic re-election:

**Terminal 1 (Publisher-1):**
```
[Election] Leader publisher-3 timeout, starting election
[Election] Node publisher-1 starting election
[Election] Received response from publisher-2 (higher ID)
[Election] Waiting for COORDINATOR message
[Election] Received COORDINATOR: publisher-2 is leader
```

**Terminal 2 (Publisher-2):**
```
[Election] Leader publisher-3 timeout, starting election
[Election] Node publisher-2 starting election
[Election] No response from higher nodes, declaring self as leader
[Publisher] 🏆 Node publisher-2 became the LEADER
```

**Timeline:**
- **~9 seconds**: Leader timeout detected (3 heartbeat intervals × 3 = 9s)
- **~10 seconds**: Election starts
- **~12 seconds**: Publisher-2 becomes new leader

**Point out:**
- ✅ Automatic failure detection (no manual intervention)
- ✅ Publisher-2 becomes new leader (next highest ID)
- ✅ System stabilizes in 5-10 seconds

---

## Step 7: Verify New Leader (Terminal 4)

Check election status again:

```bash
# Check Publisher-1 status
curl http://localhost:5003/election/status | python -m json.tool

# Check Publisher-2 status
curl http://localhost:5013/election/status | python -m json.tool
```

**Expected Output:**

**Publisher-1:**
```json
{
  "is_leader": false,
  "current_leader": "publisher-2",
  "state": "follower"
}
```

**Publisher-2:**
```json
{
  "is_leader": true,
  "current_leader": "publisher-2",
  "state": "leader"
}
```

**Point out:**
- ✅ Publisher-2 is now LEADER
- ✅ Publisher-1 is FOLLOWER
- ✅ System continues operating with new leader

---

## Step 8: Watch New Leader Operation (30 seconds)

**Watch Terminal 2 (Publisher-2 - New Leader):**
```
[Publisher] Sending leader heartbeat to followers
[Publisher] Sending leader heartbeat to followers
```

**Watch Terminal 1 (Publisher-1 - Follower):**
```
[Publisher] Received heartbeat from leader publisher-2
[Publisher] Received heartbeat from leader publisher-2
```

**This happens every 3 seconds** - new leader is working normally.

---

## Step 9: Restart Publisher-3 (Recovery)

In Terminal 4, restart publisher-3:

```bash
docker start publisher-service-3
```

**Watch Terminal 3 (Publisher-3)** - you'll see it restart:

```
[Publisher] Starting node publisher-3 on port 5023
[Publisher] Leader election initialized
[Election] Node publisher-3 starting election
[Election] No response from higher nodes, declaring self as leader
[Publisher] 🏆 Node publisher-3 became the LEADER
```

**Watch Terminal 1 & 2** - they detect new leader:

**Terminal 1 (Publisher-1):**
```
[Election] Received COORDINATOR: publisher-3 is leader
[Publisher] ⚠️  Node publisher-1 lost leadership
```

**Terminal 2 (Publisher-2):**
```
[Election] Received COORDINATOR: publisher-3 is leader
[Publisher] ⚠️  Node publisher-2 lost leadership
```

**Point out:**
- ✅ Publisher-3 reclaims leadership (highest ID)
- ✅ Publisher-1 and Publisher-2 revert to FOLLOWERS
- ✅ Original configuration restored

---

## Step 10: Verify Final State (Terminal 4)

Check election status one more time:

```bash
# Check all three publishers
curl http://localhost:5003/election/status | python -m json.tool
curl http://localhost:5013/election/status | python -m json.tool
curl http://localhost:5023/election/status | python -m json.tool
```

**Expected Output (All three):**

**Publisher-1:**
```json
{
  "is_leader": false,
  "current_leader": "publisher-3",
  "state": "follower"
}
```

**Publisher-2:**
```json
{
  "is_leader": false,
  "current_leader": "publisher-3",
  "state": "follower"
}
```

**Publisher-3:**
```json
{
  "is_leader": true,
  "current_leader": "publisher-3",
  "state": "leader"
}
```

**Point out:**
- ✅ Original configuration restored
- ✅ Publisher-3 is LEADER again
- ✅ Publisher-1 and Publisher-2 are FOLLOWERS

---

## Summary

### What This Shows:

✅ **Normal Operation:**
- Publisher-3 is leader (highest ID)
- Sends heartbeats every 3 seconds
- All nodes acknowledge it as leader

✅ **Failure & Re-election:**
- Publisher-3 crashes
- Followers detect timeout (~9-10 seconds)
- Publisher-2 automatically becomes new leader
- System stabilizes in 5-10 seconds

✅ **Recovery:**
- Publisher-3 restarts
- Reclaims LEADER role (highest ID)
- Publisher-1 and Publisher-2 revert to FOLLOWER
- Original configuration restored

✅ **Automatic & Self-Healing:**
- No manual intervention required
- Automatic failure detection
- Automatic re-election
- Automatic recovery

---

## Quick Commands Summary

```bash
# Start services
docker-compose up -d

# Open 3 terminals:
docker logs publisher-service-1 -f
docker logs publisher-service-2 -f
docker logs publisher-service-3 -f

# Check election status
curl http://localhost:5003/election/status | python -m json.tool
curl http://localhost:5013/election/status | python -m json.tool
curl http://localhost:5023/election/status | python -m json.tool

# Crash leader
docker stop publisher-service-3

# Restart leader
docker start publisher-service-3
```

---

## Timeline

| Time | Event | What You See |
|------|-------|--------------|
| **0s** | All start | Election begins |
| **~5s** | Election completes | Publisher-3 becomes leader |
| **30s** | Normal operation | Heartbeats every 3s |
| **0s** | Publisher-3 crashes | `docker stop publisher-service-3` |
| **~9s** | Timeout detected | "Leader timeout, starting election" |
| **~10s** | Election starts | "Node publisher-2 starting election" |
| **~12s** | New leader | "Publisher-2 became LEADER" |
| **0s** | Publisher-3 restarts | `docker start publisher-service-3` |
| **~2s** | Re-election | "Node publisher-3 starting election" |
| **~3s** | Leadership reclaimed | "Publisher-3 became LEADER" |
| **~5s** | Original state restored | All followers acknowledge publisher-3 |

---

## Troubleshooting

**Don't see leader election messages?**
- Wait longer (election takes a few seconds)
- Check logs: `docker logs publisher-service-1 | tail -50`

**Publisher-3 doesn't become leader?**
- Check node IDs: publisher-3 should have highest ID
- Verify all services are running: `docker ps | findstr publisher`

**Want to test again?**
```bash
# Stop all publishers
docker stop publisher-service-1 publisher-service-2 publisher-service-3

# Restart all
docker-compose restart publisher-service-1 publisher-service-2 publisher-service-3

# Watch election happen again
```

---

## Complete Demo Flow

**To demonstrate the full scenario:**

1. **Normal Operation:**
   - All 3 publishers start
   - Publisher-3 becomes leader
   - Heartbeats every 3 seconds

2. **Failure & Re-election:**
   - Stop publisher-3
   - Wait 10 seconds
   - Publisher-2 becomes new leader

3. **Recovery:**
   - Start publisher-3
   - Publisher-3 reclaims leadership
   - Original configuration restored

**This shows the complete Bully algorithm in action:**
- Automatic leader election
- Failure detection and re-election
- Self-healing and recovery

---

That's it! Simple steps to demonstrate automatic leader election, failure detection, and self-healing.

