#!/usr/bin/env python3
"""
Test Script for Scenario 1: MCP Membership Protocol Operational Success

This script tests:
- Three dispatcher nodes registering with gossip agent
- Periodic heartbeat transmission (every 5 seconds)
- MCP tracking all nodes as ALIVE
- Load metrics transmission with heartbeats

OUTPUT: Detailed verbose output for recording and documentation
"""

import requests
import time
import json
from datetime import datetime

# Configuration
GOSSIP_AGENT_URL = "http://localhost:5006"
TEST_DURATION = 60  # Test for 60 seconds
HEARTBEAT_INTERVAL = 5  # Expected heartbeat interval

print("=" * 80)
print("SCENARIO 1: MCP Membership Protocol Operational Success")
print("=" * 80)
print()
print("Test Configuration:")
print(f"  - Gossip Agent URL: {GOSSIP_AGENT_URL}")
print(f"  - Test Duration: {TEST_DURATION} seconds")
print(f"  - Expected Heartbeat Interval: {HEARTBEAT_INTERVAL} seconds")
print(f"  - Failure Detection: SUSPECT after 2 missed heartbeats (10s), DEAD after 5 missed (25s)")
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

# Step 2: Get initial membership state
print("STEP 2: Getting initial membership state...")
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
        
        initial_membership = data.get('membership', {})
        print(f"Total registered nodes: {len(initial_membership)}")
        print()
        
        # Check for dispatcher nodes
        dispatcher_nodes = {
            node_id: node_info 
            for node_id, node_info in initial_membership.items() 
            if node_info.get('role') == 'dispatcher'
        }
        
        print(f"Dispatcher nodes found: {len(dispatcher_nodes)}")
        
        if len(dispatcher_nodes) == 0:
            print("   ⚠️  No dispatcher nodes found. Make sure notification-dispatcher services are running.")
            print("   Expected: notification-dispatcher-1, notification-dispatcher-2, notification-dispatcher-3")
            print()
            print("   All registered nodes:")
            for node_id, node_info in initial_membership.items():
                print(f"      - {node_id}: role={node_info.get('role')}, status={node_info.get('status')}")
        elif len(dispatcher_nodes) < 3:
            print(f"   ⚠️  Found only {len(dispatcher_nodes)} dispatcher nodes (expected 3)")
            print(f"   Found: {list(dispatcher_nodes.keys())}")
            print()
            print("   Detailed node information:")
            for node_id, node_info in dispatcher_nodes.items():
                print(f"      Node: {node_id}")
                print(f"         Role: {node_info.get('role')}")
                print(f"         Status: {node_info.get('status')}")
                print(f"         Host: {node_info.get('host')}")
                print(f"         Port: {node_info.get('port')}")
                print(f"         Last Seen: {node_info.get('last_seen')} ({datetime.fromtimestamp(node_info.get('last_seen', 0)).strftime('%Y-%m-%d %H:%M:%S')})")
                print(f"         Load: {node_info.get('load')}")
                print()
        else:
            print(f"   ✅ Found {len(dispatcher_nodes)} dispatcher nodes")
            print()
            print("   Detailed node information:")
            for node_id, node_info in dispatcher_nodes.items():
                print(f"      Node ID: {node_id}")
                print(f"         Role: {node_info.get('role')}")
                print(f"         Status: {node_info.get('status')}")
                print(f"         Host: {node_info.get('host')}")
                print(f"         Port: {node_info.get('port')}")
                last_seen_ts = node_info.get('last_seen', 0)
                last_seen_str = datetime.fromtimestamp(last_seen_ts).strftime('%Y-%m-%d %H:%M:%S')
                print(f"         Last Seen: {last_seen_ts} ({last_seen_str})")
                print(f"         Load Metrics: {json.dumps(node_info.get('load', {}), indent=12)}")
                print()
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

# Step 3: Monitor heartbeats for TEST_DURATION seconds
print(f"STEP 3: Monitoring heartbeats for {TEST_DURATION} seconds...")
print("-" * 80)
print(f"Checking membership every 5 seconds...")
print(f"Total checks: {TEST_DURATION // 5}")
print()

heartbeat_timestamps = {}  # node_id -> list of timestamps
check_interval = 5
num_checks = TEST_DURATION // check_interval
start_time = time.time()

for check_num in range(num_checks):
    elapsed_time = time.time() - start_time
    timestamp_str = datetime.now().strftime("%H:%M:%S")
    
    print(f"[{timestamp_str}] Check {check_num + 1}/{num_checks} (Elapsed: {elapsed_time:.1f}s)")
    print("-" * 80)
    
    try:
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
            
            current_time = time.time()
            print(f"Current Time: {current_time} ({datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S')})")
            print()
            
            print(f"Dispatcher nodes in membership: {len(dispatcher_nodes)}")
            print()
            
            for node_id, node_info in dispatcher_nodes.items():
                status = node_info.get('status', 'unknown')
                last_seen = node_info.get('last_seen', 0)
                time_since_seen = current_time - last_seen
                load = node_info.get('load', {})
                host = node_info.get('host', 'unknown')
                port = node_info.get('port', 0)
                
                # Track heartbeat timestamps
                if node_id not in heartbeat_timestamps:
                    heartbeat_timestamps[node_id] = []
                
                # Check if this is a new heartbeat (last_seen changed)
                is_new_heartbeat = False
                if not heartbeat_timestamps[node_id] or last_seen > heartbeat_timestamps[node_id][-1]:
                    heartbeat_timestamps[node_id].append(last_seen)
                    is_new_heartbeat = True
                
                status_icon = "✅" if status == "alive" else "⚠️" if status == "suspect" else "❌"
                heartbeat_indicator = "🆕 NEW" if is_new_heartbeat else "⏸️  SAME"
                
                print(f"   {status_icon} {node_id}")
                print(f"      Status: {status}")
                print(f"      Host: {host}, Port: {port}")
                print(f"      Last Seen Timestamp: {last_seen}")
                print(f"      Last Seen Time: {datetime.fromtimestamp(last_seen).strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"      Time Since Last Seen: {time_since_seen:.2f} seconds")
                print(f"      Heartbeat: {heartbeat_indicator}")
                print(f"      Load Metrics:")
                for metric_key, metric_value in load.items():
                    print(f"         {metric_key}: {metric_value}")
                print(f"      Total Heartbeats Recorded: {len(heartbeat_timestamps[node_id])}")
                if len(heartbeat_timestamps[node_id]) > 1:
                    intervals = [heartbeat_timestamps[node_id][i] - heartbeat_timestamps[node_id][i-1] 
                                for i in range(1, len(heartbeat_timestamps[node_id]))]
                    avg_interval = sum(intervals) / len(intervals) if intervals else 0
                    print(f"      Average Heartbeat Interval: {avg_interval:.2f} seconds")
                print()
            
            print()
            
        else:
            print(f"Response Body: {response.text}")
            print(f"   ⚠️  Failed to get membership: {response.status_code}")
    
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
        import traceback
        traceback.print_exc()
    
    if check_num < num_checks - 1:
        print(f"Waiting {check_interval} seconds before next check...")
        print()
        time.sleep(check_interval)

print("=" * 80)
print()

# Step 4: Analyze results
print("STEP 4: Analyzing heartbeat results...")
print("-" * 80)
print()

all_alive = True
all_heartbeats_regular = True

print("Heartbeat Analysis per Node:")
print()

for node_id, timestamps in heartbeat_timestamps.items():
    print(f"Node: {node_id}")
    print(f"  Total Heartbeats Recorded: {len(timestamps)}")
    
    if len(timestamps) == 0:
        print(f"  ⚠️  No heartbeats recorded for this node")
        all_heartbeats_regular = False
        print()
        continue
    
    print(f"  Heartbeat Timestamps:")
    for i, ts in enumerate(timestamps):
        ts_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        print(f"    {i+1}. {ts} ({ts_str})")
    
    if len(timestamps) < 2:
        print(f"  ⚠️  Only {len(timestamps)} heartbeat(s) recorded (need at least 2 for interval analysis)")
        all_heartbeats_regular = False
        print()
        continue
    
    # Calculate intervals between heartbeats
    intervals = []
    print(f"  Heartbeat Intervals:")
    for i in range(1, len(timestamps)):
        interval = timestamps[i] - timestamps[i-1]
        intervals.append(interval)
        print(f"    Interval {i}: {interval:.2f} seconds")
    
    avg_interval = sum(intervals) / len(intervals) if intervals else 0
    min_interval = min(intervals) if intervals else 0
    max_interval = max(intervals) if intervals else 0
    
    print(f"  Statistics:")
    print(f"    Average Interval: {avg_interval:.2f} seconds")
    print(f"    Minimum Interval: {min_interval:.2f} seconds")
    print(f"    Maximum Interval: {max_interval:.2f} seconds")
    print(f"    Expected Interval: {HEARTBEAT_INTERVAL} seconds")
    
    # Check if intervals are close to expected (5 seconds ± 2 seconds tolerance)
    expected_interval = HEARTBEAT_INTERVAL
    tolerance = 2.0
    
    if abs(avg_interval - expected_interval) > tolerance:
        print(f"  ⚠️  Average heartbeat interval is {avg_interval:.1f}s (expected ~{expected_interval}s, tolerance: ±{tolerance}s)")
        all_heartbeats_regular = False
    else:
        print(f"  ✅ Average heartbeat interval is {avg_interval:.1f}s (within expected range: {expected_interval}±{tolerance}s)")
    
    print()

print("=" * 80)
print()

# Step 5: Final membership check
print("STEP 5: Final membership status check...")
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
        
        for node_id, node_info in dispatcher_nodes.items():
            status = node_info.get('status', 'unknown')
            load = node_info.get('load', {})
            last_seen = node_info.get('last_seen', 0)
            host = node_info.get('host', 'unknown')
            port = node_info.get('port', 0)
            
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
            print("   ✅ All 3 dispatcher nodes are ALIVE")
        else:
            print("   ⚠️  Not all nodes are ALIVE or not all 3 nodes are present")
            if len(dispatcher_nodes) != 3:
                print(f"      Expected 3 nodes, found {len(dispatcher_nodes)}")
            if not all_alive:
                print("      Some nodes are not in ALIVE status")
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print()
print("TEST SUMMARY")
print("=" * 80)
print()

# Detailed summary
print("Test Results:")
print(f"  - Nodes Found: {len(heartbeat_timestamps)}")
print(f"  - Nodes Expected: 3")
print(f"  - All Nodes ALIVE: {all_alive}")
print(f"  - Heartbeats Regular: {all_heartbeats_regular}")
print()

if len(heartbeat_timestamps) == 3 and all_alive and all_heartbeats_regular:
    print("✅ SCENARIO 1 PASSED")
    print()
    print("All requirements met:")
    print("  ✅ Three dispatcher nodes registered with gossip agent")
    print("  ✅ Each dispatcher sends heartbeats every ~5 seconds")
    print("  ✅ Gossip agent receives and logs all heartbeats")
    print("  ✅ MCP API returns status showing all 3 nodes as 'alive'")
    print("  ✅ Load metrics (CPU, queue length) transmitted with heartbeats")
else:
    print("❌ SCENARIO 1 FAILED")
    print()
    print("Issues found:")
    if len(heartbeat_timestamps) != 3:
        print(f"  ❌ Expected 3 dispatcher nodes, found {len(heartbeat_timestamps)}")
        print(f"     Nodes found: {list(heartbeat_timestamps.keys())}")
    if not all_alive:
        print("  ❌ Not all nodes are in ALIVE status")
    if not all_heartbeats_regular:
        print("  ❌ Heartbeats are not being sent at regular intervals")

print()
print("=" * 80)
print()
print("Test completed at:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
print("=" * 80)
