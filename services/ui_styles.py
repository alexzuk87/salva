"""Sistema de diseño SALVA — identidad urbana tecnológica."""

FLOW_STEPS = ["Necesidad", "Profesionales", "Reserva", "Pago", "Seguimiento", "Finalización"]

MARKETPLACE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
  color-scheme: light only;
  --salva-bg: #F7F7F4;
  --salva-surface: #FFFFFF;
  --salva-text: #16181D;
  --salva-muted: #687078;
  --salva-primary: #365CF5;
  --salva-primary-foreground: #FFFFFF;
  --salva-primary-hover: #2444C7;
  --salva-primary-soft: #EEF1FF;
  --salva-success: #18A875;
  --salva-success-soft: #E6F7F1;
  --salva-warning: #F59E42;
  --salva-warning-soft: #FFF4E8;
  --salva-border: #E6E7EA;
  --salva-error: #D93C3C;
  --salva-error-soft: #FDECEC;
  --salva-shadow: 0 1px 3px rgba(22, 24, 29, 0.06);
  --salva-radius: 20px;
}

.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], main {
  background-color: var(--salva-bg) !important;
  color: var(--salva-text) !important;
  color-scheme: light only !important;
}

html, body, [class*="css"] {
  font-family: 'Inter', sans-serif;
  color: var(--salva-text);
  color-scheme: light only;
}

/* —— Light-mode text enforcement (Streamlit Cloud / mobile dark preference) —— */
[data-testid="stAppViewContainer"] label,
[data-testid="stAppViewContainer"] label p,
[data-testid="stAppViewContainer"] label span,
[data-testid="stAppViewContainer"] [data-testid="stWidgetLabel"],
[data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] p,
[data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] li,
[data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] strong,
[data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] h1,
[data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] h2,
[data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] h3,
[data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] h4,
[data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"],
[data-testid="stAppViewContainer"] [data-testid="stMetricLabel"],
[data-testid="stAppViewContainer"] [data-testid="stMetricValue"],
[data-testid="stAppViewContainer"] [data-testid="stText"],
[data-testid="stAppViewContainer"] .stRadio label,
[data-testid="stAppViewContainer"] .stCheckbox label,
[data-testid="stAppViewContainer"] div[data-baseweb="select"] span,
[data-testid="stAppViewContainer"] input,
[data-testid="stAppViewContainer"] textarea {
  color: var(--salva-text) !important;
  -webkit-text-fill-color: var(--salva-text) !important;
}

[data-testid="stAppViewContainer"] [data-testid="stMetricLabel"],
[data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"],
[data-testid="stAppViewContainer"] .support-text,
[data-testid="stAppViewContainer"] .body-text,
[data-testid="stAppViewContainer"] .pro-specialty,
[data-testid="stAppViewContainer"] .review-meta,
[data-testid="stAppViewContainer"] .road-label {
  color: var(--salva-muted) !important;
  -webkit-text-fill-color: var(--salva-muted) !important;
}

.hero-title, .section-title, .mh-hero-title,
.pro-name, .receipt-title, .empty-title,
.diagnosis-box, .diagnosis-box p, .diagnosis-box strong,
.receipt-card, .receipt-card p, .receipt-card strong, .receipt-card h2,
.pro-marketplace-card, .pro-marketplace-card h3, .pro-marketplace-card p,
.review-item, .review-item strong, .review-text,
.road-current, .road-current strong,
.timeline-card, .form-step-num, .mh-preview p,
.benefit-card strong, .cat-tile-label {
  color: var(--salva-text) !important;
  -webkit-text-fill-color: var(--salva-text) !important;
}

.hero-title .accent, .receipt-id, .pro-price, .form-step-num {
  color: var(--salva-primary) !important;
  -webkit-text-fill-color: var(--salva-primary) !important;
}

.body-text, .support-text, .pro-specialty, .pro-price-label, .pro-stats-row,
.salvita-msg, .review-meta, .no-reviews {
  color: var(--salva-muted) !important;
  -webkit-text-fill-color: var(--salva-muted) !important;
}

/* Keep intentional light-on-dark surfaces */
.stButton button[kind="primary"],
.stButton button[kind="primary"] p,
.step-active,
.promo-blue, .promo-blue span,
.chat-user, .chat-user p, .chat-user strong,
.stTabs [aria-selected="true"] {
  color: var(--salva-primary-foreground) !important;
  -webkit-text-fill-color: var(--salva-primary-foreground) !important;
}

.stButton button[kind="secondary"],
.stButton button[kind="secondary"] p {
  color: var(--salva-text) !important;
  -webkit-text-fill-color: var(--salva-text) !important;
}

section[data-testid="stSidebar"] { display: none !important; }
header[data-testid="stHeader"] { background: transparent; }
.block-container {
  padding-top: 0.25rem !important;
  padding-bottom: 5rem !important;
  max-width: 1180px !important;
  padding-left: 1rem !important;
  padding-right: 1rem !important;
}
@media (min-width: 769px) { .block-container { padding-bottom: 2rem !important; } }

/* Header & logo */
.salva-header-row { display: flex; align-items: center; gap: 1rem; margin-bottom: 0.75rem; }
.salva-header-brand { margin: 0; line-height: 0; }
.salva-logo-nav-cell { position: relative; min-height: 36px; }
.logo-wrap { position: relative; display: inline-flex; align-items: center; pointer-events: none; }
.logo-horizontal svg { width: 140px; height: auto; max-height: 36px; display: block; }
@media (min-width: 769px) { .logo-horizontal svg { width: 148px; max-height: 38px; } }
@media (max-width: 768px) {
  .logo-horizontal svg { width: 110px; max-height: 32px; }
}
:is(div[data-testid="column"], div[data-testid="stColumn"]):has(.salva-header-brand) {
  position: relative !important;
  flex: 0 0 auto !important;
  max-width: 160px !important;
  min-width: 100px !important;
}
:is(div[data-testid="column"], div[data-testid="stColumn"]):has(.salva-header-brand) .stButton {
  position: absolute !important;
  top: 0 !important;
  left: 0 !important;
  width: 100% !important;
  height: 100% !important;
  min-height: 36px !important;
  margin: 0 !important;
  padding: 0 !important;
  z-index: 2 !important;
}
:is(div[data-testid="column"], div[data-testid="stColumn"]):has(.salva-header-brand) .stButton button {
  opacity: 0 !important;
  width: 100% !important;
  height: 100% !important;
  min-height: 36px !important;
  padding: 0 !important;
  margin: 0 !important;
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  color: transparent !important;
}
:is(div[data-testid="column"], div[data-testid="stColumn"]):has(.salva-header-brand) .stButton button:hover,
:is(div[data-testid="column"], div[data-testid="stColumn"]):has(.salva-header-brand) .stButton button:active {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  opacity: 0 !important;
}
:is(div[data-testid="column"], div[data-testid="stColumn"]):has(.salva-header-brand) .stButton button:focus-visible {
  opacity: 0.12 !important;
  outline: 2px solid var(--salva-primary) !important;
  outline-offset: 2px !important;
}
div[data-testid="stVerticalBlockBorderWrapper"] {
  transition: border-color 0.2s, box-shadow 0.2s;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
  border-color: var(--salva-primary) !important;
  box-shadow: var(--salva-shadow);
}

.nav-row { display: flex; flex-wrap: wrap; gap: 0.35rem; margin-bottom: 1rem; }

/* Typography */
.hero-title {
  font-size: 1.875rem; font-weight: 800; color: var(--salva-text);
  line-height: 1.15; margin: 0 0 0.75rem;
}
.hero-title .accent { color: var(--salva-primary); }
@media (min-width: 1024px) { .hero-title { font-size: 3rem; } }
.section-title {
  font-size: 1.45rem; font-weight: 700; color: var(--salva-text); margin: 0 0 0.5rem;
}
@media (min-width: 1024px) { .section-title { font-size: 1.875rem; } }
.body-text { font-size: 1rem; color: var(--salva-muted); line-height: 1.6; }
.support-text { font-size: 0.875rem; color: var(--salva-muted); }

/* Cards */
.salva-card {
  background: var(--salva-surface); border-radius: var(--salva-radius); padding: 1.25rem;
  border: 1px solid var(--salva-border); box-shadow: var(--salva-shadow); margin-bottom: 1rem;
}
@media (min-width: 769px) { .salva-card { padding: 1.75rem; border-radius: 24px; } }

.hero-badge {
  display: inline-block; background: var(--salva-primary-soft); color: var(--salva-primary);
  font-size: 0.8rem; font-weight: 600; padding: 0.35rem 0.85rem; border-radius: 999px; margin-bottom: 0.75rem;
}
.trust-row { font-size: 0.8rem; color: var(--salva-muted); margin-top: 1rem; }

/* Hero visual */
.hero-visual {
  background: var(--salva-surface); border-radius: 24px; border: 1px solid var(--salva-border);
  padding: 1.5rem; box-shadow: var(--salva-shadow);
}
.hero-pro-card {
  background: var(--salva-bg); border-radius: 16px; padding: 1rem;
  border: 1px solid var(--salva-border); display: flex; gap: 1rem; align-items: center;
}
.hero-avatar {
  width: 72px; height: 72px; border-radius: 50%; object-fit: cover;
  border: 3px solid var(--salva-primary-soft); flex-shrink: 0;
}
.hero-avatar-fallback {
  width: 72px; height: 72px; border-radius: 50%; background: var(--salva-primary-soft);
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.hero-price-tag {
  background: var(--salva-primary-soft); color: var(--salva-primary); border-radius: 12px;
  padding: 0.5rem 0.85rem; font-weight: 700; display: inline-block; margin-top: 0.75rem;
  font-size: 0.95rem;
}
.chip-success {
  display: inline-block; background: var(--salva-success-soft); color: var(--salva-success);
  font-size: 0.72rem; font-weight: 600; padding: 0.25rem 0.55rem; border-radius: 6px; margin-right: 0.25rem;
}
.chip-eta {
  display: inline-block; background: var(--salva-warning-soft); color: var(--salva-warning);
  font-size: 0.72rem; font-weight: 600; padding: 0.25rem 0.55rem; border-radius: 6px;
}
.chip-primary {
  display: inline-block; background: var(--salva-primary-soft); color: var(--salva-primary);
  font-size: 0.72rem; font-weight: 600; padding: 0.25rem 0.55rem; border-radius: 6px;
}

/* Categories — single clickable container */
.cat-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.75rem; }
@media (min-width: 768px) { .cat-grid { grid-template-columns: repeat(4, 1fr); gap: 1rem; } }
.cat-tile {
  background: var(--salva-surface); border: 1px solid var(--salva-border); border-radius: 16px;
  padding: 1rem 0.75rem; text-align: center; transition: border-color 0.2s, box-shadow 0.2s;
}
.cat-tile:hover { border-color: var(--salva-primary); box-shadow: var(--salva-shadow); }
.cat-tile-icon { display: flex; justify-content: center; margin-bottom: 0.5rem; }
.cat-tile-label { font-size: 0.85rem; font-weight: 600; color: var(--salva-text); }

/* Benefits */
.benefit-grid { display: grid; grid-template-columns: 1fr; gap: 0.75rem; }
@media (min-width: 769px) { .benefit-grid { grid-template-columns: repeat(2, 1fr); } }
@media (min-width: 1024px) { .benefit-grid { grid-template-columns: repeat(4, 1fr); } }
.benefit-card {
  background: var(--salva-surface); border-radius: 16px; padding: 1rem 1.15rem;
  border: 1px solid var(--salva-border);
}
.benefit-icon { display: flex; margin-bottom: 0.5rem; }
.benefit-card strong { display: block; font-size: 0.95rem; margin-bottom: 0.25rem; color: var(--salva-text); }
.benefit-card span { font-size: 0.82rem; color: var(--salva-muted); }

/* Empty state */
.empty-state {
  text-align: center; padding: 2rem 1.25rem; background: var(--salva-surface);
  border-radius: 24px; border: 1px dashed var(--salva-border);
}
.empty-icon-wrap { display: flex; justify-content: center; margin-bottom: 0.75rem; }
.empty-title { font-size: 1.1rem; font-weight: 700; color: var(--salva-text); margin-bottom: 0.35rem; }
.empty-text { font-size: 0.9rem; color: var(--salva-muted); margin-bottom: 1rem; }

/* Flow steps */
.status-track { display: flex; gap: 0.35rem; flex-wrap: wrap; margin: 0.75rem 0 1.25rem; overflow-x: auto; }
.step-active, .step-done, .step-pending {
  padding: 0.4rem 0.7rem; border-radius: 10px; font-size: 0.72rem; font-weight: 600; white-space: nowrap;
}
.step-active { background: var(--salva-primary); color: var(--salva-primary-foreground); }
.step-done { background: var(--salva-surface); color: var(--salva-primary); border: 1px solid var(--salva-primary-soft); }
.step-pending { background: var(--salva-bg); color: var(--salva-muted); border: 1px dashed var(--salva-border); }

/* Pro cards */
.pro-marketplace-card {
  background: var(--salva-surface); border-radius: 20px; padding: 1.15rem;
  border: 1px solid var(--salva-border); box-shadow: var(--salva-shadow); margin-bottom: 0.5rem;
}
.pro-card-top { display: flex; flex-direction: column; gap: 0.85rem; }
@media (min-width: 640px) { .pro-card-top { flex-direction: row; align-items: flex-start; } }
.pro-photo {
  width: 80px; height: 80px; border-radius: 50%; object-fit: cover;
  border: 3px solid var(--salva-primary-soft); align-self: center;
}
.pro-name { font-size: 1.05rem; font-weight: 700; margin: 0; color: var(--salva-text); }
.pro-specialty { font-size: 0.85rem; color: var(--salva-muted); margin: 0.1rem 0 0.4rem; }
.badge {
  display: inline-block; font-size: 0.65rem; font-weight: 600; padding: 0.2rem 0.5rem;
  border-radius: 6px; margin: 0.1rem 0.2rem 0.1rem 0;
}
.badge-verified { background: var(--salva-success-soft); color: var(--salva-success); }
.badge-identity { background: var(--salva-success-soft); color: var(--salva-success); }
.badge-matricula { background: var(--salva-primary-soft); color: var(--salva-primary); }
.badge-pending { background: var(--salva-bg); color: var(--salva-muted); }
.pro-stats-row { display: flex; flex-wrap: wrap; gap: 0.5rem; font-size: 0.82rem; color: var(--salva-muted); }
.highlight-chip {
  display: inline-block; font-size: 0.76rem; background: var(--salva-bg); padding: 0.3rem 0.6rem;
  border-radius: 8px; margin-bottom: 0.2rem; color: var(--salva-muted);
}
.highlight-chip.eta { background: var(--salva-warning-soft); color: var(--salva-warning); font-weight: 600; }
.pro-price { font-size: 1.25rem; font-weight: 800; color: var(--salva-primary); }
.pro-price-label { font-size: 0.75rem; color: var(--salva-muted); margin-left: 0.35rem; }
.review-item { background: var(--salva-bg); border-radius: 12px; padding: 0.65rem; font-size: 0.82rem; margin-bottom: 0.35rem; color: var(--salva-text); }
.review-text { color: var(--salva-text) !important; -webkit-text-fill-color: var(--salva-text) !important; }
.review-meta { color: var(--salva-muted) !important; }
.no-reviews { color: var(--salva-muted) !important; font-size: 0.82rem; }
.review-stars { color: var(--salva-warning); }

.form-step-card {
  background: var(--salva-surface); border-radius: 20px; padding: 1.25rem;
  border: 1px solid var(--salva-border); margin-bottom: 1rem;
}
.form-step-num {
  font-size: 0.75rem; font-weight: 700; color: var(--salva-primary);
  text-transform: uppercase; letter-spacing: 0.04em;
}

.timeline-card {
  background: var(--salva-surface); border-radius: 16px; padding: 1rem 1.15rem;
  border: 1px solid var(--salva-border); border-left: 4px solid var(--salva-primary); margin-bottom: 0.65rem;
}
.sim-banner {
  background: var(--salva-warning-soft); border: 1px solid #FDE0C2; border-radius: 12px;
  padding: 0.75rem 1rem; font-size: 0.85rem; color: #9A5B16; margin: 0.75rem 0;
}
.diagnosis-box {
  background: var(--salva-primary-soft); border-radius: 16px; padding: 1rem 1.25rem;
  border: 1px solid #DDE3FF; margin: 1rem 0;
}
.progress-bar-bg { background: var(--salva-border); border-radius: 999px; height: 8px; overflow: hidden; margin: 0.5rem 0; }
.progress-bar-fill { background: var(--salva-primary); height: 100%; border-radius: 999px; }

/* Buttons */
.stButton button {
  min-height: 44px !important; border-radius: 12px !important; font-weight: 600 !important;
  transition: background 0.15s, border-color 0.15s, transform 0.15s !important;
}
.stButton button[kind="primary"] {
  background: var(--salva-primary) !important; color: var(--salva-primary-foreground) !important; border: none !important;
  box-shadow: 0 2px 8px rgba(54, 92, 245, 0.25) !important;
}
.stButton button[kind="primary"]:hover {
  background: var(--salva-primary-hover) !important;
}
.stButton button[kind="secondary"] {
  background: var(--salva-surface) !important; color: var(--salva-text) !important;
  border: 1px solid var(--salva-border) !important;
}
.stButton button[kind="secondary"]:hover {
  border-color: var(--salva-primary) !important; color: var(--salva-primary) !important;
}
.nav-active button {
  background: var(--salva-primary-soft) !important; color: var(--salva-primary) !important;
  border-color: var(--salva-primary) !important;
}
.stLinkButton > a {
  min-height: 44px !important; border-radius: 12px !important;
  border: 1px solid var(--salva-border) !important;
}

.stTabs [data-baseweb="tab-list"] {
  gap: 0.25rem; background: var(--salva-surface); border-radius: 14px; padding: 0.35rem;
  border: 1px solid var(--salva-border); flex-wrap: wrap;
}
.stTabs [aria-selected="true"] {
  background: var(--salva-primary) !important; color: var(--salva-primary-foreground) !important;
}

div[data-testid="stMetric"] {
  background: var(--salva-surface); border-radius: 16px; padding: 0.85rem;
  border: 1px solid var(--salva-border); box-shadow: var(--salva-shadow);
}
div[data-testid="stMetric"] label {
  color: var(--salva-muted) !important;
  font-size: 0.75rem !important;
  line-height: 1.25 !important;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"],
div[data-testid="stMetric"] [data-testid="stMetricValue"] > div {
  font-size: clamp(1rem, 1.4vw, 1.2rem) !important;
  line-height: 1.2 !important;
}

.payment-box { background: var(--salva-bg); border-radius: 16px; padding: 1rem; border: 1px solid var(--salva-border); }
.alias-display {
  font-family: monospace; font-weight: 700; color: var(--salva-primary);
  background: var(--salva-surface); padding: 0.65rem; border-radius: 10px; border: 1px dashed var(--salva-border);
}

.promo-blue {
  background: var(--salva-primary); border-radius: 16px; padding: 1.25rem;
  color: var(--salva-primary-foreground);
}

/* Main navigation */
.main-nav-bottom-sep { border-top: 2px solid var(--salva-border); margin: 1.5rem 0 0.75rem; padding-top: 0.25rem; }
.salva-nav-marker { display: none !important; }
.salva-nav-bottom-marker { display: none !important; }
div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .salva-nav-marker) div[data-testid="stHorizontalBlock"] {
  flex-wrap: nowrap !important;
  gap: 0.35rem !important;
}
div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .salva-nav-marker) div[data-testid="stHorizontalBlock"] > :is(div[data-testid="column"], div[data-testid="stColumn"]) {
  flex: 1 1 0 !important; min-width: 0 !important;
}
div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .salva-nav-marker) .stButton button {
  font-size: 0.78rem !important; padding: 0.4rem 0.25rem !important;
  white-space: nowrap !important; min-height: 40px !important;
}
@media (max-width: 768px) {
  div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .salva-nav-bottom-marker) {
    display: none !important;
  }
  div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .salva-nav-marker) div[data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    overflow-x: auto !important;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
    padding-bottom: 2px;
  }
  div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .salva-nav-marker) div[data-testid="stHorizontalBlock"]::-webkit-scrollbar {
    display: none;
  }
  div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .salva-nav-marker) div[data-testid="stHorizontalBlock"] > :is(div[data-testid="column"], div[data-testid="stColumn"]) {
    flex: 0 0 auto !important;
    min-width: 4.5rem !important;
    max-width: none !important;
  }
  div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .salva-nav-marker) .stButton button {
    font-size: 0.62rem !important; padding: 0.28rem 0.35rem !important;
    min-height: 34px !important;
  }
  .main-nav-bottom-sep { display: none !important; }
}
@media (max-width: 390px) {
  .block-container { padding-left: 0.75rem !important; padding-right: 0.75rem !important; }
  div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .salva-nav-marker) .stButton button {
    font-size: 0.58rem !important; min-height: 32px !important;
  }
}

/* —— Desktop guard: evita que reglas mobile afecten desktop —— */
@media (min-width: 769px) {
  [data-testid="stAppViewContainer"] .hero-title,
  [data-testid="stAppViewContainer"] .section-title,
  [data-testid="stAppViewContainer"] .mh-hero-title,
  [data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] p,
  [data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] li,
  [data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] h1,
  [data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] h2,
  [data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] h3 {
    word-break: normal !important;
    overflow-wrap: normal !important;
    white-space: normal !important;
  }
  div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .salva-nav-marker) div[data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    overflow-x: visible !important;
  }
  div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .salva-nav-marker) div[data-testid="stHorizontalBlock"] > :is(div[data-testid="column"], div[data-testid="stColumn"]) {
    flex: 1 1 0 !important;
    min-width: 0 !important;
    max-width: none !important;
  }
  div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .salva-nav-marker) .stButton button {
    font-size: 0.82rem !important;
    padding: 0.5rem 0.5rem !important;
    min-height: 42px !important;
    white-space: nowrap !important;
  }
}

#MainMenu, footer, .viewerBadge_container { visibility: hidden; height: 0; }
.stDeployButton { display: none; }
div[data-testid="stToolbar"] { display: none; }

/* —— Motion system —— */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; }
}
.salva-card-hover { transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease; }
.salva-card-hover:hover { transform: translateY(-2px); box-shadow: 0 4px 14px rgba(22,24,29,0.08); border-color: var(--salva-primary); }
.stButton button:active { transform: scale(0.98); }
.fade-in { animation: fadeIn 0.35s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
.success-pop { animation: successPop 0.45s ease; }
@keyframes successPop { 0% { transform: scale(0.96); opacity: 0; } 100% { transform: scale(1); opacity: 1; } }
.anim-check { color: var(--salva-success); font-size: 2.5rem; font-weight: 800; animation: drawCheck 0.5s ease; }
@keyframes drawCheck { from { opacity: 0; transform: scale(0.5); } to { opacity: 1; transform: scale(1); } }

/* Salvita */
.salvita-wrap { display: flex; align-items: center; gap: 0.75rem; margin: 0.5rem 0; }
.salvita-icon svg { width: 48px; height: 48px; }
.salvita-msg { font-size: 0.9rem; color: var(--salva-muted); margin: 0; }
.salvita-searching .salvita-icon { animation: pulse 2.5s ease-in-out infinite; }
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.65; } }

/* Animated icons */
.icon-plomeria .anim-drop { animation: drop 2s ease infinite; }
@keyframes drop { 0%,100% { transform: translateY(0); opacity: 1; } 50% { transform: translateY(4px); opacity: 0.5; } }
.icon-electricidad .anim-bolt { animation: bolt 1.8s ease infinite; }
@keyframes bolt { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }
.icon-gas .anim-flame { animation: flame 2s ease infinite; transform-origin: center bottom; }
@keyframes flame { 0%,100% { transform: scaleY(1); } 50% { transform: scaleY(1.08); } }

/* Receipt */
.receipt-card { max-width: 420px; margin: 0 auto 1rem; background: var(--salva-surface); border: 1px solid var(--salva-border); border-radius: 20px; padding: 1.5rem; box-shadow: var(--salva-shadow); }
.receipt-title { text-align: center; font-size: 1.35rem; margin: 0.5rem 0; color: var(--salva-text); }
.receipt-id { text-align: center; font-family: monospace; color: var(--salva-primary); font-weight: 700; }
.receipt-divider { border: none; border-top: 2px dashed var(--salva-border); margin: 1rem 0; }
.receipt-pro { display: flex; gap: 0.75rem; align-items: center; margin: 0.75rem 0; }
.receipt-logo svg { height: 32px; }

/* Tracking road */
.tracking-road { margin: 1rem 0; overflow: hidden; }
.road-track { position: relative; height: 8px; background: var(--salva-border); border-radius: 999px; margin: 2rem 0 1rem; }
.road-fill { height: 100%; background: var(--salva-success); border-radius: 999px; transition: width 0.45s ease; }
.road-vehicle { position: absolute; top: -14px; transform: translateX(-50%); font-size: 1.25rem; transition: left 0.45s ease; }
.road-markers { display: flex; justify-content: space-between; gap: 0.15rem; flex-wrap: wrap; }
.road-marker { text-align: center; flex: 1; min-width: 48px; }
.road-dot { display: block; width: 10px; height: 10px; border-radius: 50%; margin: 0 auto 0.25rem; background: var(--salva-border); }
.road-marker.done .road-dot { background: var(--salva-success); }
.road-marker.active .road-dot { background: var(--salva-primary); animation: pulse 2s ease infinite; }
.road-label { font-size: 0.62rem; color: var(--salva-muted); display: block; line-height: 1.2; }
.road-current { text-align: center; margin-top: 0.75rem; color: var(--salva-text) !important; }

/* Chat */
.chat-thread { max-height: 280px; overflow-y: auto; padding: 0.5rem; background: var(--salva-bg); border-radius: 12px; margin-bottom: 0.75rem; }
.chat-bubble { padding: 0.55rem 0.75rem; border-radius: 12px; margin-bottom: 0.5rem; font-size: 0.88rem; }
.chat-system { background: var(--salva-primary-soft); border-left: 3px solid var(--salva-primary); }
.chat-pro { background: var(--salva-surface); border: 1px solid var(--salva-border); }
.chat-user { background: var(--salva-primary); color: white; margin-left: 1.5rem; }
.chat-user strong, .chat-user p { color: white; }
.chat-ts { font-size: 0.7rem; opacity: 0.7; }

/* Payment brands */
.card-brands { display: flex; gap: 0.5rem; margin: 0.5rem 0; }
.card-brand { padding: 0.25rem 0.6rem; border-radius: 8px; font-size: 0.75rem; font-weight: 700; background: var(--salva-bg); color: var(--salva-muted); border: 1px solid var(--salva-border); }
.card-brand.active { background: var(--salva-primary-soft); color: var(--salva-primary); border-color: var(--salva-primary); }

/* Time slots */
.slot-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.35rem; }
@media (min-width: 769px) { .slot-grid { grid-template-columns: repeat(4, 1fr); } }
.slot-btn-wrap { margin-bottom: 0.25rem; }

/* Hero fix */
.hero-visual .pro-photo, .hero-visual .hero-avatar { border-radius: 50%; object-fit: cover; }
.hero-symbol-inline { flex-shrink: 0; }
.promo-blue { display: flex; align-items: center; gap: 0.65rem; margin-top: 1rem; }
.avatar-fallback { width: 72px; height: 72px; border-radius: 50%; background: var(--salva-primary-soft); display: flex; align-items: center; justify-content: center; font-weight: 700; color: var(--salva-primary); }

@keyframes svcFloat { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-5px); } }
.svc-float, .svc-character { animation: svcFloat 3.2s ease-in-out infinite; }
.svc-character { display: block; margin: 0 auto; }
.svc-cat-grid-root, .svc-cat-marker { display: none !important; }
/* Grilla de servicios — scope estricto vía el marcador por columna (sin leak al app-root) */
div[data-testid="stHorizontalBlock"]:has(.svc-cat-marker) {
  display: grid !important;
  grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
  gap: 10px !important;
  width: 100% !important;
}
div[data-testid="stHorizontalBlock"]:has(.svc-cat-marker) > :is(div[data-testid="column"], div[data-testid="stColumn"]) {
  width: auto !important; min-width: 0 !important; flex: unset !important; max-width: none !important;
}
@media (max-width: 768px) {
  div[data-testid="stHorizontalBlock"]:has(.svc-cat-marker) {
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  }
}
@media (min-width: 769px) {
  div[data-testid="stHorizontalBlock"]:has(.svc-cat-marker) {
    grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
  }
}

/* Receipt pending */
.receipt-pending .receipt-clock { text-align: center; font-size: 2rem; }
.receipt-status-badge.pending {
  display: block; text-align: center; background: var(--salva-warning-soft); color: var(--salva-warning);
  font-weight: 700; padding: 0.35rem 0.75rem; border-radius: 999px; margin: 0.5rem auto; max-width: 280px;
}

/* Tracking v2 */
.tracking-road-v2 { margin: 1rem 0; overflow: hidden; }
.road-scene-ltr { display: flex; align-items: center; gap: 0.35rem; margin-bottom: 0.75rem; }
.road-track-v2 { flex: 1; position: relative; height: 8px; background: var(--salva-border); border-radius: 999px; min-width: 0; }
.road-traveller-wrap { position: absolute; top: -22px; transform: translateX(-50%); transition: left 0.45s ease; z-index: 2; }
.road-house-fixed { font-size: 1.6rem; flex-shrink: 0; margin-left: 0.25rem; }
.road-house-done { filter: drop-shadow(0 0 4px rgba(54,92,245,0.35)); }
.road-pro-traveller { font-size: 1.35rem; display: inline-block; }
.road-pro-avatar { border-radius: 50% !important; border: 2px solid var(--salva-primary); }
.road-work-tool { font-size: 0.85rem; margin-left: -0.15rem; }
.road-fill { height: 100%; background: var(--salva-success); border-radius: 999px; transition: width 0.45s ease; }
.road-stage-icon { display: block; font-size: 0.85rem; margin-bottom: 0.15rem; }

/* Chat v2 */
.chat-header { display: flex; gap: 0.65rem; align-items: center; margin-bottom: 0.75rem; }
.chat-pro { display: flex; gap: 0.5rem; align-items: flex-start; }
.chat-user { margin-left: 2rem; text-align: right; background: var(--salva-primary) !important; color: white; }
.chat-user p, .chat-user strong { color: white; }

.mh-tx-row { padding: 0.35rem 0; border-bottom: 1px solid var(--salva-border); font-size: 0.82rem; }
.mh-anchor { scroll-margin-top: 4rem; }
.star-label-active { color: #D97706; font-weight: 600; }
div[data-testid="stFeedback"] svg { color: #D97706 !important; }

/* Mi hogar */
.mh-hero-title { font-size: 1.5rem; font-weight: 800; margin: 0.25rem 0; }
.mh-card-label { font-size: 0.75rem; font-weight: 700; color: var(--salva-primary); text-transform: uppercase; margin: 0; }
.mh-balance-card { text-align: center; padding: 1.5rem; }
.mh-balance-amount { font-size: 2rem; font-weight: 800; color: var(--salva-primary); margin: 0.25rem 0; }
.mh-summary-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.75rem; }
.mh-summary-item {
  display: flex; align-items: center; gap: 0.75rem; min-width: 0;
  padding: 0.85rem; border-radius: 14px; background: var(--salva-bg);
  border: 1px solid var(--salva-border);
}
.mh-summary-item:last-child { grid-column: 1 / -1; }
.mh-summary-icon {
  width: 40px; height: 40px; border-radius: 12px; flex: 0 0 40px;
  display: inline-flex; align-items: center; justify-content: center;
  background: var(--salva-primary-soft);
}
.mh-summary-icon svg { width: 22px; height: 22px; }
.mh-summary-item strong { display: block; font-size: 0.82rem; margin-bottom: 0.15rem; }
.mh-summary-item span:not(.mh-summary-icon) {
  display: block; color: var(--salva-muted); font-size: 0.82rem;
  line-height: 1.35; overflow-wrap: anywhere;
}
@media (max-width: 768px) {
  .mh-summary-grid { grid-template-columns: 1fr; }
  .mh-summary-item:last-child { grid-column: auto; }
}
.mh-profile-card { margin-bottom: 1rem; }
.goal-card-v2 { margin-bottom: 1rem; }
.hist-card { margin-bottom: 0.75rem; }
.hist-row { display: flex; gap: 0.75rem; align-items: center; }
.hist-pro { display: flex; gap: 0.5rem; align-items: center; margin: 0.5rem 0; }
.pro-photo { width: 100%; height: 100%; border-radius: 50%; object-fit: cover; }
.pro-photo-wrap { border-radius: 50%; overflow: hidden; border: 3px solid var(--salva-primary-soft); flex-shrink: 0; }
</style>
"""
