#!/usr/bin/env bash
# Deploy a per-PR preview environment:
#   1. Create a Lakebase branch (copy-on-write from production)
#   2. Create a compute endpoint on that branch
#   3. Write a preview app.yaml pointing to the branch endpoint
#   4. Deploy the DAB bundle to the 'preview' target with pr_id=<PR>
set -euo pipefail

PR_ID="${BITBUCKET_PR_ID:?BITBUCKET_PR_ID is required}"
PROJECT="projects/sara-lakebase-dbx-app"
BRANCH_ID="pr-${PR_ID}"
APP_YAML="bundles/dashboard-metrics/src/app/app.yaml"

echo "==> Creating Lakebase branch ${BRANCH_ID}..."
databricks postgres create-branch "${PROJECT}" "${BRANCH_ID}" --replace-existing

echo "==> Creating endpoint on ${BRANCH_ID}..."
databricks postgres create-endpoint \
  "${PROJECT}/branches/${BRANCH_ID}" "primary" --replace-existing

echo "==> Resolving endpoint host..."
LAKEBASE_HOST=$(databricks postgres get-endpoint \
  "${PROJECT}/branches/${BRANCH_ID}/endpoints/primary" -o json \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['status']['hosts']['host'])")
echo "    Host: ${LAKEBASE_HOST}"

echo "==> Writing preview app.yaml..."
cat > "${APP_YAML}" << YAML
command: ['streamlit', 'run', 'app.py']
env:
  - name: CATALOG_NAME
    value: samples
  - name: SCHEMA_NAME
    value: tpch
  - name: LAKEBASE_HOST
    value: ${LAKEBASE_HOST}
  - name: LAKEBASE_DATABASE
    value: databricks_postgres
YAML

echo "==> Deploying bundle (target: preview, pr_id: ${PR_ID})..."
cd bundles/dashboard-metrics
databricks bundle deploy --target preview --var "pr_id=${PR_ID}"

echo ""
echo "==> Preview deployed!"
echo "    URL: https://preview-pr-${PR_ID}-dashboard-metrics-2591888035258875.aws.databricksapps.com"
