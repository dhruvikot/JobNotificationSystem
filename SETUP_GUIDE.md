# 🚀 Complete Setup Guide - Distributed Job Events Notifier

**Time Required:** 1-2 hours  
**Experience Level:** Beginner-friendly  
**Cost:** Free (AWS Free Tier)

---

## 📋 Table of Contents

1. [Prerequisites Installation](#step-1-prerequisites-installation)
2. [AWS Account Setup](#step-2-aws-account-setup)
3. [AWS CLI Configuration](#step-3-aws-cli-configuration)
4. [AWS Resources Creation](#step-4-aws-resources-creation)
5. [Local Environment Setup](#step-5-local-environment-setup)
6. [Running the System](#step-6-running-the-system)
7. [Testing](#step-7-testing)
8. [Troubleshooting](#troubleshooting)

---

## STEP 1: Prerequisites Installation

### 1.1 Install Docker Desktop (20 minutes)

**What is Docker?** Container platform that runs all your services.

#### Windows:

1. **Download Docker Desktop:**
   - Go to: https://www.docker.com/products/docker-desktop/
   - Click "Download for Windows"
   - Wait for download (500MB file)

2. **Install:**
   - Double-click `Docker Desktop Installer.exe`
   - Follow installer prompts
   - **Important:** Enable WSL 2 if prompted
   - Click "Install"
   - Wait 5-10 minutes

3. **Verify:**
   - Restart your computer
   - Open Docker Desktop from Start menu
   - Wait for "Docker Desktop is running" message
   - Open PowerShell and run:
     ```powershell
     docker --version
     ```
   - Should show: `Docker version 24.x.x`

#### Mac:

1. Download from https://www.docker.com/products/docker-desktop/
2. Open `.dmg` file
3. Drag Docker to Applications
4. Open Docker from Applications
5. Verify in Terminal: `docker --version`

#### Linux:

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker --version
```

---

### 1.2 Install AWS CLI (10 minutes)

**What is AWS CLI?** Command-line tool to create AWS resources.

#### Windows:

1. **Download:**
   - Go to: https://aws.amazon.com/cli/
   - Click "Download the AWS CLI MSI installer for Windows (64-bit)"
   - Or direct link: https://awscli.amazonaws.com/AWSCLIV2.msi

2. **Install:**
   - Double-click downloaded file
   - Click "Next" → "Next" → "Install"
   - Click "Finish"

3. **Verify:**
   - **Close and reopen PowerShell** (important!)
   - Run:
     ```powershell
     aws --version
     ```
   - Should show: `aws-cli/2.x.x`

#### Mac:

```bash
# Download and install
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# Verify
aws --version
```

#### Linux:

```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Verify
aws --version
```

---

### 1.3 Verify Python & Node.js (Already Installed ✅)

You already have:
- ✅ Python 3.12.10
- ✅ Node.js 22.19.0

No action needed!

---

## STEP 2: AWS Account Setup (15 minutes)

### 2.1 Create AWS Account

1. **Go to:** https://aws.amazon.com/
2. **Click:** "Create an AWS Account" (top right)
3. **Enter:**
   - Email address
   - Password
   - AWS account name (e.g., "My-Student-Account")
4. **Contact Information:**
   - Choose "Personal"
   - Fill in your details
   - Phone number (will be verified)
5. **Payment Information:**
   - Enter credit/debit card
   - **Don't worry:** We'll only use free tier services
   - You won't be charged if you stay in free tier limits
6. **Verify Phone:**
   - Enter code sent via SMS
7. **Choose Plan:**
   - Select **"Basic Support - Free"**
8. **Wait for activation:**
   - Can take 5-10 minutes
   - Check your email for confirmation

### 2.2 Enable Free Tier Services

1. **Log in to AWS Console:** https://console.aws.amazon.com/
2. **Set Region:**
   - Top right corner, click region dropdown
   - Select **"US East (N. Virginia) us-east-1"**
   - This region has best free tier coverage

### 2.3 Create IAM User (Security Best Practice)

**Why?** Don't use root account for daily operations.

1. **Go to IAM:**
   - Search "IAM" in top search bar
   - Click "IAM" service

2. **Create User:**
   - Left sidebar → "Users"
   - Click "Create user"
   - Username: `student-dev-user`
   - Click "Next"

3. **Set Permissions:**
   - Choose "Attach policies directly"
   - Search and select these policies:
     - ✅ `AmazonDynamoDBFullAccess`
     - ✅ `AmazonS3FullAccess`
     - ✅ `AmazonSNSFullAccess`
   - Click "Next"
   - Click "Create user"

4. **Create Access Key:**
   - Click on your new user (`student-dev-user`)
   - Go to "Security credentials" tab
   - Scroll to "Access keys"
   - Click "Create access key"
   - Choose "Command Line Interface (CLI)"
   - Check "I understand..." checkbox
   - Click "Next"
   - Add description: "For distributed systems project"
   - Click "Create access key"

5. **IMPORTANT - Save Credentials:**
   - **Access key ID:** Starts with `AKIA...`
   - **Secret access key:** Long string, only shown once
   - Click "Download .csv file" ← **DO THIS NOW!**
   - Store safely - you'll need these in next step

---

## STEP 3: AWS CLI Configuration (5 minutes)

### 3.1 Configure AWS Credentials

Open PowerShell (or Terminal on Mac/Linux) and run:

```bash
aws configure
```

You'll be prompted for 4 values:

```
AWS Access Key ID [None]: AKIA..................
AWS Secret Access Key [None]: ........................................
Default region name [None]: us-east-1
Default output format [None]: json
```

**Copy values from the CSV file you downloaded!**

### 3.2 Verify Configuration

```bash
# Test credentials
aws sts get-caller-identity
```

Should return:
```json
{
    "UserId": "AIDA...",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/student-dev-user"
}
```

✅ If you see this, AWS CLI is configured correctly!

---

## STEP 4: AWS Resources Creation (10 minutes)

### 4.1 Run Automated Setup Script

We'll use the interactive script I created:

```bash
# Navigate to project directory
cd C:\Users\dhruv\JobNotificationSystem

# Run setup script
bash scripts/setup-aws-interactive.sh
```

**Note for Windows:** If `bash` command doesn't work:
- Install Git Bash: https://git-scm.com/downloads
- OR use the manual commands below

### 4.2 Manual Setup (If Script Fails)

#### Create DynamoDB Tables:

```bash
# Table 1: Users
aws dynamodb create-table \
    --table-name Users \
    --attribute-definitions \
        AttributeName=user_id,AttributeType=S \
        AttributeName=email,AttributeType=S \
    --key-schema AttributeName=user_id,KeyType=HASH \
    --global-secondary-indexes \
        "[{\"IndexName\":\"EmailIndex\",\"KeySchema\":[{\"AttributeName\":\"email\",\"KeyType\":\"HASH\"}],\"Projection\":{\"ProjectionType\":\"ALL\"},\"ProvisionedThroughput\":{\"ReadCapacityUnits\":5,\"WriteCapacityUnits\":5}}]" \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --region us-east-1

# Table 2: Subscriptions
aws dynamodb create-table \
    --table-name Subscriptions \
    --attribute-definitions \
        AttributeName=user_id,AttributeType=S \
        AttributeName=topic,AttributeType=S \
    --key-schema \
        AttributeName=user_id,KeyType=HASH \
        AttributeName=topic,KeyType=RANGE \
    --global-secondary-indexes \
        "[{\"IndexName\":\"TopicIndex\",\"KeySchema\":[{\"AttributeName\":\"topic\",\"KeyType\":\"HASH\"}],\"Projection\":{\"ProjectionType\":\"ALL\"},\"ProvisionedThroughput\":{\"ReadCapacityUnits\":5,\"WriteCapacityUnits\":5}}]" \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --region us-east-1

# Table 3: Events
aws dynamodb create-table \
    --table-name Events \
    --attribute-definitions AttributeName=event_id,AttributeType=S \
    --key-schema AttributeName=event_id,KeyType=HASH \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --region us-east-1

# Table 4: TopicPopularity
aws dynamodb create-table \
    --table-name TopicPopularity \
    --attribute-definitions AttributeName=topic,AttributeType=S \
    --key-schema AttributeName=topic,KeyType=HASH \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --region us-east-1
```

**Wait 1-2 minutes for tables to be created.**

#### Verify Tables:

```bash
aws dynamodb list-tables --region us-east-1
```

Should show:
```json
{
    "TableNames": [
        "Events",
        "Subscriptions",
        "TopicPopularity",
        "Users"
    ]
}
```

#### Create S3 Bucket:

```bash
# Replace XXXX with random numbers
aws s3 mb s3://distributed-events-12345 --region us-east-1
```

**Note:** Bucket names must be globally unique. If you get an error, try a different name.

#### Create SNS Topic:

```bash
aws sns create-topic --name distributed-events-notifications --region us-east-1
```

Copy the ARN from output (looks like: `arn:aws:sns:us-east-1:123456789012:distributed-events-notifications`)

---

## STEP 5: Local Environment Setup (10 minutes)

### 5.1 Create Environment Configuration

Create file `deployment/docker/.env`:

```bash
# Method 1: Create manually
# Open: deployment/docker/.env in text editor

# Method 2: Use PowerShell
New-Item -Path "deployment\docker\.env" -ItemType File -Force
```

Add this content (replace with YOUR values):

```env
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIA..................      # ← YOUR KEY from CSV
AWS_SECRET_ACCESS_KEY=................................  # ← YOUR SECRET from CSV

# JWT Secret (can use this or generate new one)
JWT_SECRET=super-secret-jwt-key-change-this-in-production

# AWS Resources (use YOUR bucket and SNS ARN)
EVENT_MEDIA_BUCKET=distributed-events-12345    # ← YOUR BUCKET NAME
NOTIFICATIONS_SNS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789012:distributed-events-notifications  # ← YOUR SNS ARN

# DynamoDB Tables
USERS_TABLE=Users
SUBSCRIPTIONS_TABLE=Subscriptions
EVENTS_TABLE=Events
TOPIC_POPULARITY_TABLE=TopicPopularity

# RabbitMQ (don't change)
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_EXCHANGE=events.topic

# Service URLs (don't change - Docker internal)
AUTH_SERVICE_URL=http://auth-service:5001
SUBSCRIPTION_SERVICE_URL=http://subscription-service:5002
PUBLISHER_SERVICE_URL=http://publisher-service:5003
DISPATCHER_SERVICE_URL=http://notification-dispatcher:5004
GOSSIP_AGENT_URL=http://gossip-agent:5006

# Flask
FLASK_ENV=development
```

### 5.2 Verify Configuration

```bash
# Check file exists
ls deployment/docker/.env

# View content (verify keys are present)
cat deployment/docker/.env
```

---

## STEP 6: Running the System (10 minutes)

### 6.1 Start Docker Services

```bash
# Navigate to docker compose directory
cd deployment/docker

# Start all services (first time will download images - 5-10 min)
docker-compose up --build
```

**What you'll see:**
- Downloading base images (Python, Node, RabbitMQ)
- Building service images
- Starting containers
- Service logs

**Wait for these messages:**
```
rabbitmq          | Server startup complete
auth-service      | Running on http://0.0.0.0:5001
subscription-...  | Running on http://0.0.0.0:5002
publisher-...     | Running on http://0.0.0.0:5003
notification-...  | Running on http://0.0.0.0:5004
frontend          | Compiled successfully!
```

### 6.2 Verify Services (New Terminal)

Open a **new PowerShell window**:

```bash
# Check all containers are running
docker ps
```

Should show 7 containers running:
- rabbitmq
- auth-service
- subscription-service
- publisher-service
- notification-dispatcher
- gossip-agent
- frontend

### 6.3 Test API Gateway

```bash
curl http://localhost:5000/health
```

Should return:
```json
{
    "status": "healthy",
    "timestamp": 1234567890
}
```

---

## STEP 7: Testing (15 minutes)

### 7.1 Seed Sample Data

Open a **new terminal** (keep docker-compose running):

```bash
# Navigate to project root
cd C:\Users\dhruv\JobNotificationSystem

# Install dependencies
pip install requests

# Run seed script
python scripts/seed-data.py
```

**Expected output:**
```
✅ Seeded 10 sample users
✅ Seeded 25 sample subscriptions
✅ Seeded 15 sample events
```

### 7.2 Test Web Interface

1. **Open Browser:** http://localhost:3000

2. **Login:**
   - Email: `alice@student.com`
   - Password: `password123`

3. **Explore:**
   - View Dashboard
   - Check Subscriptions
   - Browse Events
   - Check Notifications

### 7.3 Test Distributed Algorithms

```bash
# Run distributed features test
python scripts/test-distributed-features.py
```

**Expected output:**
```
Testing Membership Protocol...
✅ MCP Test Passed

Testing Gossip Protocol...
✅ Gossip Test Passed

Testing Leader Election...
✅ Leader Election Test Passed

Testing Publisher-side Filtering...
✅ Filtering Test Passed

Testing Lamport Timestamps...
✅ Timestamp Ordering Test Passed
```

### 7.4 Run Unit Tests

```bash
cd backend
pip install pytest pytest-cov
pytest tests/ -v
```

Should show all tests passing:
```
test_mcp.py ✓✓✓
test_gossip.py ✓✓✓
test_leader_election.py ✓✓✓
test_filtering.py ✓✓✓
test_popularity.py ✓✓✓
test_timestamps.py ✓✓✓
```

---

## 🎉 Success!

If all tests pass, your distributed system is running!

### What You Have:

✅ Distributed publish/subscribe system  
✅ 3 Distributed algorithms (Gossip, Leader Election, Lamport Timestamps)  
✅ Microservices architecture  
✅ AWS integration (DynamoDB, S3, SNS)  
✅ React web interface  
✅ RabbitMQ message broker  
✅ Fault tolerance & scalability  

---

## Troubleshooting

### Docker won't start
- **Problem:** "Docker daemon not running"
- **Solution:** Open Docker Desktop app, wait for it to start

### AWS CLI not recognized
- **Problem:** `'aws' is not recognized`
- **Solution:** Close and reopen PowerShell after installing AWS CLI

### Cannot connect to DynamoDB
- **Problem:** `Unable to locate credentials`
- **Solution:** 
  1. Check `.env` file has AWS keys
  2. Run `aws sts get-caller-identity` to verify credentials

### Port already in use
- **Problem:** `Bind for 0.0.0.0:5000 failed: port is already allocated`
- **Solution:** 
  ```bash
  # Stop existing containers
  docker-compose down
  
  # Restart
  docker-compose up
  ```

### RabbitMQ connection refused
- **Problem:** `[Errno 111] Connection refused`
- **Solution:** Wait 30 seconds for RabbitMQ to fully start

### Frontend shows blank page
- **Problem:** White screen in browser
- **Solution:**
  1. Check browser console for errors
  2. Verify all backend services are running
  3. Try: `docker-compose restart frontend`

---

## Next Steps

### For Demo/Presentation:

1. **Record Video:**
   - Show system running
   - Demo failure scenario (kill a service)
   - Show recovery

2. **Prepare Metrics:**
   ```bash
   # Monitor system
   docker stats
   ```

3. **Test Failure Scenarios:**
   ```bash
   # Kill a service
   docker stop notification-dispatcher
   
   # Watch system recover
   docker logs gossip-agent
   
   # Restart service
   docker start notification-dispatcher
   ```

### For Report:

1. Take screenshots of:
   - AWS Console (DynamoDB tables)
   - Running system (docker ps)
   - Web interface
   - Test results

2. Generate UML diagrams (I can help with this)

3. Document distributed algorithms implementation

---

## Stopping the System

```bash
# Stop all services
cd deployment/docker
docker-compose down

# Stop and remove all data
docker-compose down -v
```

---

## AWS Cleanup (To Avoid Charges)

When project is complete:

```bash
# Delete DynamoDB tables
aws dynamodb delete-table --table-name Users
aws dynamodb delete-table --table-name Subscriptions
aws dynamodb delete-table --table-name Events
aws dynamodb delete-table --table-name TopicPopularity

# Delete S3 bucket
aws s3 rb s3://distributed-events-12345 --force

# Delete SNS topic
aws sns delete-topic --topic-arn arn:aws:sns:us-east-1:123456789012:distributed-events-notifications
```

---

## Need Help?

Common issues and solutions are listed above. If you encounter other problems:

1. Check Docker logs: `docker logs <service-name>`
2. Check service is running: `docker ps`
3. Verify AWS credentials: `aws sts get-caller-identity`

---

**You're all set! 🚀**


