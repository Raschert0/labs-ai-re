# README

## References

* [Lab 01](https://github.com/Raschert0/labs-ai-re/tree/lab/01)
* [Lab 02](https://github.com/Raschert0/labs-ai-re/tree/lab/02)

## How to run

### Clone submodules

```bash
git submodules init
git submodules update
```

### Spinning up infrastructure

```bash
cd abox
make run
```

Then, once all resources are provisioned

```bash
kubectl apply -f fluxcd/
```

## Secret management

Sensitive credentials (e.g. API keys for `AgentgatewayBackend`) are encrypted with [SOPS](https://github.com/getsops/sops) + [age](https://github.com/FiloSottile/age) before being committed. Flux decrypts them on apply using a private key stored as a cluster Secret.

### Prerequisites

```bash
# age
brew install age          # macOS
apt install age           # Debian/Ubuntu

# sops - download from https://github.com/getsops/sops/releases
```

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

## Reports

Directory `reports` contains whatever I deem necessary to prove my completion of the tasks for the given lab.
