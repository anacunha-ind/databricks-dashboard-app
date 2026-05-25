"""Altair chart components for the Retail Analytics Dashboard."""

import altair as alt
import pandas as pd


def bar_chart(df: pd.DataFrame, x: str, y: str, x_title: str, y_title: str, currency: bool = False) -> alt.Chart:
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


def bar_chart_h(
    df: pd.DataFrame,
    x: str,
    y: str,
    x_title: str,
    y_title: str,
    currency: bool = False,
    pct: bool = False,
    labels: bool = False,
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


def line_chart(df: pd.DataFrame, x: str, y: str, x_title: str, y_title: str, currency: bool = False) -> alt.Chart:
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


def stacked_delivery_chart(df: pd.DataFrame) -> alt.Chart:
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
