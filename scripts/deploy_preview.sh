#!/usr/bin/env bash
# Deploy a per-PR preview environment:
#   1. Create a Lakebase branch (copy-on-write from production)
#   2. Wait for the branch to be READY
#   3. Resolve the branch endpoint hostname + endpoint resource path
#   4. Write a preview app.yaml pointing to the branch endpoint
#   5. Deploy the DAB bundle to the 'preview' target
#   6. Create a Lakebase role for the app's auto-generated service principal
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

# ── 3. Resolve branch endpoint hostname + resource path ──────────────────────
echo "▶ Fetching branch endpoint..."
ENDPOINT_JSON=$(databricks postgres list-endpoints "${BRANCH_RESOURCE}" -o json 2>/dev/null || echo "")
BRANCH_HOST=$(echo "${ENDPOINT_JSON}" | python3 -c "
import sys, json
data = json.load(sys.stdin)
eps = data if isinstance(data, list) else data.get('endpoints', [])
host = (eps[0].get('status', {}).get('hosts', {}).get('host', '')) if eps else ''
print(host)
" 2>/dev/null || echo "")

ENDPOINT_ID=$(echo "${ENDPOINT_JSON}" | python3 -c "
import sys, json
data = json.load(sys.stdin)
eps = data if isinstance(data, list) else data.get('endpoints', [])
name = (eps[0].get('name', '')) if eps else ''
# name is the full resource path, extract just the endpoint ID segment
print(name.split('/')[-1] if name else '')
" 2>/dev/null || echo "primary")

BRANCH_ENDPOINT="projects/${LAKEBASE_PROJECT}/branches/${BRANCH_NAME}/endpoints/${ENDPOINT_ID:-primary}"

if [[ -z "${BRANCH_HOST}" ]]; then
  echo "   ⚠ Could not determine branch host — aborting"
  exit 1
fi
echo "   ✓ Branch host:     ${BRANCH_HOST}"
echo "   ✓ Branch endpoint: ${BRANCH_ENDPOINT}"

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
  - name: LAKEBASE_ENDPOINT
    value: ${BRANCH_ENDPOINT}
APPYAML
echo "   ✓ app.yaml written"

# ── 5. Deploy bundle ──────────────────────────────────────────────────────────
echo "▶ Deploying bundle (target: preview, pr_id: ${PR_ID})..."
cd bundles/dashboard-metrics
if ! databricks bundle deploy --target preview --var "pr_id=${PR_ID}" 2>&1; then
  # A previous failed deploy may have created the app outside of Terraform state.
  # Delete the stale app and retry once — Terraform will recreate it cleanly.
  echo "   ⚠ Deploy failed — deleting stale app and retrying..."
  databricks apps delete "${APP_NAME}" 2>/dev/null || true
  sleep 5
  databricks bundle deploy --target preview --var "pr_id=${PR_ID}"
fi
databricks bundle run dashboard_metrics_app --target preview --var "pr_id=${PR_ID}"
cd "${OLDPWD}"

# ── 6. Create Lakebase role for the app's auto-generated service principal ────
echo "▶ Fetching app service principal..."
APP_SP=$(databricks apps get "${APP_NAME}" -o json 2>/dev/null \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('service_principal_client_id',''))" \
  2>/dev/null || echo "")

if [[ -z "${APP_SP}" ]]; then
  echo "   ⚠ Could not determine app SP — skipping role creation"
else
  echo "   ✓ App SP: ${APP_SP}"
  ROLE_ID="sp-${APP_SP}"

  echo "▶ Removing stale Lakebase role (if any)..."
  databricks postgres delete-role \
    "${BRANCH_RESOURCE}/roles/${ROLE_ID}" \
    --no-wait 2>/dev/null || echo "   ✓ No stale role to remove"

  echo "▶ Creating Lakebase role for app SP..."
  databricks postgres create-role "${BRANCH_RESOURCE}" \
    --role-id "${ROLE_ID}" \
    --json "{\"spec\": {\"identity_type\": \"SERVICE_PRINCIPAL\", \"postgres_role\": \"${APP_SP}\", \"auth_method\": \"LAKEBASE_OAUTH_V1\", \"membership_roles\": [\"DATABRICKS_SUPERUSER\"]}}" \
    && echo "   ✓ Role ${ROLE_ID} created" \
    || echo "   ⚠ Could not create role — grant manually via databricks postgres create-role"
fi

# ── 7. Grant CAN_USE to all workspace users ───────────────────────────────────
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
