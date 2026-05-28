"""Unit tests for charts.py — smoke tests for chart builder functions."""

import charts
import pandas as pd
import pytest


@pytest.fixture
def orders_df():
    return pd.DataFrame({"status": ["Finalizado", "Aberto"], "total": [1500, 800]})


@pytest.fixture
def revenue_df():
    return pd.DataFrame({"segment": ["AUTOMOBILE", "BUILDING"], "revenue": [100000.0, 75000.0]})


@pytest.fixture
def monthly_df():
    return pd.DataFrame({"month": pd.to_datetime(["1993-01-01", "1993-02-01"]), "revenue": [50000.0, 60000.0]})


@pytest.fixture
def delivery_df():
    return pd.DataFrame({
        "shipmode": ["AIR", "SHIP", "TRUCK"],
        "pct_on_time": [95.0, 88.0, 72.0],
        "pct_late": [5.0, 12.0, 28.0],
    })


class TestBarChart:
    def test_returns_something(self, orders_df):
        result = charts.bar_chart(orders_df, "status", "total", "Status", "Pedidos")
        assert result is not None

    def test_currency_flag_accepted(self, revenue_df):
        result = charts.bar_chart(revenue_df, "segment", "revenue", "Segmento", "Receita", currency=True)
        assert result is not None


class TestBarChartH:
    def test_returns_something(self, revenue_df):
        result = charts.bar_chart_h(revenue_df, "revenue", "segment", "Receita", "Segmento")
        assert result is not None

    def test_pct_format(self, delivery_df):
        result = charts.bar_chart_h(delivery_df, "pct_on_time", "shipmode", "%", "Modal", pct=True)
        assert result is not None


class TestLineChart:
    def test_returns_something(self, monthly_df):
        result = charts.line_chart(monthly_df, "month", "revenue", "Mês", "Receita", currency=True)
        assert result is not None

    def test_without_currency(self, monthly_df):
        result = charts.line_chart(monthly_df, "month", "revenue", "Mês", "Total")
        assert result is not None


class TestStackedDeliveryChart:
    def test_returns_something(self, delivery_df):
        result = charts.stacked_delivery_chart(delivery_df)
        assert result is not None

    def test_does_not_mutate_input(self, delivery_df):
        original_cols = list(delivery_df.columns)
        charts.stacked_delivery_chart(delivery_df)
        assert list(delivery_df.columns) == original_cols

    def test_single_shipmode(self):
        df = pd.DataFrame({"shipmode": ["AIR"], "pct_on_time": [90.0], "pct_late": [10.0]})
        result = charts.stacked_delivery_chart(df)
        assert result is not None
