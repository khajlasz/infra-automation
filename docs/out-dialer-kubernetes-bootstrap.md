# Out-Dialer Portal — Kubernetes Lab Bootstrap

**Status:** Manually deployed and verified  
**Verified:** 2026-10-23  
**Scope:** UTM/kubeadm local lab; Portal only

## Purpose

Record the first working Kubernetes deployment of the Out-Dialer Portal and provide a repeatable manual verification procedure. This is a bootstrap milestone, not the final model-driven deployment workflow. Kubernetes manifests are currently maintained directly; generation from the infra-automation model is future work.

## Lab topology and access

- Control plane: `k8s-c00`; workers: `k8s-w00`, `k8s-w10`.
- API server data-plane address: `10.10.50.10:6443`.
- API server management address, reachable from the macOS host: `192.168.64.40:6443`.
- Pod network: `10.244.0.0/16`; Service network: `10.96.0.0/12`.
- Deployment namespace: `out-dialer`.
- macOS kubeconfig: `~/.kube/utm-lab-config` (local credential file; **never commit**).

The existing macOS default kubeconfig targets a separate Kind cluster. Use the UTM kubeconfig explicitly or export `KUBECONFIG` in a dedicated shell:

```bash
export KUBECONFIG="$HOME/.kube/utm-lab-config"
kubectl config current-context
kubectl get nodes -o wide
```

### API server certificate SAN update (manual prerequisite)

The original kubeadm API server serving certificate contained `10.10.50.10`, but not `192.168.64.40`. Connecting through the management interface therefore required regenerating the serving certificate with an additional SAN. The cluster's `kubeadm-config` was also updated so the configuration is retained for future maintenance.

The effective `ClusterConfiguration` includes:

```yaml
apiServer:
  certSANs:
    - 10.10.50.10
    - 192.168.64.40
```

The replacement certificate was generated with `kubeadm init phase certs apiserver --config ...`, using the existing cluster CA, and the static API server Pod was restarted to load it. The original certificate and key were backed up on the control-plane host (outside Git). The new certificate was verified to contain both IP SANs, and macOS `kubectl` connectivity succeeded with normal TLS verification.

For future recreation, use the appropriate kubeadm cluster configuration during initialization rather than repeating certificate replacement after cluster creation. **Do not commit kubeconfig credentials, CA private keys, API server keys, or certificate backups.**

## Portal deployment artifacts

| Path | Purpose |
| --- | --- |
| `k8s/out-dialer/portal-deployment.yaml` | One Portal replica, HTTP readiness/liveness probes at `/health`, application port `8443`, metrics port `9090` |
| `k8s/out-dialer/portal-service.yaml` | Internal `ClusterIP` Service exposing ports `8443` and `9090` |

Container image: `out-dialer/portal:0.1`.

For this bootstrap, the image was manually imported into containerd on **both** workers and the Deployment uses `imagePullPolicy: Never`. A fresh worker without the image cannot run this Pod; image distribution is not yet automated.

Although the application listens on port `8443`, it currently serves **HTTP**, not HTTPS. Do not assume TLS from the port number.

## Manual deployment

From the repository root on macOS, with the UTM kubeconfig selected:

```bash
kubectl get namespace out-dialer || kubectl create namespace out-dialer
kubectl apply --dry-run=server -f k8s/out-dialer/
kubectl apply -f k8s/out-dialer/
kubectl rollout status deployment/portal -n out-dialer --timeout=120s
kubectl get pods,deployments,services -n out-dialer -o wide
```

The namespace is a manual prerequisite in this bootstrap and is not created by the two Portal manifests.

## Functional verification

In one macOS terminal:

```bash
kubectl port-forward -n out-dialer svc/portal 8443:8443
```

In another:

```bash
curl -i http://localhost:8443/health
curl http://localhost:8443/
```

Observed on 2026-10-23:

- Deployment successfully rolled out: `1/1` available.
- Portal Pod: `Running`, `1/1` Ready, zero restarts; scheduled to `k8s-w00`.
- Pod IP: `10.244.250.178` (ephemeral).
- Service: `ClusterIP` `10.100.64.252` (observed allocation, not a pinned address), ports `8443/TCP` and `9090/TCP`.
- `GET /health`: body `OK`.
- `GET /`: `{"metrics_port":9090,"port":8443,"service":"portal"}`.

These checks verify the running Pod, Service-backed port-forward, and HTTP application responses. They do **not** yet demonstrate ingress, external user access, inter-service communication, or end-to-end campaign functionality.

## Known limitations

- The Campaign Manager service is not yet deployed; Portal operations that depend on `http://campaign:8080` are not end-to-end tested.
- No container registry or automated image build/publish/distribution process exists for this deployment.
- `imagePullPolicy: Never` is suitable for this preloaded-image lab, not the eventual CI/CD flow.
- The `ClusterIP` is internal; local access was tested using `kubectl port-forward`.
- No Ingress, TLS termination, persistence, or production-grade availability configuration is established here.
- The current macOS kubeconfig uses administrative cluster credentials; these should not be reused as GitHub Actions deployment credentials.

## Next milestone: Kubernetes CD

Implement a separate `.github/workflows/deploy-k8s.yml` on the existing macOS self-hosted GitHub Actions runner. Start with manifest validation, `kubectl apply`, rollout checks and clear failure reporting. Before enabling automated deployment, create a dedicated namespace-scoped ServiceAccount and RBAC permissions; avoid embedding cluster-admin credentials in CI. Image publishing/distribution and model-generated manifests are subsequent, separate milestones. Argo CD is not part of this bootstrap.

## Recovery and diagnostics

```bash
kubectl -n out-dialer get pods -o wide
kubectl -n out-dialer describe deployment portal
kubectl -n out-dialer describe pods -l app=portal
kubectl -n out-dialer logs deployment/portal --tail=100
kubectl -n out-dialer get endpointslices -l kubernetes.io/service-name=portal
```

If a Pod reports an image error, verify that `out-dialer/portal:0.1` exists in the `k8s.io` containerd namespace **on the worker where the Pod is scheduled**. If `kubectl` targets the wrong cluster, check `KUBECONFIG` and the current context before applying anything.
