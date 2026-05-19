"""Retail Analytics Dashboard - Databricks App.

Dashboard de varejo com dados reais do catálogo samples.tpch (Delta Lake).
"""

import os
import traceback

import pandas as pd
import streamlit as st
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState

WAREHOUSE_ID = os.getenv("WAREHOUSE_ID")
CATALOG = os.getenv("CATALOG_NAME", "samples")
SCHEMA = os.getenv("SCHEMA_NAME", "tpch")

if not WAREHOUSE_ID:
    st.error("WAREHOUSE_ID environment variable is required.")
    st.stop()


@st.cache_resource
def _client() -> WorkspaceClient:
    # Uses DATABRICKS_CLIENT_ID + DATABRICKS_CLIENT_SECRET from env (M2M OAuth)
    return WorkspaceClient()


def _run_query(statement: str) -> pd.DataFrame:
    w = _client()
    response = w.statement_execution.execute_statement(
        statement=statement,
        warehouse_id=WAREHOUSE_ID,
        catalog=CATALOG,
        schema=SCHEMA,
        wait_timeout="30s",
    )

    if response.status.state != StatementState.SUCCEEDED:
        error = response.status.error
        msg = error.message if error else str(response.status.state)
        raise RuntimeError(f"Query failed: {msg}")

    cols = [c.name for c in response.manifest.schema.columns]
    rows = response.result.data_array or []
    df = pd.DataFrame(rows, columns=cols)

    for col in df.columns:
        converted = pd.to_numeric(df[col], errors="coerce")
        if converted.notna().all():
            df[col] = converted

    return df


@st.cache_data(ttl=300)
def _kpis() -> dict:
    df = _run_query("""
        SELECT
            COUNT(*)          AS total_orders,
            SUM(o_totalprice) AS total_revenue,
            AVG(o_totalprice) AS avg_order_value
        FROM orders
    """)
    row = df.iloc[0]
    return {
        "total_orders": int(row["total_orders"]),
        "total_revenue": float(row["total_revenue"]),
        "avg_order_value": float(row["avg_order_value"]),
    }


@st.cache_data(ttl=300)
def _orders_by_status() -> pd.DataFrame:
    return _run_query("""
        SELECT o_orderstatus AS status, COUNT(*) AS total
        FROM orders
        GROUP BY o_orderstatus
        ORDER BY total DESC
    """)


@st.cache_data(ttl=300)
def _top_customers() -> pd.DataFrame:
    return _run_query("""
        SELECT c.c_name AS customer, SUM(o.o_totalprice) AS revenue
        FROM orders o JOIN customer c ON o.o_custkey = c.c_custkey
        GROUP BY c.c_name
        ORDER BY revenue DESC
        LIMIT 10
    """)


@st.cache_data(ttl=300)
def _monthly_revenue() -> pd.DataFrame:
    return _run_query("""
        SELECT
            DATE_TRUNC('month', o_orderdate) AS month,
            SUM(o_totalprice)                AS revenue
        FROM orders
        GROUP BY 1
        ORDER BY 1
    """)


def main():
    st.set_page_config(
        page_title="Retail Dashboard",
        page_icon="🛒",
        layout="wide",
    )

    st.title("🛒 Retail Analytics Dashboard")
    st.caption(f"Fonte: `{CATALOG}.{SCHEMA}` · Databricks Apps + Delta Lake")

    # KPIs
    try:
        with st.spinner("Carregando métricas..."):
            kpis = _kpis()
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Pedidos", f"{kpis['total_orders']:,}")
        col2.metric("Receita Total", f"${kpis['total_revenue']:,.0f}")
        col3.metric("Ticket Médio", f"${kpis['avg_order_value']:,.2f}")
    except Exception as e:
        st.error(f"Erro ao carregar KPIs: {e}")
        st.code(traceback.format_exc())
        st.stop()

    st.divider()

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Pedidos por Status")
        try:
            st.bar_chart(_orders_by_status().set_index("status"))
        except Exception as e:
            st.error(f"Erro: {e}")
            st.code(traceback.format_exc())

    with col_right:
        st.subheader("Top 10 Clientes por Receita")
        try:
            st.bar_chart(_top_customers().set_index("customer"))
        except Exception as e:
            st.error(f"Erro: {e}")
            st.code(traceback.format_exc())

    st.divider()

    st.subheader("Receita Mensal")
    try:
        st.line_chart(_monthly_revenue().set_index("month"))
    except Exception as e:
        st.error(f"Erro: {e}")
        st.code(traceback.format_exc())


if __name__ == "__main__":
    main()
