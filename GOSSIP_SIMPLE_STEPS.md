# Gossip Protocol Demo - Simple Steps

## What You'll See
- 3 gossip agents exchanging state every 5 seconds
- All 3 agents eventually have the same membership information
- State synchronization happening automatically

---

## Step 1: Start Everything

```bash
cd deployment/docker
docker-compose up -d
```

**Wait 30 seconds** for services to start.

---

## Step 2: Open 3 Terminal Windows Side-by-Side

### Terminal 1 - Gossip Agent 1
```bash
docker logs gossip-agent-1 -f
```

### Terminal 2 - Gossip Agent 2
```bash
docker logs gossip-agent-2 -f
```

### Terminal 3 - Gossip Agent 3
```bash
docker logs gossip-agent-3 -f
```

**That's it!** Just watch these 3 terminals.

---

## Step 3: What You'll See

### After 30 seconds, you'll see messages like:

**Terminal 1 (Gossip Agent 1):**
```
[Gossip] [GOSSIP] Gossiping with http://gossip-agent-2:5007
[Gossip] [GOSSIP] Gossiping with http://gossip-agent-3:5008
[Gossip Agent] [GOSSIP] Received gossip exchange from gossip-2
[Gossip Agent] [GOSSIP] Received gossip exchange from gossip-3
```

**Terminal 2 (Gossip Agent 2):**
```
[Gossip] [GOSSIP] Gossiping with http://gossip-agent-1:5006
[Gossip] [GOSSIP] Gossiping with http://gossip-agent-3:5008
[Gossip Agent] [GOSSIP] Received gossip exchange from gossip-1
[Gossip Agent] [GOSSIP] Received gossip exchange from gossip-3
```

**Terminal 3 (Gossip Agent 3):**
```
[Gossip] [GOSSIP] Gossiping with http://gossip-agent-1:5006
[Gossip] [GOSSIP] Gossiping with http://gossip-agent-2:5007
[Gossip Agent] [GOSSIP] Received gossip exchange from gossip-1
[Gossip Agent] [GOSSIP] Received gossip exchange from gossip-2
```

**These messages appear every 5 seconds** - showing gossip exchanges!

---

## Step 4: Verify They Have Same State (Optional)

Open a **4th terminal** and run:

```bash
# Check how many dispatchers each agent knows about
echo "Agent 1 knows:" && curl -s http://localhost:5006/gossip/state | python -m json.tool | grep -c "dispatcher"
echo "Agent 2 knows:" && curl -s http://localhost:5007/gossip/state | python -m json.tool | grep -c "dispatcher"
echo "Agent 3 knows:" && curl -s http://localhost:5008/gossip/state | python -m json.tool | grep -c "dispatcher"
```

**All three should show the same number** (usually 3 dispatchers).

---

## That's It!

### What This Shows:

✅ **3 gossip agents running** - You see all 3 terminals with logs

✅ **Gossip exchanges every 5 seconds** - Messages appear regularly

✅ **State synchronization** - All agents eventually have the same information

✅ **Automatic propagation** - No manual intervention needed

---

## Troubleshooting

**Don't see any messages?**
- Wait 30-60 seconds (gossip happens every 5 seconds)
- Check if services are running: `docker ps | grep gossip-agent`

**Still nothing?**
- Restart: `docker-compose restart gossip-agent-1 gossip-agent-2 gossip-agent-3`

---

## Summary

1. Start services: `docker-compose up -d`
2. Open 3 terminals with `docker logs gossip-agent-X -f`
3. Watch gossip exchanges happen every 5 seconds
4. (Optional) Verify they have same state

**That's all you need!**

