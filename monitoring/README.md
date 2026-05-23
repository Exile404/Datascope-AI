# Monitoring Stack

Three-layer observability for DataScope AI: **application metrics**, **container metrics**, and **host metrics**, surfaced through Prometheus and Grafana with Alertmanager for incident notification.

## Architecture

```
+----------------------+        +---------------+        +-----------+
|  FastAPI backend     | -----> |  Prometheus   | -----> |  Grafana  |
|  /metrics endpoint   |        |  (TSDB, 15d)  |        |  (2 dash) |
+----------------------+        +-------+-------+        +-----------+
                                        |
            +---------------------------+---------------------------+
            |                                                       |
   +--------v---------+                                  +----------v---------+
   |  cAdvisor        |                                  |  node-exporter     |
   |  (containers)    |                                  |  (host kernel)     |
   +------------------+                                  +--------------------+
                                        |
                                 +------v-------+
                                 | Alertmanager |
                                 | (Gmail SMTP) |
                                 +--------------+
```

The monitoring stack runs in `docker-compose.monitor.yml` on a separate Docker network (`datascope-monitor-net`) so it survives crashes of the production stack and can be torn down independently.

## Services

| Service | Image | Host Port | Purpose |
|---|---|---|---|
| Prometheus | `prom/prometheus:v3.0.1` | 9091 | Time-series database, scraper, alert evaluator |
| Grafana | `grafana/grafana:11.3.1` | 3001 | Dashboards (provisioned), visualisation |
| Alertmanager | `prom/alertmanager:v0.27.0` | 9093 | Alert routing, deduplication, Gmail delivery |
| node-exporter | `prom/node-exporter:v1.8.2` | 9100 | Host kernel metrics (CPU, RAM, disk, network) |
| cAdvisor | `gcr.io/cadvisor/cadvisor:v0.52.1` | 8081 | Container runtime metrics |

## Application instrumentation

The FastAPI backend exposes Prometheus metrics at `GET /metrics` via a custom middleware at `backend/app/middleware/prometheus.py`. The middleware is gated by the `ENABLE_METRICS=true` env var and exposes three metric families:

- `http_requests_total{method, handler, status}` counter
- `http_request_duration_seconds{method, handler}` histogram with LLM-friendly buckets up to 120s
- `http_requests_in_progress{method, handler}` gauge

Route templates are pulled from `request.scope["route"]` to keep cardinality bounded (unmatched paths bucket into a single `unmatched` label rather than exploding the time-series space).

### Why custom middleware?

The community library `prometheus-fastapi-instrumentator` was the obvious choice but pins `starlette<1.0.0`. The backend uses `starlette==1.0.0` (transitive pin from `fastapi==0.136.1`), so no published version of the instrumentator is compatible. Rather than downgrade Starlette and risk other transitive breakage, the middleware was reimplemented against the raw `prometheus-client` SDK in ~120 lines. This kept the dependency tree clean and gave full control over label cardinality and bucket boundaries.

## Dashboards

Two Grafana dashboards are provisioned from `monitoring/grafana/dashboards/`:

- **DataScope AI: Application Metrics** (`/d/datascope-app` (port 3002)): RPS by status, latency percentiles (p50/p95/p99), in-flight requests, error rate, total requests, backend up/down indicator, top routes by RPS.
- **DataScope AI: Infrastructure Metrics** (`/d/datascope-infra`): host CPU/RAM/disk usage gauges, load average, network I/O, memory breakdown, disk I/O.

Both dashboards are loaded automatically at Grafana boot via `monitoring/grafana/provisioning/dashboards/dashboards.yml`. The Prometheus datasource is also auto-provisioned (`monitoring/grafana/provisioning/datasources/prometheus.yml`) so the stack is fully reproducible: a fresh `docker compose up` brings everything online with no manual UI clicks.

## Known limitation: container metrics on Docker 29 + Pop!_OS

cAdvisor scrapes successfully (target is `up` in Prometheus) and exposes cgroup-level CPU, memory, and network metrics for the host's systemd slices. However, per-container Docker enrichment (the `name`, `image`, and `container_label_*` labels that cAdvisor normally injects) is unavailable on this host because:

- Docker 29.1.3 on Pop!_OS defaults to the **`overlayfs`** storage driver (not classic `overlay2`).
- cAdvisor's Docker factory expects `overlay2`-style layer metadata at `/var/lib/docker/image/overlay2/layerdb/mounts/<id>/mount-id`. With `overlayfs`, this path does not exist and the Docker factory registration fails with `Registration of the docker container factory failed`.
- Without Docker registration, cAdvisor falls back to systemd-cgroup discovery, which exposes raw metrics under `id="/system.slice/docker-<hash>.scope"` but cannot map back to container names or image tags.

### Decision

Switching Docker's storage driver to `overlay2` would resolve this, but is destructive: it requires wiping `/var/lib/docker/`, which would delete ~95 GB of image layers, all named volumes (including Jenkins build history, the production backend's SQLite metrics store, and Hyperledger Fabric chaincode state for an unrelated coursework project), and force a full rebuild of every image. The trade-off was not justified for this assignment.

Instead, container observability is provided indirectly through:

1. **Host-level resource accounting** via node-exporter (catches runaway containers via host CPU/RAM/disk pressure)
2. **Application-level health signals** via the custom backend middleware (catches degraded service behaviour even when container metrics would not)
3. **Liveness probes** on the production compose file (Docker's own `healthcheck` directive surfaces container failures to `docker ps`)

This is documented as a deliberate engineering decision rather than an oversight. Tracked upstream: cAdvisor compatibility with Docker's `overlayfs` driver is an open issue in the cAdvisor repository.

## Operations

```bash
# Start monitoring stack
docker compose -f docker-compose.monitor.yml up -d

# Tear down
docker compose -f docker-compose.monitor.yml down

# Hot-reload Prometheus config (after editing prometheus.yml or alerts.yml)
curl -X POST http://localhost:9091/-/reload

# Check scrape target health
curl -s localhost:9091/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health}'

# Default Grafana credentials
# user: admin, password: admin (or set GRAFANA_ADMIN_PASSWORD env var before up)
```

## Storage

Persistent volumes (declared in `docker-compose.monitor.yml`):

- `prometheus-data` TSDB, 15-day retention configured via `--storage.tsdb.retention.time=15d`
- `grafana-data` dashboard state, user preferences (dashboards themselves are file-provisioned and not stored here)
- `alertmanager-data` silence and notification log state