# README

## Requirements

### Hardware

* Accelerator for running LLM workloads
    > For the goal of this task I'm using AMD GPU with 16 GB VRAM and RoCM toolchain

### Software

> I'm using minikube to to run this workload on my desktop.
> It supports hardware acceleration using [amd-gpu-device-plugin](https://minikube.sigs.k8s.io/docs/tutorials/amd/) addon

* Docker
* kubectl
* helm
* minikube
* cilium-cli
* ollama (CLI)

## Dependencies

* agentgateway 1.1.0
* cilium 1.19.3
* ollama 0.23.1-rocm

## How to run

### Considerations

CIDR `192.168.80.0/18` was chosen for this exercise, and so it was hardcoded in `networking.sh` and its subnets were used by Cilium and Minikube to define CIDRS for nodes and services respectively.

### Starting minikube

Spin up minikube cluster. 2 nodes to avoid messing with replicaset for cilium controller. Additional addons were added to simplify setup process and can be safely removed.

```bash
minikube start --driver docker \
  --container-runtime docker \
  --gpus amd \
  --addons metrics-server,dashboard \
  --cpus 6 \
  --memory max \
  --disk-size 20g \
  -n 2 \
  --network-plugin=cni \
  --cni=false \
  --service-cluster-ip-range '192.168.80.0/20'
```

Add route to k8s CIDR

```bash
./networking.sh
```

### Cilium setup

Install cilium and wait untill it finishes startup

```bash
helm install cilium oci://quay.io/cilium/charts/cilium \
  --version 1.19.3 \
  --namespace kube-system \
  -f cilium/values.yaml
```

```bash
cilium status --wait
```

### Agentgateway preparation

> Mainly a copy of official docs

Install CRDs

```bash
kubectl apply --server-side --force-conflicts -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.5.0/standard-install.yaml
```

```bash
helm upgrade -i agentgateway-crds oci://cr.agentgateway.dev/charts/agentgateway-crds \
  --create-namespace --namespace agentgateway-system \
  --version v1.1.0 \
  --set controller.image.pullPolicy=Always
```

```bash
helm upgrade -i agentgateway oci://cr.agentgateway.dev/charts/agentgateway \
  --namespace agentgateway-system \
  --version v1.1.0 \
  --set controller.image.pullPolicy=Always \
  --set controller.extraEnv.KGW_ENABLE_GATEWAY_API_EXPERIMENTAL_FEATURES=true \
  --wait
```

Provision agentgateway proxy

```bash
kubectl apply -f agentgateway/manifests/01-simple-gateway.yml
```

Then, once the external IP is "provisioned" for the proxy, capture it for later use

```bash
export INGRESS_GW_ADDRESS=$(kubectl get svc -n agentgateway-system agentgateway-proxy -o jsonpath="{.status.loadBalancer.ingress[0].ip}:{.spec.ports[0].nodePort}")
```

### Ollama setup

Create ollama deployment with underlying PVC for storing downloaded models.

```bash
kubectl apply -f ollama/manifests/01-deployment.yml
```

Then, once the external IP is "provisioned" for the service and pod is running, tell ollama CLI where to connect.

```bash
export OLLAMA_HOST=$(kubectl get svc -n ollama ollama -o jsonpath="{.status.loadBalancer.ingress[0].ip}:{.spec.ports[0].nodePort}")
```

Pull the model specified in the manifest.

```bash
ollama pull granite4.1:8b-q4_K_M
```

### Configure Ollama as backend for agentgateway

Create necessary binding and specify which ollama model should be user

```bash
kubectl apply -f agentgateway/manifests/02-ollama.yml
```

Verify that everything works as expected at this point

```bash
curl $INGRESS_GW_ADDRESS/v1/chat/completions -H "content-type: application/json" -d '{
    "model": "granite4.1:8b-q4_K_M",
    "messages": [
      {
        "role": "user",
        "content": "Explain the benefits of running models locally."
      }
    ]
  }' | jq .
```

### Kagent setup

Install CRDs

```bash
helm install kagent-crds oci://ghcr.io/kagent-dev/kagent/helm/kagent-crds \
    --namespace kagent \
    --create-namespace
```

Install chart

```bash
helm install kagent oci://ghcr.io/kagent-dev/kagent/helm/kagent \
    --namespace kagent \
    -f kagent/values.yaml
```
