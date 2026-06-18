#!/usr/bin/env bash
set -euo pipefail

DEPLOY_ROOT="${DEPLOY_ROOT:-/opt/smawell}"
REPO_DIR="$DEPLOY_ROOT/shopify"
DEPLOY_DIR="$DEPLOY_ROOT/deploy"

echo "[storefront] deploying from $REPO_DIR"

cd "$REPO_DIR"
git fetch --all --prune
git reset --hard "origin/${GITHUB_REF_NAME:-main}"

cd "$DEPLOY_DIR"
docker compose build store-web store-api
docker compose up -d store-web store-api

echo "[storefront] deployment finished"
