"""Retail Analytics Dashboard - Databricks App.

Dashboard de varejo com dados reais do catálogo samples.tpch (Delta Lake).
"""

import os
import traceback
from datetime import date

import altair as alt
import pandas as pd
import streamlit as st
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState

WAREHOUSE_ID = os.getenv("WAREHOUSE_ID")
CATALOG = os.getenv("CATALOG_NAME", "samples")
SCHEMA = os.getenv("SCHEMA_NAME", "tpch")

# TPC-H scale 10 date range
DATE_MIN = date(1992, 1, 1)
DATE_MAX = date(1998, 12, 31)
ALL_SEGMENTS = ["AUTOMOBILE", "BUILDING", "FURNITURE", "HOUSEHOLD", "MACHINERY"]

if not WAREHOUSE_ID:
    st.error("WAREHOUSE_ID environment variable is required.")
    st.stop()


@st.cache_resource
def _client() -> WorkspaceClient:
    # M2M OAuth — DATABRICKS_CLIENT_ID + DATABRICKS_CLIENT_SECRET injected by Databricks Apps
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


def _date_clause(start: date, end: date, col: str = "o.o_orderdate") -> str:
    return f"{col} BETWEEN '{start}' AND '{end}'"


def _segment_clause(segments: tuple[str, ...]) -> str:
    if not segments:
        return "1=1"
    vals = ", ".join(f"'{s}'" for s in segments)
    return f"c.c_mktsegment IN ({vals})"


@st.cache_data(ttl=300)
def _kpis(start: date, end: date, segments: tuple[str, ...]) -> dict:
    seg_join = "JOIN customer c ON o.o_custkey = c.c_custkey" if segments else ""
    seg_where = f"AND {_segment_clause(segments)}" if segments else ""
    df = _run_query(f"""
        SELECT
            COUNT(*)          AS total_orders,
            SUM(o_totalprice) AS total_revenue,
            AVG(o_totalprice) AS avg_order_value
        FROM orders o
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
def _orders_by_status(start: date, end: date, segments: tuple[str, ...]) -> pd.DataFrame:
    seg_join = "JOIN customer c ON o.o_custkey = c.c_custkey" if segments else ""
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
        FROM orders o
        {seg_join}
        WHERE {_date_clause(start, end)}
        {seg_where}
        GROUP BY o.o_orderstatus
        ORDER BY total DESC
    """)


@st.cache_data(ttl=300)
def _revenue_by_segment(start: date, end: date) -> pd.DataFrame:
    return _run_query(f"""
        SELECT c.c_mktsegment AS segment, SUM(o.o_totalprice) AS revenue
        FROM orders o JOIN customer c ON o.o_custkey = c.c_custkey
        WHERE {_date_clause(start, end)}
        GROUP BY c.c_mktsegment
        ORDER BY revenue DESC
    """)


@st.cache_data(ttl=300)
def _top_customers(start: date, end: date, segments: tuple[str, ...]) -> pd.DataFrame:
    seg_where = f"AND {_segment_clause(segments)}" if segments else ""
    return _run_query(f"""
        SELECT c.c_name AS customer, SUM(o.o_totalprice) AS revenue
        FROM orders o JOIN customer c ON o.o_custkey = c.c_custkey
        WHERE {_date_clause(start, end)}
        {seg_where}
        GROUP BY c.c_name
        ORDER BY revenue DESC
        LIMIT 10
    """)


@st.cache_data(ttl=300)
def _top_products(start: date, end: date, segments: tuple[str, ...]) -> pd.DataFrame:
    seg_join = "JOIN customer c ON o.o_custkey = c.c_custkey" if segments else ""
    seg_where = f"AND {_segment_clause(segments)}" if segments else ""
    return _run_query(f"""
        SELECT p.p_name AS product,
               ROUND(SUM(l.l_extendedprice * (1 - l.l_discount)), 2) AS net_revenue
        FROM lineitem l
        JOIN part p ON l.l_partkey = p.p_partkey
        JOIN orders o ON l.l_orderkey = o.o_orderkey
        {seg_join}
        WHERE {_date_clause(start, end)}
        {seg_where}
        GROUP BY p.p_name
        ORDER BY net_revenue DESC
        LIMIT 10
    """)


@st.cache_data(ttl=300)
def _monthly_revenue(start: date, end: date, segments: tuple[str, ...]) -> pd.DataFrame:
    seg_join = "JOIN customer c ON o.o_custkey = c.c_custkey" if segments else ""
    seg_where = f"AND {_segment_clause(segments)}" if segments else ""
    return _run_query(f"""
        SELECT DATE_TRUNC('month', o.o_orderdate) AS month,
               SUM(o.o_totalprice) AS revenue
        FROM orders o
        {seg_join}
        WHERE {_date_clause(start, end)}
        {seg_where}
        GROUP BY 1
        ORDER BY 1
    """)


@st.cache_data(ttl=300)
def _delivery_performance(start: date, end: date, segments: tuple[str, ...]) -> pd.DataFrame:
    seg_where = f"AND {_segment_clause(segments)}" if segments else ""
    return _run_query(f"""
        SELECT
            l.l_shipmode AS shipmode,
            ROUND(COUNT(CASE WHEN l.l_receiptdate <= l.l_commitdate THEN 1 END) * 100.0 / COUNT(*), 1) AS pct_on_time,
            ROUND(COUNT(CASE WHEN l.l_receiptdate > l.l_commitdate THEN 1 END) * 100.0 / COUNT(*), 1)  AS pct_late
        FROM lineitem l
        JOIN orders o ON l.l_orderkey = o.o_orderkey
        JOIN customer c ON o.o_custkey = c.c_custkey
        WHERE l.l_shipdate BETWEEN '{start}' AND '{end}'
        {seg_where}
        GROUP BY l.l_shipmode
        ORDER BY pct_on_time DESC
    """)


def _bar_chart(df: pd.DataFrame, x: str, y: str, x_title: str, y_title: str, currency: bool = False) -> alt.Chart:
    fmt = "$,.0f" if currency else ",.0f"
    return (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X(f"{x}:N", sort="-y", title=x_title),
            y=alt.Y(f"{y}:Q", title=y_title, axis=alt.Axis(format=fmt)),
            color=alt.Color(f"{x}:N", legend=alt.Legend(title=x_title)),
            tooltip=[
                alt.Tooltip(f"{x}:N", title=x_title),
                alt.Tooltip(f"{y}:Q", title=y_title, format=fmt),
            ],
        )
        .properties(height=300)
    )


def _bar_chart_h(
    df: pd.DataFrame, x: str, y: str, x_title: str, y_title: str,
    currency: bool = False, pct: bool = False, labels: bool = False,
) -> alt.Chart:
    fmt = ".1f" if pct else ("$,.0f" if currency else ",.0f")
    base = alt.Chart(df)
    bars = base.mark_bar().encode(
        y=alt.Y(f"{y}:N", sort="-x", title=y_title),
        x=alt.X(f"{x}:Q", title=x_title, axis=alt.Axis(format=fmt)),
        tooltip=[
            alt.Tooltip(f"{y}:N", title=y_title),
            alt.Tooltip(f"{x}:Q", title=x_title, format=fmt),
        ],
    )
    if labels:
        text = base.mark_text(align="left", dx=4, fontSize=12).encode(
            y=alt.Y(f"{y}:N", sort="-x"),
            x=alt.X(f"{x}:Q"),
            text=alt.Text(f"{x}:Q", format=fmt),
        )
        return (bars + text).properties(height=300)
    return bars.properties(height=300)


def _line_chart(df: pd.DataFrame, x: str, y: str, x_title: str, y_title: str, currency: bool = False) -> alt.Chart:
    fmt = "$,.0f" if currency else ",.0f"
    return (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X(f"{x}:T", title=x_title),
            y=alt.Y(f"{y}:Q", title=y_title, axis=alt.Axis(format=fmt)),
            tooltip=[
                alt.Tooltip(f"{x}:T", title=x_title),
                alt.Tooltip(f"{y}:Q", title=y_title, format=fmt),
            ],
        )
        .properties(height=300)
    )


def _stacked_delivery_chart(df: pd.DataFrame) -> alt.Chart:
    sort_order = df["shipmode"].tolist()  # already sorted by pct_on_time DESC from query

    df = df.copy()
    df["mid_on_time"] = df["pct_on_time"] / 2
    df["mid_late"] = df["pct_on_time"] + df["pct_late"] / 2

    df_long = df[["shipmode", "pct_on_time", "pct_late"]].melt(id_vars="shipmode", var_name="tipo", value_name="pct")
    df_long["tipo"] = df_long["tipo"].map({"pct_on_time": "No Prazo", "pct_late": "Atrasado"})

    bars = alt.Chart(df_long).mark_bar().encode(
        y=alt.Y("shipmode:N", sort=sort_order, title="Modal"),
        x=alt.X("pct:Q", title="%", stack="zero", axis=alt.Axis(format=".1f")),
        color=alt.Color(
            "tipo:N",
            scale=alt.Scale(domain=["No Prazo", "Atrasado"], range=["#42A5F5", "#EF5350"]),
            legend=alt.Legend(title=""),
        ),
        tooltip=[
            alt.Tooltip("shipmode:N", title="Modal"),
            alt.Tooltip("tipo:N", title="Status"),
            alt.Tooltip("pct:Q", title="%", format=".1f"),
        ],
    )
    text_on_time = alt.Chart(df).mark_text(align="center", color="white", fontSize=11).encode(
        y=alt.Y("shipmode:N", sort=sort_order),
        x=alt.X("mid_on_time:Q"),
        text=alt.Text("pct_on_time:Q", format=".1f"),
    )
    text_late = alt.Chart(df).mark_text(align="center", color="white", fontSize=11).encode(
        y=alt.Y("shipmode:N", sort=sort_order),
        x=alt.X("mid_late:Q"),
        text=alt.Text("pct_late:Q", format=".1f"),
    )
    return (bars + text_on_time + text_late).properties(height=300)


def main():
    st.set_page_config(page_title="Retail Dashboard", page_icon="🛒", layout="wide")

    with st.sidebar:
        st.header("Filtros")
        date_range = st.date_input(
            "Período",
            value=(DATE_MIN, DATE_MAX),
            min_value=DATE_MIN,
            max_value=DATE_MAX,
        )
        segments = st.multiselect("Segmento de Mercado", ALL_SEGMENTS, placeholder="Todos os segmentos")

    start_date, end_date = (date_range if len(date_range) == 2 else (DATE_MIN, DATE_MAX))
    seg_tuple = tuple(segments)

    st.title("🛒 Retail Analytics Dashboard")
    st.caption(f"Fonte: `{CATALOG}.{SCHEMA}` · Databricks Apps + Delta Lake")

    # KPIs
    try:
        with st.spinner("Carregando métricas..."):
            kpis = _kpis(start_date, end_date, seg_tuple)
        c1, c2, c3 = st.columns(3)
        c1.metric("Total de Pedidos", f"{kpis['total_orders']:,}")
        c2.metric("Receita Total", f"${kpis['total_revenue']:,.0f}")
        c3.metric("Ticket Médio", f"${kpis['avg_order_value']:,.2f}")
    except Exception as e:
        st.error(f"Erro ao carregar KPIs: {e}")
        st.code(traceback.format_exc())
        st.stop()

    st.divider()

    # Pedidos por status | Receita por segmento
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Pedidos por Status")
        try:
            df = _orders_by_status(start_date, end_date, seg_tuple)
            st.altair_chart(_bar_chart(df, "status", "total", "Status", "Pedidos"), use_container_width=True)
        except Exception as e:
            st.error(f"Erro: {e}")
            st.code(traceback.format_exc())

    with col2:
        st.subheader("Receita por Segmento")
        try:
            df = _revenue_by_segment(start_date, end_date)
            st.altair_chart(_bar_chart_h(df, "revenue", "segment", "Receita", "Segmento", currency=True), use_container_width=True)
        except Exception as e:
            st.error(f"Erro: {e}")
            st.code(traceback.format_exc())

    st.divider()

    # Top clientes | Top produtos
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Top 10 Clientes por Receita")
        try:
            df = _top_customers(start_date, end_date, seg_tuple)
            st.altair_chart(_bar_chart_h(df, "revenue", "customer", "Receita", "Cliente", currency=True), use_container_width=True)
        except Exception as e:
            st.error(f"Erro: {e}")
            st.code(traceback.format_exc())

    with col2:
        st.subheader("Top 10 Produtos por Receita Líquida")
        try:
            df = _top_products(start_date, end_date, seg_tuple)
            st.altair_chart(_bar_chart_h(df, "net_revenue", "product", "Receita Líquida", "Produto", currency=True), use_container_width=True)
        except Exception as e:
            st.error(f"Erro: {e}")
            st.code(traceback.format_exc())

    st.divider()

    # Receita mensal | Performance de entrega por modal
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Receita Mensal")
        try:
            df = _monthly_revenue(start_date, end_date, seg_tuple)
            st.altair_chart(_line_chart(df, "month", "revenue", "Mês", "Receita", currency=True), use_container_width=True)
        except Exception as e:
            st.error(f"Erro: {e}")
            st.code(traceback.format_exc())

    with col2:
        st.subheader("Performance de Entrega por Modal (%)")
        try:
            df = _delivery_performance(start_date, end_date, seg_tuple)
            st.altair_chart(_stacked_delivery_chart(df), use_container_width=True)
        except Exception as e:
            st.error(f"Erro: {e}")
            st.code(traceback.format_exc())


if __name__ == "__main__":
    main()
