# README

## References

* [Lab 01](https://github.com/Raschert0/labs-ai-re/tree/lab/01)
* [Lab 02](https://github.com/Raschert0/labs-ai-re/tree/lab/02)
* [Lab 04](https://github.com/Raschert0/labs-ai-re/tree/lab/04)

## Repository structure

```
.
├── abox/                         # Git submodule — forked infra-as-code tooling used to
│                                 #   spin up the local k8s cluster (kind + Flux bootstrap)
├── agentgateway/
│   └── manifests/                # Standalone agentgateway manifests (exploratory / lab reference)
├── fluxcd/
│   ├── oci-repository.yaml       # Flux OCIRepository — pulls releases OCI image from GHCR
│   └── kustomization.yaml        # Flux Kustomization — reconciles releases/ with SOPS decryption
├── kagent/                       # kagent-related exploration / scratch files
├── notes/                        # Freeform lab notes and research
├── releases/                     # Primary manifests — packaged as OCI and reconciled by Flux
│   ├── kustomization.yaml        # Kustomize entry point for everything in this directory
│   ├── agentgateway-backend-secrets.enc.yaml   # SOPS-encrypted API key secrets
│   ├── agentgateway-backend.yaml               # AgentgatewayBackend (Gemini/Google) + HTTPRoute
│   ├── agentgateway-kagent-mcp.yaml            # AgentgatewayBackend exposing kagent MCP server
│   ├── kagent-model.yaml                       # ModelConfig (Gemini via agentgateway)
│   ├── kagent-k8s-inspector.yaml               # kagent Agent — read-only k8s cluster inspector
│   └── debug.yaml                              # Debug namespace + netshoot pod
├── reports/                      # Lab completion artefacts (screenshots, retrospectives)
├── .github/workflows/
│   └── flux-push.yaml            # CI — packages releases/ as OCI and pushes to GHCR on merge
├── .sops.yaml                    # SOPS config — age key selection rules
└── Makefile                      # Convenience targets (push tag, etc.)
```

Flux pulls the `releases/` directory from GHCR as an OCI artifact (pushed by CI on every merge to `main`) and applies it to the cluster every 2 minutes. SOPS decryption runs transparently at reconcile time using the `sops-age` cluster secret.

## How to run

### Clone submodules

Here I use fork of `abox` to make it possible to use up-to-date kagent version

```bash
git submodules init
git submodules update
```

### Spinning up infrastructure

```bash
cd abox
make run
```

## Secret management

Sensitive credentials (e.g. API keys for `AgentgatewayBackend`) are encrypted with [SOPS](https://github.com/getsops/sops) + [age](https://github.com/FiloSottile/age) before being committed. Flux decrypts them on apply using a private key stored as a cluster Secret.

### One-time cluster setup

```bash
# 1. Generate an age key pair (keep age.agekey out of git — it is gitignored)
age-keygen -o age.agekey

# 2. Extract and insert the public key into .sops.yaml
age-keygen -y age.agekey   # prints: age1...

# 3. Store the private key in the cluster so Flux can decrypt at reconcile time
kubectl create secret generic sops-age \
  --namespace=flux-system \
  --from-file=age.agekey=age.agekey

# 4.Then, once all resources are provisioned, add another upstream, which depends on that secret
kubectl apply -f fluxcd/
```

### Encrypting a secret

```bash
# 1. Fill in real values in the plaintext template (gitignored)
$EDITOR releases/agentgateway-backend-secrets.yaml

# 2. Encrypt — .sops.yaml auto-selects the age key for files matching releases/*.enc.yaml
sops --encrypt releases/agentgateway-backend-secrets.yaml \
  > releases/agentgateway-backend-secrets.enc.yaml

# 3. Register it in releases/kustomization.yaml
#    Add under resources:
#      - agentgateway-backend-secrets.enc.yaml

# 4. Commit only the encrypted file
git add releases/agentgateway-backend-secret.enc.yaml releases/kustomization.yaml
```

### Editing an existing encrypted secret

```bash
sops edit releases/agentgateway-backend-secrets.enc.yaml
# Opens the decrypted content in $EDITOR; re-encrypts on save
```

## Development

### How to package and push changes

```bash
# First, commit changes, then run
make push
# to push a new tag
```

## MCP Inspector

To inspect MCP servers exposed via agentgateway:

```bash
# Replace the origin with your actual browser URL (check what origin the inspector logs as "Invalid origin")
ALLOWED_ORIGINS=https://<codespace-name>-6274.app.github.dev npx @modelcontextprotocol/inspector
```

Then open the printed URL in your browser and configure:

- **Transport Type**: Streamable HTTP
- **URL**: `http://<gateway-ip>/kagent-mcp`
- **Connection Type**: Proxy (not Direct)
- **Inspector Proxy Address**: `https://<codespace-name>-6277.app.github.dev`

Make sure port `6277` (proxy) is set to **Public** visibility in the Codespace Ports panel.

## Reports

Directory `reports` contains whatever I deem necessary to prove my completion of the tasks for the given lab.
