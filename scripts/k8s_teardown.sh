#!/bin/bash
set -euo pipefail

NAMESPACE="passive-investment"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()   { echo -e "${GREEN}[✔]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }

echo ""
echo "========================================="
echo "  Kubernetes Teardown — passive-investment"
echo "========================================="
echo ""

warn "Deleting namespace '$NAMESPACE' and all its resources..."
kubectl delete namespace "$NAMESPACE" --ignore-not-found
log "Namespace deleted"

echo ""
warn "Stopping minikube..."
minikube stop
log "Minikube stopped"

echo ""
log "Teardown complete"
