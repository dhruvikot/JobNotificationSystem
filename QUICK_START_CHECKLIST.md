# ✅ Quick Start Checklist

**Follow these steps in order. Check off each one as you complete it.**

---

## Phase 1: Prerequisites (30 minutes)

### Step 1: Install Docker Desktop
- [ ] Go to: https://www.docker.com/products/docker-desktop/
- [ ] Download installer for Windows
- [ ] Run installer
- [ ] Restart computer
- [ ] Open Docker Desktop
- [ ] Wait for "Docker Desktop is running"
- [ ] Test: Open PowerShell and run `docker --version`
- [ ] ✅ Should show: `Docker version 24.x.x`

### Step 2: Install AWS CLI
- [ ] Go to: https://awscli.amazonaws.com/AWSCLIV2.msi
- [ ] Download and run installer
- [ ] Close PowerShell
- [ ] Open new PowerShell
- [ ] Test: Run `aws --version`
- [ ] ✅ Should show: `aws-cli/2.x.x`

---

## Phase 2: AWS Account Setup (20 minutes)

### Step 3: Create AWS Account
- [ ] Go to: https://aws.amazon.com/
- [ ] Click "Create an AWS Account"
- [ ] Enter email and password
- [ ] Fill in personal information
- [ ] Add credit card (won't be charged with free tier)
- [ ] Verify phone number
- [ ] Select "Basic Support - Free"
- [ ] Wait for account activation email

### Step 4: Create IAM User
- [ ] Log in to AWS Console: https://console.aws.amazon.com/
- [ ] Set region to "US East (N. Virginia) us-east-1"
- [ ] Search for "IAM" and open service
- [ ] Click "Users" → "Create user"
- [ ] Username: `student-dev-user`
- [ ] Click "Next"
- [ ] Select "Attach policies directly"
- [ ] Search and check:
  - [ ] `AmazonDynamoDBFullAccess`
  - [ ] `AmazonS3FullAccess`
  - [ ] `AmazonSNSFullAccess`
- [ ] Click "Next" → "Create user"

### Step 5: Generate Access Keys
- [ ] Click on your new user (`student-dev-user`)
- [ ] Go to "Security credentials" tab
- [ ] Scroll to "Access keys"
- [ ] Click "Create access key"
- [ ] Select "Command Line Interface (CLI)"
- [ ] Check "I understand" box
- [ ] Click "Next"
- [ ] Description: "For distributed systems project"
- [ ] Click "Create access key"
- [ ] **IMPORTANT:** Click "Download .csv file"
- [ ] Save the CSV file securely
- [ ] ✅ You now have: Access Key ID and Secret Access Key

---

## Phase 3: Configure AWS CLI (5 minutes)

### Step 6: Configure Credentials
- [ ] Open PowerShell
- [ ] Run: `aws configure`
- [ ] Paste **Access Key ID** from CSV (starts with AKIA...)
- [ ] Paste **Secret Access Key** from CSV
- [ ] Enter region: `us-east-1`
- [ ] Enter output format: `json`

### Step 7: Verify Configuration
- [ ] Run: `aws sts get-caller-identity`
- [ ] ✅ Should show your Account ID and User ARN
- [ ] If error: Check credentials and try again

---

## Phase 4: Create AWS Resources (15 minutes)

### Step 8: Create DynamoDB Tables

Run these commands one by one in PowerShell:

```powershell
# Table 1: Users
aws dynamodb create-table --table-name Users --attribute-definitions AttributeName=user_id,AttributeType=S AttributeName=email,AttributeType=S --key-schema AttributeName=user_id,KeyType=HASH --global-secondary-indexes '[{\"IndexName\":\"EmailIndex\",\"KeySchema\":[{\"AttributeName\":\"email\",\"KeyType\":\"HASH\"}],\"Projection\":{\"ProjectionType\":\"ALL\"},\"ProvisionedThroughput\":{\"ReadCapacityUnits\":5,\"WriteCapacityUnits\":5}}]' --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 --region us-east-1
```

- [ ] ✅ Users table created

```powershell
# Table 2: Subscriptions
aws dynamodb create-table --table-name Subscriptions --attribute-definitions AttributeName=user_id,AttributeType=S AttributeName=topic,AttributeType=S --key-schema AttributeName=user_id,KeyType=HASH AttributeName=topic,KeyType=RANGE --global-secondary-indexes '[{\"IndexName\":\"TopicIndex\",\"KeySchema\":[{\"AttributeName\":\"topic\",\"KeyType\":\"HASH\"}],\"Projection\":{\"ProjectionType\":\"ALL\"},\"ProvisionedThroughput\":{\"ReadCapacityUnits\":5,\"WriteCapacityUnits\":5}}]' --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 --region us-east-1
```

- [ ] ✅ Subscriptions table created

```powershell
# Table 3: Events
aws dynamodb create-table --table-name Events --attribute-definitions AttributeName=event_id,AttributeType=S --key-schema AttributeName=event_id,KeyType=HASH --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 --region us-east-1
```

- [ ] ✅ Events table created

```powershell
# Table 4: TopicPopularity
aws dynamodb create-table --table-name TopicPopularity --attribute-definitions AttributeName=topic,AttributeType=S --key-schema AttributeName=topic,KeyType=HASH --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 --region us-east-1
```

- [ ] ✅ TopicPopularity table created

### Step 9: Verify Tables
- [ ] Run: `aws dynamodb list-tables --region us-east-1`
- [ ] ✅ Should show all 4 tables

### Step 10: Create S3 Bucket
- [ ] Choose a unique bucket name (e.g., `distributed-events-YOURNAME-12345`)
- [ ] Run: `aws s3 mb s3://YOUR-BUCKET-NAME --region us-east-1`
- [ ] ✅ Bucket created
- [ ] **Write down your bucket name:** ____________events-jobs_______________

### Step 11: Create SNS Topic
- [ ] Run: `aws sns create-topic --name distributed-events-notifications --region us-east-1`
- [ ] ✅ Copy the ARN (looks like: `arn:aws:sns:us-east-1:123456789012:...`)
- [ ] **Write down your SNS ARN:** _______{
    "TopicArn": "arn:aws:sns:us-east-1:525858612396:events-notifications"
}____________________

---

## Phase 5: Configure Project (10 minutes)

### Step 12: Create .env File
- [ ] Open project in editor: `C:\Users\dhruv\JobNotificationSystem`
- [ ] Create file: `deployment\docker\.env`
- [ ] Copy content from `SETUP_GUIDE.md` (Section 5.1)
- [ ] Replace these values with YOUR values:
  - [ ] `AWS_ACCESS_KEY_ID=` (from CSV)
  - [ ] `AWS_SECRET_ACCESS_KEY=` (from CSV)
  - [ ] `EVENT_MEDIA_BUCKET=` (your bucket name)
  - [ ] `NOTIFICATIONS_SNS_TOPIC_ARN=` (your SNS ARN)
- [ ] Save file

### Step 13: Verify .env File
- [ ] Run: `cat deployment\docker\.env`
- [ ] Check all values are filled
- [ ] ✅ Configuration complete

---

## Phase 6: Start System (15 minutes)

### Step 14: Start Docker Compose
- [ ] Open PowerShell
- [ ] Run: `cd C:\Users\dhruv\JobNotificationSystem\deployment\docker`
- [ ] Run: `docker-compose up --build`
- [ ] Wait 5-10 minutes for first build
- [ ] ✅ Look for these messages:
  - [ ] `rabbitmq | Server startup complete`
  - [ ] `auth-service | Running on http://0.0.0.0:5001`
  - [ ] `frontend | Compiled successfully!`

### Step 15: Verify Services (New Terminal)
- [ ] Open NEW PowerShell window
- [ ] Run: `docker ps`
- [ ] ✅ Should show 7 running containers

### Step 16: Test API
- [ ] Run: `curl http://localhost:5000/health`
- [ ] ✅ Should return JSON with "status": "healthy"

---

## Phase 7: Load Sample Data (5 minutes)

### Step 17: Seed Database
- [ ] In NEW terminal (keep docker-compose running)
- [ ] Run: `cd C:\Users\dhruv\JobNotificationSystem`
- [ ] Run: `pip install requests`
- [ ] Run: `python scripts\seed-data.py`
- [ ] ✅ Should show:
  - [ ] "✅ Seeded 10 sample users"
  - [ ] "✅ Seeded 25 sample subscriptions"
  - [ ] "✅ Seeded 15 sample events"

---

## Phase 8: Test Everything (15 minutes)

### Step 18: Test Web Interface
- [ ] Open browser: http://localhost:3000
- [ ] Login with:
  - Email: `alice@student.com`
  - Password: `password123`
- [ ] ✅ Should see Dashboard
- [ ] Click "Subscriptions" - see your topics
- [ ] Click "Events" - see event list
- [ ] Click "Notifications" - see notifications

### Step 19: Test Distributed Algorithms
- [ ] Run: `python scripts\test-distributed-features.py`
- [ ] ✅ Should show:
  - [ ] "✅ MCP Test Passed"
  - [ ] "✅ Gossip Test Passed"
  - [ ] "✅ Leader Election Test Passed"
  - [ ] "✅ Filtering Test Passed"

### Step 20: Run Unit Tests
- [ ] Run: `cd backend`
- [ ] Run: `pip install pytest pytest-cov`
- [ ] Run: `pytest tests\ -v`
- [ ] ✅ All tests should pass

---

## 🎉 SUCCESS!

If all checkboxes are checked, your system is fully operational!

### You now have:
✅ Distributed publish/subscribe system running  
✅ 3 Distributed algorithms implemented (Gossip, Leader Election, Lamport Timestamps)  
✅ AWS resources created and integrated  
✅ React web interface working  
✅ All tests passing  

---

## Next Steps for Demo:

### 1. Record Presentation Video
- [ ] Show system running (`docker ps`)
- [ ] Demo web interface
- [ ] Show distributed algorithm logs
- [ ] Demonstrate failure scenario (kill a service, show recovery)

### 2. Prepare Report
- [ ] Take screenshots of running system
- [ ] Document architecture (use UML diagrams in docs/)
- [ ] Explain each distributed algorithm
- [ ] Show test results

### 3. Failure Scenario Demo
```powershell
# Kill a service
docker stop notification-dispatcher

# Show logs of other services handling failure
docker logs gossip-agent

# Restart service
docker start notification-dispatcher

# Verify recovery
docker logs notification-dispatcher
```

---

## To Stop System:

```powershell
# In the terminal running docker-compose
Press Ctrl+C

# Or in new terminal:
cd C:\Users\dhruv\JobNotificationSystem\deployment\docker
docker-compose down
```

---

## Need Help?

Refer to `SETUP_GUIDE.md` for:
- Detailed explanations
- Troubleshooting
- Common errors and solutions

---

**Estimated Total Time:** 2 hours  
**Difficulty:** Medium (Beginner-friendly with guide)  
**Cost:** $0 (AWS Free Tier)

Good luck! 🚀


