# Publisher Leader Election Bug Fix

## 🐛 Bug Found

There's a **node ID mismatch** in the publisher leader election that prevents it from working correctly.

### The Problem

1. **NODE_ID** in docker-compose.yml: `publisher-1`, `publisher-2`, `publisher-3`
2. **NODE_URL** in docker-compose.yml: `http://publisher-service-1:5003`, etc.
3. **Peer ID extraction** in `app.py` line 797:
   ```python
   peer_id = peer_url.split('//')[1].split(':')[0]
   ```
   This extracts `publisher-service-2` from `http://publisher-service-2:5013`

### Result

The `all_nodes` dictionary ends up with mismatched keys:
```python
{
    'publisher-1': 'http://publisher-service-1:5003',  # ✅ Correct
    'publisher-service-2': 'http://publisher-service-2:5013',  # ❌ Wrong key!
    'publisher-service-3': 'http://publisher-service-3:5023'   # ❌ Wrong key!
}
```

But the actual NODE_ID is `publisher-2`, not `publisher-service-2`!

### Impact

- Leader election can't find peers correctly
- Node comparisons fail (`publisher-2` vs `publisher-service-2`)
- Election may not work or may have inconsistent state

---

## ✅ Fix

Update the peer ID extraction to match the NODE_ID format:

```python
# In backend/publisher_service/app.py, line 797
# OLD:
peer_id = peer_url.split('//')[1].split(':')[0]

# NEW:
hostname = peer_url.split('//')[1].split(':')[0]
# Extract node ID from hostname (remove '-service' if present)
# publisher-service-1 -> publisher-1
peer_id = hostname.replace('-service', '') if '-service' in hostname else hostname
```

Or better yet, use a more robust extraction:

```python
# Extract node ID from hostname
hostname = peer_url.split('//')[1].split(':')[0]
# Convert publisher-service-1 -> publisher-1
if hostname.startswith('publisher-service-'):
    peer_id = hostname.replace('publisher-service-', 'publisher-')
else:
    peer_id = hostname
```

---

## 🔧 Implementation

Let me fix this in the code.

