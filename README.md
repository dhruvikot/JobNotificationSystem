# Distributed Job Events Notifier

> **🚀 NEW USER? START HERE:** Read [`START_HERE.md`](START_HERE.md) for complete setup instructions!  
> **📋 CHECKLIST:** Follow [`QUICK_START_CHECKLIST.md`](QUICK_START_CHECKLIST.md) step-by-step.

---

A production-grade distributed publish/subscribe notification system built for **COEN 317 – Distributed Systems** course, demonstrating real-world distributed systems concepts including Membership & Coordination Protocol (MCP), Gossip Protocol, Bully Leader Election, Publisher-Side Filtering, Popularity-Based Routing, and **Lamport Logical Clocks**.

## 🎯 Project Overview

This system enables event organizers, companies, and career centers to publish events (hackathons, jobs, career fairs, workshops) while students and professionals receive real-time notifications through multiple channels (web, email, SMS).

### Key Features

- **Distributed Architecture**: Microservices-based system with event-driven communication
- **3 Core Distributed Algorithms**: Gossip Protocol, Bully Leader Election, Lamport Timestamps ✨
- **Multiple Notification Channels**: In-app, email (via AWS SNS), and SMS
- **Intelligent Filtering**: Publisher-side filtering reduces network overhead
- **Priority-Based Routing**: Popular topics receive higher priority
- **Fault Tolerant**: Leader election, gossip protocol, and failure detection
- **Cloud-Native**: Designed for AWS EKS (Kubernetes) with real AWS services integration

### ✨ What's New (November 2025)

- **Lamport Logical Clocks**: Added distributed timestamp ordering for causal consistency
- **Complete Setup Guides**: Step-by-step instructions for first-time AWS users
- **Comprehensive Testing**: 45+ unit tests covering all distributed algorithms
- **Algorithm Documentation**: Detailed design docs with examples and scenarios

## 🏗️ Architecture

### High-Level Architecture

```
┌─────────────┐
│   Frontend  │ (React Web App)
│   (Port 80) │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│  API Gateway     │ (Single Entry Point, JWT Auth)
│   (Port 5000)    │
└────────┬─────────┘
         │
    ┌────┴────┬────────────┬──────────────┐
    │         │            │              │
    ▼         ▼            ▼              ▼
┌────────┐ ┌──────┐ ┌──────────┐ ┌──────────────┐
│  Auth  │ │ Sub  │ │Publisher │ │Notification  │
│Service │ │Service│ │ Service  │ │  Dispatcher  │
│ :5001  │ │ :5002 │ │  :5003   │ │    :5004     │
└────────┘ └──────┘ └─────┬────┘ └───────┬──────┘
                          │               │
                          └───► RabbitMQ ◄┘
                                Topic Exchange
                                  │
                          ┌───────┴────────┐
                          │  Gossip Agent  │
                          │    (:5006)     │
                          │  MCP & Gossip  │
                          └────────────────┘

┌─────────────────────────────────────────────┐
│         AWS Services                         │
│  • DynamoDB (Users, Events, Subscriptions)  │
│  • S3 (Event Media Storage)                 │
│  • SNS (Email/SMS Notifications)            │
└─────────────────────────────────────────────┘
```

### Microservices

1. **API Gateway** (Port 5000)
   - Single public entry point
   - JWT authentication & authorization
   - Request routing to internal services

2. **Auth Service** (Port 5001)
   - User registration & login
   - JWT token generation
   - DynamoDB integration for user storage

3. **Subscription Service** (Port 5002)
   - Manage user topic subscriptions
   - Support for wildcards (*, #)
   - Channel preferences (app, email, SMS)

4. **Publisher Service** (Port 5003)
   - Event CRUD operations
   - **Publisher-side filtering** (key optimization)
   - Publishes to RabbitMQ topic exchange
   - S3 integration for event media

5. **Notification Dispatcher** (Port 5004)
   - Consumes from RabbitMQ
   - Sends notifications via multiple channels
   - **Bully leader election** for coordination
   - Leader performs cleanup & aggregation tasks

6. **Gossip Agent** (Port 5006)
   - **Gossip protocol implementation**
   - **MCP (Membership & Coordination Protocol)**
   - State dissemination across cluster

## 🔧 Distributed Systems Concepts

### 1. Membership & Coordination Protocol (MCP)

**Location**: `backend/libs/mcp/__init__.py`

- Tracks health of all nodes in the system
- Handles JOIN, LEAVE, and HEARTBEAT events
- Failure detection: `alive → suspect → dead` transitions
- Soft-state membership (not persisted)

### 2. Gossip Protocol

**Location**: `backend/libs/gossip/__init__.py`

- **Push-pull gossip** for state dissemination
- Exchanges membership, popularity, and event data
- Eventual consistency through epidemic-style propagation
- Configurable fanout and gossip interval

### 3. Leader Election (Bully Algorithm)

**Location**: `backend/libs/leader_election/__init__.py`

**IMPORTANT NOTE**: This is **application-level** leader election, separate from Kubernetes control plane election. Used for coordinating distributed tasks among notification dispatcher nodes.

- Highest-ID node becomes leader
- Automatic re-election on leader failure
- Leader-only tasks:
  - Periodic cleanup of old notifications
  - Aggregation of popularity metrics to DynamoDB
  - Global health monitoring

### 4. Publisher-Side Filtering

**Location**: `backend/libs/filtering/__init__.py`

Key distributed systems optimization:
- Filters subscribers **before** publishing to RabbitMQ
- Reduces network traffic and processing overhead
- Supports topic matching with wildcards
- Location and level-based filtering

### 5. Popularity-Based Routing

**Location**: `backend/libs/popularity/__init__.py`

- Tracks topic view/subscription counts
- Assigns priority: low/medium/high
- High-priority notifications processed first
- Periodically persisted to DynamoDB by leader

## 🛠️ Technology Stack

### Backend
- **Language**: Python 3.11
- **Framework**: Flask
- **Message Broker**: RabbitMQ (topic exchange)
- **Messaging Protocol**: AMQP

### Frontend
- **Framework**: React 18
- **Routing**: React Router
- **HTTP Client**: Axios

### Cloud & Infrastructure
- **Platform**: AWS EKS (Kubernetes)
- **Database**: AWS DynamoDB
- **Storage**: AWS S3
- **Notifications**: AWS SNS
- **Containerization**: Docker
- **Orchestration**: Kubernetes

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- kubectl (for Kubernetes deployment)
- AWS Account with:
  - DynamoDB access
  - S3 bucket
  - SNS topic
  - EKS cluster (optional, for production)

## 🚀 Getting Started

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/distributed-job-events-notifier.git
cd distributed-job-events-notifier
```

### 2. Set Up AWS Resources

Create DynamoDB tables:

```bash
# Users table
aws dynamodb create-table \
    --table-name Users \
    --attribute-definitions AttributeName=user_id,AttributeType=S AttributeName=email,AttributeType=S \
    --key-schema AttributeName=user_id,KeyType=HASH \
    --global-secondary-indexes "IndexName=EmailIndex,KeySchema=[{AttributeName=email,KeyType=HASH}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5}" \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5

# Subscriptions table
aws dynamodb create-table \
    --table-name Subscriptions \
    --attribute-definitions AttributeName=user_id,AttributeType=S AttributeName=topic,AttributeType=S \
    --key-schema AttributeName=user_id,KeyType=HASH AttributeName=topic,KeyType=RANGE \
    --global-secondary-indexes "IndexName=TopicIndex,KeySchema=[{AttributeName=topic,KeyType=HASH}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5}" \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5

# Events table
aws dynamodb create-table \
    --table-name Events \
    --attribute-definitions AttributeName=event_id,AttributeType=S \
    --key-schema AttributeName=event_id,KeyType=HASH \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5

# TopicPopularity table
aws dynamodb create-table \
    --table-name TopicPopularity \
    --attribute-definitions AttributeName=topic,AttributeType=S \
    --key-schema AttributeName=topic,KeyType=HASH \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
```

### 3. Local Development with Docker Compose

Create `.env` file:

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# JWT Secret
JWT_SECRET=your-very-long-and-secure-secret-key

# AWS Resources
EVENT_MEDIA_BUCKET=your-s3-bucket-name
NOTIFICATIONS_SNS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789:notifications
```

Start all services:

```bash
cd deployment/docker
docker-compose up --build
```

Access the application:
- **Frontend**: http://localhost:3000
- **API Gateway**: http://localhost:5000
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)

### 4. Production Deployment on Kubernetes

See detailed guide: [deployment/k8s/README.md](deployment/k8s/README.md)

Quick start:

```bash
# Build and push images
export REGISTRY="your-ecr-repo"
# ... build commands

# Deploy to K8s
cd deployment/k8s
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secrets.yaml
kubectl apply -f .
```

## 📚 API Documentation

### Authentication

#### Register
```http
POST /auth/register
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "password123",
  "phone": "+1234567890",
  "role": "student"
}
```

#### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "password123"
}

Response:
{
  "success": true,
  "token": "eyJ...",
  "user": {...}
}
```

### Subscriptions

#### Get Available Topics
```http
GET /subscriptions/topics
```

#### Create Subscription
```http
POST /subscriptions
Authorization: Bearer <token>
Content-Type: application/json

{
  "topic": "hackathon.aiml",
  "channels": ["app", "email"],
  "filters": {
    "locations": ["San Francisco", "Remote"],
    "levels": ["beginner", "intermediate"]
  }
}
```

### Events

#### Create Event (Organizer/Admin only)
```http
POST /events
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "AI/ML Hackathon 2024",
  "description": "Join us for 48 hours of coding...",
  "topic": "hackathon.aiml",
  "start_time": 1734567890,
  "location": "San Francisco, CA",
  "level": "beginner"
}
```

#### Publish Event
```http
POST /events/{event_id}/publish
Authorization: Bearer <token>

Response:
{
  "success": true,
  "subscribers_count": 150,
  "priority": "high"
}
```

## 🧪 Testing

### Test User Flow

1. **Register** as a student
2. **Login** to get JWT token
3. **Subscribe** to topics (e.g., `hackathon.aiml`, `jobs.internship`)
4. **Browse events**
5. **Register** as an organizer (separate account)
6. **Create and publish** an event
7. **Check notifications** in the first account

### Test Distributed Features

```bash
# Check MCP membership
curl http://localhost:5006/mcp/membership

# Check gossip statistics
curl http://localhost:5006/gossip/stats

# Check leader election status
curl http://localhost:5004/election/status

# View topic popularity
# (Inspect DynamoDB TopicPopularity table)
```

## 🎓 Distributed Systems Properties Addressed

### 1. Heterogeneity
- Multiple languages/technologies: Python, JavaScript, RabbitMQ, DynamoDB, S3
- Standard protocols: HTTP/REST, AMQP, JSON
- Multi-platform: Web, mobile-ready API

### 2. Openness
- RESTful APIs with clear documentation
- Standard authentication (JWT)
- Extensible microservices architecture

### 3. Security
- JWT-based authentication
- Role-based access control (student, organizer, admin)
- AWS IAM integration for service-level security

### 4. Failure Handling & Fault Tolerance
- Leader election for automatic failover
- Gossip protocol for state recovery
- RabbitMQ message persistence and acknowledgments
- Kubernetes health checks and auto-restart

### 5. Concurrency
- Multiple instances of each service
- Thread-safe data structures in MCP/Gossip
- Optimistic locking in DynamoDB

### 6. Quality of Service (QoS)
- Priority-based message processing
- RabbitMQ delivery guarantees
- At-least-once notification delivery

### 7. Scalability
- Horizontal scaling via Kubernetes HPA
- Stateless services (except RabbitMQ)
- Distributed state via gossip

### 8. Transparency
- **Location**: Clients unaware of service locations
- **Migration**: Pods can move across nodes
- **Replication**: Multiple service instances
- **Concurrency**: Hidden from clients
- **Failure**: Automatic recovery

## 📂 Project Structure

```
distributed-job-events-notifier/
├── backend/
│   ├── libs/
│   │   ├── mcp/              # Membership & Coordination Protocol
│   │   ├── gossip/           # Gossip protocol
│   │   ├── leader_election/  # Bully algorithm
│   │   ├── filtering/        # Publisher-side filtering
│   │   └── popularity/       # Popularity tracking
│   ├── api_gateway/
│   ├── auth_service/
│   ├── subscription_service/
│   ├── publisher_service/
│   ├── notification_dispatcher/
│   ├── gossip_agent/
│   └── requirements.txt
├── frontend/
│   └── web/                  # React application
├── deployment/
│   ├── docker/
│   │   └── docker-compose.yml
│   └── k8s/                  # Kubernetes manifests
│       ├── namespace.yaml
│       ├── configmap.yaml
│       ├── secrets.yaml
│       ├── *.yaml            # Service deployments
│       └── README.md
├── docs/
│   ├── ARCHITECTURE.md
│   └── DESIGN.md
└── README.md
```

## 🤝 Contributing

This is a university project. For academic integrity, please do not copy directly. Use it as a reference for understanding distributed systems concepts.

## 📝 License

This project is for educational purposes as part of COEN 317 - Distributed Systems course.

## 👥 Authors

- **Your Name** - COEN 317 Student

## 🙏 Acknowledgments

- COEN 317 - Distributed Systems course materials
- AWS Documentation
- Flask and React communities
- RabbitMQ tutorials

## 📞 Support

For questions or issues:
- Create an issue in the repository
- Contact: your.email@example.com

---

**Built with ❤️ for COEN 317 - Distributed Systems**

