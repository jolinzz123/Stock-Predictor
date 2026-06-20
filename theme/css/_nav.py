def css_nav(T: dict) -> str:
    return f"""
/* ── Nav back breadcrumb ─ */
.st-key-nav_back button {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: {T["text_muted"]} !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 0.72rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.04em !important;
    padding: 0.35rem 1.2rem !important;
    min-height: auto !important;
    max-height: auto !important;
    height: auto !important;
    transition: color 0.18s !important;
}}
.st-key-nav_back button:hover {{
    color: {T["accent_blue"]} !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}}
.st-key-nav_back button:focus,
.st-key-nav_back button:active {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
    color: {T["accent_blue"]} !important;
}}

/* ── Nav ─ */
.topnav {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.5rem 0 0.9rem;
    border-bottom: 1px solid {T["border"]};
    margin-bottom: 2rem;
    position: relative;
}}
.topnav::after {{
    content: '';
    position: absolute;
    bottom: -1px; left: 0;
    width: 160px; height: 1px;
    background: linear-gradient(90deg, {T["accent_blue"]}, {T["accent_green"]}, transparent);
}}
.topnav-left {{
    display: flex;
    align-items: center;
    gap: 1.4rem;
}}
.topnav-brand {{
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    letter-spacing: -0.025em;
    background: linear-gradient(120deg, {T["accent_blue"]} 0%, {T["accent_green"]} 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-fill-color: transparent;
}}
.brand-mark {{
    width: 40px; height: 40px;
    border-radius: 7px;
    background: linear-gradient(135deg, {T["accent_blue"]}22, {T["accent_green"]}22);
    border: 1px solid {T["accent_blue"]}33;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
    position: relative;
    overflow: hidden;
}}
.brand-mark::after {{
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, {T["accent_blue"]}18, transparent 60%);
}}
.topnav-pills {{
    display: flex;
    align-items: center;
    gap: 0.35rem;
}}
.nav-pill {{
    font-size: 0.65rem;
    font-weight: 600;
    font-family: 'Space Grotesk', sans-serif;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    padding: 3px 9px;
    border-radius: 999px;
    border: 1px solid {T["border"]};
    color: {T["text_muted"]};
    background: {T["bg_card"]};
    white-space: nowrap;
    transition: border-color 0.2s, color 0.2s;
}}
.nav-pill:hover {{
    border-color: {T["accent_blue"]}55;
    color: {T["text_secondary"]};
}}
.nav-pill.active {{
    border-color: {T["accent_blue"]}44;
    color: {T["accent_blue"]};
    background: {T["accent_blue"]}0d;
}}

/* ── Theme toggle ─ */
.st-key-nav_theme_toggle {{
    display: flex;
    justify-content: flex-end;
    margin-right: 0;
}}
.st-key-nav_theme_toggle button {{
    width: 38px !important;
    height: 38px !important;
    min-height: 38px !important;
    max-height: 38px !important;
    min-width: 38px !important;
    padding: 0 !important;
    border-radius: 50% !important;
    border: 1px solid {T["border"]} !important;
    background: {T["bg_card"]} !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 1.1rem !important;
    line-height: 1 !important;
    box-shadow: none !important;
    transition: border-color 0.2s, background 0.2s, box-shadow 0.2s !important;
}}
.st-key-nav_theme_toggle button:hover {{
    border-color: {T["accent_blue"]} !important;
    background: {T["accent_blue"]}12 !important;
    box-shadow: 0 0 0 3px {T["accent_blue"]}20 !important;
}}
.st-key-nav_theme_toggle button:focus,
.st-key-nav_theme_toggle button:active,
.st-key-nav_theme_toggle button:focus-visible {{
    border-color: {T["accent_blue"]} !important;
    box-shadow: 0 0 0 3px {T["accent_blue"]}30 !important;
    outline: none !important;
}}
"""
