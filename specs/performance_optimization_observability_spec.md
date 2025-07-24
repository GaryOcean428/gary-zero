### Performance Optimization & Observability Specification

#### Target SLIs/SLOs
- **Latency:** 95th percentile response time of API calls should be under 100ms.
- **Availability:** The system should have 99.9% uptime.
- **Error rate:** Less than 0.1% of requests should fail over a rolling 30-day period.

#### Async Patterns
- Utilize asynchronous functions using `async/await` in Python and TypeScript where possible.
- WebSocket connections are managed to support real-time updates.

#### Resource Limits
- **CPU:** Use no more than 75% of available CPU resources to ensure system responsiveness.
- **Memory:** Trigger alerts if memory usage exceeds 80%.

#### Cache Strategy (Redis)
- **Session Storage:** Use Redis for storing session data with a default TTL of 3600 seconds.
- **Caching Layer:** Redis caching for enhanced read performance, using LRU eviction policy.
- **Rate Limiting:** Implement rate limiting using Redis to control API usage.
- **Real-Time Features:** Support WebSocket connections and live updates.
- Environment Variables for Redis specified in `railway.json` and respective spec files.

#### Monitoring Dashboards
- **Metrics Collection:** Utilize existing MetricsCollector and ResourceTracker to gather real-time performance metrics (CPU, Memory, I/O).
- **Alerting:** Alerts triggered if CPU usage exceeds 75% or memory usage exceeds 80%.
- **Logging:** Utilize the unified logging system for performance and error tracking.

#### Log Schema
- **Log Levels and Events:** Define log levels (INFO, WARN, ERROR) and log events using the unified logger.
- **JSON Format:** Logs should be structured in JSON for compatibility with various analytics tools.

#### Metrics Endpoints
- **Health Check:** Endpoint `/health` provides basic application health status.
- **Metrics API:** Expose an endpoint to retrieve performance metrics collected by `MetricsCollector`.

#### Alert Thresholds
- **CPU Usage Alert:** Trigger if CPU usage exceeds 75% for longer than 5 minutes.
- **Memory Usage Alert:** Trigger if memory usage exceeds 80% for more than 5 minutes.
- **I/O Operations:** Alert on high disk IO activity that could indicate a bottleneck.
