#!/bin/bash
# One-time setup on a fresh Oracle Ubuntu VM: firewall, k3s, secret, deploy, initial data.
# WARNING: the last step resets the database — run only once.
set -euo pipefail
cd "$(dirname "$0")/.."
NS=passive-investment

# OCI Ubuntu images reject everything except SSH; open HTTP/S and pod/service networks
sudo iptables -I INPUT 1 -p tcp -m multiport --dports 80,443 -j ACCEPT
sudo iptables -I INPUT 1 -s 10.42.0.0/16 -j ACCEPT
sudo iptables -I INPUT 1 -s 10.43.0.0/16 -j ACCEPT
sudo iptables -D FORWARD -j REJECT --reject-with icmp-host-prohibited || true
sudo netfilter-persistent save

curl -sfL https://get.k3s.io | sh -s - --write-kubeconfig-mode 644
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
# `kubectl wait --all` fails immediately if the node hasn't registered yet
until kubectl get nodes -o name 2>/dev/null | grep -q node/; do sleep 2; done
kubectl wait --for=condition=ready node --all --timeout=180s

PW=$(openssl rand -hex 16)
kubectl apply -f k8s/namespace.yml
kubectl -n $NS create secret generic db-credentials \
    --from-literal=POSTGRES_USER=app \
    --from-literal=POSTGRES_PASSWORD="$PW" \
    --from-literal=POSTGRES_DB=passive_investment \
    --from-literal=DATABASE_URL="postgresql+psycopg2://app:$PW@postgres:5432/passive_investment"

./scripts/oci_k3s_deploy.sh

# data/ CSVs are stored in Git LFS
sudo apt-get install -y git-lfs
git lfs install
git lfs pull

curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv sync --no-dev
kubectl -n $NS port-forward svc/postgres 15432:5432 >/dev/null &
sleep 3
DATABASE_URL="postgresql+psycopg2://app:$PW@localhost:15432/passive_investment" uv run python scripts/init_dev_db.py
kill %1
