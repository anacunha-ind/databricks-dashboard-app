#!/usr/bin/env bash
# Auto-cleanup orphaned PR preview environments after a production deploy.
# Lists all preview-pr-* apps and pr-* Lakebase branches, then deletes any
# whose PR is no longer open in Bitbucket.
#
# Required env vars:
#   DATABRICKS_HOST            workspace URL
#   DATABRICKS_CLIENT_ID       service principal application ID
#   DATABRICKS_CLIENT_SECRET   service principal secret
#   LAKEBASE_PROJECT           Lakebase project name (default: sara-lakebase-dbx-app)
#   BITBUCKET_REPO_FULL_NAME   injected by Bitbucket Pipelines (e.g. anascunha/databricks-dashboard-app)
#
# Optional (required for Bitbucket API check):
#   BITBUCKET_TOKEN            Repository access token (Pull requests: Read)
set -euo pipefail

: "${DATABRICKS_HOST:?DATABRICKS_HOST is required}"
: "${DATABRICKS_CLIENT_ID:?DATABRICKS_CLIENT_ID is required}"
: "${DATABRICKS_CLIENT_SECRET:?DATABRICKS_CLIENT_SECRET is required}"
: "${LAKEBASE_PROJECT:=sara-lakebase-dbx-app}"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Dashboard Metrics — Preview Cleanup                         ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ── 1. Get open PR IDs from Bitbucket API ────────────────────────────────────
echo "▶ Fetching open PRs from Bitbucket..."
OPEN_PR_IDS=""
USE_AGE_FALLBACK=true

if [ -n "${BITBUCKET_REPO_FULL_NAME:-}" ] && [ -n "${BITBUCKET_TOKEN:-}" ]; then
  USE_AGE_FALLBACK=false
  OPEN_PR_IDS=$(curl -s \
    "https://api.bitbucket.org/2.0/repositories/${BITBUCKET_REPO_FULL_NAME}/pullrequests?state=OPEN&pagelen=100" \
    -H "Authorization: Bearer ${BITBUCKET_TOKEN}" \
    | python3 -c "
import sys,json
data=json.load(sys.stdin)
print(' '.join(str(p['id']) for p in data.get('values',[])))
" 2>/dev/null || echo "") || true
  echo "   ✓ Open PRs: ${OPEN_PR_IDS:-none}"
else
  echo "   ⚠ BITBUCKET_TOKEN not set — all preview envs will be considered orphaned"
fi

# ── 2. Find all preview apps (pr-*-dashboard-metrics) ────────────────────────
echo "▶ Listing preview Databricks Apps..."
ALL_PREVIEW_APPS=$(databricks apps list -o json 2>/dev/null \
  | python3 -c "
import sys,json,re
data=json.load(sys.stdin)
apps=data if isinstance(data,list) else data.get('apps',[])
print('\n'.join(a['name'] for a in apps if re.match(r'^pr-[0-9]+-', a['name'])))
" 2>/dev/null || echo "")

[ -n "${ALL_PREVIEW_APPS}" ] \
  && echo "   Found: $(echo "${ALL_PREVIEW_APPS}" | tr '\n' ' ')" \
  || echo "   ✓ No preview apps found"

# ── 3. Find all preview Lakebase branches (pr-*) ────────────────────────────
echo "▶ Listing preview Lakebase branches..."
ALL_PREVIEW_BRANCHES=$(databricks postgres list-branches \
  "projects/${LAKEBASE_PROJECT}" -o json 2>/dev/null \
  | python3 -c "
import sys,json
data=json.load(sys.stdin)
branches=data if isinstance(data,list) else data.get('branches',[])
names=[b['name'].split('/')[-1] for b in branches if b['name'].split('/')[-1].startswith('pr-')]
print('\n'.join(names))
" 2>/dev/null || echo "")

[ -n "${ALL_PREVIEW_BRANCHES}" ] \
  && echo "   Found: $(echo "${ALL_PREVIEW_BRANCHES}" | tr '\n' ' ')" \
  || echo "   ✓ No preview branches found"

# ── 4. Tear down orphaned resources ─────────────────────────────────────────
echo "▶ Cleaning up orphaned resources..."
CLEANED=0

for APP_NAME in ${ALL_PREVIEW_APPS}; do
  PR_ID=$(echo "${APP_NAME}" | sed 's/pr-\([0-9]*\)-.*/\1/')

  IS_OPEN=false
  if [ "${USE_AGE_FALLBACK}" = "false" ]; then
    for OPEN_ID in ${OPEN_PR_IDS}; do
      [ "${OPEN_ID}" = "${PR_ID}" ] && IS_OPEN=true && break
    done
  fi

  if [ "${IS_OPEN}" = "false" ]; then
    echo "   Tearing down PR #${PR_ID} (${APP_NAME})..."
    PR_ID="${PR_ID}" \
    DATABRICKS_HOST="${DATABRICKS_HOST}" \
    DATABRICKS_CLIENT_ID="${DATABRICKS_CLIENT_ID}" \
    DATABRICKS_CLIENT_SECRET="${DATABRICKS_CLIENT_SECRET}" \
    LAKEBASE_PROJECT="${LAKEBASE_PROJECT}" \
    bash "$(dirname "$0")/teardown_preview.sh"
    CLEANED=$((CLEANED + 1))
  else
    echo "   ✓ PR #${PR_ID} is still open — keeping ${APP_NAME}"
  fi
done

# Also clean orphaned branches whose app is already gone
for BRANCH_NAME in ${ALL_PREVIEW_BRANCHES}; do
  PR_ID="${BRANCH_NAME#pr-}"
  APP_NAME="pr-${PR_ID}-dashboard-metrics"
  echo "${ALL_PREVIEW_APPS}" | grep -q "^${APP_NAME}$" && continue

  IS_OPEN=false
  if [ "${USE_AGE_FALLBACK}" = "false" ]; then
    for OPEN_ID in ${OPEN_PR_IDS}; do
      [ "${OPEN_ID}" = "${PR_ID}" ] && IS_OPEN=true && break
    done
  fi

  if [ "${IS_OPEN}" = "false" ]; then
    echo "   Deleting orphaned branch ${BRANCH_NAME}..."
    databricks postgres delete-branch \
      "projects/${LAKEBASE_PROJECT}/branches/${BRANCH_NAME}" --no-wait \
      && echo "   ✓ Branch deleted" \
      || echo "   ⚠ Branch delete failed"
    CLEANED=$((CLEANED + 1))
  fi
done

echo ""
[ "${CLEANED}" -eq 0 ] \
  && echo "✅ Nothing to clean up — all preview environments are active" \
  || echo "✅ Cleaned up ${CLEANED} orphaned preview environment(s)"
echo ""
