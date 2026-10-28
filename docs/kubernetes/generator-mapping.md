# Kubernetes Generator Mapping — Out-Dialer

**Status:** Design contract for incremental implementation
**Target:** `docs/kubernetes/generator-mapping.md`
**Initial scope:** Out-Dialer `portal` Deployment and Service, local UTM/kubeadm lab
**Inputs:** Validated Platform Model + `realizations/out-dialer/local-lab.yaml`

## 1. Architectural boundary

The Platform Model remains deployment-independent. Its objects express logical workloads, application endpoints, and resource requirements. The Deployment Realization selects workloads and configures Kubernetes-specific behavior. The Kubernetes generator projects those inputs into ordinary Kubernetes resources without duplicating authoritative model values.

```text
Platform Model (nodes, deployments, applications, compute profiles,
                platform.external_interfaces.metrics)
                     +
Deployment Realization (kubernetes.namespace, workloads, probes,
                        service type, replica count, image policy,
                        metrics discovery convention)
                     |
                     v
            Validation / reference resolution
                     |
                     v
              Kubernetes Generator
                     |
          +----------+-----------+
          |                      |
          v                      v
  portal-deployment.yaml   portal-service.yaml
```

Do not derive Kubernetes networking from `compute.nodes.*.interfaces` or `external_interfaces.metrics.sourceNetwork` in the initial version. Kubernetes CNI, NetworkPolicy, Ingress, and Prometheus connectivity are separate realization concerns.

## 2. Reference platform facts and changes

The currently running Portal container (`docker/portal/app.py`) listens on **HTTP 8443** and exposes Prometheus metrics at **HTTP 9090** (path `/metrics`). `docker/portal/Dockerfile` does not configure TLS. The existing manually deployed Kubernetes manifests expose those two ports, use `imagePullPolicy: Never`, and configure `/health` HTTP readiness/liveness probes.

Milestone 1 corrects the former `Portal.endpoints.https` / `HTTPS` metadata to `Portal.endpoints.http` / `HTTP`, retaining port **8443** because the application serves HTTP. Do **not** change the Flask server or Kubernetes bootstrap manifests. Future external HTTPS will be terminated by an Ingress/Gateway with HTTP forwarded to the Service on 8443. The separately modeled `Authentication.https` endpoint is not part of this correction.

The existing `portal` deployment references both `Portal` and `Authentication`. The Kubernetes realization must explicitly select `Portal.http` for the main port. It must not implicitly expose every endpoint of every application listed under a deployment (in particular, do not expose `Authentication.https:8444`).

## 3. Compute profile resource policy

Compute profiles are shared logical **capacity budgets**, including operating-system and supporting-service overhead. CPU is in cores; RAM is in MiB. A profile is neither a Kubernetes worker specification nor a per-replica request. Existing compute nodes retain their profile relationships for other realizations.

Kubernetes workloads bind `computeProfile` directly in the realization. Sizing bypasses `compute.nodes`: application scheduling and replicas are independent of logical compute-node placement. No specific physical node's CPU or RAM is reserved by this binding.

The fixed v1 lab convention allocates 25% to OS/supporting services, 25% to headroom, and 50% to the application:

```text
application_budget = profile_capacity × 0.50
request_per_replica = application_budget / replicas
cpu_millicores = floor(cpu_cores × 1000 / (2 × replicas))
memory_MiB = floor(ram_MiB / (2 × replicas))
```

| Profile | Capacity | 1 replica | 2 replicas |
|---|---|---|---|
| small | 1 CPU / 1024 MiB | 500m / 512 MiB | 250m / 256 MiB |
| medium | 2 CPU / 2048 MiB | 1000m / 1024 MiB | 500m / 512 MiB |
| large | 4 CPU / 4096 MiB | 2000m / 2048 MiB | 1000m / 1024 MiB |

Use exact rational arithmetic from decimal model CPU values; round down independently to whole millicores and MiB. Emit strings such as `1000m` and `1024Mi`. For small with three replicas, each request is `166m` / `170Mi`. Reject nonpositive/noninteger replica counts (including booleans), missing or unknown profile bindings, nonpositive/nonfinite CPU, nonpositive/noninteger RAM, or requests rounding below `1m` / `1Mi`.

The logical total application budget stays fixed as replicas change. Flooring can leave a small unused remainder (less than one unit per replica); the aggregate emitted requests never exceed 50% of capacity. Do not round up or allocate unequal requests to replicas.

Only `containers[].resources.requests` is populated; no automatic CPU or memory limits. These percentages are a lab modeling convention, not actual Kubernetes node reservations, kubelet settings or scheduler guarantees. Verify usage and cluster headroom operationally. The policy is fixed outside the Platform Model; no second profile registry is introduced. Docker Compose and RouterOS do not consume profile resource values.

## 4. Kubernetes realization section

Append to the **existing** `realizations/out-dialer/local-lab.yaml`, retaining the existing `name`, `docker` and `routeros` sections unchanged:

```yaml
kubernetes:
  namespace: out-dialer

  workloads:
    portal:
      application: Portal
      deployment: portal
      computeProfile: small
      replicas: 2
      imagePullPolicy: Never

      endpoints:
        http:
          application: Portal
          endpoint: http

      service:
        type: ClusterIP

      probes:
        readiness:
          path: /health
          port: http
          initialDelaySeconds: 3
          periodSeconds: 5

        liveness:
          path: /health
          port: http
          initialDelaySeconds: 10
          periodSeconds: 10

  observability:
    metrics:
      externalInterface: metrics
      discovery: prometheus-annotations
```

Each key under `kubernetes.workloads` is a stable Kubernetes workload name, independent of `compute.nodes`. There is no `node` field. `application` selects one application installed by the explicitly referenced `deployment`; the deployment supplies `product` (image). `computeProfile` directly references the shared capacity budget. Portal's deployment also lists Authentication, but that application is not selected or generated. The `endpoints` binding selects which ordinary application endpoints are exported. Distinct selected endpoints must resolve to distinct numeric container ports within each workload, regardless of protocol. Health probe `port` references that named selected port; it is not an arbitrary numeric literal.

`observability.metrics.externalInterface` selects the **existing** `platform.external_interfaces.metrics` definition. Metrics endpoint identities and ports are not redefined in the realization. `discovery` enables the optional Prometheus-style Service annotation convention. This configures discovery metadata only, not Prometheus deployment, scrape configuration, firewall/routing, or ServiceMonitor.

## 5. Application endpoint metadata

The Platform Model already defines metric endpoints on applications and the `platform.external_interfaces.metrics` target list. Add an optional deployment-independent `path` attribute under application endpoint metadata, validated as a path beginning with `/`.

For currently implemented metrics producers, define `/metrics` on the `metrics` endpoint (Portal, CampaignManager and CallSimulator). This avoids hard-coding the metrics URL path inside the generator. The initial generator only materializes Portal. Authentication's separately modeled endpoints are not part of the Portal endpoint selection.

Example Portal definition:

```yaml
Portal:
  description: User-facing REST API for campaign management.
  endpoints:
    http:
      protocol: HTTP
      port: 8443
    metrics:
      protocol: HTTP
      port: 9090
      path: /metrics
```

## 6. Kubernetes resource mapping

| Kubernetes resource path | Source | Rule |
|---|---|---|
| Deployment/Service `metadata.name` | `kubernetes.workloads.<name>` | Stable workload name (`portal`) |
| `metadata.namespace` | `kubernetes.namespace` | Copy (`out-dialer`) |
| Labels: `app`, `app.kubernetes.io/part-of` | Workload name, `platform.platform.id` | `portal`, `out-dialer` |
| Deployment `spec.replicas` | `workloads.portal.replicas` | Copy; current prototype `2` |
| `spec.selector.matchLabels`, Pod labels | Workload name | Consistent `app: portal` |
| Container `name` | Workload name | `portal` |
| Container `image` | Workload `deployment` → `product` | Reuse image naming convention: `out-dialer/portal:0.1` |
| `imagePullPolicy` | Realization workload | `Never` for preloaded-image lab |
| `resources.requests.cpu` | Workload `computeProfile` → `cpu` | Floor 50% capacity / replicas to millicores |
| `resources.requests.memory` | Workload `computeProfile` → `ram` | Floor 50% capacity / replicas to MiB |
| Main `containerPort` | Realization selected application endpoint → model port | `http: 8443`, `protocol: TCP` |
| Metrics `containerPort` | External metrics interface target → model endpoint | `metrics: 9090`, `protocol: TCP`; deduplicate |
| HTTP readiness/liveness probes | Realization `probes` | `/health` on named port `http`; scheme HTTP for HTTP endpoint |
| Service `spec.type` | `workloads.portal.service.type` | `ClusterIP` |
| Service selector | Workload name | `app: portal` |
| Main Service port | Selected application endpoint | `port: 8443`, `targetPort: http`, TCP |
| Metrics Service port | External metrics interface target | `port: 9090`, `targetPort: metrics`, TCP |
| Service scrape annotations | Discovery convention + model metrics endpoint | See below |

Protocol mapping: application-level `HTTP`/`HTTPS` implies transport `TCP` for Kubernetes container and Service port definitions. Protocol-aware HTTP probes should use the selected application endpoint's actual HTTP/HTTPS protocol. Do not assume `8443` means HTTPS. Unknown protocols must not silently default to TCP without a validated mapping.

### Metrics selection

For a workload, resolve its explicitly selected `application` and `deployment`, without traversing compute nodes. Inspect `platform.external_interfaces[externalInterface].targets`; a matching metrics target must reference the selected application and a valid `metrics` endpoint under that application. For Portal, the authoritative target is `Portal.metrics`; it resolves to TCP port 9090 and HTTP path `/metrics`.

Do not use the entire `external_interfaces.metrics.targets` list to open ports on every workload. Do not materialize targets of other applications (CampaignManager or CallSimulator) in the Portal Service. Preserve separation of application endpoint data from exposure policy. Validate every target in the selected external metrics interface before workload filtering, including application/endpoint references, HTTP metrics metadata and explicit path, and required source/target network references. Invalid targets fail even when their applications are not installed by the current workload. Zero matching targets is valid: omit metrics ports and Prometheus scrape annotations for that workload. Exactly one matching target is valid. Multiple matching targets are ambiguous and fail with the workload ID and target identities.

### Prometheus annotations

When discovery is `prometheus-annotations` and the workload has one matching metrics target, add the following **Service** annotations:

```yaml
metadata:
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/path: "/metrics"
    prometheus.io/port: "9090"
```

`path` and `port` come from the selected metrics application endpoint. These annotations are a convention interpreted only when a Prometheus Kubernetes service-discovery/relabeling configuration is later installed. They **do not** themselves cause scraping or establish network connectivity. Do not create a Prometheus server, `ServiceMonitor`, `NetworkPolicy`, or scrape job in the first generator.

## 7. Expected initial generated artifacts

Generate only two files under a caller-specified output directory:

```text
portal-deployment.yaml
portal-service.yaml
```

Expected Deployment key values: `replicas: 2`, `image: out-dialer/portal:0.1`, `imagePullPolicy: Never`, `requests: {cpu: 250m, memory: 256Mi}`, named ports `http:8443` and `metrics:9090`, and the current `/health` HTTP readiness/liveness settings.

Expected Service key values: `ClusterIP`, `app: portal` selector, `http:8443` and `metrics:9090` TCP ports, and the three Prometheus annotations shown above.

Compare **semantic YAML structures**, not raw YAML text, against `k8s/out-dialer/portal-deployment.yaml` and `k8s/out-dialer/portal-service.yaml`. Differences in replicas, resource requests, and annotations are intentional. Preserve other established behavior.

## 8. CLI and incremental implementation

Validate the model, realization schema and semantic bindings through the public CLI:

```bash
.venv/bin/python src/cli.py validate models/out-dialer \
  --realization realizations/out-dialer/local-lab.yaml
```

Capacity calculation is implemented by `realization.resources.resolve_kubernetes_requests`. A Kubernetes manifest generator is not yet implemented in this checkout. Target generation interface for a later milestone:

```bash
.venv/bin/python src/cli.py generate kubernetes \
  models/out-dialer \
  --realization realizations/out-dialer/local-lab.yaml \
  --output-dir build/k8s/out-dialer
```

Follow the existing generator API shape (`generate(model, realization)` plus `serialize()`), current YAML serialization practices, and repository `AGENTS.md`. Generation should be deterministic and read-only with respect to the live cluster.

**Milestone 1 — model and realization preparation:**
- Update Portal endpoint identity/protocol (without modifying Flask or live manifests).
- Introduce model endpoint optional `path` and appropriate metrics paths.
- Update compute profile values and CPU/RAM schema; document units.
- Append Kubernetes realization section and schema validation.
- Extend realization dataclass/loader to expose `.kubernetes` without disturbing Docker/RouterOS.
- Add minimal semantic realization-reference checks for selected Kubernetes application/deployment, direct capacity-profile binding, and external metrics interface; keep the existing reference registry/docs in sync.
- Add/adjust tests and document these mappings.

**Milestone 2 — generator + CLI:** implement `src/generators/kubernetes.py`, `generate kubernetes`, output files, and comprehensive generator tests.

**Milestone 3 — integration:** add CI generation and manifest validation, then switch CD to generate artifacts from reviewed `main` before deploying. Preserve existing manual manifests and working CD pipeline until the generated output is verified and the change is reviewed.

## 9. Explicit non-goals

- No Flask TLS changes, certificate provisioning, or Ingress in these milestones.
- No Kubernetes cluster mutation during model/generator development.
- No Kubernetes RBAC, namespace bootstrap, metrics server, external Prometheus, or ServiceMonitor generation.
- No container build/push/image registry pipeline.
- No resource limits or HPA in v1; keep `replicas` realization-owned.
- No changes to Docker Compose or RouterOS output other than consequences of intentionally correcting Portal endpoint metadata; regression tests must continue to pass.

## 10. Milestone 1 validation

REF-010 validates direct compute-profile bindings, positive capacities, replica counts and representable requests. REF-011 resolves the explicit deployment and selected application, requires endpoint selections to belong to that application, requires unique resolved numeric container ports, validates supported protocols (HTTP, HTTPS, TCP, UDP), and requires probe ports to select HTTP/HTTPS endpoints. REF-012 validates the external metrics interface and all targets before filtering by the selected application. Each workload may have zero targets (omit scrape annotations) or one valid HTTP `metrics` target with an explicit path. Multiple matches fail with target identities and workload ID; invalid references or metadata always fail. No Kubernetes networking is inferred from model interfaces or source networks. Kubernetes remains optional; manifest generation is deferred.

Initial networking remains governed by ADR-010: CNI networking, ClusterIP Services, and no generated NetworkPolicies or logical-zone translation. These sizing changes do not alter that decision.
