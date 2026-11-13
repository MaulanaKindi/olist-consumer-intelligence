"""Reusable chart functions for Olist intelligence analysis."""

from __future__ import annotations

from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go

# Consistent color palette
COLOR_PALETTE = [
    "#1f77b4",  # blue
    "#ff7f0e",  # orange
    "#2ca02c",  # green
    "#d62728",  # red
    "#9467bd",  # purple
    "#8c564b",  # brown
    "#e377c2",  # pink
    "#7f7f7f",  # gray
    "#bcbd22",  # olive
    "#17becf",  # cyan
]


def plot_distribution(
    df,
    column: str,
    title: str,
    output_path: Path | None = None,
    nbins: int = 30,
) -> go.Figure:
    """Plot a histogram distribution of a numeric column."""
    fig = px.histogram(
        df,
        x=column,
        nbins=nbins,
        title=title,
        color_discrete_sequence=COLOR_PALETTE,
    )
    fig.update_layout(
        xaxis_title=column,
        yaxis_title="Count",
        showlegend=False,
        template="plotly_white",
    )

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.write_image(str(output_path))
        fig.write_html(str(output_path.with_suffix(".html")))

    return fig


def plot_bar_comparison(
    df,
    x: str,
    y: str,
    title: str,
    output_path: Path | None = None,
    color: str | None = None,
    orientation: str = "v",
) -> go.Figure:
    """Plot a bar chart comparing categories."""
    fig = px.bar(
        df,
        x=x,
        y=y,
        color=color,
        title=title,
        color_discrete_sequence=COLOR_PALETTE,
        orientation=orientation,
    )
    fig.update_layout(
        xaxis_title=x,
        yaxis_title=y,
        showlegend=color is not None,
        template="plotly_white",
    )

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.write_image(str(output_path))
        fig.write_html(str(output_path.with_suffix(".html")))

    return fig


def plot_scatter(
    df,
    x: str,
    y: str,
    title: str,
    output_path: Path | None = None,
    color: str | None = None,
    trendline: str = "ols",
) -> go.Figure:
    """Plot a scatter plot with optional trendline."""
    fig = px.scatter(
        df,
        x=x,
        y=y,
        color=color,
        title=title,
        trendline=trendline,
        color_discrete_sequence=COLOR_PALETTE,
    )
    fig.update_layout(
        xaxis_title=x,
        yaxis_title=y,
        template="plotly_white",
    )

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.write_image(str(output_path))
        fig.write_html(str(output_path.with_suffix(".html")))

    return fig


def plot_line(
    df,
    x: str,
    y: str,
    title: str,
    output_path: Path | None = None,
    color: str | None = None,
) -> go.Figure:
    """Plot a line chart."""
    fig = px.line(
        df,
        x=x,
        y=y,
        color=color,
        title=title,
        color_discrete_sequence=COLOR_PALETTE,
        markers=True,
    )
    fig.update_layout(
        xaxis_title=x,
        yaxis_title=y,
        template="plotly_white",
    )

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.write_image(str(output_path))
        fig.write_html(str(output_path.with_suffix(".html")))

    return fig


def plot_box(
    df,
    x: str,
    y: str,
    title: str,
    output_path: Path | None = None,
) -> go.Figure:
    """Plot a box plot."""
    fig = px.box(
        df,
        x=x,
        y=y,
        title=title,
        color_discrete_sequence=COLOR_PALETTE,
    )
    fig.update_layout(
        xaxis_title=x,
        yaxis_title=y,
        template="plotly_white",
    )

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.write_image(str(output_path))
        fig.write_html(str(output_path.with_suffix(".html")))

    return fig
