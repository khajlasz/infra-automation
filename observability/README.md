# Observability Stack

This directory contains a local observability stack for the reference platform.

It provides:

- Prometheus for metrics collection
- Grafana for metrics and log visualisation
- Loki for log storage
- Promtail for log collection

Start the stack from this directory:

```bash
docker compose up -d
```

Grafana is available at `http://localhost:3000` with the default credentials
`admin` / `admin`. Prometheus is available at `http://localhost:9090`.

The Grafana provisioning and dashboards directories are intentionally empty
until dashboards and data sources are defined for the platform model.
