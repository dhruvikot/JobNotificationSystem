# How to Verify Publisher Leader Election is Working

## Quick Test

### 1. Check Election Status

Test each publisher instance:

```powershell
# Publisher 1
curl http://localhost:5003/election/status

# Publisher 2
curl http://localhost:5013/election/status

# Publisher 3
curl http://localhost:5023/election/status
```

### Expected Response

```json
{
  "node_id": "publisher-1",
  "is_leader": false,
  "current_leader": "publisher-3",
  "state": "follower"
}
```

### ✅ Success Criteria

1. **Exactly ONE leader**: Only one publisher should have `"is_leader": true`
2. **All agree on leader**: All publishers should have the same `"current_leader"` value
3. **Highest ID is leader**: `publisher-3` should be the leader (highest ID)
4. **State is correct**: Leader has `"state": "leader"`, followers have `"state": "follower"`

---

## Automated Test

Run the test script:

```powershell
python test_publisher_election.py
```

This will:
- Check all 3 publisher instances
- Verify exactly one leader exists
- Verify all nodes agree on the leader
- Report any issues

---

## Check Logs

### Publisher 1 Logs
```powershell
docker logs publisher-service-1 2>&1 | Select-String -Pattern "Election|Leader"
```

### Publisher 2 Logs
```powershell
docker logs publisher-service-2 2>&1 | Select-String -Pattern "Election|Leader"
```

### Publisher 3 Logs
```powershell
docker logs publisher-service-3 2>&1 | Select-String -Pattern "Election|Leader"
```

### Expected Log Output

**Leader (publisher-3):**
```
[Election] Initialized Bully Election for node publisher-3
[Election] Started election monitoring
[Election] Node publisher-3 starting election
[Election] *** Node publisher-3 is now LEADER ***
[Publisher] 🏆 Node publisher-3 became the LEADER
```

**Followers (publisher-1, publisher-2):**
```
[Election] Initialized Bully Election for node publisher-1
[Election] Started election monitoring
[Election] Node publisher-1 starting election
[Election] Sending ELECTION to 2 higher nodes
[Election] Accepted publisher-3 as leader
```

---

## Common Issues

### ❌ Issue: "Election not initialized"

**Cause:** `PEER_NODES` environment variable not set or empty

**Fix:** Check docker-compose.yml has:
```yaml
PEER_NODES: http://publisher-service-2:5013,http://publisher-service-3:5023
```

### ❌ Issue: Multiple leaders

**Cause:** Nodes can't communicate with each other

**Fix:** 
- Check all containers are running: `docker ps`
- Check network connectivity: `docker network inspect docker_distributed-events-net`
- Verify URLs are correct in PEER_NODES

### ❌ Issue: No leader elected

**Cause:** 
- Node ID mismatch (should be fixed now)
- Communication failures
- Election timeout

**Fix:**
- Check logs for errors
- Verify all publishers can reach each other
- Restart containers if needed

### ❌ Issue: Wrong node ID format

**Cause:** The bug we just fixed - peer_id extraction mismatch

**Fix:** Already fixed in the code! The fix converts `publisher-service-1` → `publisher-1`

---

## Test Leader Failover

### 1. Check current leader
```powershell
curl http://localhost:5003/election/status | ConvertFrom-Json | Select-Object current_leader
```

### 2. Stop the leader
```powershell
docker stop publisher-service-3
```

### 3. Wait 10-15 seconds for election

### 4. Check new leader
```powershell
curl http://localhost:5003/election/status | ConvertFrom-Json | Select-Object current_leader
```

**Expected:** `publisher-2` should become the new leader (next highest ID)

### 5. Restart the old leader
```powershell
docker start publisher-service-3
```

**Expected:** After election, `publisher-3` should become leader again (highest ID)

---

## Summary

✅ **Fixed Bug:** Node ID extraction mismatch  
✅ **Test Script:** `test_publisher_election.py`  
✅ **Verification:** Check `/election/status` endpoint on all publishers

The leader election should now work correctly!




