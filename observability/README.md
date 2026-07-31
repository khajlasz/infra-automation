# Observability Stack

This directory contains a local observability stack for the framework.

It provides:

- Prometheus for metrics collection
- Grafana for metrics and log visualisation
- Loki for log storage
- Promtail for log collection

Start the stack from the repository root:

```bash
docker compose -f observability/docker-compose.yml up -d
```

Grafana is available at `http://localhost:3000` with the default credentials
`admin` / `admin`. Prometheus is available at `http://localhost:9090`.

## Log Flow

Framework modules obtain loggers through `observability.get_logger()`. The
shared logger writes console output and appends events to:

```text
observability/logs/infra.log
```

Promtail mounts `observability/logs/` as `/var/log/infra`, sends `*.log`
files to Loki, and Grafana displays them through its provisioned Loki data
source. The provisioned **Application Overview** dashboard includes framework
log and recent-error panels.

Generate loader activity:

```bash
.venv/bin/python -c "import sys; from pathlib import Path; sys.path.insert(0, 'src'); from loader import Loader; Loader().load(Path('models/telecom'))"
```

Generate schema-validation activity:

```bash
.venv/bin/python src/cli.py validate models/telecom
```

To inspect the shared log file directly:

```bash
tail -f observability/logs/infra.log
```
