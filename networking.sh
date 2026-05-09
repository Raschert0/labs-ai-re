#!/usr/bin/env bash
set -euo pipefail

sudo ip route add 192.168.64.0/18 via $(minikube ip)
