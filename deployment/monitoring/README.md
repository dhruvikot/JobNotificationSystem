# Monitoring & Observability Setup

This directory contains monitoring configuration for the Distributed Job Events Notifier system using Prometheus and Grafana.

## Components

### Prometheus
- **Purpose**: Metrics collection and alerting
- **Port**: 9090
- **Configuration**: `prometheus-config.yml`
- **Alert Rules**: `alert_rules.yml`

### Grafana
- **Purpose**: Metrics visualization
- **Port**: 3000
- **Dashboard**: `grafana-dashboard.json`

### Alert Manager
- **Purpose**: Alert routing and notification
- **Port**: 9093

## Deployment

### 1. Deploy Prometheus

```bash
kubectl create namespace monitoring

kubectl create configmap prometheus-config \
  --from-file=prometheus-config.yml \
  --namespace=monitoring

kubectl create configmap prometheus-rules \
  --from-file=alert_rules.yml \
  --namespace=monitoring

kubectl apply -f prometheus-deployment.yaml
```

### 2. Deploy Grafana

```bash
kubectl apply -f grafana-deployment.yaml

# Import the dashboard
# 1. Access Grafana at http://localhost:3000
# 2. Login (admin/admin)
# 3. Import grafana-dashboard.json
```

### 3. Deploy Alert Manager

```bash
kubectl apply -f alertmanager-deployment.yaml
```

## Metrics Exposed

### Application Metrics

Each service exposes metrics at `/metrics` endpoint:

- **HTTP Metrics**:
  - `http_requests_total` - Total HTTP requests
  - `http_request_duration_seconds` - Request latency
  - `http_requests_in_progress` - Active requests

- **MCP Metrics**:
  - `mcp_nodes_total` - Total nodes in cluster
  - `mcp_nodes_alive` - Alive nodes
  - `mcp_nodes_suspect` - Suspect nodes
  - `mcp_nodes_dead` - Dead nodes
  - `mcp_heartbeats_received_total` - Heartbeats received

- **Gossip Metrics**:
  - `gossip_rounds_total` - Gossip rounds completed
  - `gossip_messages_sent_total` - Messages sent
  - `gossip_messages_received_total` - Messages received
  - `gossip_peers` - Number of peers

- **Leader Election Metrics**:
  - `leader_election_is_leader` - Is this node the leader (0/1)
  - `leader_election_elections_total` - Elections triggered
  - `leader_election_leader_changes_total` - Leader changes

- **Publisher Metrics**:
  - `publisher_events_created_total` - Events created
  - `publisher_events_published_total` - Events published
  - `publisher_filtered_subscribers_count` - Subscribers after filtering
  - `publisher_filtering_duration_seconds` - Filtering time

- **Popularity Metrics**:
  - `topic_popularity_count` - Popularity count per topic
  - `topic_priority` - Priority level per topic

- **Notification Metrics**:
  - `notifications_delivered_total` - Notifications delivered
  - `notification_delivery_failures_total` - Delivery failures
  - `notification_queue_depth` - Queue depth

## Alerts

Key alerts configured:

1. **Service Down**: Service unavailable for > 2 minutes
2. **High Error Rate**: Error rate > 5% for 5 minutes
3. **High Latency**: P95 latency > 1s for 5 minutes
4. **No Leader**: No leader elected for 2 minutes
5. **Gossip Stopped**: No gossip activity for 5 minutes
6. **RabbitMQ Down**: RabbitMQ unavailable
7. **High Memory/CPU**: Resource usage > 80-90%

## Dashboard Panels

The Grafana dashboard includes:

1. **Service Health**: Real-time service status
2. **Request Rate**: Requests per second by service
3. **Error Rate**: Error percentage over time
4. **Latency**: P50, P95, P99 latencies
5. **MCP Membership**: Node states
6. **Gossip Activity**: Gossip rounds and messages
7. **Leader Election**: Current leader
8. **RabbitMQ Queue**: Message queue depth
9. **Topic Popularity**: Most popular topics
10. **Notification Delivery**: Success/failure rates

## Adding Metrics to Services

To add metrics to a Python service:

```python
from prometheus_client import Counter, Histogram, Gauge
from prometheus_client import start_http_server

# Define metrics
requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

# Use metrics
@app.route('/api/endpoint')
def endpoint():
    with request_duration.labels(method='GET', endpoint='/api/endpoint').time():
        # ... your code ...
        requests_total.labels(method='GET', endpoint='/api/endpoint', status=200).inc()
        return response

# Start metrics server
start_http_server(8000)  # Metrics at :8000/metrics
```

## Querying Metrics

Example Prometheus queries:

```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Alive nodes
sum(mcp_nodes_alive)

# Leader count
sum(leader_election_is_leader)
```

## Troubleshooting

### Metrics not appearing

1. Check if service is exposing `/metrics`:
   ```bash
   kubectl port-forward svc/service-name 8000:8000
   curl localhost:8000/metrics
   ```

2. Check Prometheus targets:
   - Access Prometheus UI
   - Go to Status → Targets
   - Verify services are being scraped

3. Check Prometheus logs:
   ```bash
   kubectl logs -n monitoring deployment/prometheus
   ```

### Alerts not firing

1. Check alert rules in Prometheus UI: Status → Rules
2. Verify Alert Manager configuration
3. Check Alert Manager logs

## Production Recommendations

1. **Persistent Storage**: Use PersistentVolumes for Prometheus data
2. **Retention**: Configure appropriate retention period (default 15d)
3. **High Availability**: Deploy Prometheus in HA mode
4. **Remote Storage**: Consider using Thanos or Cortex for long-term storage
5. **Alerting**: Configure AlertManager with proper routing (email, Slack, PagerDuty)
6. **Security**: Enable authentication and TLS
7. **Resource Limits**: Set appropriate CPU/memory limits

## References

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)


