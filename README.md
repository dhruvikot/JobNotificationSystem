

Job Notification System

A distributed event notification system built with microservices architecture, supporting real-time notifications, publisher-subscriber pattern, and distributed coordination protocols.


Overview
This system provides a distributed platform for event management and notifications with the following features:

- Event creation and publishing by organizers
- Category-based subscriptions by students
- Real-time notifications via WebSocket
- Push notifications (browser desktop notifications)
- Distributed services with leader election
- Membership and coordination protocol (MCP)
- Gossip protocol for state synchronization
- Publisher-side filtering for efficiency

Prerequisites
Before setting up the project, ensure you have the following installed:

1. Docker Desktop (version 20.10 or higher)
   - Download from: https://www.docker.com/products/docker-desktop
   - Ensure Docker Desktop is running

2. Docker Compose (usually included with Docker Desktop)
   - Verify installation: `docker-compose --version`

3. AWS CLI (optional, for AWS services)
   - Required if using AWS DynamoDB, S3, or SNS
   - Download from: https://aws.amazon.com/cli/

4. Git (for cloning the repository)
   - Download from: https://git-scm.com/downloads

5. Web Browser (Chrome, Firefox, Edge, or Safari)
   - For accessing the web application

 Project Setup
Step 1: Start Docker Services
* Navigate to the docker directory and start all services:

```bash
cd deployment/docker
docker-compose up -d
```
* This command will:
-Build all service images
-Start all containers in detached mode
-Set up networking between services
* Wait 30-60 seconds for all services to initialize.

 Step 2: Verify Services are Running
* Check that all containers are running:

```bash
docker ps
```

* You should see containers for:
- api-gateway
- auth-service
- subscription-service
- publisher-service-1, publisher-service-2, publisher-service-3
- notification-dispatcher-1, notification-dispatcher-2, notification-dispatcher-3
- gossip-agent-1, gossip-agent-2, gossip-agent-3
- rabbitmq
- redis
- frontend-web

Running the Project:

 Access the Web Application

1. Open your web browser
2. Navigate to: `http://localhost:3000`
3. You should see the login/register page

 Default Test Accounts

After seeding data, you can use these accounts:

Organizer Account:
- Email: `charlie@organizer.com`
- Password: `password123`

Student Account:
- Email: `alice@student.com`
- Password: `password123`

Admin Account:
- Email: `diana@admin.com`
- Password: `password123`

 Service Endpoints

- Frontend: http://localhost:3000
- API Gateway: http://localhost:5000
- Gossip Agent: http://localhost:5006
- RabbitMQ Management: http://localhost:15672 (guest/guest)

 Testing:

 Basic Functionality Test

# Test 1: User Registration and Login

1. Open browser to `http://localhost:3000`
2. Click "Register"
3. Fill in registration form:
   - Name: Test User
   - Email: test@example.com
   - Password: password123
   - Role: Student
4. Click "Register"
5. You should be redirected to the dashboard
6. Logout and login again with the same credentials

# Test 2: Create and Publish Event (Organizer)

1. Login as organizer: `charlie@organizer.com` / `password123`
2. Click "Create Event"
3. Fill in event details:
   - Title: Test Event
   - Description: This is a test event
   - Category: Select any category
   - Date: Select a future date
   - Location: Test Location
4. Click "Create Event"
5. Find the created event and click "Publish"
6. You should see a success message

# Test 3: Subscribe and Receive Notifications (Student)

1. Open a new browser window (or use incognito mode)
2. Login as student: `alice@student.com` / `password123`
3. Click "Subscriptions"
4. Subscribe to the same category used in the event
5. Allow browser notifications when prompted
6. Go back to organizer window
7. Publish the event again (or create a new one)
8. In the student window:
   - Check "Notifications" page - should show new notification
   - Check desktop - should show push notification popup

# Test 4: Real-Time Notifications

1. Keep the student's notifications page open
2. In organizer window, create and publish a new event
3. The notification should appear immediately in the student window
4. This demonstrates WebSocket real-time delivery

 Service Health Checks

Check if services are responding:

```bash
# API Gateway
curl http://localhost:5000/health

# Gossip Agent
curl http://localhost:5006/health

# Check dispatcher status
curl http://localhost:5004/health
```

 View Service Logs

Monitor service logs for debugging:

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker logs api-gateway -f
docker logs publisher-service-1 -f
docker logs notification-dispatcher-1 -f
docker logs gossip-agent-1 -f
```

 Test Distributed Features

# Test Leader Election (Publishers)

1. Check election status:
   ```bash
   curl http://localhost:5003/election/status | python -m json.tool
   curl http://localhost:5013/election/status | python -m json.tool
   curl http://localhost:5023/election/status | python -m json.tool
   ```
2. One publisher should show `"is_leader": true`
3. Stop the leader: `docker stop publisher-service-3`
4. Wait 10 seconds
5. Check status again - a new leader should be elected

# Test MCP Membership

1. Check membership status:
   ```bash
   curl http://localhost:5006/mcp/membership | python -m json.tool
   ```
2. Should show all dispatcher nodes with status "alive"
3. Stop a dispatcher: `docker stop notification-dispatcher-2`
4. Wait 30 seconds
5. Check membership again - dispatcher-2 should show status "dead"

# Test Gossip Protocol

1. Check gossip state on all agents:
   ```bash
   curl http://localhost:5006/gossip/state | python -m json.tool
   curl http://localhost:5007/gossip/state | python -m json.tool
   curl http://localhost:5008/gossip/state | python -m json.tool
   ```
2. All three should show similar membership data
3. This demonstrates state synchronization via gossip protocol

 Architecture

 Services

- API Gateway: Routes requests to appropriate services
- Auth Service: Handles user authentication and authorization
- Subscription Service: Manages user subscriptions to event categories
- Publisher Service: Creates and publishes events (3 replicas)
- Notification Dispatcher: Delivers notifications via WebSocket (3 replicas)
- Gossip Agent: Manages membership and state synchronization (3 replicas)
- RabbitMQ: Message broker for event distribution
- Redis: Cache for persistent notifications
- Frontend: React web application

 Distributed Features

- Leader Election: Bully algorithm for publisher coordination
- MCP (Membership & Coordination Protocol): Tracks node health and status
- Gossip Protocol: Synchronizes state across gossip agents
- Publisher-Side Filtering: Reduces network traffic by filtering before publishing

 Configuration

 Docker Compose Services

All services are defined in `deployment/docker/docker-compose.yml`. Key configurations:

- Ports: Services are exposed on different ports to avoid conflicts
- Environment Variables: Configured via docker-compose or .env file
- Networking: All services on `distributed-events-net` network
- Volumes: Data persistence for RabbitMQ and Redis

 Environment Variables

Key environment variables (set in docker-compose.yml or .env):

- `AWS_REGION`: AWS region for services
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `JWT_SECRET`: Secret for JWT token signing
- `GOSSIP_AGENT_URL`: URL for gossip agent service
- `RABBITMQ_HOST`: RabbitMQ host address
- `REDIS_HOST`: Redis host address

 Troubleshooting

 Services Not Starting

1. Check Docker is running: `docker ps`
2. Check for port conflicts: `netstat -ano | findstr :5000`
3. View logs: `docker-compose logs`
4. Restart services: `docker-compose restart`

 Cannot Access Frontend

1. Verify frontend container is running: `docker ps | findstr frontend`
2. Check frontend logs: `docker logs frontend-web`
3. Try accessing directly: `http://localhost:3000`

 Notifications Not Working

1. Check browser notification permissions
2. Verify WebSocket connection in browser console (F12)
3. Check dispatcher logs: `docker logs notification-dispatcher-1`
4. Verify subscriptions match event categories

 Database Issues

1. Check if DynamoDB is accessible (if using AWS)
2. Verify AWS credentials are correct
3. Check subscription service logs: `docker logs subscription-service`

 Stopping the Project

To stop all services:

```bash
cd deployment/docker
docker-compose down
```

To stop and remove all data:

```bash
docker-compose down -v
```

 Additional Resources

- Service logs: `docker-compose logs -f [service-name]`
- Container shell access: `docker exec -it [container-name] /bin/sh`
- Network inspection: `docker network inspect distributed-events-net`

 Support

For issues or questions, check the service logs or review the configuration files in the deployment directory.


