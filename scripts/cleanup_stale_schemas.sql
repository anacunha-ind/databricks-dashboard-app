-- Cleanup: stale schemas from databricks-dashboard-app (study project)
-- Created: 2026-05-27
-- Context: schemas were created by Terraform deploys (CI pipeline and local)
-- that lost state sync. Safe to drop — no production data, TPC-H sample data only.
-- Run as workspace admin in the Databricks SQL Editor.

-- ── Schemas created by CI/CD service principal (mesh-dev-sp) ──────────────────
-- These require admin or MANAGE grant — cannot be dropped by ana.cunha directly.

DROP SCHEMA IF EXISTS mesh_dev_db.dev_mesh_dev_sp_dev_ana_cunha     CASCADE;
DROP SCHEMA IF EXISTS mesh_dev_db.dev_mesh_dev_sp_pr_7_dev_ana_cunha CASCADE;
DROP SCHEMA IF EXISTS mesh_dev_db.dev_mesh_dev_sp_pr_8_dev_ana_cunha CASCADE;
DROP SCHEMA IF EXISTS mesh_dev_db.dev_mesh_dev_sp_preview_pr_5       CASCADE;

-- ── Schemas created by ana.cunha (local deploys) ──────────────────────────────
-- ana.cunha may be able to drop these herself; included here for completeness.

DROP SCHEMA IF EXISTS mesh_dev_db.dev_ana_cunha                      CASCADE;
DROP SCHEMA IF EXISTS mesh_dev_db.dev_ana_cunha_dev_ana_cunha        CASCADE;
DROP SCHEMA IF EXISTS mesh_dev_db.dev_ana_cunha_pr_7_dev_ana_cunha   CASCADE;
