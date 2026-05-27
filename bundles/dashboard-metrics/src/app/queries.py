"""Data access layer for the Retail Analytics Dashboard.

Connects to Databricks Lakebase via psycopg2 (PostgreSQL-compatible protocol).
Falls back to a plain PAT in DATABRICKS_TOKEN for local development.
"""

import os
from datetime import date

import pandas as pd
import psycopg2
import streamlit as st
from databricks.sdk import WorkspaceClient

LAKEBASE_HOST = os.getenv(
    "LAKEBASE_HOST",
    "ep-purple-bonus-d11nbh15.database.us-west-2.cloud.databricks.com",
)
LAKEBASE_PORT = int(os.getenv("LAKEBASE_PORT", "5432"))
LAKEBASE_DATABASE = os.getenv("LAKEBASE_DATABASE", "databricks_postgres")
# LAKEBASE_ENDPOINT: resource path used to generate short-lived OAuth tokens.
# Format: projects/{project_id}/branches/{branch_id}/endpoints/{endpoint_id}
LAKEBASE_ENDPOINT = os.getenv(
    "LAKEBASE_ENDPOINT",
    "projects/sara-lakebase-dbx-app/branches/production/endpoints/primary",
)
# In Apps M2M runtime DATABRICKS_CLIENT_ID is the service-principal's client ID,
# which doubles as the PostgreSQL username for Lakebase.
# For local dev, set LAKEBASE_USER to your Databricks account e-mail.
LAKEBASE_USER = os.getenv("LAKEBASE_USER") or os.getenv("DATABRICKS_CLIENT_ID")

CATALOG = os.getenv("CATALOG_NAME", "samples")
SCHEMA = os.getenv("SCHEMA_NAME", "tpch")

DATE_MIN = date(1992, 1, 1)
DATE_MAX = date(1998, 12, 31)
ALL_SEGMENTS = ["AUTOMOBILE", "BUILDING", "FURNITURE", "HOUSEHOLD", "MACHINERY"]

# Table names — unqualified; schema is set via search_path at connection time.
_T_ORDERS = "orders"
_T_CUSTOMER = "customer"
_T_LINEITEM = "lineitem"
_T_PART = "part"


@st.cache_resource
def _workspace_client() -> WorkspaceClient:
    # M2M OAuth — DATABRICKS_CLIENT_ID + DATABRICKS_CLIENT_SECRET injected by Databricks Apps
    return WorkspaceClient()


@st.cache_data(ttl=2700)  # 45 min — Lakebase OAuth tokens last ~60 min
def _get_token(endpoint: str) -> str:
    """Return a short-lived OAuth token for Lakebase via generate_database_credential."""
    cred = _workspace_client().postgres.generate_database_credential(endpoint=endpoint)
    return cred.token


def _connect() -> psycopg2.extensions.connection:
    return psycopg2.connect(
        host=LAKEBASE_HOST,
        port=LAKEBASE_PORT,
        dbname=LAKEBASE_DATABASE,
        user=LAKEBASE_USER,
        password=_get_token(LAKEBASE_ENDPOINT),
        sslmode="require",
        connect_timeout=30,
        options=f"-c search_path={SCHEMA}",
    )


def _run_query(sql: str) -> pd.DataFrame:
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            cols = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
        df = pd.DataFrame(rows, columns=cols)
    finally:
        conn.close()

    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            continue
        converted = pd.to_numeric(df[col], errors="coerce")
        if converted.notna().all():
            df[col] = converted

    return df


def _date_clause(start: date, end: date, col: str = "o.o_orderdate") -> str:
    return f"{col} BETWEEN '{start}' AND '{end}'"


def _segment_clause(segments: tuple[str, ...]) -> str:
    if not segments:
        return "1=1"
    vals = ", ".join(f"'{s}'" for s in segments)
    return f"c.c_mktsegment IN ({vals})"


@st.cache_data(ttl=300)
def get_kpis(start: date, end: date, segments: tuple[str, ...]) -> dict:
    """Return total orders, total revenue and average order value for the given filters."""
    seg_join = f"JOIN {_T_CUSTOMER} c ON o.o_custkey = c.c_custkey" if segments else ""
    seg_where = f"AND {_segment_clause(segments)}" if segments else ""
    df = _run_query(f"""
        SELECT
            COUNT(*)          AS total_orders,
            SUM(o_totalprice) AS total_revenue,
            AVG(o_totalprice) AS avg_order_value
        FROM {_T_ORDERS} o
        {seg_join}
        WHERE {_date_clause(start, end)}
        {seg_where}
    """)
    row = df.iloc[0]
    return {
        "total_orders": int(row["total_orders"]),
        "total_revenue": float(row["total_revenue"]),
        "avg_order_value": float(row["avg_order_value"]),
    }


@st.cache_data(ttl=300)
def get_orders_by_status(start: date, end: date, segments: tuple[str, ...]) -> pd.DataFrame:
    """Return order counts grouped by translated status label."""
    seg_join = f"JOIN {_T_CUSTOMER} c ON o.o_custkey = c.c_custkey" if segments else ""
    seg_where = f"AND {_segment_clause(segments)}" if segments else ""
    return _run_query(f"""
        SELECT
            CASE o.o_orderstatus
                WHEN 'F' THEN 'Finalizado'
                WHEN 'O' THEN 'Aberto'
                WHEN 'P' THEN 'Em Processamento'
                ELSE o.o_orderstatus
            END AS status,
            COUNT(*) AS total
        FROM {_T_ORDERS} o
        {seg_join}
        WHERE {_date_clause(start, end)}
        {seg_where}
        GROUP BY o.o_orderstatus
        ORDER BY total DESC
    """)


@st.cache_data(ttl=300)
def get_revenue_by_segment(start: date, end: date) -> pd.DataFrame:
    """Return total revenue per market segment, sorted descending."""
    return _run_query(f"""
        SELECT c.c_mktsegment AS segment, SUM(o.o_totalprice) AS revenue
        FROM {_T_ORDERS} o JOIN {_T_CUSTOMER} c ON o.o_custkey = c.c_custkey
        WHERE {_date_clause(start, end)}
        GROUP BY c.c_mktsegment
        ORDER BY revenue DESC
    """)


@st.cache_data(ttl=300)
def get_monthly_revenue(start: date, end: date, segments: tuple[str, ...]) -> pd.DataFrame:
    """Return monthly revenue aggregated by order date truncated to month."""
    seg_join = f"JOIN {_T_CUSTOMER} c ON o.o_custkey = c.c_custkey" if segments else ""
    seg_where = f"AND {_segment_clause(segments)}" if segments else ""
    return _run_query(f"""
        SELECT DATE_TRUNC('month', o.o_orderdate) AS month,
               SUM(o.o_totalprice) AS revenue
        FROM {_T_ORDERS} o
        {seg_join}
        WHERE {_date_clause(start, end)}
        {seg_where}
        GROUP BY 1
        ORDER BY 1
    """)


@st.cache_data(ttl=300)
def get_top_customers(start: date, end: date, segments: tuple[str, ...]) -> pd.DataFrame:
    """Return the top 10 customers by total revenue."""
    seg_where = f"AND {_segment_clause(segments)}" if segments else ""
    return _run_query(f"""
        SELECT c.c_name AS customer, SUM(o.o_totalprice) AS revenue
        FROM {_T_ORDERS} o JOIN {_T_CUSTOMER} c ON o.o_custkey = c.c_custkey
        WHERE {_date_clause(start, end)}
        {seg_where}
        GROUP BY c.c_name
        ORDER BY revenue DESC
        LIMIT 10
    """)


@st.cache_data(ttl=300)
def get_top_products(start: date, end: date, segments: tuple[str, ...]) -> pd.DataFrame:
    """Return the top 10 products by net revenue (extended price minus discount)."""
    seg_join = f"JOIN {_T_CUSTOMER} c ON o.o_custkey = c.c_custkey" if segments else ""
    seg_where = f"AND {_segment_clause(segments)}" if segments else ""
    return _run_query(f"""
        SELECT p.p_name AS product,
               ROUND(SUM(l.l_extendedprice * (1 - l.l_discount)), 2) AS net_revenue
        FROM {_T_LINEITEM} l
        JOIN {_T_PART} p ON l.l_partkey = p.p_partkey
        JOIN {_T_ORDERS} o ON l.l_orderkey = o.o_orderkey
        {seg_join}
        WHERE {_date_clause(start, end)}
        {seg_where}
        GROUP BY p.p_name
        ORDER BY net_revenue DESC
        LIMIT 10
    """)


@st.cache_data(ttl=300)
def get_delivery_performance(start: date, end: date, segments: tuple[str, ...]) -> pd.DataFrame:
    """Return on-time vs late delivery percentages per ship mode."""
    seg_where = f"AND {_segment_clause(segments)}" if segments else ""
    return _run_query(f"""
        SELECT
            l.l_shipmode AS shipmode,
            ROUND(COUNT(CASE WHEN l.l_receiptdate <= l.l_commitdate THEN 1 END) * 100.0 / COUNT(*), 1) AS pct_on_time,
            ROUND(COUNT(CASE WHEN l.l_receiptdate > l.l_commitdate THEN 1 END) * 100.0 / COUNT(*), 1)  AS pct_late
        FROM {_T_LINEITEM} l
        JOIN {_T_ORDERS} o ON l.l_orderkey = o.o_orderkey
        JOIN {_T_CUSTOMER} c ON o.o_custkey = c.c_custkey
        WHERE l.l_shipdate BETWEEN '{start}' AND '{end}'
        {seg_where}
        GROUP BY l.l_shipmode
        ORDER BY pct_on_time DESC
    """)
