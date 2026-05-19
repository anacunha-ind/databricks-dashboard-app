"""Retail Analytics Dashboard - Databricks App.

Dashboard de varejo com dados reais do catálogo samples.tpch (Delta Lake).
"""

import os

import pandas as pd
import streamlit as st
from databricks import sql as dbsql

WAREHOUSE_ID = os.getenv("WAREHOUSE_ID")
CATALOG = os.getenv("CATALOG_NAME", "samples")
SCHEMA = os.getenv("SCHEMA_NAME", "tpch")

if not WAREHOUSE_ID:
    st.error("WAREHOUSE_ID environment variable is required.")
    st.stop()


def _run_query(statement: str) -> pd.DataFrame:
    """Execute SQL via sql-connector using the logged-in user's OBO token.

    The Databricks Apps platform injects the user's OAuth token in the
    X-Forwarded-Access-Token header. Using it here lets the app query the
    warehouse with the user's own permissions, avoiding SP permission issues.
    """
    host = os.getenv("DATABRICKS_HOST", "").removeprefix("https://")
    token = st.context.headers.get("X-Forwarded-Access-Token")

    with dbsql.connect(
        server_hostname=host,
        http_path=f"/sql/1.0/warehouses/{WAREHOUSE_ID}",
        access_token=token,
        catalog=CATALOG,
        schema=SCHEMA,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(statement)
            return cur.fetchall_arrow().to_pandas()


@st.cache_data(ttl=300)
def _kpis() -> dict:
    df = _run_query("""
        SELECT
            COUNT(*)        AS total_orders,
            SUM(totalprice) AS total_revenue,
            AVG(totalprice) AS avg_order_value
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
        SELECT orderstatus AS status, COUNT(*) AS total
        FROM orders
        GROUP BY orderstatus
        ORDER BY total DESC
    """)


@st.cache_data(ttl=300)
def _top_customers() -> pd.DataFrame:
    return _run_query("""
        SELECT c.name AS customer, SUM(o.totalprice) AS revenue
        FROM orders o JOIN customer c ON o.custkey = c.custkey
        GROUP BY c.name
        ORDER BY revenue DESC
        LIMIT 10
    """)


@st.cache_data(ttl=300)
def _monthly_revenue() -> pd.DataFrame:
    return _run_query("""
        SELECT
            DATE_TRUNC('month', orderdate) AS month,
            SUM(totalprice)                AS revenue
        FROM orders
        GROUP BY 1
        ORDER BY 1
    """)


def main():
    """Main application entry point."""
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
        st.stop()

    st.divider()

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Pedidos por Status")
        try:
            st.bar_chart(_orders_by_status().set_index("status"))
        except Exception as e:
            st.error(f"Erro: {e}")

    with col_right:
        st.subheader("Top 10 Clientes por Receita")
        try:
            st.bar_chart(_top_customers().set_index("customer"))
        except Exception as e:
            st.error(f"Erro: {e}")

    st.divider()

    st.subheader("Receita Mensal")
    try:
        st.line_chart(_monthly_revenue().set_index("month"))
    except Exception as e:
        st.error(f"Erro: {e}")


if __name__ == "__main__":
    main()
