#!/usr/bin/env bash
# Deploy a per-PR preview environment:
#   1. Create a Lakebase branch (copy-on-write from production)
#   2. Wait for the branch to be READY
#   3. Resolve the branch endpoint hostname
#   4. Write a preview app.yaml pointing to the branch endpoint
#   5. Deploy the DAB bundle to the 'preview' target
#
# Required env vars (injected by Bitbucket Pipelines):
#   BITBUCKET_PR_ID            PR number
#   DATABRICKS_HOST            workspace URL
#   DATABRICKS_CLIENT_ID       service principal application ID
#   DATABRICKS_CLIENT_SECRET   service principal secret (secured)
#   LAKEBASE_PROJECT           Lakebase project name (default: sara-lakebase-dbx-app)
set -euo pipefail

: "${BITBUCKET_PR_ID:?BITBUCKET_PR_ID is required}"
: "${DATABRICKS_HOST:?DATABRICKS_HOST is required}"
: "${DATABRICKS_CLIENT_ID:?DATABRICKS_CLIENT_ID is required}"
: "${DATABRICKS_CLIENT_SECRET:?DATABRICKS_CLIENT_SECRET is required}"
: "${LAKEBASE_PROJECT:=sara-lakebase-dbx-app}"

PR_ID="${BITBUCKET_PR_ID}"
BRANCH_NAME="pr-${PR_ID}"
APP_NAME="preview-pr-${PR_ID}-dashboard-metrics"
BRANCH_RESOURCE="projects/${LAKEBASE_PROJECT}/branches/${BRANCH_NAME}"
APP_YAML="bundles/dashboard-metrics/src/app/app.yaml"
APP_YAML_BAK="${APP_YAML}.preview.bak"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Dashboard Metrics — Preview Deploy                          ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  PR:     #${PR_ID}"
echo "║  App:    ${APP_NAME}"
echo "║  Branch: ${BRANCH_NAME}"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Restore app.yaml on exit
restore_appyaml() {
  if [[ -f "${APP_YAML_BAK}" ]]; then
    mv "${APP_YAML_BAK}" "${APP_YAML}"
    echo "   ✓ app.yaml restored"
  fi
}
trap restore_appyaml EXIT

# ── 1. Create Lakebase branch (idempotent) ────────────────────────────────────
echo "▶ Creating Lakebase branch: ${BRANCH_NAME}..."
databricks postgres create-branch \
  "projects/${LAKEBASE_PROJECT}" \
  "${BRANCH_NAME}" \
  --json "{\"spec\": {\"source_branch\": \"projects/${LAKEBASE_PROJECT}/branches/production\", \"no_expiry\": true}}" \
  --no-wait 2>&1 | grep -v "^⟐" || echo "   ✓ Branch already exists — reusing"

# ── 2. Wait for branch to be READY ───────────────────────────────────────────
echo "▶ Waiting for branch to be ready..."
for attempt in $(seq 1 30); do
  STATE=$(databricks postgres get-branch "${BRANCH_RESOURCE}" -o json 2>/dev/null \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status',{}).get('current_state',''))" \
    2>/dev/null || echo "")
  if [[ "${STATE}" == "READY" ]]; then
    echo "   ✓ Branch state: READY"
    break
  fi
  echo "   ... attempt ${attempt}/30 — state=${STATE:-unknown}, waiting 5s"
  sleep 5
done

# ── 3. Resolve branch endpoint hostname ──────────────────────────────────────
echo "▶ Fetching branch endpoint hostname..."
BRANCH_HOST=$(databricks postgres list-endpoints "${BRANCH_RESOURCE}" -o json 2>/dev/null \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
eps = data if isinstance(data, list) else data.get('endpoints', [])
host = (eps[0].get('status', {}).get('hosts', {}).get('host', '')) if eps else ''
print(host)
" 2>/dev/null || echo "")

if [[ -z "${BRANCH_HOST}" ]]; then
  echo "   ⚠ Could not determine branch host — aborting"
  exit 1
fi
echo "   ✓ Branch host: ${BRANCH_HOST}"

# ── 4. Write preview app.yaml ─────────────────────────────────────────────────
echo "▶ Writing preview app.yaml..."
cp "${APP_YAML}" "${APP_YAML_BAK}"
cat > "${APP_YAML}" << APPYAML
command: ['streamlit', 'run', 'app.py']
env:
  - name: CATALOG_NAME
    value: samples
  - name: SCHEMA_NAME
    value: tpch
  - name: LAKEBASE_HOST
    value: ${BRANCH_HOST}
  - name: LAKEBASE_DATABASE
    value: databricks_postgres
APPYAML
echo "   ✓ app.yaml written"

# ── 5. Deploy bundle + ensure app is running ─────────────────────────────────
echo "▶ Deploying bundle (target: preview, pr_id: ${PR_ID})..."
cd bundles/dashboard-metrics
databricks bundle deploy --target preview --var "pr_id=${PR_ID}"

echo "▶ Starting app: ${APP_NAME}..."
cd "${OLDPWD}"
databricks apps start "${APP_NAME}" 2>/dev/null \
  && echo "   ✓ App started" \
  || echo "   ✓ App already running"

echo "▶ Granting CAN_USE to all workspace users..."
databricks apps set-permissions "${APP_NAME}" \
  --json '{"access_control_list": [{"group_name": "users", "permission_level": "CAN_USE"}]}' \
  && echo "   ✓ Permissions set" \
  || echo "   ⚠ Could not set permissions — grant manually in the Databricks UI"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ✅ Preview deployed                                         ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  URL: https://${APP_NAME}-2591888035258875.aws.databricksapps.com"
echo "║  DB:  Lakebase branch ${BRANCH_NAME} (copy-on-write)"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Export preview URL for after-script (Bitbucket PR comment)
echo "PREVIEW_URL=https://${APP_NAME}-2591888035258875.aws.databricksapps.com" \
  >> "${BITBUCKET_EXPORT_VARIABLES:-/dev/null}" 2>/dev/null || true
