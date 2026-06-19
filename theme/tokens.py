import streamlit as st


DARK = {
    "bg_base":        "#080C10",
    "bg_surface":     "#0F1923",
    "bg_card":        "#111D2B",
    "bg_card_hover":  "#162234",
    "bg_input":       "#0D1824",
    "border":         "#1E2D3D",
    "border_accent":  "#4C9BE8",
    "accent_green":   "#2ECC71",
    "accent_blue":    "#4C9BE8",
    "accent_red":     "#FF4D6D",
    "accent_amber":   "#F5A623",
    "text_primary":   "#E8F1F9",
    "text_secondary": "#7A92A8",
    "text_muted":     "#3D5166",
    "chart_grid":     "#111D2B",
    "chart_paper":    "rgba(0,0,0,0)",
    "plotly_theme":   "plotly_dark",
    "glow_blue":      "rgba(76,155,232,0.35)",
    "glow_green":     "rgba(46,204,113,0.3)",
    "shadow":         "0 4px 28px rgba(0,0,0,0.55)",
    "pos_pill_bg":    "rgba(46,204,113,0.10)",
    "neg_pill_bg":    "rgba(255,77,109,0.10)",
    "neu_pill_bg":    "rgba(122,146,168,0.10)",
    "scrollbar_track": "#0F1923",
    "scrollbar_thumb": "#1E2D3D",
    "badge_buy_bg":   "rgba(46,204,113,0.10)",
    "badge_buy_bd":   "rgba(46,204,113,0.30)",
    "badge_sell_bg":  "rgba(255,77,109,0.10)",
    "badge_sell_bd":  "rgba(255,77,109,0.30)",
    "badge_hold_bg":  "rgba(245,166,35,0.10)",
    "badge_hold_bd":  "rgba(245,166,35,0.30)",
    "wl_hover":       "#16202e",
    "wl_border":      "#1E2D3D",
    "disclaimer_bg":  "rgba(245,166,35,0.06)",
}

LIGHT = {
    "bg_base":        "#FFFFFF",
    "bg_surface":     "#F7F9FC",
    "bg_card":        "#FFFFFF",
    "bg_card_hover":  "#F0F5FB",
    "bg_input":       "#FFFFFF",
    "border":         "#D4DDE8",
    "border_accent":  "#1A72CC",
    "accent_green":   "#16A34A",
    "accent_blue":    "#1A72CC",
    "accent_red":     "#D93052",
    "accent_amber":   "#C07B00",
    "text_primary":   "#0A1929",
    "text_secondary": "#4A6280",
    "text_muted":     "#9EB3C8",
    "chart_grid":     "#E8EEF5",
    "chart_paper":    "rgba(0,0,0,0)",
    "plotly_theme":   "plotly_white",
    "glow_blue":      "rgba(26,114,204,0.18)",
    "glow_green":     "rgba(22,163,74,0.15)",
    "shadow":         "0 2px 16px rgba(0,40,90,0.08)",
    "pos_pill_bg":    "rgba(22,163,74,0.09)",
    "neg_pill_bg":    "rgba(217,48,82,0.09)",
    "neu_pill_bg":    "rgba(74,98,128,0.09)",
    "scrollbar_track": "#EEF2F7",
    "scrollbar_thumb": "#C8D5E3",
    "badge_buy_bg":   "rgba(22,163,74,0.09)",
    "badge_buy_bd":   "rgba(22,163,74,0.28)",
    "badge_sell_bg":  "rgba(217,48,82,0.09)",
    "badge_sell_bd":  "rgba(217,48,82,0.28)",
    "badge_hold_bg":  "rgba(192,123,0,0.09)",
    "badge_hold_bd":  "rgba(192,123,0,0.28)",
    "wl_hover":       "#F4F7FB",
    "wl_border":      "#D4DDE8",
    "disclaimer_bg":  "rgba(192,123,0,0.06)",
}


def get_tokens() -> dict:
    return DARK if st.session_state.get("theme") == "dark" else LIGHT


def get_is_dark() -> bool:
    return st.session_state.get("theme") == "dark"
