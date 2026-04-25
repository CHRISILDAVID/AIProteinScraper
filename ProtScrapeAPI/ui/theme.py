"""
ui/theme.py
───────────
Premium dark theme with glassmorphism, gradients, and micro-animations.
"""

import streamlit as st


def inject_custom_css():
    """Inject the ProtScrape premium theme CSS."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ── Global ──────────────────────────────────────────────────────── */
    :root {
        --bg-primary: #0a0e1a;
        --bg-secondary: #111827;
        --bg-card: rgba(17, 24, 39, 0.7);
        --bg-glass: rgba(255, 255, 255, 0.03);
        --border-glass: rgba(255, 255, 255, 0.08);
        --text-primary: #f0f4f8;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
        --accent-primary: #6366f1;
        --accent-secondary: #8b5cf6;
        --accent-tertiary: #06b6d4;
        --accent-success: #10b981;
        --accent-warning: #f59e0b;
        --accent-error: #ef4444;
        --gradient-primary: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #06b6d4 100%);
        --gradient-subtle: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.05) 100%);
        --shadow-glow: 0 0 30px rgba(99, 102, 241, 0.15);
        --radius: 16px;
        --radius-sm: 10px;
        --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .stApp {
        background: var(--bg-primary) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        color: var(--text-primary) !important;
    }

    .stApp > header {
        background: transparent !important;
    }

    /* ── Sidebar ─────────────────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f1729 0%, #111827 100%) !important;
        border-right: 1px solid var(--border-glass) !important;
    }

    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown label,
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stCheckbox label,
    [data-testid="stSidebar"] .stSlider label,
    [data-testid="stSidebar"] .stTextInput label,
    [data-testid="stSidebar"] .stTextArea label {
        color: var(--text-secondary) !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* ── Glass cards ─────────────────────────────────────────────────── */
    .glass-card {
        background: var(--bg-glass);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid var(--border-glass);
        border-radius: var(--radius);
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: var(--transition);
    }

    .glass-card:hover {
        border-color: rgba(99, 102, 241, 0.2);
        box-shadow: var(--shadow-glow);
        transform: translateY(-2px);
    }

    /* ── Source cards ─────────────────────────────────────────────────── */
    .source-card {
        background: var(--bg-glass);
        backdrop-filter: blur(16px);
        border: 1px solid var(--border-glass);
        border-radius: var(--radius-sm);
        padding: 1.2rem 1.5rem;
        margin-bottom: 0.75rem;
        transition: var(--transition);
        position: relative;
        overflow: hidden;
    }

    .source-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: var(--gradient-primary);
        border-radius: 4px 0 0 4px;
    }

    .source-card:hover {
        border-color: rgba(99, 102, 241, 0.25);
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.1);
        transform: translateX(4px);
    }

    .source-card h4 {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        margin: 0 0 0.5rem 0 !important;
        font-family: 'Inter', sans-serif !important;
    }

    .source-card .source-url {
        color: var(--accent-tertiary) !important;
        font-size: 0.8rem;
        text-decoration: none;
        opacity: 0.8;
        transition: var(--transition);
    }

    .source-card .source-url:hover {
        opacity: 1;
    }

    .source-card .entry-count {
        color: var(--accent-success);
        font-weight: 500;
        font-size: 0.85rem;
    }

    .source-card .error-msg {
        color: var(--accent-error);
        font-size: 0.85rem;
    }

    /* ── Hero header ─────────────────────────────────────────────────── */
    .hero-title {
        font-family: 'Inter', sans-serif !important;
        font-weight: 800 !important;
        font-size: 2.8rem !important;
        background: var(--gradient-primary);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.25rem !important;
        letter-spacing: -1px;
    }

    .hero-subtitle {
        font-family: 'Inter', sans-serif !important;
        color: var(--text-secondary) !important;
        font-size: 1.05rem !important;
        font-weight: 300 !important;
        margin-bottom: 2rem !important;
    }

    /* ── Metric chips ────────────────────────────────────────────────── */
    .metric-row {
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
        margin-bottom: 1.5rem;
    }

    .metric-chip {
        background: var(--bg-glass);
        backdrop-filter: blur(10px);
        border: 1px solid var(--border-glass);
        border-radius: 50px;
        padding: 0.6rem 1.2rem;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        font-family: 'Inter', sans-serif;
        transition: var(--transition);
    }

    .metric-chip:hover {
        border-color: rgba(99, 102, 241, 0.3);
    }

    .metric-chip .label {
        color: var(--text-muted);
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .metric-chip .value {
        color: var(--text-primary);
        font-size: 1rem;
        font-weight: 600;
    }

    /* ── Status indicators ───────────────────────────────────────────── */
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
    }

    .status-dot.success {
        background: var(--accent-success);
        box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
    }

    .status-dot.error {
        background: var(--accent-error);
        box-shadow: 0 0 8px rgba(239, 68, 68, 0.5);
    }

    .status-dot.warning {
        background: var(--accent-warning);
        box-shadow: 0 0 8px rgba(245, 158, 11, 0.5);
    }

    /* ── Confidence bar ──────────────────────────────────────────────── */
    .confidence-bar-container {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 50px;
        height: 8px;
        overflow: hidden;
        margin: 0.5rem 0;
    }

    .confidence-bar-fill {
        height: 100%;
        border-radius: 50px;
        background: var(--gradient-primary);
        transition: width 1s ease-out;
    }

    /* ── Verdict badge ───────────────────────────────────────────────── */
    .verdict-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.35rem 1rem;
        border-radius: 50px;
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        font-weight: 600;
        letter-spacing: 0.3px;
    }

    .verdict-badge.valid {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }

    .verdict-badge.invalid {
        background: rgba(239, 68, 68, 0.15);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }

    .verdict-badge.uncertain {
        background: rgba(245, 158, 11, 0.15);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }

    /* ── Evidence quote ──────────────────────────────────────────────── */
    .evidence-quote {
        background: rgba(99, 102, 241, 0.05);
        border-left: 3px solid var(--accent-primary);
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
        font-size: 0.9rem;
        color: var(--text-secondary);
    }

    .evidence-quote .quote-source {
        color: var(--accent-tertiary);
        font-size: 0.75rem;
        font-weight: 500;
        margin-top: 0.35rem;
    }

    /* ── Expander overrides ──────────────────────────────────────────── */
    .streamlit-expanderHeader {
        background: var(--bg-glass) !important;
        border: 1px solid var(--border-glass) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text-primary) !important;
        font-family: 'Inter', sans-serif !important;
    }

    div[data-testid="stExpander"] > details {
        background: var(--bg-glass) !important;
        border: 1px solid var(--border-glass) !important;
        border-radius: var(--radius-sm) !important;
    }

    /* ── Buttons ──────────────────────────────────────────────────────── */
    .stButton > button {
        background: var(--gradient-primary) !important;
        color: white !important;
        border: none !important;
        border-radius: 50px !important;
        padding: 0.6rem 2rem !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        transition: var(--transition) !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3) !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 25px rgba(99, 102, 241, 0.45) !important;
    }

    .stButton > button:active {
        transform: translateY(0) !important;
    }

    .stDownloadButton > button {
        background: transparent !important;
        border: 1px solid var(--border-glass) !important;
        color: var(--text-primary) !important;
        border-radius: 50px !important;
        font-family: 'Inter', sans-serif !important;
        transition: var(--transition) !important;
    }

    .stDownloadButton > button:hover {
        border-color: var(--accent-primary) !important;
        background: rgba(99, 102, 241, 0.1) !important;
    }

    /* ── Inputs ───────────────────────────────────────────────────────── */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: var(--bg-glass) !important;
        border: 1px solid var(--border-glass) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text-primary) !important;
        font-family: 'Inter', sans-serif !important;
        transition: var(--transition) !important;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2) !important;
    }

    .stSelectbox > div > div {
        background: var(--bg-glass) !important;
        border: 1px solid var(--border-glass) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text-primary) !important;
    }

    /* ── Dataframe ────────────────────────────────────────────────────── */
    .stDataFrame {
        border-radius: var(--radius-sm) !important;
        overflow: hidden;
    }

    /* ── Pulse animation for loading ─────────────────────────────────── */
    @keyframes pulse-glow {
        0%, 100% { opacity: 0.6; }
        50% { opacity: 1; }
    }

    .pulse {
        animation: pulse-glow 2s ease-in-out infinite;
    }

    @keyframes fade-in-up {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .fade-in {
        animation: fade-in-up 0.6s ease-out forwards;
    }

    /* ── Field table ─────────────────────────────────────────────────── */
    .field-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        border-radius: var(--radius-sm);
        overflow: hidden;
        font-family: 'Inter', sans-serif;
    }

    .field-table th {
        background: rgba(99, 102, 241, 0.1);
        color: var(--text-secondary);
        padding: 0.75rem 1rem;
        text-align: left;
        font-weight: 600;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .field-table td {
        padding: 0.75rem 1rem;
        border-bottom: 1px solid var(--border-glass);
        color: var(--text-primary);
        font-size: 0.9rem;
    }

    .field-table tr:last-child td {
        border-bottom: none;
    }

    .field-table tr:hover td {
        background: rgba(99, 102, 241, 0.05);
    }

    .field-table .source-tag {
        display: inline-block;
        background: rgba(6, 182, 212, 0.12);
        color: var(--accent-tertiary);
        padding: 0.15rem 0.6rem;
        border-radius: 50px;
        font-size: 0.75rem;
        font-weight: 500;
    }

    /* ── Section headers ─────────────────────────────────────────────── */
    .section-header {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 1.3rem;
        color: var(--text-primary);
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--border-glass);
    }

    /* ── Scrollbar ────────────────────────────────────────────────────── */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }

    ::-webkit-scrollbar-track {
        background: transparent;
    }

    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 3px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.2);
    }
    </style>
    """, unsafe_allow_html=True)
