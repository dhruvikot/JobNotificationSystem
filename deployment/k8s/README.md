# Kubernetes Deployment Guide

This directory contains Kubernetes manifests for deploying the Distributed Job Events Notifier system on AWS EKS.

## Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **kubectl** installed and configured
3. **eksctl** (recommended for EKS cluster creation)
4. **Docker** for building images
5. **AWS Resources**:
   - DynamoDB tables created
   - S3 bucket for event media
   - SNS topic for notifications
   - ECR repositories for Docker images (or another container registry)

## AWS DynamoDB Tables

Create the following tables before deployment:

```bash
# Users table
aws dynamodb create-table \
    --table-name Users \
    --attribute-definitions \
        AttributeName=user_id,AttributeType=S \
        AttributeName=email,AttributeType=S \
    --key-schema \
        AttributeName=user_id,KeyType=HASH \
    --global-secondary-indexes \
        "IndexName=EmailIndex,KeySchema=[{AttributeName=email,KeyType=HASH}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5}" \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5

# Subscriptions table
aws dynamodb create-table \
    --table-name Subscriptions \
    --attribute-definitions \
        AttributeName=user_id,AttributeType=S \
        AttributeName=topic,AttributeType=S \
    --key-schema \
        AttributeName=user_id,KeyType=HASH \
        AttributeName=topic,KeyType=RANGE \
    --global-secondary-indexes \
        "IndexName=TopicIndex,KeySchema=[{AttributeName=topic,KeyType=HASH}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5}" \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5

# Events table
aws dynamodb create-table \
    --table-name Events \
    --attribute-definitions \
        AttributeName=event_id,AttributeType=S \
    --key-schema \
        AttributeName=event_id,KeyType=HASH \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5

# TopicPopularity table
aws dynamodb create-table \
    --table-name TopicPopularity \
    --attribute-definitions \
        AttributeName=topic,AttributeType=S \
    --key-schema \
        AttributeName=topic,KeyType=HASH \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5
```

## Create EKS Cluster

```bash
# Create EKS cluster with eksctl
eksctl create cluster \
    --name distributed-events-cluster \
    --region us-east-1 \
    --nodegroup-name standard-workers \
    --node-type t3.medium \
    --nodes 3 \
    --nodes-min 2 \
    --nodes-max 5 \
    --managed

# Configure kubectl
aws eks update-kubeconfig --region us-east-1 --name distributed-events-cluster
```

## Build and Push Docker Images

```bash
# Set your container registry
export REGISTRY="your-account-id.dkr.ecr.us-east-1.amazonaws.com"

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $REGISTRY

# Build and push all services
cd ../../backend

# API Gateway
docker build -t $REGISTRY/api-gateway:latest -f api_gateway/Dockerfile api_gateway/
docker push $REGISTRY/api-gateway:latest

# Auth Service
docker build -t $REGISTRY/auth-service:latest -f auth_service/Dockerfile auth_service/
docker push $REGISTRY/auth-service:latest

# Subscription Service
docker build -t $REGISTRY/subscription-service:latest -f subscription_service/Dockerfile subscription_service/
docker push $REGISTRY/subscription-service:latest

# Publisher Service
docker build -t $REGISTRY/publisher-service:latest -f publisher_service/Dockerfile publisher_service/
docker push $REGISTRY/publisher-service:latest

# Notification Dispatcher
docker build -t $REGISTRY/notification-dispatcher:latest -f notification_dispatcher/Dockerfile notification_dispatcher/
docker push $REGISTRY/notification-dispatcher:latest

# Gossip Agent
docker build -t $REGISTRY/gossip-agent:latest -f gossip_agent/Dockerfile gossip_agent/
docker push $REGISTRY/gossip-agent:latest

# Frontend
cd ../frontend/web
docker build -t $REGISTRY/frontend-web:latest .
docker push $REGISTRY/frontend-web:latest
```

## Configure Secrets

Edit `secrets.yaml` with your actual values, then apply:

```bash
kubectl apply -f secrets.yaml
```

Or create secrets via kubectl:

```bash
kubectl create secret generic app-secrets \
    --from-literal=JWT_SECRET='your-long-secure-secret' \
    --from-literal=AWS_ACCESS_KEY_ID='your-key' \
    --from-literal=AWS_SECRET_ACCESS_KEY='your-secret' \
    --from-literal=RABBITMQ_PASSWORD='guest' \
    --from-literal=NOTIFICATIONS_SNS_TOPIC_ARN='arn:aws:sns:...' \
    --from-literal=EVENT_MEDIA_BUCKET='your-bucket-name' \
    --namespace=distributed-events
```

## Deploy to Kubernetes

```bash
# Apply manifests in order
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secrets.yaml
kubectl apply -f serviceaccount.yaml
kubectl apply -f rabbitmq.yaml
kubectl apply -f gossip-agent.yaml
kubectl apply -f auth-service.yaml
kubectl apply -f subscription-service.yaml
kubectl apply -f publisher-service.yaml
kubectl apply -f notification-dispatcher.yaml
kubectl apply -f api-gateway.yaml
kubectl apply -f frontend.yaml

# Wait for all pods to be ready
kubectl get pods -n distributed-events -w
```

## Verify Deployment

```bash
# Check all pods
kubectl get pods -n distributed-events

# Check services
kubectl get svc -n distributed-events

# Get frontend and API gateway URLs
kubectl get svc -n distributed-events frontend-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
kubectl get svc -n distributed-events api-gateway-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'

# Check logs
kubectl logs -n distributed-events -l app=notification-dispatcher --tail=100
kubectl logs -n distributed-events -l app=gossip-agent --tail=100
```

## Scaling

```bash
# Manual scaling
kubectl scale deployment notification-dispatcher -n distributed-events --replicas=5

# Check HPA status
kubectl get hpa -n distributed-events
```

## Monitoring

```bash
# Watch pods
kubectl get pods -n distributed-events -w

# Describe pod for events
kubectl describe pod -n distributed-events <pod-name>

# Check leader election status (from any dispatcher pod)
kubectl exec -it -n distributed-events <dispatcher-pod> -- curl localhost:5004/election/status
```

## Cleanup

```bash
# Delete all resources
kubectl delete namespace distributed-events

# Delete EKS cluster
eksctl delete cluster --name distributed-events-cluster --region us-east-1
```

## Architecture Notes

### Distributed Systems Features

1. **Leader Election**: Notification dispatcher pods use Bully algorithm for leader election
2. **Gossip Protocol**: Gossip agents disseminate state across nodes
3. **MCP**: Membership protocol tracks node health
4. **Publisher-Side Filtering**: Reduces network overhead
5. **Popularity-Based Routing**: High-priority topics get preferential treatment

### High Availability

- Multiple replicas for each service
- Horizontal Pod Autoscaling (HPA) based on CPU/memory
- Load balancers for external access
- Persistent storage for RabbitMQ

### Security

- Secrets management via Kubernetes Secrets
- Service accounts with IAM roles (IRSA)
- Network policies (can be added)
- Internal ClusterIP services for backend communication


