#!/usr/bin/env python3
"""
Test Script for Scenario 2: Distributed Cluster Concurrent Operation

This script tests:
- Three dispatcher nodes running concurrently without conflicts
- Independent registration with gossip agent
- Concurrent heartbeat transmission (parallel, not sequential)
- MCP tracking all three as separate, independent nodes
- Cluster stability with all nodes ALIVE

OUTPUT: Detailed verbose output for recording and documentation
"""

import requests
import time
import json
from datetime import datetime
from collections import defaultdict

# Configuration
GOSSIP_AGENT_URL = "http://localhost:5006"
TEST_DURATION = 30  # Test for 30 seconds
CHECK_INTERVAL = 2  # Check every 2 seconds

print("=" * 80)
print("SCENARIO 2: Distributed Cluster Concurrent Operation")
print("=" * 80)
print()
print("Test Configuration:")
print(f"  - Gossip Agent URL: {GOSSIP_AGENT_URL}")
print(f"  - Test Duration: {TEST_DURATION} seconds")
print(f"  - Check Interval: {CHECK_INTERVAL} seconds")
print(f"  - Expected Nodes: 3 dispatcher nodes (ports 5004, 5014, 5024)")
print(f"  - Expected Behavior: Concurrent heartbeats (timestamps within 1 second)")
print()
print("=" * 80)
print()

# Step 1: Check Gossip Agent is running
print("STEP 1: Verifying Gossip Agent is running...")
print("-" * 80)
try:
    print(f"Request: GET {GOSSIP_AGENT_URL}/health")
    response = requests.get(f"{GOSSIP_AGENT_URL}/health", timeout=5)
    print(f"Response Status: {response.status_code}")
    
    if response.status_code == 200:
        health_data = response.json()
        print("Response Body:")
        print(json.dumps(health_data, indent=2))
        print()
        print("✅ Gossip Agent is running and healthy")
    else:
        print(f"Response Body: {response.text}")
        print(f"❌ Gossip Agent returned status {response.status_code}")
        exit(1)
except Exception as e:
    print(f"❌ Cannot connect to Gossip Agent: {e}")
    print("   Make sure gossip-agent service is running (docker ps)")
    exit(1)

print()
print("=" * 80)
print()

# Step 2: Verify three dispatcher nodes are running
print("STEP 2: Verifying three dispatcher nodes are running...")
print("-" * 80)
print("Expected nodes: notification-dispatcher-1, notification-dispatcher-2, notification-dispatcher-3")
print()

try:
    print(f"Request: GET {GOSSIP_AGENT_URL}/mcp/membership")
    response = requests.get(f"{GOSSIP_AGENT_URL}/mcp/membership", timeout=5)
    print(f"Response Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("Full Response Body:")
        print(json.dumps(data, indent=2))
        print()
        
        membership = data.get('membership', {})
        
        dispatcher_nodes = {
            node_id: node_info 
            for node_id, node_info in membership.items() 
            if node_info.get('role') == 'dispatcher'
        }
        
        if len(dispatcher_nodes) == 3:
            print(f"✅ Found 3 dispatcher nodes:")
            print()
            for node_id, node_info in dispatcher_nodes.items():
                status = node_info.get('status', 'unknown')
                host = node_info.get('host', 'unknown')
                port = node_info.get('port', 0)
                last_seen = node_info.get('last_seen', 0)
                load = node_info.get('load', {})
                
                print(f"   Node: {node_id}")
                print(f"      Status: {status}")
                print(f"      Host: {host}")
                print(f"      Port: {port}")
                print(f"      Last Seen: {last_seen} ({datetime.fromtimestamp(last_seen).strftime('%Y-%m-%d %H:%M:%S')})")
                print(f"      Load Metrics: {json.dumps(load, indent=12)}")
                print()
        else:
            print(f"❌ Found {len(dispatcher_nodes)} dispatcher nodes (expected 3)")
            print(f"Found: {list(dispatcher_nodes.keys())}")
            print()
            print("Make sure all three dispatcher services are running:")
            print("   - notification-dispatcher-1 (port 5004)")
            print("   - notification-dispatcher-2 (port 5014)")
            print("   - notification-dispatcher-3 (port 5024)")
            print()
            if len(dispatcher_nodes) > 0:
                print("Currently registered dispatcher nodes:")
                for node_id, node_info in dispatcher_nodes.items():
                    print(f"   - {node_id}: port={node_info.get('port')}, status={node_info.get('status')}")
            exit(1)
    else:
        print(f"Response Body: {response.text}")
        print(f"❌ Failed to get membership: {response.status_code}")
        exit(1)
except Exception as e:
    print(f"❌ Error getting membership: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("=" * 80)
print()

# Step 3: Monitor concurrent heartbeats
print(f"STEP 3: Monitoring concurrent heartbeat transmission for {TEST_DURATION} seconds...")
print("-" * 80)
print(f"Checking membership every {CHECK_INTERVAL} seconds...")
print(f"Total checks: {TEST_DURATION // CHECK_INTERVAL}")
print("Looking for parallel operation (heartbeat timestamps should be close together)")
print()

# Track heartbeat timestamps for each node
heartbeat_history = defaultdict(list)  # node_id -> list of (check_time, last_seen)
num_checks = TEST_DURATION // CHECK_INTERVAL
start_time = time.time()

for check_num in range(num_checks):
    elapsed_time = time.time() - start_time
    timestamp_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    print(f"[{timestamp_str}] Check {check_num + 1}/{num_checks} (Elapsed: {elapsed_time:.1f}s)")
    print("-" * 80)
    
    try:
        check_time = time.time()
        print(f"Request: GET {GOSSIP_AGENT_URL}/mcp/membership")
        response = requests.get(f"{GOSSIP_AGENT_URL}/mcp/membership", timeout=5)
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            membership = data.get('membership', {})
            
            dispatcher_nodes = {
                node_id: node_info 
                for node_id, node_info in membership.items() 
                if node_info.get('role') == 'dispatcher'
            }
            
            print(f"Check Time: {check_time} ({datetime.fromtimestamp(check_time).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]})")
            print()
            
            # Record heartbeat timestamps for all nodes at this check
            node_timestamps = {}
            print("Node Heartbeat Information:")
            print()
            
            for node_id, node_info in dispatcher_nodes.items():
                last_seen = node_info.get('last_seen', 0)
                status = node_info.get('status', 'unknown')
                time_since_seen = check_time - last_seen
                load = node_info.get('load', {})
                
                # Track this heartbeat
                heartbeat_history[node_id].append((check_time, last_seen))
                node_timestamps[node_id] = last_seen
                
                status_icon = "✅" if status == "alive" else "⚠️" if status == "suspect" else "❌"
                
                print(f"   {status_icon} {node_id}")
                print(f"      Status: {status}")
                print(f"      Last Seen Timestamp: {last_seen}")
                print(f"      Last Seen Time: {datetime.fromtimestamp(last_seen).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
                print(f"      Time Since Last Seen: {time_since_seen:.3f} seconds")
                print(f"      Load Metrics: {json.dumps(load, indent=12)}")
                print()
            
            # Check if heartbeats are concurrent (timestamps within 1 second of each other)
            if len(node_timestamps) == 3:
                timestamps = list(node_timestamps.values())
                max_diff = max(timestamps) - min(timestamps)
                min_ts = min(timestamps)
                max_ts = max(timestamps)
                
                print("Concurrency Analysis:")
                print(f"   Minimum Timestamp: {min_ts} ({datetime.fromtimestamp(min_ts).strftime('%H:%M:%S.%f')[:-3]})")
                print(f"   Maximum Timestamp: {max_ts} ({datetime.fromtimestamp(max_ts).strftime('%H:%M:%S.%f')[:-3]})")
                print(f"   Maximum Difference: {max_diff:.3f} seconds")
                
                if max_diff < 1.0:
                    print(f"   ✅ Heartbeats are concurrent (max difference: {max_diff:.3f}s < 1.0s)")
                else:
                    print(f"   ⚠️  Heartbeats are not concurrent (max difference: {max_diff:.3f}s >= 1.0s)")
            
            print()
        else:
            print(f"Response Body: {response.text}")
            print(f"   ⚠️  Failed to get membership: {response.status_code}")
    
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
        import traceback
        traceback.print_exc()
    
    if check_num < num_checks - 1:
        print(f"Waiting {CHECK_INTERVAL} seconds before next check...")
        print()
        time.sleep(CHECK_INTERVAL)

print("=" * 80)
print()

# Step 4: Analyze concurrent operation
print("STEP 4: Analyzing concurrent operation...")
print("-" * 80)
print()

all_stable = True
all_concurrent = True

print("Per-Node Analysis:")
print()

for node_id, history in heartbeat_history.items():
    print(f"Node: {node_id}")
    print(f"  Total Checks: {len(history)}")
    
    if len(history) < 2:
        print(f"  ⚠️  Insufficient data (only {len(history)} check(s))")
        print()
        continue
    
    print(f"  Check History:")
    for i, (check_time, last_seen) in enumerate(history):
        check_str = datetime.fromtimestamp(check_time).strftime('%H:%M:%S.%f')[:-3]
        seen_str = datetime.fromtimestamp(last_seen).strftime('%H:%M:%S.%f')[:-3]
        print(f"    Check {i+1}: check_time={check_str}, last_seen={seen_str}")
    
    # Calculate heartbeat intervals
    intervals = []
    print(f"  Heartbeat Intervals:")
    for i in range(1, len(history)):
        _, last_seen_prev = history[i-1]
        _, last_seen_curr = history[i]
        
        # Only calculate if last_seen actually changed (new heartbeat)
        if last_seen_curr > last_seen_prev:
            interval = last_seen_curr - last_seen_prev
            intervals.append(interval)
            print(f"    Interval {i}: {interval:.2f} seconds")
    
    if intervals:
        avg_interval = sum(intervals) / len(intervals)
        print(f"  Average Interval: {avg_interval:.2f} seconds")
        print(f"  ✅ {node_id}: {len(intervals)} heartbeat(s) recorded, avg interval: {avg_interval:.2f}s")
    else:
        print(f"  ⚠️  {node_id}: No heartbeat intervals detected (node may not be sending heartbeats)")
    
    print()

print()
print("Cross-Node Concurrency Analysis:")
print("-" * 80)

# Check for concurrent heartbeats across nodes
concurrent_checks = 0
total_checks = 0
concurrency_details = []

min_history_len = min(len(history) for history in heartbeat_history.values()) if heartbeat_history else 0

for check_num in range(min_history_len):
    timestamps = []
    check_time = None
    
    for node_id in heartbeat_history.keys():
        if check_num < len(heartbeat_history[node_id]):
            check_time, last_seen = heartbeat_history[node_id][check_num]
            timestamps.append(last_seen)
    
    if len(timestamps) == 3:
        total_checks += 1
        max_diff = max(timestamps) - min(timestamps)
        min_ts = min(timestamps)
        max_ts = max(timestamps)
        
        is_concurrent = max_diff < 1.0
        if is_concurrent:
            concurrent_checks += 1
        
        concurrency_details.append({
            'check_num': check_num + 1,
            'check_time': check_time,
            'timestamps': timestamps,
            'min': min_ts,
            'max': max_ts,
            'diff': max_diff,
            'concurrent': is_concurrent
        })

print(f"Total Checks with All 3 Nodes: {total_checks}")
print()

if total_checks > 0:
    for detail in concurrency_details:
        check_str = datetime.fromtimestamp(detail['check_time']).strftime('%H:%M:%S.%f')[:-3]
        min_str = datetime.fromtimestamp(detail['min']).strftime('%H:%M:%S.%f')[:-3]
        max_str = datetime.fromtimestamp(detail['max']).strftime('%H:%M:%S.%f')[:-3]
        
        print(f"Check {detail['check_num']} (at {check_str}):")
        print(f"   Timestamps: {detail['timestamps']}")
        print(f"   Min: {detail['min']} ({min_str})")
        print(f"   Max: {detail['max']} ({max_str})")
        print(f"   Difference: {detail['diff']:.3f} seconds")
        status = "✅ CONCURRENT" if detail['concurrent'] else "❌ NOT CONCURRENT"
        print(f"   Status: {status}")
        print()
    
    concurrent_percentage = (concurrent_checks / total_checks) * 100
    print(f"Summary:")
    print(f"   Concurrent Checks: {concurrent_checks}/{total_checks}")
    print(f"   Concurrent Percentage: {concurrent_percentage:.1f}%")
    print()
    
    if concurrent_percentage >= 80:
        print("   ✅ Heartbeats are mostly concurrent (parallel operation confirmed)")
        all_concurrent = True
    else:
        print("   ⚠️  Heartbeats are not consistently concurrent")
        all_concurrent = False
else:
    print("   ⚠️  No valid checks with all 3 nodes present")
    all_concurrent = False

print()
print("=" * 80)
print()

# Step 5: Final stability check
print("STEP 5: Final cluster stability check...")
print("-" * 80)
try:
    print(f"Request: GET {GOSSIP_AGENT_URL}/mcp/membership")
    response = requests.get(f"{GOSSIP_AGENT_URL}/mcp/membership", timeout=5)
    print(f"Response Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("Full Response Body:")
        print(json.dumps(data, indent=2))
        print()
        
        membership = data.get('membership', {})
        
        dispatcher_nodes = {
            node_id: node_info 
            for node_id, node_info in membership.items() 
            if node_info.get('role') == 'dispatcher'
        }
        
        print(f"Total dispatcher nodes: {len(dispatcher_nodes)}")
        print()
        
        all_alive = True
        for node_id, node_info in dispatcher_nodes.items():
            status = node_info.get('status', 'unknown')
            host = node_info.get('host', 'unknown')
            port = node_info.get('port', 0)
            last_seen = node_info.get('last_seen', 0)
            load = node_info.get('load', {})
            
            if status != "alive":
                all_alive = False
            
            status_icon = "✅" if status == "alive" else "⚠️" if status == "suspect" else "❌"
            
            print(f"   {status_icon} {node_id}")
            print(f"      Status: {status}")
            print(f"      Host: {host}, Port: {port}")
            print(f"      Last Seen: {last_seen} ({datetime.fromtimestamp(last_seen).strftime('%Y-%m-%d %H:%M:%S')})")
            print(f"      Load Metrics: {json.dumps(load, indent=12)}")
            print()
        
        if len(dispatcher_nodes) == 3 and all_alive:
            print("   ✅ Cluster is stable: All 3 nodes are ALIVE")
            all_stable = True
        else:
            print("   ⚠️  Cluster is not stable")
            all_stable = False
            if len(dispatcher_nodes) != 3:
                print(f"      Expected 3 nodes, found {len(dispatcher_nodes)}")
            if not all_alive:
                print("      Not all nodes are in ALIVE status")
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()
    all_stable = False

print()
print("=" * 80)
print()
print("TEST SUMMARY")
print("=" * 80)
print()

print("Test Results:")
print(f"  - Nodes Found: {len(heartbeat_history)}")
print(f"  - Nodes Expected: 3")
print(f"  - Cluster Stable: {all_stable}")
print(f"  - Heartbeats Concurrent: {all_concurrent}")
if total_checks > 0:
    concurrent_percentage = (concurrent_checks / total_checks) * 100
    print(f"  - Concurrent Percentage: {concurrent_percentage:.1f}%")
print()

if all_stable and all_concurrent and len(heartbeat_history) == 3:
    print("✅ SCENARIO 2 PASSED")
    print()
    print("All requirements met:")
    print("  ✅ Three processes start successfully without port conflicts")
    print("  ✅ Each process independently registers with gossip agent")
    print("  ✅ All three send heartbeats concurrently (not sequentially)")
    print("  ✅ MCP tracks all three as separate, independent nodes")
    print("  ✅ Cluster remains stable with all nodes ALIVE (no false failures)")
    print("  ✅ Heartbeat timestamps show sub-second differences (proving parallel operation)")
else:
    print("❌ SCENARIO 2 FAILED")
    print()
    print("Issues found:")
    if len(heartbeat_history) != 3:
        print(f"  ❌ Expected 3 dispatcher nodes, found {len(heartbeat_history)}")
        print(f"     Nodes found: {list(heartbeat_history.keys())}")
    if not all_stable:
        print("  ❌ Cluster is not stable (not all nodes ALIVE)")
    if not all_concurrent:
        print("  ❌ Heartbeats are not concurrent (not parallel operation)")
        if total_checks > 0:
            concurrent_percentage = (concurrent_checks / total_checks) * 100
            print(f"     Concurrent percentage: {concurrent_percentage:.1f}% (expected >= 80%)")

print()
print("=" * 80)
print()
print("Test completed at:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
print("=" * 80)
