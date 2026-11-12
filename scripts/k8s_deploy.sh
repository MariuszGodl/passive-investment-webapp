#!/bin/bash
set -euo pipefail

NAMESPACE="passive-investment"
K8S_DIR="$(cd "$(dirname "$0")/../k8s" && pwd)"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()   { echo -e "${GREEN}[✔]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

# --- 1. Start minikube if not running ---
echo ""
echo "========================================="
echo "  Kubernetes Deploy — passive-investment"
echo "========================================="
echo ""

MINIKUBE_STATUS=$(minikube status --format='{{.APIServer}}' 2>/dev/null || echo "Stopped")
if [ "$MINIKUBE_STATUS" != "Running" ]; then
    warn "Minikube is not running. Starting..."
    minikube start
    log "Minikube started"
else
    log "Minikube already running"
fi

# --- 2. Apply manifests ---
echo ""
warn "Applying Kubernetes manifests..."

kubectl apply -f "$K8S_DIR/namespace.yml"
kubectl apply -f "$K8S_DIR/secret.yml"
kubectl apply -f "$K8S_DIR/postgres.yml"
kubectl apply -f "$K8S_DIR/webapp.yml"

log "All manifests applied"

# --- 3. Pull latest webapp image ---
echo ""
warn "Forcing webapp to pull the latest image from Docker Hub..."
kubectl rollout restart deployment/webapp -n "$NAMESPACE"
log "Rollout restart triggered"

# --- 4. Wait for pods to be ready ---
echo ""
warn "Waiting for pods to be ready (timeout: 120s)..."

kubectl wait --for=condition=ready pod -l app=postgres -n "$NAMESPACE" --timeout=120s
log "PostgreSQL pod ready"

kubectl wait --for=condition=ready pod -l app=webapp -n "$NAMESPACE" --timeout=120s
log "Webapp pod ready"

# --- 5. Show status ---
echo ""
echo "-----------------------------------------"
kubectl get pods -n "$NAMESPACE"
echo "-----------------------------------------"
kubectl get svc -n "$NAMESPACE"
echo "-----------------------------------------"
echo ""

# --- 6. Start port-forwarding ---
log "Starting port-forward: localhost:30080 → webapp:8000"
echo ""C
echo "  App:     http://localhost:30080"
echo "  Swagger: http://localhost:30080/docs"
echo ""
warn "Press Ctrl+C to stop port-forwarding"
echo ""

kubectl port-forward -n "$NAMESPACE" svc/webapp 30080:8000
