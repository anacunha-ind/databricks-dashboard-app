"""Altair chart components for the Retail Analytics Dashboard."""

import altair as alt
import pandas as pd

# Indicium AI brand palette
_PALETTE = ["#3a58ee", "#699bfb", "#aae2e5", "#dedaf4", "#1c1d2f"]
_COLOR_ON_TIME = "#3a58ee"
_COLOR_LATE = "#aae2e5"

# Vega expression: compact currency with Portuguese Mi / Bi suffixes
_CURRENCY_AXIS_EXPR = (
    "datum.value >= 1e9 ? '$' + format(datum.value / 1e9, '.1f') + 'Bi' : "
    "datum.value >= 1e6 ? '$' + format(datum.value / 1e6, '.1f') + 'Mi' : "
    "'$' + format(datum.value, ',.0f')"
)

# Vega expression: compact number (no currency symbol)
_COMPACT_AXIS_EXPR = (
    "datum.value >= 1e9 ? format(datum.value / 1e9, '.1f') + 'Bi' : "
    "datum.value >= 1e6 ? format(datum.value / 1e6, '.1f') + 'Mi' : "
    "datum.value >= 1e3 ? format(datum.value / 1e3, '.1f') + 'k' : "
    "format(datum.value, ',.0f')"
)


def _currency_label_expr(field: str) -> str:
    """Return a Vega calculate expression that formats a field as $Mi / $Bi."""
    return (
        f"datum['{field}'] >= 1e9 ? '$' + format(datum['{field}'] / 1e9, '.1f') + 'Bi' : "
        f"datum['{field}'] >= 1e6 ? '$' + format(datum['{field}'] / 1e6, '.1f') + 'Mi' : "
        f"'$' + format(datum['{field}'], ',.0f')"
    )


def _compact_label_expr(field: str) -> str:
    """Return a Vega calculate expression that formats a count field as k / Mi."""
    return (
        f"datum['{field}'] >= 1e6 ? format(datum['{field}'] / 1e6, '.1f') + 'Mi' : "
        f"datum['{field}'] >= 1e3 ? format(datum['{field}'] / 1e3, '.1f') + 'k' : "
        f"format(datum['{field}'], ',.0f')"
    )


def bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    x_title: str,
    y_title: str,
    currency: bool = False,
    labels: bool = False,
) -> alt.Chart:
    """Return a vertical bar chart sorted by descending value."""
    tooltip_fmt = "$,.0f" if currency else ",.0f"
    y_axis = alt.Axis(labelExpr=_CURRENCY_AXIS_EXPR) if currency else alt.Axis(format=",.0f")
    base = alt.Chart(df)
    bars = (
        base.mark_bar()
        .encode(
            x=alt.X(f"{x}:N", sort="-y", title=x_title),
            y=alt.Y(f"{y}:Q", title=y_title, axis=y_axis),
            color=alt.Color(
                f"{x}:N",
                scale=alt.Scale(range=_PALETTE),
                legend=alt.Legend(title=x_title),
            ),
            tooltip=[
                alt.Tooltip(f"{x}:N", title=x_title),
                alt.Tooltip(f"{y}:Q", title=y_title, format=tooltip_fmt),
            ],
        )
        .properties(height=300)
    )
    if not labels:
        return bars
    label_expr = _currency_label_expr(y) if currency else _compact_label_expr(y)
    text_layer = (
        base.transform_calculate(label=label_expr)
        .mark_text(align="center", dy=-6, fontSize=11, color="#0d0e1c")
        .encode(
            x=alt.X(f"{x}:N", sort="-y"),
            y=alt.Y(f"{y}:Q"),
            text=alt.Text("label:N"),
        )
    )
    return (bars + text_layer).properties(height=300)


def bar_chart_h(
    df: pd.DataFrame,
    x: str,
    y: str,
    x_title: str,
    y_title: str,
    currency: bool = False,
    pct: bool = False,
) -> alt.Chart:
    """Return a horizontal bar chart with inline value labels."""
    tooltip_fmt = ".1f" if pct else ("$,.0f" if currency else ",.0f")
    x_axis = alt.Axis(labelExpr=_CURRENCY_AXIS_EXPR) if currency else alt.Axis(format=".1f" if pct else ",.0f")

    base = alt.Chart(df)
    bars = base.mark_bar(color=_PALETTE[0]).encode(
        y=alt.Y(f"{y}:N", sort="-x", title=y_title),
        x=alt.X(f"{x}:Q", title=x_title, axis=x_axis),
        tooltip=[
            alt.Tooltip(f"{y}:N", title=y_title),
            alt.Tooltip(f"{x}:Q", title=x_title, format=tooltip_fmt),
        ],
    )

    if currency:
        text_layer = (
            base.transform_calculate(label=_currency_label_expr(x))
            .mark_text(align="left", dx=4, fontSize=11, color="#0d0e1c")
            .encode(
                y=alt.Y(f"{y}:N", sort="-x"),
                x=alt.X(f"{x}:Q"),
                text=alt.Text("label:N"),
            )
        )
    else:
        fmt = ".1f" if pct else ",.0f"
        text_layer = base.mark_text(align="left", dx=4, fontSize=11, color="#0d0e1c").encode(
            y=alt.Y(f"{y}:N", sort="-x"),
            x=alt.X(f"{x}:Q"),
            text=alt.Text(f"{x}:Q", format=fmt),
        )

    return (bars + text_layer).properties(height=300)


def line_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    x_title: str,
    y_title: str,
    currency: bool = False,
    compact: bool = False,
    y_tick_step: float | None = None,
) -> alt.Chart:
    """Return a line chart with point markers."""
    tooltip_fmt = "$,.0f" if currency else ",.0f"
    if currency:
        axis_kwargs: dict = {"labelExpr": _CURRENCY_AXIS_EXPR}
    elif compact:
        axis_kwargs = {"labelExpr": _COMPACT_AXIS_EXPR}
    else:
        axis_kwargs = {"format": ",.0f"}
    if y_tick_step is not None:
        axis_kwargs["tickMinStep"] = y_tick_step
    y_axis = alt.Axis(**axis_kwargs)
    return (
        alt.Chart(df)
        .mark_line(point=True, color=_PALETTE[0])
        .encode(
            x=alt.X(f"{x}:T", title=x_title),
            y=alt.Y(f"{y}:Q", title=y_title, axis=y_axis),
            tooltip=[
                alt.Tooltip(f"{x}:T", title=x_title),
                alt.Tooltip(f"{y}:Q", title=y_title, format=tooltip_fmt),
            ],
        )
        .properties(height=300)
    )


def stacked_delivery_chart(df: pd.DataFrame) -> alt.Chart:
    """Return a stacked horizontal bar chart for on-time vs late delivery rates."""
    sort_order = df["shipmode"].tolist()

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
            scale=alt.Scale(domain=["No Prazo", "Atrasado"], range=[_COLOR_ON_TIME, _COLOR_LATE]),
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
