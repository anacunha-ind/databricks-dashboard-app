#!/usr/bin/env bash
# Tear down a per-PR preview environment:
#   1. Delete the Databricks App for the PR
#   2. Delete the Lakebase branch for the PR
# Usage: teardown_preview.sh <pr_id>
set -euo pipefail

PR_ID="${1:?Usage: teardown_preview.sh <pr_id>}"
PROJECT="projects/sara-lakebase-dbx-app"
APP_NAME="preview-pr-${PR_ID}-dashboard-metrics"

echo "==> Deleting app ${APP_NAME}..."
databricks apps delete "${APP_NAME}" || echo "    App not found, skipping"

echo "==> Deleting Lakebase branch pr-${PR_ID}..."
databricks postgres delete-branch "${PROJECT}/branches/pr-${PR_ID}" || echo "    Branch not found, skipping"

echo "==> Teardown complete for PR ${PR_ID}"
