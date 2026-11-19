"""Tests for pure chart title helpers and synthetic chart rendering."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from scripts.export_analysis import (
    apply_chart_style,
    plot_monthly_orders,
    plot_revenue_by_state,
    plot_review_by_delivery,
    title_monthly_orders,
    title_revenue_by_state,
    title_review_by_delivery,
)


def _review_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "delivery_time_bucket": [
                "0-3 days",
                "4-7 days",
                "8-14 days",
                "15-30 days",
                "30+ days",
            ],
            "reviews": [6951, 23730, 37986, 23485, 4207],
            "avg_review_score": [4.464, 4.397, 4.298, 3.940, 2.204],
        }
    )


def _monthly_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "month": ["2017-01", "2017-02", "2017-03"],
            "order_count": [1000, 5000, 3000],
            "gmv_payments": [100000.0, 500000.0, 300000.0],
            "is_partial_boundary_month": [False, False, False],
        }
    )


def _geo_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "state": ["SP", "RJ", "MG"],
            "order_count": [41746, 12852, 11635],
            "gmv_payments": [5998227.0, 2144380.0, 1872257.0],
        }
    )


def _is_png(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 0 and path.read_bytes()[:4] == b"\x89PNG"


def test_review_title_computes_from_data():
    title = title_review_by_delivery(_review_df())
    assert "30+ days" in title
    assert "2.2" in title
    assert "0-3 days" in title
    assert "4.5" in title


def test_review_title_changes_when_data_changes():
    base = title_review_by_delivery(_review_df())
    altered = _review_df()
    altered.loc[altered["delivery_time_bucket"] == "30+ days", "avg_review_score"] = 4.0
    changed = title_review_by_delivery(altered)
    assert changed != base
    assert "15-30 days" in changed
    assert "3.9" in changed


def test_monthly_title_uses_peak_month():
    title = title_monthly_orders(_monthly_df())
    assert "2017-02" in title
    assert "5,000" in title


def test_monthly_title_changes_when_data_changes():
    base = title_monthly_orders(_monthly_df())
    altered = _monthly_df()
    altered.loc[altered["month"] == "2017-03", "order_count"] = 9000
    changed = title_monthly_orders(altered)
    assert changed != base
    assert "2017-03" in changed


def test_state_title_computes_share():
    title = title_revenue_by_state(_geo_df())
    total = 5998227.0 + 2144380.0 + 1872257.0
    share = 5998227.0 / total
    assert "SP" in title
    assert f"{share:.0%}" in title


def test_state_title_changes_when_data_changes():
    base = title_revenue_by_state(_geo_df())
    altered = _geo_df()
    altered.loc[altered["state"] == "RJ", "gmv_payments"] = 9000000.0
    changed = title_revenue_by_state(altered)
    assert changed != base
    assert "RJ" in changed


def test_apply_chart_style_removes_top_right_spines():
    fig, ax = plt.subplots()
    ax.plot([1, 2], [1, 2])
    apply_chart_style(ax)
    assert not ax.spines["top"].get_visible()
    assert not ax.spines["right"].get_visible()
    plt.close(fig)


def test_render_review_by_delivery_png(tmp_path):
    fig, ax = plt.subplots()
    plot_review_by_delivery(ax, _review_df())
    out = tmp_path / "review_by_delivery_bucket.png"
    fig.savefig(out)
    plt.close(fig)
    assert _is_png(out)


def test_render_monthly_orders_png(tmp_path):
    fig, ax = plt.subplots()
    plot_monthly_orders(ax, _monthly_df())
    out = tmp_path / "monthly_orders.png"
    fig.savefig(out)
    plt.close(fig)
    assert _is_png(out)


def test_render_revenue_by_state_png(tmp_path):
    fig, ax = plt.subplots()
    plot_revenue_by_state(ax, _geo_df())
    out = tmp_path / "revenue_by_state.png"
    fig.savefig(out)
    plt.close(fig)
    assert _is_png(out)


def _monthly_alignment_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "month": ["2017-01", "2017-02", "2017-03", "2017-04", "2017-05", "2017-06"],
            "order_count": [100, 0, 200, 300, 250, 150],
            "gmv_payments": [1000.0, 0.0, 2000.0, 3000.0, 2500.0, 1500.0],
            "is_partial_boundary_month": [True, False, False, False, False, True],
        }
    )


def test_monthly_chart_x_alignment():
    """Regression: plotted x positions must equal spine indices, not a re-indexed subset."""
    fig, ax = plt.subplots()
    df = _monthly_alignment_df()
    plot_monthly_orders(ax, df)

    line = ax.lines[0]
    xs = [float(v) for v in line.get_xdata()]
    ys = [float(v) for v in line.get_ydata()]
    labels = [lbl.get_text() for lbl in ax.get_xticklabels()]

    months = list(df["month"])
    n = len(months)

    # (a) every plotted x equals that month's index in the spine
    for x in xs:
        assert x == int(x), f"non-integer x: {x}"
        assert 0 <= int(x) < n, f"x out of spine range: {x}"

    # (b) the tick label at each plotted x equals that month's string
    for x in xs:
        xi = int(x)
        assert (
            labels[xi] == months[xi]
        ), f"tick label mismatch at x={xi}: {labels[xi]!r} != {months[xi]!r}"

    # (c) the x of the maximum-order point has a tick label equal to the month
    # named by title_monthly_orders
    max_i = ys.index(max(ys))
    max_x = int(xs[max_i])
    title = title_monthly_orders(df)
    peak_month = title.split("peaked in ")[1].split(" with ")[0]
    assert (
        labels[max_x] == peak_month
    ), f"peak x tick {labels[max_x]!r} != title month {peak_month!r}"

    # scatter (partial/near-zero months) must also sit at spine positions
    if ax.collections:
        offsets = ax.collections[0].get_offsets()
        for ox, _ in offsets:
            oxi = int(round(float(ox)))
            assert 0 <= oxi < n, f"scatter x out of spine range: {ox}"

    plt.close(fig)
