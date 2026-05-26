#!/usr/bin/env bash
# Tear down a PR preview environment:
#   1. Delete the Databricks App
#   2. Delete the Lakebase branch
#   3. Delete workspace bundle files
#
# Usage (Bitbucket custom pipeline):
#   PR_ID=42 bash scripts/teardown_preview.sh
#
# Required env vars:
#   PR_ID                      PR number
#   DATABRICKS_HOST            workspace URL
#   DATABRICKS_CLIENT_ID       service principal application ID
#   DATABRICKS_CLIENT_SECRET   service principal secret
#   LAKEBASE_PROJECT           Lakebase project name (default: sara-lakebase-dbx-app)
set -euo pipefail

: "${PR_ID:?PR_ID is required}"
: "${DATABRICKS_HOST:?DATABRICKS_HOST is required}"
: "${DATABRICKS_CLIENT_ID:?DATABRICKS_CLIENT_ID is required}"
: "${DATABRICKS_CLIENT_SECRET:?DATABRICKS_CLIENT_SECRET is required}"
: "${LAKEBASE_PROJECT:=sara-lakebase-dbx-app}"

BRANCH_NAME="pr-${PR_ID}"
BRANCH_RESOURCE="projects/${LAKEBASE_PROJECT}/branches/${BRANCH_NAME}"
APP_NAME="preview-pr-${PR_ID}-dashboard-metrics"
WORKSPACE_BUNDLE_PATH="/Workspace/Users/${DATABRICKS_CLIENT_ID}/.bundle/dashboard-metrics/preview-pr-${PR_ID}"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Dashboard Metrics — Preview Teardown                        ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  PR:     #${PR_ID}"
echo "║  App:    ${APP_NAME}"
echo "║  Branch: ${BRANCH_NAME}"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ── 1. Delete Databricks App ──────────────────────────────────────────────────
echo "▶ Deleting Databricks App: ${APP_NAME}..."
if databricks apps get "${APP_NAME}" >/dev/null 2>&1; then
  databricks apps delete "${APP_NAME}" \
    && echo "   ✓ App deleted" \
    || echo "   ⚠ App delete failed (may already be gone)"
else
  echo "   ✓ App not found — already cleaned up"
fi

# ── 2. Delete Lakebase branch ────────────────────────────────────────────────
echo "▶ Deleting Lakebase branch: ${BRANCH_NAME}..."
if databricks postgres get-branch "${BRANCH_RESOURCE}" >/dev/null 2>&1; then
  databricks postgres delete-branch "${BRANCH_RESOURCE}" --no-wait \
    && echo "   ✓ Branch deleted" \
    || echo "   ⚠ Branch delete failed — check manually"
else
  echo "   ✓ Branch not found — already cleaned up"
fi

# ── 3. Delete workspace bundle files ────────────────────────────────────────
echo "▶ Removing workspace files: ${WORKSPACE_BUNDLE_PATH}..."
if databricks workspace ls "${WORKSPACE_BUNDLE_PATH}" >/dev/null 2>&1; then
  databricks workspace delete --recursive "${WORKSPACE_BUNDLE_PATH}" \
    && echo "   ✓ Workspace files removed" \
    || echo "   ⚠ Workspace delete failed — check manually"
else
  echo "   ✓ Workspace path not found — already cleaned up"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ✅ PR #${PR_ID} preview torn down                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
