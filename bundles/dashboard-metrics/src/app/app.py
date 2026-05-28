"""Retail Analytics Dashboard - Databricks App.

Dashboard de varejo com dados do catálogo samples.tpch via Databricks Lakebase.
"""

import os
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
        c2.metric("Receita Total", _fmt_currency(kpis['total_revenue']))
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
            st.altair_chart(charts.bar_chart(df, "status", "total", "Status", "Pedidos", labels=True), use_container_width=True)
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
            charts.line_chart(df, "month", "revenue", "Mês", "Receita", currency=True, y_tick_step=5e9),
            use_container_width=True,
        )
    except Exception as e:
        st.error(f"Erro: {e}")
        st.code(traceback.format_exc())

    st.divider()

    st.subheader("Pedidos por Mês")
    try:
        df = queries.get_monthly_orders(start, end, segments)
        step = _nice_tick_step(float(df["total_orders"].max()))
        st.altair_chart(
            charts.line_chart(df, "month", "total_orders", "Mês", "Pedidos", compact=True, y_tick_step=step),
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


def _nice_tick_step(max_val: float) -> float:
    """Return a round tick step that produces ~5-8 ticks for the given max value."""
    import math
    if max_val <= 0:
        return 1.0
    rough = max_val / 6
    mag = 10 ** math.floor(math.log10(rough))
    n = rough / mag
    factor = 1 if n < 1.5 else 2 if n < 3.5 else 5 if n < 7.5 else 10
    return factor * mag


def _fmt_currency(value: float) -> str:
    if abs(value) >= 1e9:
        return f"${value / 1e9:.1f}Bi"
    if abs(value) >= 1e6:
        return f"${value / 1e6:.1f}Mi"
    return f"${value:,.0f}"


_INTER_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="st-"] { font-family: 'Inter', sans-serif !important; }
</style>
"""


def main():
    """Run the Retail Analytics Dashboard Streamlit app."""
    st.set_page_config(page_title="Retail Analytics Dashboard", page_icon="assets/IndiciumAI_icon.svg", layout="wide")
    st.html(_INTER_CSS)
    st.logo("assets/IndiciumAI_logo_blue.png", size="large")

    start, end, segments = _sidebar()

    pr_id = os.getenv("BITBUCKET_PR_ID")
    env_label = f"Preview PR #{pr_id}" if pr_id else "Dev"

    st.title("Retail Analytics Dashboard")
    st.caption(f"Fonte: `{queries.CATALOG}.{queries.SCHEMA}` · Databricks Apps + Lakebase · {env_label}")

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
