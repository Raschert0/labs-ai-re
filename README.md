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

## Dependencies

* agentgateway 1.1.0
* cilium 1.19.3
* ollama 0.23.1-rocm

## How to run

### Starting minikube

```bash
minikube start --driver docker \
  --container-runtime docker \
  --gpus amd \
  --addons metrics-server,dashboard \
  --cpus 2 \
  --memory 8g \
  --disk-size 10g \
  -n 2 \
  --network-plugin=cni \
  --cni=false \
  --service-cluster-ip-range '192.168.80.0/20'
```

Add route to k8s CIDR 192.168.80.0/18 (includes Cilium CIDR)

```bash
./networking.sh
```

### Cilium setup

```bash
helm install cilium oci://quay.io/cilium/charts/cilium \
  --version 1.19.3 \
  --namespace kube-system \
  -f cilium/values.yaml
```

```bash
cilium status --wait
```

### Then

```bash
kubectl apply --server-side --force-conflicts -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.5.0/standard-install.yaml

helm upgrade -i agentgateway-crds oci://cr.agentgateway.dev/charts/agentgateway-crds \
  --create-namespace --namespace agentgateway-system \
  --version v1.1.0 \
  --set controller.image.pullPolicy=Always

helm upgrade -i agentgateway oci://cr.agentgateway.dev/charts/agentgateway \
  --namespace agentgateway-system \
  --version v1.1.0 \
  --set controller.image.pullPolicy=Always \
  --set controller.extraEnv.KGW_ENABLE_GATEWAY_API_EXPERIMENTAL_FEATURES=true \
  --wait

kubectl apply -f manifests/simple-gateway.yml
```


### Ollama setup

```bash

```
