.PHONY: help create-cluster delete-cluster build-images load-images deploy clean all install-kind check-kind deploy-infrastructure init-dynamodb

# Variables
CLUSTER_NAME := job-notification-cluster
NAMESPACE := distributed-events
REGISTRY_NAME := kind-registry
REGISTRY_PORT := 5001
IMAGE_TAG := latest

# Image names
API_GATEWAY_IMAGE := api-gateway:$(IMAGE_TAG)
AUTH_SERVICE_IMAGE := auth-service:$(IMAGE_TAG)
SUBSCRIPTION_SERVICE_IMAGE := subscription-service:$(IMAGE_TAG)
PUBLISHER_SERVICE_IMAGE := publisher-service:$(IMAGE_TAG)
NOTIFICATION_DISPATCHER_IMAGE := notification-dispatcher:$(IMAGE_TAG)
GOSSIP_AGENT_IMAGE := gossip-agent:$(IMAGE_TAG)
FRONTEND_IMAGE := frontend:$(IMAGE_TAG)

# Kubernetes manifests directory
K8S_DIR := deployment/k8s

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

check-kind: ## Check if kind is installed
	@which kind > /dev/null || (echo "kind is not installed. Run 'make install-kind' or visit https://kind.sigs.k8s.io/docs/user/quick-start/#installation" && exit 1)

check-docker: ## Check if Docker is running
	@docker info > /dev/null 2>&1 || (echo "ERROR: Docker is not running. Please start Docker Desktop and try again." && exit 1)

install-kind: ## Install kind (macOS)
	@echo "Installing kind..."
	@brew install kind || (echo "Please install Homebrew first: https://brew.sh" && exit 1)

create-cluster: check-kind check-docker ## Create a kind cluster with local registry
	@echo "Creating kind cluster: $(CLUSTER_NAME)"
	@if kind get clusters 2>/dev/null | grep -q $(CLUSTER_NAME); then \
		echo "Cluster $(CLUSTER_NAME) already exists"; \
	else \
		echo "kind: Cluster" > /tmp/kind-config.yaml; \
		echo "apiVersion: kind.x-k8s.io/v1alpha4" >> /tmp/kind-config.yaml; \
		echo "nodes:" >> /tmp/kind-config.yaml; \
		echo "- role: control-plane" >> /tmp/kind-config.yaml; \
		echo "  kubeadmConfigPatches:" >> /tmp/kind-config.yaml; \
		echo "  - |" >> /tmp/kind-config.yaml; \
		echo "    kind: InitConfiguration" >> /tmp/kind-config.yaml; \
		echo "    nodeRegistration:" >> /tmp/kind-config.yaml; \
		echo "      kubeletExtraArgs:" >> /tmp/kind-config.yaml; \
		echo "        node-labels: \"ingress-ready=true\"" >> /tmp/kind-config.yaml; \
		echo "  extraPortMappings:" >> /tmp/kind-config.yaml; \
		echo "  - containerPort: 30000" >> /tmp/kind-config.yaml; \
		echo "    hostPort: 30000" >> /tmp/kind-config.yaml; \
		echo "    protocol: TCP" >> /tmp/kind-config.yaml; \
		echo "  - containerPort: 30001" >> /tmp/kind-config.yaml; \
		echo "    hostPort: 30001" >> /tmp/kind-config.yaml; \
		echo "    protocol: TCP" >> /tmp/kind-config.yaml; \
		echo "  - containerPort: 30002" >> /tmp/kind-config.yaml; \
		echo "    hostPort: 30002" >> /tmp/kind-config.yaml; \
		echo "    protocol: TCP" >> /tmp/kind-config.yaml; \
		echo "- role: worker" >> /tmp/kind-config.yaml; \
		echo "- role: worker" >> /tmp/kind-config.yaml; \
		kind create cluster --name $(CLUSTER_NAME) --config=/tmp/kind-config.yaml; \
		rm -f /tmp/kind-config.yaml; \
		echo "Cluster created successfully"; \
	fi
	@kubectl cluster-info --context kind-$(CLUSTER_NAME)

delete-cluster: check-kind ## Delete the kind cluster
	@echo "Deleting kind cluster: $(CLUSTER_NAME)"
	@kind delete cluster --name $(CLUSTER_NAME)

build-images: check-docker ## Build all Docker images
	@echo "Building Docker images..."
	
	@echo "Building API Gateway..."
	@docker build -t $(API_GATEWAY_IMAGE) -f backend/api_gateway/Dockerfile backend/
	
	@echo "Building Auth Service..."
	@docker build -t $(AUTH_SERVICE_IMAGE) -f backend/auth_service/Dockerfile backend/
	
	@echo "Building Subscription Service..."
	@docker build -t $(SUBSCRIPTION_SERVICE_IMAGE) -f backend/subscription_service/Dockerfile backend/
	
	@echo "Building Publisher Service..."
	@docker build -t $(PUBLISHER_SERVICE_IMAGE) -f backend/publisher_service/Dockerfile backend/
	
	@echo "Building Notification Dispatcher..."
	@docker build -t $(NOTIFICATION_DISPATCHER_IMAGE) -f backend/notification_dispatcher/Dockerfile backend/
	
	@echo "Building Gossip Agent..."
	@docker build -t $(GOSSIP_AGENT_IMAGE) -f backend/gossip_agent/Dockerfile backend/
	
	@echo "Building Frontend..."
	@docker build -t $(FRONTEND_IMAGE) -f frontend/web/Dockerfile frontend/web/
	
	@echo "All images built successfully!"

load-images: check-kind ## Load Docker images into kind cluster
	@echo "Loading images into kind cluster..."
	@kind load docker-image $(API_GATEWAY_IMAGE) --name $(CLUSTER_NAME)
	@kind load docker-image $(AUTH_SERVICE_IMAGE) --name $(CLUSTER_NAME)
	@kind load docker-image $(SUBSCRIPTION_SERVICE_IMAGE) --name $(CLUSTER_NAME)
	@kind load docker-image $(PUBLISHER_SERVICE_IMAGE) --name $(CLUSTER_NAME)
	@kind load docker-image $(NOTIFICATION_DISPATCHER_IMAGE) --name $(CLUSTER_NAME)
	@kind load docker-image $(GOSSIP_AGENT_IMAGE) --name $(CLUSTER_NAME)
	@kind load docker-image $(FRONTEND_IMAGE) --name $(CLUSTER_NAME)
	@echo "All images loaded successfully!"

deploy-infrastructure: ## Deploy RabbitMQ and DynamoDB Local
	@echo "Deploying infrastructure services..."
	
	@echo "Deploying DynamoDB Local..."
	@kubectl apply -f $(K8S_DIR)/dynamodb-local.yaml
	
	@echo "Deploying RabbitMQ..."
	@kubectl apply -f $(K8S_DIR)/rabbitmq-local.yaml
	
	@echo "Deploying Redis..."
	@kubectl apply -f $(K8S_DIR)/redis-local.yaml
	
	@echo "Waiting for infrastructure to be ready..."
	@kubectl wait --for=condition=ready pod -l app=dynamodb-local -n $(NAMESPACE) --timeout=120s
	@kubectl wait --for=condition=ready pod -l app=rabbitmq -n $(NAMESPACE) --timeout=120s
	@kubectl wait --for=condition=ready pod -l app=redis -n $(NAMESPACE) --timeout=120s
	
	@echo "Initializing DynamoDB tables..."
	@kubectl apply -f $(K8S_DIR)/dynamodb-init-job.yaml
	@kubectl wait --for=condition=complete job/dynamodb-init -n $(NAMESPACE) --timeout=120s
	
	@echo "✅ Infrastructure deployed successfully!"

init-dynamodb: ## Initialize DynamoDB Local tables (using Kubernetes Job)
	@echo "Deploying DynamoDB initialization job..."
	@kubectl delete job dynamodb-init -n $(NAMESPACE) --ignore-not-found=true
	@kubectl apply -f $(K8S_DIR)/dynamodb-init-job.yaml
	@echo "Waiting for initialization to complete..."
	@kubectl wait --for=condition=complete job/dynamodb-init -n $(NAMESPACE) --timeout=120s
	@echo "DynamoDB tables initialized successfully!"
	@kubectl logs -n $(NAMESPACE) job/dynamodb-init

deploy: ## Deploy all Kubernetes manifests
	@echo "Deploying to Kubernetes..."
	
	@echo "Creating namespace..."
	@kubectl apply -f $(K8S_DIR)/namespace.yaml
	
	@echo "Creating service account..."
	@kubectl apply -f $(K8S_DIR)/serviceaccount.yaml
	
	@echo "Creating secrets..."
	@kubectl apply -f $(K8S_DIR)/secrets.yaml
	
	@echo "Creating configmap..."
	@kubectl apply -f $(K8S_DIR)/configmap.yaml
	
	@echo "Deploying infrastructure..."
	@$(MAKE) deploy-infrastructure
	
	@echo "Waiting for infrastructure services to be fully ready..."
	@sleep 5
	
	@echo "Deploying Auth Service..."
	@kubectl apply -f $(K8S_DIR)/auth-service.yaml
	
	@echo "Deploying Subscription Service..."
	@kubectl apply -f $(K8S_DIR)/subscription-service.yaml
	
	@echo "Deploying Publisher Service..."
	@kubectl apply -f $(K8S_DIR)/publisher-service.yaml
	
	@echo "Deploying Notification Dispatcher..."
	@kubectl apply -f $(K8S_DIR)/notification-dispatcher.yaml
	
	@echo "Deploying Gossip Agent..."
	@kubectl apply -f $(K8S_DIR)/gossip-agent.yaml
	
	@echo "Deploying API Gateway..."
	@kubectl apply -f $(K8S_DIR)/api-gateway.yaml
	
	@echo "Deploying Frontend..."
	@kubectl apply -f $(K8S_DIR)/frontend.yaml
	
	@echo "All resources deployed successfully!"
	@echo ""
	@echo "Waiting for pods to be ready (excluding completed jobs)..."
	@kubectl wait --for=condition=ready pod -l 'job-name notin (dynamodb-init)' -n $(NAMESPACE) --timeout=300s
	@echo ""
	@echo "✅ All pods are ready!"
	@echo ""
	@kubectl get pods -n $(NAMESPACE)
	@echo ""
	@echo "Deployment complete!"

undeploy: ## Delete all Kubernetes resources
	@echo "Removing all deployments..."
	@kubectl delete -f $(K8S_DIR)/frontend.yaml --ignore-not-found=true
	@kubectl delete -f $(K8S_DIR)/api-gateway.yaml --ignore-not-found=true
	@kubectl delete -f $(K8S_DIR)/gossip-agent.yaml --ignore-not-found=true
	@kubectl delete -f $(K8S_DIR)/notification-dispatcher.yaml --ignore-not-found=true
	@kubectl delete -f $(K8S_DIR)/publisher-service.yaml --ignore-not-found=true
	@kubectl delete -f $(K8S_DIR)/subscription-service.yaml --ignore-not-found=true
	@kubectl delete -f $(K8S_DIR)/auth-service.yaml --ignore-not-found=true
	@kubectl delete -f $(K8S_DIR)/dynamodb-init-job.yaml --ignore-not-found=true
	@kubectl delete -f $(K8S_DIR)/rabbitmq-local.yaml --ignore-not-found=true
	@kubectl delete -f $(K8S_DIR)/dynamodb-local.yaml --ignore-not-found=true
	@kubectl delete -f $(K8S_DIR)/configmap.yaml --ignore-not-found=true
	@kubectl delete -f $(K8S_DIR)/secrets.yaml --ignore-not-found=true
	@kubectl delete -f $(K8S_DIR)/serviceaccount.yaml --ignore-not-found=true
	@kubectl delete -f $(K8S_DIR)/namespace.yaml --ignore-not-found=true
	@echo "All resources removed!"

status: ## Check the status of all resources
	@echo "Checking cluster status..."
	@kubectl cluster-info --context kind-$(CLUSTER_NAME)
	@echo ""
	@echo "Pods status:"
	@kubectl get pods -n $(NAMESPACE)
	@echo ""
	@echo "Services status:"
	@kubectl get services -n $(NAMESPACE)
	@echo ""
	@echo "Deployments status:"
	@kubectl get deployments -n $(NAMESPACE)

logs: ## View logs for all pods
	@echo "Recent logs from all pods:"
	@kubectl logs -n $(NAMESPACE) -l app --tail=50

restart: ## Restart all deployments
	@echo "Restarting all deployments..."
	@kubectl rollout restart deployment -n $(NAMESPACE)
	@echo "Deployments restarted!"

clean: undeploy delete-cluster ## Clean everything (delete cluster and resources)
	@echo "Cleanup complete!"

rebuild: build-images load-images restart ## Rebuild images, load them, and restart deployments
	@echo "Rebuild complete!"

all: create-cluster build-images load-images deploy ## Create cluster, build images, and deploy (complete setup)
	@echo ""
	@echo "=========================================="
	@echo "Setup Complete!"
	@echo "=========================================="
	@echo ""
	@echo "Cluster: $(CLUSTER_NAME)"
	@echo ""
	@echo "To check the status, run:"
	@echo "  make status"
	@echo ""
	@echo "To view logs, run:"
	@echo "  make logs"
	@echo ""
	@echo "To access services, use port-forward:"
	@echo "  kubectl port-forward -n $(NAMESPACE) svc/api-gateway 5000:5000"
	@echo "  kubectl port-forward -n $(NAMESPACE) svc/frontend 3000:80"
	@echo "  kubectl port-forward -n $(NAMESPACE) svc/rabbitmq 15672:15672"
	@echo "  kubectl port-forward -n $(NAMESPACE) svc/dynamodb-local 8000:8000"
	@echo ""
	@echo "Or simply run: make port-forward"
	@echo ""

port-forward: ## Port forward services for local access
	@echo "Port forwarding services..."
	@echo "API Gateway will be available at http://localhost:8080"
	@echo "Frontend will be available at http://localhost:3000"
	@echo "WebSocket will be available at ws://localhost:5004"
	@echo "RabbitMQ Management UI at http://localhost:15672 (guest/guest)"
	@echo ""
	@echo "Starting port forwards in background..."
	@kubectl port-forward -n $(NAMESPACE) svc/api-gateway-service 8080:80 > /dev/null 2>&1 & \
	echo $$! > /tmp/api-gateway-pf.pid; \
	kubectl port-forward -n $(NAMESPACE) svc/frontend-service 3000:80 > /dev/null 2>&1 & \
	echo $$! > /tmp/frontend-pf.pid; \
	kubectl port-forward -n $(NAMESPACE) svc/notification-dispatcher-service 5004:5004 > /dev/null 2>&1 & \
	echo $$! > /tmp/websocket-pf.pid; \
	kubectl port-forward -n $(NAMESPACE) svc/rabbitmq 15672:15672 > /dev/null 2>&1 & \
	echo $$! > /tmp/rabbitmq-pf.pid; \
	sleep 2; \
	echo ""; \
	echo "✅ Port forwards active:"; \
	echo "  - API Gateway:    http://localhost:8080"; \
	echo "  - Frontend:       http://localhost:3000"; \
	echo "  - WebSocket:      ws://localhost:5004"; \
	echo "  - RabbitMQ UI:    http://localhost:15672"; \
	echo ""; \
	echo "To stop all port forwards: make stop-port-forward"; \
	echo "Press Ctrl+C to stop (or let them run in background)"; \
	wait

stop-port-forward: ## Stop all port forwards
	@echo "Stopping port forwards..."
	@kill $$(cat /tmp/api-gateway-pf.pid) 2>/dev/null || true
	@kill $$(cat /tmp/frontend-pf.pid) 2>/dev/null || true
	@kill $$(cat /tmp/websocket-pf.pid) 2>/dev/null || true
	@kill $$(cat /tmp/rabbitmq-pf.pid) 2>/dev/null || true
	@rm -f /tmp/*-pf.pid
	@echo "✅ All port forwards stopped"

shell: ## Open a shell in a pod (usage: make shell POD=<pod-name>)
	@kubectl exec -it -n $(NAMESPACE) $(POD) -- /bin/sh

describe: ## Describe a resource (usage: make describe RESOURCE=<resource-type/name>)
	@kubectl describe -n $(NAMESPACE) $(RESOURCE)

watch: ## Watch pod status in real-time
	@watch kubectl get pods -n $(NAMESPACE)

rabbitmq-ui: ## Open RabbitMQ Management UI in browser
	@echo "Opening RabbitMQ Management UI..."
	@echo "Forwarding port 15672..."
	@kubectl port-forward -n $(NAMESPACE) svc/rabbitmq 15672:15672 > /dev/null 2>&1 & \
	echo $$! > /tmp/rabbitmq-port-forward.pid; \
	sleep 2; \
	open http://localhost:15672 || echo "Please open http://localhost:15672 in your browser (guest/guest)"; \
	echo "Press Ctrl+C to stop port forwarding"; \
	wait

dynamodb-shell: ## Access DynamoDB Local shell
	@echo "Starting AWS CLI for DynamoDB Local..."
	@echo "Port forwarding DynamoDB Local to localhost:8000..."
	@kubectl port-forward -n $(NAMESPACE) svc/dynamodb-local 8000:8000 > /dev/null 2>&1 & \
	echo $$! > /tmp/dynamodb-port-forward.pid; \
	sleep 2; \
	echo ""; \
	echo "DynamoDB Local is now available at http://localhost:8000"; \
	echo "Example commands:"; \
	echo "  aws dynamodb list-tables --endpoint-url http://localhost:8000 --region us-east-1"; \
	echo "  aws dynamodb scan --table-name Users --endpoint-url http://localhost:8000 --region us-east-1"; \
	echo ""; \
	echo "Press Ctrl+C to stop port forwarding"; \
	wait

list-tables: ## List all DynamoDB tables
	@echo "Listing DynamoDB tables..."
	@kubectl port-forward -n $(NAMESPACE) svc/dynamodb-local 8000:8000 > /dev/null 2>&1 & \
	echo $$! > /tmp/dynamodb-port-forward.pid; \
	sleep 2; \
	aws dynamodb list-tables --endpoint-url http://localhost:8000 --region us-east-1 --no-cli-pager; \
	kill $$(cat /tmp/dynamodb-port-forward.pid) 2>/dev/null || true; \
	rm -f /tmp/dynamodb-port-forward.pid

infrastructure-only: create-cluster ## Deploy only infrastructure (RabbitMQ + DynamoDB)
	@echo "Creating namespace..."
	@kubectl apply -f $(K8S_DIR)/namespace.yaml
	
	@echo "Deploying infrastructure..."
	@$(MAKE) deploy-infrastructure
	
	@echo ""
	@echo "=========================================="
	@echo "Infrastructure Setup Complete!"
	@echo "=========================================="
	@echo ""
	@echo "Services deployed:"
	@echo "  - RabbitMQ (AMQP: 5672, Management: 15672)"
	@echo "  - DynamoDB Local (Port: 8000)"
	@echo "  - DynamoDB tables initialized"
	@echo ""
	@echo "Access RabbitMQ UI: make rabbitmq-ui"
	@echo "Access DynamoDB: make dynamodb-shell"
	@echo ""

