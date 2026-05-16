# Retrospective — Lab 04: Agentic AI on Kubernetes

## What was built

A multi-component agentic AI platform deployed on a kind cluster managed via Flux CD (GitOps, OCI artifacts to GHCR).

| Component | Technology | Notes |
|-----------|-----------|-------|
| A2A Agent | Google ADK + LiteLlm | `ai-infra-advisor`, routed through agentgateway |
| Agent Registry | agentregistry-inventory v0.5.4 | Discovers kagent resources |
| MCP Governance | mcp-security-governance v0.22.2 | Scores MCP security posture |
| Vector Database | Qdrant v1.18.0 | REST + gRPC, ready for embeddings |

## A2A Protocol

The Agent-to-Agent (A2A) protocol defines how agents discover and communicate with each other:

- **Agent Card** served at `/.well-known/agent.json` — describes the agent's capabilities, skills, and endpoint
- **JSON-RPC 2.0** transport: `message/send` (synchronous) and `message/stream` (SSE streaming)
- **Task lifecycle**: `submitted → working → completed/failed/canceled`
- Complements MCP: MCP handles tool calls (agent↔tool), A2A handles agent↔agent delegation

Google ADK's `to_a2a()` wrapper handles all of this — you just write an `Agent` and it becomes an A2A server.

## Key technical details

### Agent name must be a valid Python identifier
`ai-infra-advisor` (with hyphens) caused a pydantic `ValidationError` from ADK. Had to rename to `ai_infra_advisor` (underscores). The Kubernetes service name and HTTP route can still use hyphens — only the ADK `Agent(name=...)` value is constrained.

### agentgateway A2A integration requires no extra CRDs
There is no `AgentgatewayBackend` needed for A2A agents. Setting `appProtocol: kgateway.dev/a2a` on the Service port is sufficient for agentgateway to treat it as an A2A backend. An `HTTPRoute` with `ReplacePrefixMatch` strips the path prefix before forwarding, and a `ReferenceGrant` enables cross-namespace backend references.

### Flux image update without Image Automation controllers
Rather than deploying Flux's Image Automation controllers, the CI pipeline handles updates directly:
1. Build and push image, capture the digest
2. `sed` the digest into `releases/a2a-agent.yaml`
3. Commit (without `[skip ci]` — that flag suppresses ALL push-triggered workflows including tag-based ones)
4. Bump the `v*` patch tag → triggers `flux-push.yaml` → publishes OCI artifact to GHCR → Flux reconciles

### mcp-governance: three iterations to get right
1. Default chart images use `localhost/...:latest` with `pullPolicy: Never` (local dev defaults) — had to override to `ghcr.io/techwithhuz/...` images
2. Release CI strips the `v` prefix from tags: `VERSION=${GITHUB_REF#refs/tags/v}`, so the image tag is `0.22.2`, not `v0.22.2`
3. OCIRepository apiVersion must be `source.toolkit.fluxcd.io/v1`, not `v1beta2`
4. HelmRelease must use `chartRef` (direct OCI reference) rather than `chart.spec.sourceRef` — the latter creates an intermediate `HelmChart` resource which does not support `OCIRepository` as a source kind in this Flux version

### Recovering a corrupted Helm release
When a Helm release is in `failed` state and `helm uninstall` returns "release: not found", the release secrets in the target namespace are corrupted. Fix:
```bash
kubectl delete secrets -n <namespace> -l owner=helm
flux reconcile helmrelease <name> -n flux-system
```
Or for a completely broken state: suspend HelmRelease → delete namespace → resume.

## Observations

- The Flux `OCIRepository` + `chartRef` pattern is cleaner than `HelmRepository` for charts distributed as OCI artifacts, but the distinction between `chart.spec.sourceRef` and `chartRef` at the HelmRelease level is not obvious from the docs and causes silent failures.
- agentregistry's `DiscoveryConfig` CRD is required but not created automatically — easy to miss since the Helm release succeeds without it.
- Qdrant is straightforward to deploy; the Helm chart has sensible defaults and the REST API works immediately after pod startup.
