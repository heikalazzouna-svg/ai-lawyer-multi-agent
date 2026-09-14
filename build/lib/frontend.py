import streamlit as st
import time
import html
from vector_database import index_pdf, upload_pdf, retrieve_docs
from rag_pipeline import answer_query, summarize_document, get_llm_model, proactive_scan
from report_service import generate_report

# ─── Page Configuration ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Lawyer — Legal Intelligence",
    page_icon="⚖️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─── Design System: CSS Tokens + Global Styles ───────────────────────────────
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">

<style>
/* ═══════════════════════════════════════════════════════════════════════
   DESIGN TOKENS
   ═══════════════════════════════════════════════════════════════════════ */
:root {
    /* ── Colors ── */
    --bg-primary:      #0B0F19;
    --bg-secondary:    #111827;
    --bg-surface:      #1A1F2E;
    --bg-glass:        rgba(26, 31, 46, 0.55);
    --bg-glass-border: rgba(148, 163, 184, 0.08);
    --bg-glass-hover:  rgba(26, 31, 46, 0.75);

    --accent:          #818CF8;
    --accent-dim:      #6366F1;
    --accent-bright:   #A5B4FC;
    --accent-glow:     rgba(129, 140, 248, 0.12);
    --accent-glow-strong: rgba(129, 140, 248, 0.25);

    --text-primary:    #F1F5F9;
    --text-secondary:  #94A3B8;
    --text-muted:      #64748B;
    --text-on-accent:  #FFFFFF;

    --border:          rgba(148, 163, 184, 0.1);
    --border-hover:    rgba(148, 163, 184, 0.2);

    --success:         #34D399;
    --success-bg:      rgba(52, 211, 153, 0.1);
    --warning:         #FBBF24;
    --warning-bg:      rgba(251, 191, 36, 0.1);
    --error:           #F87171;
    --error-bg:        rgba(248, 113, 113, 0.1);

    /* ── Typography ── */
    --font-sans:       'Inter', system-ui, -apple-system, sans-serif;
    --font-mono:       'JetBrains Mono', 'Fira Code', monospace;

    --text-xs:   0.75rem;    /* 12px */
    --text-sm:   0.875rem;   /* 14px */
    --text-base: 1rem;       /* 16px */
    --text-lg:   1.125rem;   /* 18px */
    --text-xl:   1.25rem;    /* 20px */
    --text-2xl:  1.5rem;     /* 24px */
    --text-3xl:  1.875rem;   /* 30px */
    --text-4xl:  2.25rem;    /* 36px */

    --leading-tight:   1.25;
    --leading-snug:    1.375;
    --leading-normal:  1.5;
    --leading-relaxed: 1.625;

    --tracking-tight:  -0.025em;
    --tracking-normal: 0;

    /* ── Spacing (4/8px rhythm) ── */
    --space-1:  0.25rem;   /* 4px  */
    --space-2:  0.5rem;    /* 8px  */
    --space-3:  0.75rem;   /* 12px */
    --space-4:  1rem;      /* 16px */
    --space-5:  1.25rem;   /* 20px */
    --space-6:  1.5rem;    /* 24px */
    --space-8:  2rem;      /* 32px */
    --space-10: 2.5rem;    /* 40px */
    --space-12: 3rem;      /* 48px */
    --space-16: 4rem;      /* 64px */

    /* ── Border Radius ── */
    --radius-sm:   0.375rem;  /* 6px  */
    --radius-md:   0.5rem;    /* 8px  */
    --radius-lg:   0.75rem;   /* 12px */
    --radius-xl:   1rem;      /* 16px */
    --radius-2xl:  1.5rem;    /* 24px */
    --radius-full: 9999px;

    /* ── Shadows ── */
    --shadow-sm:  0 1px 2px 0 rgba(0,0,0,0.2);
    --shadow-md:  0 4px 6px -1px rgba(0,0,0,0.25), 0 2px 4px -2px rgba(0,0,0,0.15);
    --shadow-lg:  0 10px 15px -3px rgba(0,0,0,0.3), 0 4px 6px -4px rgba(0,0,0,0.2);
    --shadow-xl:  0 20px 25px -5px rgba(0,0,0,0.3), 0 8px 10px -6px rgba(0,0,0,0.2);
    --shadow-glow: 0 0 20px var(--accent-glow), 0 0 40px rgba(129,140,248,0.05);

    /* ── Motion ── */
    --duration-fast:   150ms;
    --duration-normal: 200ms;
    --duration-slow:   300ms;
    --ease-out:        cubic-bezier(0.16, 1, 0.3, 1);
    --ease-in-out:     cubic-bezier(0.4, 0, 0.2, 1);
}

/* ═══════════════════════════════════════════════════════════════════════
   GLOBAL OVERRIDES
   ═══════════════════════════════════════════════════════════════════════ */
html, body, [data-testid="stAppViewContainer"],
[data-testid="stApp"] {
    font-family: var(--font-sans) !important;
    color: var(--text-primary);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

[data-testid="stAppViewContainer"] {
    background: var(--bg-primary) !important;
}

/* Hide default Streamlit header/footer */
header[data-testid="stHeader"] {
    background: transparent !important;
}
#MainMenu, footer, header .stDeployButton {
    display: none !important;
}

/* Scrollbar styling */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb {
    background: var(--text-muted);
    border-radius: var(--radius-full);
}
::-webkit-scrollbar-thumb:hover { background: var(--text-secondary); }

/* ═══════════════════════════════════════════════════════════════════════
   ANIMATIONS
   ═══════════════════════════════════════════════════════════════════════ */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeIn {
    from { opacity: 0; }
    to   { opacity: 1; }
}
@keyframes subtlePulse {
    0%, 100% { opacity: 0.6; }
    50%      { opacity: 1; }
}
@keyframes shimmer {
    0%   { background-position: -200% center; }
    100% { background-position: 200% center; }
}
@keyframes slideInLeft {
    from { opacity: 0; transform: translateX(-12px); }
    to   { opacity: 1; transform: translateX(0); }
}
@keyframes slideInRight {
    from { opacity: 0; transform: translateX(12px); }
    to   { opacity: 1; transform: translateX(0); }
}

/* ═══════════════════════════════════════════════════════════════════════
   HERO SECTION
   ═══════════════════════════════════════════════════════════════════════ */
.hero-container {
    text-align: center;
    padding: var(--space-12) var(--space-4) var(--space-8);
    animation: fadeInUp 0.6s var(--ease-out) both;
}
.hero-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 64px;
    height: 64px;
    border-radius: var(--radius-xl);
    background: linear-gradient(135deg, var(--accent-glow-strong), var(--accent-glow));
    border: 1px solid var(--border);
    margin-bottom: var(--space-6);
    box-shadow: var(--shadow-glow);
}
.hero-icon svg {
    width: 32px;
    height: 32px;
    color: var(--accent);
}
.hero-title {
    font-family: var(--font-sans);
    font-size: var(--text-4xl);
    font-weight: 700;
    letter-spacing: var(--tracking-tight);
    line-height: var(--leading-tight);
    margin: 0 0 var(--space-3) 0;
    background: linear-gradient(135deg, var(--text-primary) 0%, var(--accent-bright) 50%, var(--accent) 100%);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: shimmer 6s linear infinite;
}
.hero-subtitle {
    font-family: var(--font-sans);
    font-size: var(--text-lg);
    font-weight: 400;
    color: var(--text-secondary);
    line-height: var(--leading-relaxed);
    max-width: 520px;
    margin: 0 auto;
}
.hero-divider {
    width: 48px;
    height: 3px;
    background: linear-gradient(90deg, var(--accent-dim), var(--accent-bright));
    border-radius: var(--radius-full);
    margin: var(--space-8) auto var(--space-6);
    opacity: 0.7;
}

/* ═══════════════════════════════════════════════════════════════════════
   GLASS CARD (Upload, Summary)
   ═══════════════════════════════════════════════════════════════════════ */
.glass-card {
    background: var(--bg-glass);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid var(--bg-glass-border);
    border-radius: var(--radius-xl);
    padding: var(--space-6);
    box-shadow: var(--shadow-md);
    transition: border-color var(--duration-normal) var(--ease-in-out),
                box-shadow var(--duration-normal) var(--ease-in-out);
    animation: fadeInUp 0.5s var(--ease-out) both;
}
.glass-card:hover {
    border-color: var(--border-hover);
    box-shadow: var(--shadow-lg);
}
.glass-card-header {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    margin-bottom: var(--space-4);
}
.glass-card-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    border-radius: var(--radius-md);
    background: var(--accent-glow);
    flex-shrink: 0;
}
.glass-card-icon svg {
    width: 20px;
    height: 20px;
    color: var(--accent);
}
.glass-card-title {
    font-family: var(--font-sans);
    font-size: var(--text-base);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
    letter-spacing: var(--tracking-tight);
}
.glass-card-desc {
    font-size: var(--text-sm);
    color: var(--text-muted);
    margin: 0;
}

/* ═══════════════════════════════════════════════════════════════════════
   FILE UPLOADER OVERRIDE
   ═══════════════════════════════════════════════════════════════════════ */
[data-testid="stFileUploader"] {
    animation: fadeIn 0.4s var(--ease-out) both;
}
[data-testid="stFileUploader"] section {
    background: var(--bg-surface) !important;
    border: 1.5px dashed var(--border-hover) !important;
    border-radius: var(--radius-lg) !important;
    padding: var(--space-6) !important;
    transition: border-color var(--duration-normal) var(--ease-in-out),
                background var(--duration-normal) var(--ease-in-out);
}
[data-testid="stFileUploader"] section:hover {
    border-color: var(--accent) !important;
    background: var(--bg-glass) !important;
}
[data-testid="stFileUploader"] label {
    font-family: var(--font-sans) !important;
    font-size: var(--text-sm) !important;
    font-weight: 500 !important;
    color: var(--text-secondary) !important;
}
[data-testid="stFileUploader"] button {
    background-color: var(--accent-dim) !important;
    color: var(--text-on-accent) !important;
    border-radius: var(--radius-md) !important;
    font-weight: 500 !important;
    border: none !important;
    transition: all var(--duration-fast) var(--ease-out) !important;
}
[data-testid="stFileUploader"] button:hover {
    background-color: var(--accent) !important;
    box-shadow: var(--shadow-glow) !important;
}

/* ═══════════════════════════════════════════════════════════════════════
   BUTTONS
   ═══════════════════════════════════════════════════════════════════════ */
.stButton > button {
    font-family: var(--font-sans) !important;
    font-size: var(--text-sm) !important;
    font-weight: 600 !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    padding: var(--space-2) var(--space-5) !important;
    background: var(--bg-surface) !important;
    color: var(--text-primary) !important;
    cursor: pointer;
    transition: all var(--duration-normal) var(--ease-out) !important;
    min-height: 44px;
    box-shadow: var(--shadow-sm) !important;
}
.stButton > button:hover {
    background: var(--accent-dim) !important;
    color: var(--text-on-accent) !important;
    border-color: var(--accent-dim) !important;
    box-shadow: var(--shadow-glow), var(--shadow-md) !important;
    transform: translateY(-1px);
}
.stButton > button:active {
    transform: translateY(0px);
    box-shadow: var(--shadow-sm) !important;
}

/* Primary action button (Ask AI) */
.primary-action .stButton > button {
    background: linear-gradient(135deg, var(--accent-dim), var(--accent)) !important;
    color: var(--text-on-accent) !important;
    border: none !important;
    box-shadow: var(--shadow-glow), var(--shadow-md) !important;
    font-size: var(--text-base) !important;
    padding: var(--space-3) var(--space-6) !important;
    min-height: 48px;
}
.primary-action .stButton > button:hover {
    box-shadow: var(--shadow-glow), var(--shadow-lg) !important;
    transform: translateY(-2px);
    filter: brightness(1.1);
}

/* ═══════════════════════════════════════════════════════════════════════
   TEXT AREA
   ═══════════════════════════════════════════════════════════════════════ */
[data-testid="stTextArea"] textarea {
    font-family: var(--font-sans) !important;
    font-size: var(--text-base) !important;
    background: var(--bg-surface) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    color: var(--text-primary) !important;
    padding: var(--space-4) !important;
    transition: border-color var(--duration-normal) var(--ease-in-out),
                box-shadow var(--duration-normal) var(--ease-in-out) !important;
    line-height: var(--leading-normal) !important;
    resize: vertical;
}
[data-testid="stTextArea"] textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-glow) !important;
    outline: none !important;
}
[data-testid="stTextArea"] textarea::placeholder {
    color: var(--text-muted) !important;
    font-style: normal;
}
[data-testid="stTextArea"] label {
    font-family: var(--font-sans) !important;
    font-weight: 500 !important;
    color: var(--text-secondary) !important;
    font-size: var(--text-sm) !important;
}

/* ═══════════════════════════════════════════════════════════════════════
   CHAT BUBBLES
   ═══════════════════════════════════════════════════════════════════════ */
.chat-container {
    display: flex;
    flex-direction: column;
    gap: var(--space-4);
    padding: var(--space-4) 0;
}
.chat-bubble {
    max-width: 85%;
    padding: var(--space-4) var(--space-5);
    font-family: var(--font-sans);
    font-size: var(--text-base);
    line-height: var(--leading-relaxed);
    word-wrap: break-word;
    overflow-wrap: break-word;
}
.chat-bubble-user {
    align-self: flex-end;
    background: linear-gradient(135deg, var(--accent-dim), var(--accent));
    color: var(--text-on-accent);
    border-radius: var(--radius-xl) var(--radius-xl) var(--radius-sm) var(--radius-xl);
    box-shadow: var(--shadow-md);
    animation: slideInRight 0.3s var(--ease-out) both;
}
.chat-bubble-ai {
    align-self: flex-start;
    background: var(--bg-surface);
    color: var(--text-primary);
    border: 1px solid var(--border);
    border-radius: var(--radius-xl) var(--radius-xl) var(--radius-xl) var(--radius-sm);
    box-shadow: var(--shadow-sm);
    animation: slideInLeft 0.3s var(--ease-out) both;
}
.chat-label {
    font-size: var(--text-xs);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: var(--space-1);
    opacity: 0.7;
}
.chat-label-user { color: rgba(255,255,255,0.7); }
.chat-label-ai   { color: var(--accent); }

/* ═══════════════════════════════════════════════════════════════════════
   SUMMARY PANEL
   ═══════════════════════════════════════════════════════════════════════ */
.summary-panel {
    background: var(--bg-glass);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid var(--bg-glass-border);
    border-left: 3px solid var(--accent);
    border-radius: var(--radius-lg);
    padding: var(--space-6);
    margin-top: var(--space-4);
    color: var(--text-primary);
    font-family: var(--font-sans);
    font-size: var(--text-base);
    line-height: var(--leading-relaxed);
    box-shadow: var(--shadow-md);
    animation: fadeInUp 0.4s var(--ease-out) both;
}
.summary-panel h3 {
    font-size: var(--text-lg);
    font-weight: 600;
    color: var(--accent-bright);
    margin: 0 0 var(--space-3) 0;
    letter-spacing: var(--tracking-tight);
}

/* ═══════════════════════════════════════════════════════════════════════
   STATUS BADGES
   ═══════════════════════════════════════════════════════════════════════ */
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: var(--space-2);
    padding: var(--space-2) var(--space-4);
    border-radius: var(--radius-full);
    font-family: var(--font-sans);
    font-size: var(--text-sm);
    font-weight: 500;
    animation: fadeIn 0.3s var(--ease-out) both;
}
.status-success {
    background: var(--success-bg);
    color: var(--success);
    border: 1px solid rgba(52, 211, 153, 0.2);
}
.status-error {
    background: var(--error-bg);
    color: var(--error);
    border: 1px solid rgba(248, 113, 113, 0.2);
}

/* ═══════════════════════════════════════════════════════════════════════
   STREAMLIT ALERT OVERRIDES (success, error, warning, info)
   ═══════════════════════════════════════════════════════════════════════ */
[data-testid="stAlert"] {
    border-radius: var(--radius-lg) !important;
    font-family: var(--font-sans) !important;
    border: 1px solid var(--border) !important;
    animation: fadeIn 0.3s var(--ease-out) both;
}

/* ═══════════════════════════════════════════════════════════════════════
   SPINNER
   ═══════════════════════════════════════════════════════════════════════ */
[data-testid="stSpinner"] {
    font-family: var(--font-sans) !important;
    color: var(--text-secondary) !important;
}

/* ═══════════════════════════════════════════════════════════════════════
   DOWNLOAD BUTTON
   ═══════════════════════════════════════════════════════════════════════ */
.stDownloadButton > button {
    font-family: var(--font-sans) !important;
    font-weight: 600 !important;
    background: var(--bg-surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    color: var(--text-primary) !important;
    transition: all var(--duration-normal) var(--ease-out) !important;
    min-height: 44px;
}
.stDownloadButton > button:hover {
    background: var(--accent-glow) !important;
    border-color: var(--accent) !important;
    color: var(--accent-bright) !important;
}

/* ═══════════════════════════════════════════════════════════════════════
   SECTION LABELS & DIVIDERS
   ═══════════════════════════════════════════════════════════════════════ */
.section-label {
    font-family: var(--font-sans);
    font-size: var(--text-xs);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-muted);
    margin-bottom: var(--space-3);
}
.divider {
    border: none;
    border-top: 1px solid var(--border);
    margin: var(--space-8) 0;
}

/* ═══════════════════════════════════════════════════════════════════════
   FOOTER
   ═══════════════════════════════════════════════════════════════════════ */
.app-footer {
    text-align: center;
    padding: var(--space-8) var(--space-4) var(--space-6);
    color: var(--text-muted);
    font-size: var(--text-xs);
    font-family: var(--font-sans);
    letter-spacing: 0.02em;
}
.app-footer a {
    color: var(--accent);
    text-decoration: none;
}
.app-footer a:hover {
    text-decoration: underline;
}
</style>
""", unsafe_allow_html=True)


# ─── Session State ────────────────────────────────────────────────────────────
if "user_queries" not in st.session_state:
    st.session_state.user_queries = []
if "ai_responses" not in st.session_state:
    st.session_state.ai_responses = []
if "summary" not in st.session_state:
    st.session_state.summary = None


# ─── SVG Icons (inline, no emoji) ────────────────────────────────────────────
ICON_SCALE = '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 256 256" fill="currentColor"><path d="M228,200a12,12,0,0,1-12,12H40a12,12,0,0,1,0-24h4V104A84,84,0,0,1,212,104v84h4A12,12,0,0,1,228,200ZM68,176H188V104a60,60,0,0,0-120,0Zm60-100a12,12,0,0,1-12,12,12,12,0,0,0-12,12,12,12,0,0,1-24,0,36,36,0,0,1,36-36A12,12,0,0,1,128,76Z"/></svg>'
ICON_UPLOAD = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 256 256" fill="currentColor"><path d="M213.66,82.34l-56-56A8,8,0,0,0,152,24H56A16,16,0,0,0,40,40V216a16,16,0,0,0,16,16H200a16,16,0,0,0,16-16V88A8,8,0,0,0,213.66,82.34ZM160,176H96a8,8,0,0,1,0-16h64a8,8,0,0,1,0,16Zm0-32H96a8,8,0,0,1,0-16h64a8,8,0,0,1,0,16Zm-8-56V44l44,44Z"/></svg>'
ICON_CHAT = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 256 256" fill="currentColor"><path d="M216,48H40A16,16,0,0,0,24,64V222.77c0,8.25,9.53,12.76,15.52,7.34L70.4,204H216a16,16,0,0,0,16-16V64A16,16,0,0,0,216,48ZM160,152H96a8,8,0,0,1,0-16h64a8,8,0,0,1,0,16Zm0-32H96a8,8,0,0,1,0-16h64a8,8,0,0,1,0,16Z"/></svg>'
ICON_SUMMARY = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 256 256" fill="currentColor"><path d="M213.66,82.34l-56-56A8,8,0,0,0,152,24H56A16,16,0,0,0,40,40V216a16,16,0,0,0,16,16H200a16,16,0,0,0,16-16V88A8,8,0,0,0,213.66,82.34ZM160,176H96a8,8,0,0,1,0-16h64a8,8,0,0,1,0,16Zm0-32H96a8,8,0,0,1,0-16h64a8,8,0,0,1,0,16Zm-8-56V44l44,44Z"/></svg>'
ICON_DOWNLOAD = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 256 256" fill="currentColor"><path d="M232,136v64a16,16,0,0,1-16,16H40a16,16,0,0,1-16-16V136a16,16,0,0,1,16-16H72a8,8,0,0,1,0,16H40v64H216V136H184a8,8,0,0,1,0-16h32A16,16,0,0,1,232,136Zm-101.66,5.66a8,8,0,0,0,11.32,0l40-40a8,8,0,0,0-11.32-11.32L136,124.69V24a8,8,0,0,0-16,0v100.69L85.66,90.34a8,8,0,0,0-11.32,11.32Z"/></svg>'


# ─── Hero Section ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero-container">
    <div class="hero-icon">{ICON_SCALE}</div>
    <h1 class="hero-title">AI Lawyer</h1>
    <p class="hero-subtitle">
        Upload a legal document and get AI-powered analysis,
        summaries, and answers — grounded in the text.
    </p>
    <div class="hero-divider"></div>
</div>
""", unsafe_allow_html=True)


# ─── Document Upload Section ─────────────────────────────────────────────────
st.markdown(f"""
<div class="glass-card" style="animation-delay: 0.15s;">
    <div class="glass-card-header">
        <div class="glass-card-icon">{ICON_UPLOAD}</div>
        <div>
            <p class="glass-card-title">Upload Document</p>
            <p class="glass-card-desc">Drag and drop a PDF or click to browse</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

uploaded_files = st.file_uploader(
    "Upload legal documents (PDF)",
    type="pdf",
    accept_multiple_files=True,
    label_visibility="collapsed",
)

if uploaded_files:
    # Get current uploaded file names
    current_file_names = [f.name for f in uploaded_files]
    
    # Save & index any new files that aren't already indexed
    if "indexed_files" not in st.session_state:
        st.session_state.indexed_files = []
        
    new_files_indexed = False
    for uploaded_file in uploaded_files:
        if uploaded_file.name not in st.session_state.indexed_files:
            file_path = upload_pdf(uploaded_file)
            index_pdf(file_path)
            st.session_state.indexed_files.append(uploaded_file.name)
            new_files_indexed = True

    st.markdown(f"""
    <div class="status-badge status-success">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 256 256" fill="currentColor">
            <path d="M229.66,77.66l-128,128a8,8,0,0,1-11.32,0l-56-56a8,8,0,0,1,11.32-11.32L96,188.69,218.34,66.34a8,8,0,0,1,11.32,11.32Z"/>
        </svg>
        {len(uploaded_files)} document(s) uploaded and indexed
    </div>
    """, unsafe_allow_html=True)
    
    # ── Proactive Scan ────────────────────────────────────────────────────
    if new_files_indexed:
        with st.spinner("Proactively scanning for key legal clauses..."):
            scan_docs = retrieve_docs("Governing law, jurisdiction, term, termination, liability, obligations", current_file_names)
            if scan_docs:
                scan_result = proactive_scan(scan_docs)
                st.session_state.proactive_scan_result = str(scan_result.content) if hasattr(scan_result, 'content') else str(scan_result)

    if st.session_state.get("proactive_scan_result"):
        with st.expander("🔍 Proactive Legal Scan (Key Clauses)", expanded=True):
            st.markdown(st.session_state.proactive_scan_result)

    # ── Action buttons row ────────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        summarize_clicked = st.button("Summarize Document", use_container_width=True)
    with col2:
        if st.session_state.user_queries and st.session_state.ai_responses:
            report_clicked = st.button("Download Report", use_container_width=True)
        else:
            report_clicked = False

    # ── Summarization ─────────────────────────────────────────────────────
    if summarize_clicked:
        with st.spinner("Analyzing document structure..."):
            retrieved_docs = retrieve_docs("Summarize this document", current_file_names)
            if not retrieved_docs:
                st.error("Could not retrieve content. Please try re-uploading the document(s).")
            else:
                summary = summarize_document(retrieved_docs)
                st.session_state.summary = str(summary.content) if hasattr(summary, 'content') else str(summary)

    if st.session_state.summary:
        st.markdown(f"""
        <div class="summary-panel">
            <h3>Document Summary</h3>
            {st.session_state.summary}
        </div>
        """, unsafe_allow_html=True)

    # ── Report Download ───────────────────────────────────────────────────
    if report_clicked:
        report_path = generate_report(st.session_state.user_queries, st.session_state.ai_responses)
        with open(report_path, "rb") as file:
            st.download_button(
                label="Save Report as DOCX",
                data=file,
                file_name="AI_Lawyer_Report.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )


# ─── Divider ──────────────────────────────────────────────────────────────────
st.markdown('<hr class="divider">', unsafe_allow_html=True)


# ─── Chat Section ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="glass-card-header" style="padding: 0; margin-bottom: 4px;">
    <div class="glass-card-icon">{ICON_CHAT}</div>
    <div>
        <p class="glass-card-title">Legal Consultation</p>
        <p class="glass-card-desc">Ask questions about your uploaded document</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Conversation History ──────────────────────────────────────────────────────
if st.session_state.user_queries:
    chat_parts = []
    for q, a in zip(st.session_state.user_queries, st.session_state.ai_responses):
        response_text = str(a.content) if hasattr(a, 'content') else str(a)
        safe_q = html.escape(q)
        safe_a = html.escape(response_text).replace('&#x27;', "'")
        chat_parts.append(
            f'<div class="chat-bubble chat-bubble-user">'
            f'<div class="chat-label chat-label-user">You</div>'
            f'{safe_q}</div>'
            f'<div class="chat-bubble chat-bubble-ai">'
            f'<div class="chat-label chat-label-ai">AI Lawyer</div>'
            f'{safe_a}</div>'
        )
    full_chat = '<div class="chat-container">' + ''.join(chat_parts) + '</div>'
    st.markdown(full_chat, unsafe_allow_html=True)

# ── Query Input ───────────────────────────────────────────────────────────────
user_query = st.text_area(
    "Your question",
    height=100,
    placeholder="e.g. What are the key obligations defined in this contract?",
    label_visibility="collapsed",
)

st.markdown('<div class="primary-action">', unsafe_allow_html=True)
ask_clicked = st.button("Ask AI Lawyer", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

if ask_clicked:
    if not uploaded_files:
        st.error("Please upload at least one PDF document first.")
    elif not user_query.strip():
        st.error("Please type a question before asking.")
    else:
        with st.spinner("Reasoning through the document(s)..."):
            retrieved_docs = retrieve_docs(user_query, current_file_names)
            response = answer_query(documents=retrieved_docs, model=get_llm_model(), query=user_query)

            st.session_state.user_queries.append(user_query)
            st.session_state.ai_responses.append(response)
            st.rerun()


# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-footer">
    AI Lawyer &mdash; Retrieval-Augmented Generation with LLM reasoning<br>
    Responses are grounded in document context. Not a substitute for professional legal advice.
</div>
""", unsafe_allow_html=True)