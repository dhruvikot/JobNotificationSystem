#!/usr/bin/env python3
"""
Seed Script for Distributed Job Events Notifier

This script populates the system with sample data for testing:
- Sample users (students, organizers, admins)
- Sample subscriptions
- Sample events
"""

import os
import sys
import time
import requests
import json

# Configuration
API_BASE_URL = os.getenv('API_URL', 'http://localhost:5000')

print("🌱 Seeding Distributed Job Events Notifier")
print(f"API URL: {API_BASE_URL}\n")

# Sample data
SAMPLE_USERS = [
    {
        "name": "Alice Student",
        "email": "alice@student.com",
        "password": "password123",
        "phone": "+14155551001",
        "role": "student"
    },
    {
        "name": "Bob Developer",
        "email": "bob@student.com",
        "password": "password123",
        "phone": "+14155551002",
        "role": "student"
    },
    {
        "name": "Charlie Organizer",
        "email": "charlie@organizer.com",
        "password": "password123",
        "phone": "+14155551003",
        "role": "organizer"
    },
    {
        "name": "Diana Admin",
        "email": "diana@admin.com",
        "password": "password123",
        "phone": "+14155551004",
        "role": "admin"
    }
]

SAMPLE_EVENTS = [
    {
        "title": "AI/ML Hackathon 2024",
        "description": "Join us for 48 hours of innovation! Build AI-powered applications, compete for prizes, and network with industry professionals.",
        "topic": "hackathon.aiml",
        "start_time": int(time.time()) + 86400 * 7,  # 7 days from now
        "end_time": int(time.time()) + 86400 * 9,    # 9 days from now
        "location": "San Francisco, CA",
        "level": "intermediate"
    },
    {
        "title": "Web Development Workshop",
        "description": "Learn modern web development with React, Node.js, and MongoDB. Hands-on session with experienced developers.",
        "topic": "workshop.technical",
        "start_time": int(time.time()) + 86400 * 3,
        "end_time": int(time.time()) + 86400 * 3 + 14400,  # 4 hours
        "location": "Remote",
        "level": "beginner"
    },
    {
        "title": "Software Engineering Internship - Google",
        "description": "Summer 2024 SWE Internship at Google. Work on real products used by billions. Competitive compensation.",
        "topic": "jobs.internship",
        "start_time": int(time.time()) + 86400 * 30,
        "end_time": int(time.time()) + 86400 * 120,
        "location": "Mountain View, CA",
        "level": "intermediate"
    },
    {
        "title": "Tech Career Fair 2024",
        "description": "Meet recruiters from top tech companies. Bring your resume and be ready to interview on the spot!",
        "topic": "careerfair.tech",
        "start_time": int(time.time()) + 86400 * 14,
        "end_time": int(time.time()) + 86400 * 14 + 28800,  # 8 hours
        "location": "Santa Clara Convention Center",
        "level": ""
    },
    {
        "title": "Blockchain Hackathon",
        "description": "Build decentralized applications on Ethereum, Solana, or Polygon. $50,000 in prizes!",
        "topic": "hackathon.blockchain",
        "start_time": int(time.time()) + 86400 * 21,
        "end_time": int(time.time()) + 86400 * 23,
        "location": "Austin, TX",
        "level": "advanced"
    },
    {
        "title": "Full-Stack Developer Position - Startup",
        "description": "Join our fast-growing startup as a full-stack developer. Work with React, Python, AWS.",
        "topic": "jobs.fulltime",
        "start_time": int(time.time()) + 86400 * 7,
        "end_time": int(time.time()) + 86400 * 60,
        "location": "San Francisco, CA (Hybrid)",
        "level": ""
    }
]

SAMPLE_SUBSCRIPTIONS = {
    "alice@student.com": [
        {"topic": "hackathon.aiml", "channels": ["app", "email"]},
        {"topic": "jobs.internship", "channels": ["app", "email", "sms"]},
        {"topic": "workshop.technical", "channels": ["app"]}
    ],
    "bob@student.com": [
        {"topic": "hackathon.*", "channels": ["app", "email"]},
        {"topic": "careerfair.tech", "channels": ["app", "email"]}
    ]
}


def register_users():
    """Register sample users"""
    print("👥 Registering users...")
    tokens = {}
    
    for user in SAMPLE_USERS:
        try:
            # Register
            response = requests.post(
                f"{API_BASE_URL}/auth/register",
                json=user,
                timeout=10
            )
            
            if response.status_code in [201, 409]:  # 409 = already exists
                # Login to get token
                login_response = requests.post(
                    f"{API_BASE_URL}/auth/login",
                    json={
                        "email": user["email"],
                        "password": user["password"]
                    },
                    timeout=10
                )
                
                if login_response.status_code == 200:
                    data = login_response.json()
                    tokens[user["email"]] = data["token"]
                    print(f"  ✅ {user['name']} ({user['role']})")
                else:
                    print(f"  ❌ Failed to login {user['name']}: {login_response.text}")
            else:
                print(f"  ❌ Failed to register {user['name']}: {response.text}")
        
        except Exception as e:
            print(f"  ❌ Error with {user['name']}: {e}")
    
    return tokens


def create_subscriptions(tokens):
    """Create sample subscriptions"""
    print("\n📬 Creating subscriptions...")
    
    for email, subs in SAMPLE_SUBSCRIPTIONS.items():
        if email not in tokens:
            continue
        
        token = tokens[email]
        headers = {"Authorization": f"Bearer {token}"}
        
        for sub in subs:
            try:
                response = requests.post(
                    f"{API_BASE_URL}/subscriptions",
                    json=sub,
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code in [200, 201]:
                    print(f"  ✅ {email} subscribed to {sub['topic']}")
                else:
                    print(f"  ⚠️  {email} subscription failed: {response.text}")
            
            except Exception as e:
                print(f"  ❌ Error: {e}")


def create_events(tokens):
    """Create and publish sample events"""
    print("\n📅 Creating events...")
    
    # Use organizer token
    organizer_email = "charlie@organizer.com"
    if organizer_email not in tokens:
        print("  ❌ Organizer not found")
        return
    
    token = tokens[organizer_email]
    headers = {"Authorization": f"Bearer {token}"}
    event_ids = []
    
    for event in SAMPLE_EVENTS:
        try:
            # Create event
            response = requests.post(
                f"{API_BASE_URL}/events",
                json=event,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 201:
                data = response.json()
                event_id = data["event_id"]
                event_ids.append(event_id)
                print(f"  ✅ Created: {event['title']}")
            else:
                print(f"  ❌ Failed to create {event['title']}: {response.text}")
        
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    return event_ids


def publish_events(tokens, event_ids):
    """Publish some events to trigger notifications"""
    print("\n📢 Publishing events...")
    
    organizer_email = "charlie@organizer.com"
    if organizer_email not in tokens:
        return
    
    token = tokens[organizer_email]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Publish first 3 events
    for event_id in event_ids[:3]:
        try:
            response = requests.post(
                f"{API_BASE_URL}/events/{event_id}/publish",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ Published event {event_id}")
                print(f"     → {data.get('subscribers_count', 0)} subscribers, priority: {data.get('priority', 'N/A')}")
            else:
                print(f"  ⚠️  Failed to publish {event_id}: {response.text}")
        
        except Exception as e:
            print(f"  ❌ Error: {e}")


def verify_system():
    """Verify system health"""
    print("\n🔍 Verifying system health...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ API Gateway: {data.get('status')}")
            
            services = data.get('services', {})
            for service, status in services.items():
                icon = "✅" if status == "healthy" else "⚠️"
                print(f"  {icon} {service}: {status}")
        else:
            print(f"  ❌ Health check failed: {response.status_code}")
    
    except Exception as e:
        print(f"  ❌ Error: {e}")


def main():
    """Main seeding function"""
    try:
        # 1. Verify system is running
        verify_system()
        
        # 2. Register users
        tokens = register_users()
        
        if not tokens:
            print("\n❌ Failed to register users. Is the system running?")
            sys.exit(1)
        
        # 3. Create subscriptions
        create_subscriptions(tokens)
        
        # 4. Create events
        event_ids = create_events(tokens)
        
        # 5. Publish some events
        if event_ids:
            publish_events(tokens, event_ids)
        
        print("\n✅ Seeding complete!")
        print(f"\n📝 Test credentials:")
        print(f"   Student: alice@student.com / password123")
        print(f"   Organizer: charlie@organizer.com / password123")
        print(f"   Admin: diana@admin.com / password123")
        print(f"\n🌐 Access the app at: http://localhost:3000")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Seeding interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


