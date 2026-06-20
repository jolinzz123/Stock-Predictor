import streamlit as st
from data_fetcher import fetch_stock_data, get_stock_info
from ticker_strip import render_ticker_strip
from theme import get_tokens, icon, rail_header, sparkline_svg, render_nav


WATCHLIST = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "META", "AMZN", "TSLA",
    "TSM", "AMD", "BABA", "PDD", "JD", "BIDU",
    "SPY", "QQQ", "JPM", "BRK-B", "NFLX", "DIS", "ENPH",
]


@st.cache_data(ttl=900)
def _load_watchlist() -> list[dict]:
    rows = []
    for t in WATCHLIST:
        try:
            df_w = fetch_stock_data(t, period="3mo")
            info_w = get_stock_info(t)
            close = df_w["Close"].values.astype(float)
            prev = close[-2] if len(close) >= 2 else close[-1]
            curr = close[-1]
            rows.append({
                "ticker":    t,
                "name":      info_w["name"][:26],
                "price":     curr,
                "chg":       curr - prev,
                "pct":       (curr - prev) / prev * 100,
                "open":      float(df_w["Open"].values[-1]),
                "high":      float(df_w["High"].values[-1]),
                "low":       float(df_w["Low"].values[-1]),
                "prev":      prev,
                "close_arr": close,
            })
        except Exception:
            pass
    return rows


def _watchlist_table_html(rows: list[dict]) -> str:
    T = get_tokens()
    header = f"""
<div class="wl-wrap">
<table class="wl-table">
<thead><tr>
  <th>Ticker</th>
  <th>Price</th>
  <th>Change</th>
  <th>Change %</th>
  <th>Open</th>
  <th>High</th>
  <th>Low</th>
  <th>Prev close</th>
  <th style="text-align:center;">60D trend</th>
</tr></thead>
<tbody>"""
    body = ""
    for r in rows:
        up = r["chg"] >= 0
        cls = "wl-up" if up else "wl-dn"
        sign = "+" if up else ""
        spark = sparkline_svg(r["close_arr"][-60:])
        detail_url = f"?theme={st.session_state.get('theme', 'dark')}&ticker={r['ticker']}"
        body += f"""
<tr class="wl-row">
  <td><a href="{detail_url}" class="wl-cell-link"><div class="wl-ticker">{r["ticker"]}</div><div class="wl-name">{r["name"]}</div></a></td>
  <td><a href="{detail_url}" class="wl-cell-link">{r["price"]:.2f}</a></td>
  <td class="{cls}"><a href="{detail_url}" class="wl-cell-link">{sign}{r["chg"]:.2f}</a></td>
  <td class="{cls}"><a href="{detail_url}" class="wl-cell-link">{sign}{r["pct"]:.2f}%</a></td>
  <td><a href="{detail_url}" class="wl-cell-link">{r["open"]:.2f}</a></td>
  <td><a href="{detail_url}" class="wl-cell-link">{r["high"]:.2f}</a></td>
  <td><a href="{detail_url}" class="wl-cell-link">{r["low"]:.2f}</a></td>
  <td><a href="{detail_url}" class="wl-cell-link">{r["prev"]:.2f}</a></td>
  <td style="text-align:center;"><a href="{detail_url}" class="wl-cell-link">{spark}</a></td>
</tr>"""
    return header + body + "</tbody></table></div>"


def render_watchlist_page():
    render_nav(show_back=False, active_page="watchlist")
    render_ticker_strip()

    T = get_tokens()

    _prefill = st.session_state.pop("prefill", "")
    _auto_run = st.session_state.pop("auto_run", False)

    col_input, col_btn = st.columns([4, 1])
    with col_input:
        ticker = st.text_input(
            "Ticker",
            value=_prefill,
            placeholder="e.g. AAPL, TSLA, 600519.SS, 000858.SZ",
            label_visibility="collapsed",
        ).strip().upper()
    with col_btn:
        run_btn = st.button("Analyse", type="primary",
                            use_container_width=True) or _auto_run

    if "recent_searches" not in st.session_state:
        st.session_state.recent_searches = []

    if run_btn and ticker:
        if ticker in st.session_state.recent_searches:
            st.session_state.recent_searches.remove(ticker)
        st.session_state.recent_searches.insert(0, ticker)
        st.session_state.recent_searches = st.session_state.recent_searches[:8]

        st.session_state.selected_ticker = ticker
        st.session_state.page = "detail"
        st.rerun()

    if st.session_state.recent_searches:
        recent_line = "  ·  ".join(st.session_state.recent_searches)
        st.caption(f"Recent: {recent_line}")


    rail_header("Market watchlist", icon("chart-line", 13, T["text_muted"]))
    with st.spinner("Loading market data…"):
        wl_rows = _load_watchlist()

    if wl_rows:
        cols = st.columns(min(len(wl_rows), 10))
        for i, r in enumerate(wl_rows):
            up = r["chg"] >= 0
            label = f"{'▲' if up else '▼'} {r['ticker']}"
            with cols[i % 10]:
                if st.button(label, key=f"chip_{r['ticker']}", use_container_width=True, type="secondary"):
                    st.session_state.selected_ticker = r["ticker"]
                    st.session_state.page = "detail"
                    st.rerun()

        st.markdown(_watchlist_table_html(wl_rows), unsafe_allow_html=True)
