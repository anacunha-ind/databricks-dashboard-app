"""Retail Analytics Dashboard - Databricks App.

Dashboard de varejo com dados do catálogo samples.tpch via Databricks Lakebase.
"""

import traceback

import charts
import queries
import streamlit as st
from queries import ALL_SEGMENTS, DATE_MAX, DATE_MIN


def _sidebar() -> tuple:
    with st.sidebar:
        st.header("Filtros")
        date_range = st.date_input(
            "Período",
            value=(DATE_MIN, DATE_MAX),
            min_value=DATE_MIN,
            max_value=DATE_MAX,
        )
        segments = st.multiselect("Segmento de Mercado", ALL_SEGMENTS, placeholder="Todos os segmentos")

    start, end = date_range if len(date_range) == 2 else (DATE_MIN, DATE_MAX)
    return start, end, tuple(segments)


def _kpi_row(start, end, segments):
    try:
        with st.spinner("Carregando métricas..."):
            kpis = queries.get_kpis(start, end, segments)
        c1, c2, c3 = st.columns(3)
        c1.metric("Total de Pedidos", f"{kpis['total_orders']:,}")
        c2.metric("Receita Total", f"${kpis['total_revenue']:,.0f}")
        c3.metric("Ticket Médio", f"${kpis['avg_order_value']:,.2f}")
    except Exception as e:
        st.error(f"Erro ao carregar KPIs: {e}")
        st.code(traceback.format_exc())
        st.stop()


def _tab_overview(start, end, segments):
    _kpi_row(start, end, segments)
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Pedidos por Status")
        try:
            df = queries.get_orders_by_status(start, end, segments)
            st.altair_chart(charts.bar_chart(df, "status", "total", "Status", "Pedidos"), use_container_width=True)
        except Exception as e:
            st.error(f"Erro: {e}")
            st.code(traceback.format_exc())

    with col2:
        st.subheader("Receita por Segmento")
        try:
            df = queries.get_revenue_by_segment(start, end)
            st.altair_chart(
                charts.bar_chart_h(df, "revenue", "segment", "Receita", "Segmento", currency=True),
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Erro: {e}")
            st.code(traceback.format_exc())


def _tab_orders(start, end, segments):
    st.subheader("Receita Mensal")
    try:
        df = queries.get_monthly_revenue(start, end, segments)
        st.altair_chart(
            charts.line_chart(df, "month", "revenue", "Mês", "Receita", currency=True),
            use_container_width=True,
        )
    except Exception as e:
        st.error(f"Erro: {e}")
        st.code(traceback.format_exc())

    st.divider()

    st.subheader("Pedidos por Status")
    try:
        df = queries.get_orders_by_status(start, end, segments)
        st.altair_chart(
            charts.bar_chart(df, "status", "total", "Status", "Pedidos"),
            use_container_width=True,
        )
    except Exception as e:
        st.error(f"Erro: {e}")
        st.code(traceback.format_exc())


def _tab_customers(start, end, segments):
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Top 10 Clientes por Receita")
        try:
            df = queries.get_top_customers(start, end, segments)
            st.altair_chart(
                charts.bar_chart_h(df, "revenue", "customer", "Receita", "Cliente", currency=True),
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Erro: {e}")
            st.code(traceback.format_exc())

    with col2:
        st.subheader("Receita por Segmento")
        try:
            df = queries.get_revenue_by_segment(start, end)
            st.altair_chart(
                charts.bar_chart_h(df, "revenue", "segment", "Receita", "Segmento", currency=True),
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Erro: {e}")
            st.code(traceback.format_exc())


def _tab_products(start, end, segments):
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Top 10 Produtos por Receita Líquida")
        try:
            df = queries.get_top_products(start, end, segments)
            st.altair_chart(
                charts.bar_chart_h(df, "net_revenue", "product", "Receita Líquida", "Produto", currency=True),
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Erro: {e}")
            st.code(traceback.format_exc())

    with col2:
        st.subheader("Performance de Entrega por Modal (%)")
        try:
            df = queries.get_delivery_performance(start, end, segments)
            st.altair_chart(charts.stacked_delivery_chart(df), use_container_width=True)
        except Exception as e:
            st.error(f"Erro: {e}")
            st.code(traceback.format_exc())


def main():
    """Run the Retail Analytics Dashboard Streamlit app."""
    st.set_page_config(page_title="Retail Dashboard", page_icon="🛒", layout="wide")

    start, end, segments = _sidebar()

    st.title("🛒 Retail Analytics Dashboard")
    st.caption(f"Fonte: `{queries.CATALOG}.{queries.SCHEMA}` · Databricks Apps + Lakebase")

    tab1, tab2, tab3, tab4 = st.tabs(["Visão Geral", "Pedidos", "Clientes", "Produtos & Logística"])

    with tab1:
        _tab_overview(start, end, segments)

    with tab2:
        _tab_orders(start, end, segments)

    with tab3:
        _tab_customers(start, end, segments)

    with tab4:
        _tab_products(start, end, segments)


if __name__ == "__main__":
    main()
