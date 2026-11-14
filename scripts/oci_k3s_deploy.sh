#!/bin/bash
# Deploy/upgrade the app on the Oracle k3s VM. Called by CD over SSH.
# Usage: scripts/oci_k3s_deploy.sh [IMAGE]   (default: :latest)
set -euo pipefail
cd "$(dirname "$0")/.."
NS=passive-investment
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
IMAGE=${1:-godlewskimariusz/passive-investment-webapp:latest}

git pull --ff-only
kubectl apply -f k8s/namespace.yml -f k8s/postgres.yml -f k8s/ingress.yml
sed "s|image: .*|image: $IMAGE|" k8s/webapp.yml | kubectl apply -f -
if [ -z "${1:-}" ]; then
    kubectl -n $NS rollout restart deployment/webapp
fi
kubectl -n $NS rollout status deployment/postgres --timeout=300s
kubectl -n $NS rollout status deployment/webapp --timeout=300s
kubectl -n $NS exec deploy/webapp -- sh -c "cd db && uv run C--no-sync alembic upgrade head"
kubectl -n $NS get pods
