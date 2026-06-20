import streamlit as st
from theme import inject_global_css
from page_watchlist import render_watchlist_page
from page_detail import render_detail_page
from page_compare import render_compare_page

# ── Page config (must run before any other st call) ─────────────────────────
st.set_page_config(
    page_title="Foresight — Stock Intelligence",
    page_icon="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><polyline points='3 17 9 11 13 15 21 7' fill='none' stroke='%234C9BE8' stroke-width='2.5' stroke-linecap='round'/></svg>",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Session state ───────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "watchlist"
if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = None
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

# ── Table row click → ?ticker= → navigate to detail ────────────────────────
try:
    qp = st.query_params
    if "ticker" in qp:
        st.session_state.selected_ticker = str(qp["ticker"]).strip().upper()
        st.session_state.page = "detail"
        st.query_params.clear()
        st.rerun()
except Exception:
    pass

# ── Inject global CSS ──────────────────────────────────────────────────────
inject_global_css()

# ── Route dispatch ─────────────────────────────────────────────────────────
if st.session_state.page == "detail" and st.session_state.selected_ticker:
    render_detail_page(st.session_state.selected_ticker)
elif st.session_state.page == "compare":
    render_compare_page()
else:
    render_watchlist_page()
