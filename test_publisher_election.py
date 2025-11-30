"""
Test script to verify Publisher Leader Election is working
"""
import requests
import time
import json

# Publisher service URLs
PUBLISHERS = {
    'publisher-1': 'http://localhost:5003',
    'publisher-2': 'http://localhost:5013',
    'publisher-3': 'http://localhost:5023'
}

def check_election_status(publisher_name, url):
    """Check election status for a publisher"""
    try:
        response = requests.get(f"{url}/election/status", timeout=2)
        if response.status_code == 200:
            return response.json()
        else:
            return {'error': f'HTTP {response.status_code}'}
    except Exception as e:
        return {'error': str(e)}

def test_election():
    """Test leader election across all publishers"""
    print("=" * 60)
    print("Testing Publisher Leader Election")
    print("=" * 60)
    print()
    
    # Check all publishers
    results = {}
    for name, url in PUBLISHERS.items():
        print(f"Checking {name} at {url}...")
        status = check_election_status(name, url)
        results[name] = status
        
        if 'error' in status:
            print(f"  ❌ Error: {status['error']}")
        else:
            leader_icon = "👑" if status.get('is_leader') else "  "
            print(f"  {leader_icon} Node ID: {status.get('node_id')}")
            print(f"     Is Leader: {status.get('is_leader')}")
            print(f"     Current Leader: {status.get('current_leader')}")
            print(f"     State: {status.get('state')}")
        print()
    
    # Analyze results
    print("=" * 60)
    print("Analysis")
    print("=" * 60)
    
    leaders = [name for name, status in results.items() 
               if status.get('is_leader') == True]
    errors = [name for name, status in results.items() 
              if 'error' in status]
    
    if errors:
        print(f"❌ Errors found: {', '.join(errors)}")
        print("   Check if publishers are running and accessible")
        return False
    
    if len(leaders) == 0:
        print("❌ No leader elected!")
        print("   Possible issues:")
        print("   - Election not initialized")
        print("   - PEER_NODES not configured")
        print("   - Nodes can't communicate")
        return False
    
    if len(leaders) > 1:
        print(f"❌ Multiple leaders detected: {', '.join(leaders)}")
        print("   This should not happen - only one leader should exist")
        return False
    
    leader = leaders[0]
    print(f"✅ Leader: {leader}")
    
    # Check if all nodes agree on leader
    all_agree = all(
        status.get('current_leader') == results[leader].get('node_id')
        for name, status in results.items()
        if 'error' not in status
    )
    
    if all_agree:
        print("✅ All nodes agree on the leader")
    else:
        print("❌ Nodes disagree on leader")
        for name, status in results.items():
            if 'error' not in status:
                print(f"   {name} thinks leader is: {status.get('current_leader')}")
        return False
    
    return True

if __name__ == '__main__':
    print("Waiting 5 seconds for election to stabilize...")
    time.sleep(5)
    print()
    
    success = test_election()
    
    if success:
        print()
        print("✅ Leader election is working correctly!")
    else:
        print()
        print("❌ Leader election has issues. Check the output above.")
    
    exit(0 if success else 1)

