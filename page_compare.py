import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from ticker_strip import render_ticker_strip
from comparator import compare_stocks
from theme import get_tokens, get_is_dark, icon, rail_header, chart_layout, render_nav


def _cached_compare(ticker_a, ticker_b):
    return compare_stocks(ticker_a, ticker_b)


def _build_radar_chart(report):
    T = get_tokens()
    fig = go.Figure()
    ta = report["ticker_a"]
    tb = report["ticker_b"]
    sc = report["scores"]

    axes = ["Predicted Return", "Risk", "Confidence", "Sentiment"]
    kv = {"predicted_return": 0, "volatility": 1,
          "model_confidence": 2, "sentiment": 3}
    ra, rb = [], []
    for dk, idx in kv.items():
        dd = sc.get(dk, {})
        na = dd.get("norm_a", 50) or 50
        nb = dd.get("norm_b", 50) or 50
        ra.append(na)
        rb.append(nb)
    ra.append(ra[0])
    rb.append(rb[0])
    axes.append(axes[0])

    fig.add_trace(go.Scatterpolar(
        r=ra, theta=axes, fill="toself",
        name=ta, line=dict(color=T["accent_blue"], width=2),
        fillcolor=f"rgba({int(T['accent_blue'][1:3],16)},{int(T['accent_blue'][3:5],16)},{int(T['accent_blue'][5:7],16)},0.22)",
    ))
    fig.add_trace(go.Scatterpolar(
        r=rb, theta=axes, fill="toself",
        name=tb, line=dict(color=T["accent_amber"], width=2),
        fillcolor=f"rgba({int(T['accent_amber'][1:3],16)},{int(T['accent_amber'][3:5],16)},{int(T['accent_amber'][5:7],16)},0.15)",
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100],
                            tickfont=dict(family="JetBrains Mono",
                                          size=9, color=T["text_muted"]),
                            gridcolor=T["border"]),
            angularaxis=dict(tickfont=dict(
                family="Space Grotesk", size=11, color=T["text_secondary"])),
            bgcolor=T["bg_card"],
        ),
        template=T["plotly_theme"], height=340,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=50, r=50, t=50, b=80),
        font=dict(color=T["text_secondary"]),
        legend=dict(orientation="h", yanchor="bottom",
                    y=1.02, xanchor="right", x=1,
                    font=dict(color=T["text_primary"])),
    )
    return fig


def _display_compare_results(report):
    T = get_tokens()
    ta = report["ticker_a"]
    tb = report["ticker_b"]
    sc = report["scores"]
    wr = report.get("winner")
    win_tag = wr.get("winner") if isinstance(wr, dict) else wr
    _tsec = T["text_secondary"]

    st.markdown("<hr/>", unsafe_allow_html=True)

    # ── Winner banner ─────────────────────────────────────────────────────────
    c1, spacer, c2 = st.columns([4, 0.5, 4])
    with c1:
        if win_tag:
            bg_col = T["badge_buy_bg"]
            bd_col = T["badge_buy_bd"]
            txt_col = T["accent_green"]
            txt = f"↑ Recommended: {win_tag}"
        else:
            bg_col = T["badge_hold_bg"]
            bd_col = T["badge_hold_bd"]
            txt_col = T["accent_amber"]
            txt = "⚠ Tie — see suggestions below"
        st.markdown(
            f"<div style='background:{bg_col};border:1px solid {bd_col};color:{txt_col};"
            f"font-family:Space Grotesk,sans-serif;font-size:1.15rem;font-weight:700;"
            f"padding:0.65rem 1.2rem;border-radius:10px;text-align:center;'>{txt}</div>",
            unsafe_allow_html=True,
        )
    with c2:
        ca, cb = st.columns(2)
        ca.metric(f"{ta} Score", f"{report['score_a']:.0f}/{report['total']}",
                  help="Combined weighted score (higher = better)")
        cb.metric(f"{tb} Score", f"{report['score_b']:.0f}/{report['total']}",
                  help="Combined weighted score (higher = better)")

    st.markdown(
        f'<div class="rec-box">{report["reason"]}</div>', unsafe_allow_html=True)

    # ── Score table + radar ───────────────────────────────────────────────────
    cl, cr = st.columns([1, 1])
    with cl:
        rail_header("Dimension breakdown", icon("layers", 13, T["text_muted"]))
        st.caption("*Total score is a weighted sum of the sub-scores below.*")
        rows = []
        wmap = {"predicted_return": 3, "volatility": 2,
                "model_confidence": 2, "sentiment": 2, "price_trend": 1}
        for dk, dd in sc.items():
            w = wmap.get(dk, 1)
            ww = dd.get("winner")
            better = ta if ww == "a" else (tb if ww == "b" else "Tie")
            pts = f"+{w}" if ww in ("a", "b") else f"+{w/2}"
            rows.append({
                "Dimension": dd["label"],
                ta: dd.get("stars_a", "—"),
                tb: dd.get("stars_b", "—"),
                "Better": better,
                "Weight": pts,
            })
        df = pd.DataFrame(rows)
        html = '<table style="width:100%; border-collapse:collapse; font-size:0.84rem; font-family:Inter,sans-serif;">'
        html += f'<thead><tr>'
        for col_name in ["Dimension", ta, tb, "Better", "Pts (Weight)"]:
            align = "left" if col_name == "Dimension" else "center"
            html += (
                f'<th style="text-align:{align}; padding:0.7rem 0.9rem; background:{T["bg_surface"]}; '
                f'color:{_tsec}; border-bottom:1px solid {T["border"]}; font-weight:600; '
                f'text-transform:uppercase; font-size:0.68rem; letter-spacing:0.06em;">{col_name}</th>'
            )
        html += f'</tr></thead><tbody>'
        for _, row in df.iterrows():
            winner = row["Better"]
            if winner == ta:
                better_color = T["accent_green"]
                row_bg = "rgba(46,204,113,0.05)"
            elif winner == tb:
                better_color = T["accent_blue"]
                row_bg = "rgba(76,155,232,0.05)"
            else:
                better_color = T["text_secondary"]
                row_bg = "transparent"
            html += f'<tr style="background:{row_bg};">'
            html += f'<td style="text-align:left; padding:0.6rem 0.9rem; border-bottom:1px solid {T["border"]}; color:{T["text_primary"]};">{row["Dimension"]}</td>'
            html += f'<td style="text-align:center; padding:0.6rem 0.9rem; border-bottom:1px solid {T["border"]}; color:{T["text_primary"]}; font-family:JetBrains Mono,monospace;">{row[ta]}</td>'
            html += f'<td style="text-align:center; padding:0.6rem 0.9rem; border-bottom:1px solid {T["border"]}; color:{T["text_primary"]}; font-family:JetBrains Mono,monospace;">{row[tb]}</td>'
            html += f'<td style="text-align:center; padding:0.6rem 0.9rem; border-bottom:1px solid {T["border"]}; color:{better_color}; font-weight:600; font-size:0.78rem;">{winner}</td>'
            html += f'<td style="text-align:center; padding:0.6rem 0.9rem; border-bottom:1px solid {T["border"]}; color:{_tsec}; font-family:JetBrains Mono,monospace; font-size:0.78rem;">{row["Weight"]}</td>'
            html += '</tr>'
        html += '</tbody></table>'
        st.markdown(html, unsafe_allow_html=True)
        st.caption(
            "Risk: std-dev of daily returns · Confidence: LSTM backtest MSE")

    with cr:
        rail_header("Radar comparison", icon("activity", 13, T["text_muted"]))
        st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
        st.plotly_chart(_build_radar_chart(report), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Forecast chart ────────────────────────────────────────────────────────
    da = report["data_a"]
    db = report["data_b"]
    pa = da.get("predicted_price_7d")
    pb = db.get("predicted_price_7d")
    ha = da.get("historical_prices_30d")
    hb = db.get("historical_prices_30d")
    if pa and pb and ha and hb:
        rail_header("30-day history + 7-day forecast",
                    icon("chart-line", 13, T["text_muted"]))
        base_a = ha[0]
        base_b = hb[0]
        ha_pct = [(p / base_a - 1) * 100 for p in ha]
        pa_pct = [(p / base_a - 1) * 100 for p in pa]
        hb_pct = [(p / base_b - 1) * 100 for p in hb]
        pb_pct = [(p / base_b - 1) * 100 for p in pb]
        hist_days = list(range(1, len(ha) + 1))
        pred_days = list(range(len(ha) + 1, len(ha) + len(pa) + 1))
        f2 = go.Figure()
        f2.add_trace(go.Scatter(x=hist_days, y=ha_pct,
                                mode="lines", name=ta,
                                line=dict(color=T["accent_blue"], width=2)))
        f2.add_trace(go.Scatter(x=[len(ha)] + pred_days, y=[ha_pct[-1]] + pa_pct,
                                mode="lines", showlegend=False,
                                line=dict(color=T["accent_blue"], width=2, dash="dash")))
        f2.add_trace(go.Scatter(x=hist_days, y=hb_pct,
                                mode="lines", name=tb,
                                line=dict(color=T["accent_amber"], width=2)))
        f2.add_trace(go.Scatter(x=[len(hb)] + pred_days, y=[hb_pct[-1]] + pb_pct,
                                mode="lines", showlegend=False,
                                line=dict(color=T["accent_amber"], width=2, dash="dash")))
        f2.add_vline(x=len(ha), line_dash="dot", line_color=T["text_muted"],
                     annotation_text="Today", annotation_position="top left",
                     annotation_font=dict(color=T["text_muted"], size=11, family="Space Grotesk"))
        f2.add_hline(y=0, line_dash="dot",
                     line_color=T["text_muted"], line_width=1)
        f2.update_layout(
            title=dict(text="30-Day History + 7-Day Forecast", font=dict(color=T["text_primary"])),
            xaxis_title="Day", yaxis_title="Cumulative Return (%)",
            template=T["plotly_theme"], height=340,
            margin=dict(l=0, r=0, t=40, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color=T["text_secondary"]),
            legend=dict(orientation="h", yanchor="bottom",
                        y=1.02, xanchor="right", x=1,
                        font=dict(color=T["text_primary"])),
        )
        st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
        st.plotly_chart(f2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f"""
<div class="disclaimer">
  {icon("alert", 13, T["accent_amber"])}
  For educational and research purposes only — not investment advice.
</div>
""", unsafe_allow_html=True)


def render_compare_page():
    T = get_tokens()
    render_ticker_strip()
    render_nav(show_back=False, active_page="compare")

    rail_header("Stock comparison", icon("compare", 13, T["text_muted"]))

    st.markdown("### Select Two Stocks to Compare")
    col_a, col_b, col_btn = st.columns([4, 4, 3])
    with col_a:
        ticker_a = st.text_input(
            "Stock A", placeholder="e.g. AAPL", key="comp_a").strip().upper()
    with col_b:
        ticker_b = st.text_input(
            "Stock B", placeholder="e.g. TSLA", key="comp_b").strip().upper()
    with col_btn:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        run_compare = st.button("Compare", type="primary",
                                use_container_width=True, key="compare_go")

    if run_compare:
        if ticker_a == ticker_b:
            st.warning("Please enter two different stocks to compare.")
            return

        with st.spinner("Fetching data and running predictions for both stocks (this may take a minute)..."):
            report = _cached_compare(ticker_a, ticker_b)

        if report is None:
            st.error(
                "Could not complete comparison. Check the ticker symbols and try again.")
            return

        _display_compare_results(report)
