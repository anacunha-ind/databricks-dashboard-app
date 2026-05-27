"""Unit tests for queries.py — helper functions and data access layer."""

from datetime import date
from unittest.mock import MagicMock, patch

import pandas as pd
import queries


class TestDateClause:
    def test_default_column(self):
        result = queries._date_clause(date(1992, 1, 1), date(1995, 12, 31))
        assert result == "o.o_orderdate BETWEEN '1992-01-01' AND '1995-12-31'"

    def test_custom_column(self):
        result = queries._date_clause(date(1993, 6, 1), date(1994, 6, 1), col="l.l_shipdate")
        assert result == "l.l_shipdate BETWEEN '1993-06-01' AND '1994-06-01'"

    def test_same_day_range(self):
        result = queries._date_clause(date(1995, 1, 1), date(1995, 1, 1))
        assert "1995-01-01" in result


class TestSegmentClause:
    def test_empty_segments_returns_passthrough(self):
        assert queries._segment_clause(()) == "1=1"

    def test_single_segment(self):
        result = queries._segment_clause(("AUTOMOBILE",))
        assert result == "c.c_mktsegment IN ('AUTOMOBILE')"

    def test_multiple_segments(self):
        result = queries._segment_clause(("AUTOMOBILE", "BUILDING"))
        assert "'AUTOMOBILE'" in result
        assert "'BUILDING'" in result
        assert "c.c_mktsegment IN" in result

    def test_all_segments(self):
        result = queries._segment_clause(tuple(queries.ALL_SEGMENTS))
        for seg in queries.ALL_SEGMENTS:
            assert f"'{seg}'" in result


class TestRunQuery:
    def _mock_connection(self, columns: list[str], rows: list[tuple]):
        mock_cursor = MagicMock()
        mock_cursor.description = [(col,) for col in columns]
        mock_cursor.fetchall.return_value = rows
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        return mock_conn

    @patch("queries._connect")
    def test_returns_dataframe(self, mock_connect):
        mock_connect.return_value = self._mock_connection(
            columns=["name", "value"],
            rows=[("alice", 100), ("bob", 200)],
        )
        df = queries._run_query("SELECT name, value FROM t")
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["name", "value"]
        assert len(df) == 2

    @patch("queries._connect")
    def test_numeric_columns_are_converted(self, mock_connect):
        mock_connect.return_value = self._mock_connection(
            columns=["total"],
            rows=[("42",), ("100",)],
        )
        df = queries._run_query("SELECT total FROM t")
        assert df["total"].dtype in ["float64", "int64"]

    @patch("queries._connect")
    def test_mixed_columns_not_converted(self, mock_connect):
        mock_connect.return_value = self._mock_connection(
            columns=["name", "total"],
            rows=[("alice", "42"), ("bob", "100")],
        )
        df = queries._run_query("SELECT name, total FROM t")
        assert pd.api.types.is_string_dtype(df["name"])
        assert pd.api.types.is_numeric_dtype(df["total"])

    @patch("queries._connect")
    def test_connection_is_always_closed(self, mock_connect):
        mock_conn = self._mock_connection(columns=["x"], rows=[(1,)])
        mock_connect.return_value = mock_conn
        queries._run_query("SELECT x FROM t")
        mock_conn.close.assert_called_once()


class TestConstants:
    def test_all_segments_has_five_entries(self):
        assert len(queries.ALL_SEGMENTS) == 5

    def test_date_range_covers_tpch(self):
        assert date(1992, 1, 1) == queries.DATE_MIN
        assert date(1998, 12, 31) == queries.DATE_MAX

    def test_table_references_are_unqualified(self):
        # Lakebase is PostgreSQL — 3-part catalog.schema.table names are not
        # supported. Schema resolution is done via search_path at connect time.
        assert queries._T_ORDERS == "orders"
        assert queries._T_CUSTOMER == "customer"
        assert queries._T_LINEITEM == "lineitem"
        assert queries._T_PART == "part"
