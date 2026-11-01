import streamlit as st
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import os
import uuid
import json

# API_BASE is the primary URL (Render production)
API_BASE = os.getenv("API_BASE", "https://algo-trading-api-mpd1.onrender.com")
# Fallback API for when Render is rate-limited (local Docker)
FALLBACK_API_BASE = os.getenv("FALLBACK_API_BASE", "http://localhost:8000")

st.set_page_config(
    page_title="Algo Trading API | Quantitative Backtesting Engine",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

    :root {
        --bg-primary: #0B0F1A;
        --bg-secondary: #111827;
        --bg-tertiary: #1E293B;
        --bg-card: #151E2E;
        --border-color: #1F2937;
        --border-light: #374151;
        --text-primary: #F3F4F6;
        --text-secondary: #9CA3AF;
        --text-muted: #6B7280;
        --accent-primary: #10B981;
        --accent-primary-dim: #059669;
        --accent-secondary: #3B82F6;
        --accent-danger: #EF4444;
        --accent-warning: #F59E0B;
        --accent-purple: #A855F7;
        --gradient-primary: linear-gradient(135deg, #10B981 0%, #059669 100%);
        --gradient-secondary: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%);
        --gradient-card: linear-gradient(145deg, #151E2E 0%, #1E293B 100%);
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.3);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -2px rgba(0, 0, 0, 0.3);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -4px rgba(0, 0, 0, 0.3);
        --shadow-glow: 0 0 20px rgba(16, 185, 129, 0.15);
        --radius-sm: 6px;
        --radius-md: 10px;
        --radius-lg: 16px;
        --transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .stApp {
        background: var(--bg-primary);
        color: var(--text-primary);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    header[data-testid="stHeader"] {
        background: transparent;
        height: 0;
    }

    .stSidebar {
        background: var(--bg-secondary);
        border-right: 1px solid var(--border-color);
    }

    .stSidebar > div:first-child {
        padding-top: 1rem;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        letter-spacing: -0.02em;
        color: var(--text-primary);
    }

    .hero-section {
        background: var(--gradient-card);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        padding: 3rem 2rem;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }

    .hero-section::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: var(--gradient-primary);
    }

    .hero-section::after {
        content: '';
        position: absolute;
        top: -50%;
        right: -10%;
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, rgba(16, 185, 129, 0.08) 0%, transparent 70%);
        pointer-events: none;
    }

    .hero-title {
        font-size: 2.5rem;
        font-weight: 700;
        line-height: 1.1;
        margin-bottom: 0.75rem;
        background: linear-gradient(135deg, var(--text-primary) 0%, var(--accent-primary) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .hero-subtitle {
        font-size: 1.125rem;
        color: var(--text-secondary);
        max-width: 600px;
        line-height: 1.6;
    }

    .hero-badges {
        display: flex;
        gap: 0.75rem;
        margin-top: 1.5rem;
        flex-wrap: wrap;
    }

    .badge {
        display: inline-flex;
        align-items: center;
        gap: 0.375rem;
        padding: 0.5rem 1rem;
        background: var(--bg-tertiary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        font-size: 0.8rem;
        font-weight: 500;
        color: var(--text-secondary);
        transition: var(--transition);
    }

    .badge:hover {
        border-color: var(--accent-primary);
        color: var(--accent-primary);
        transform: translateY(-1px);
    }

    .badge.accent {
        background: rgba(16, 185, 129, 0.1);
        border-color: var(--accent-primary);
        color: var(--accent-primary);
    }

    .metric-card {
        background: var(--gradient-card);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        padding: 1.5rem;
        transition: var(--transition);
        position: relative;
        overflow: hidden;
    }

    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: var(--gradient-primary);
        opacity: 0;
        transition: var(--transition);
    }

    .metric-card:hover {
        border-color: var(--border-light);
        box-shadow: var(--shadow-lg), var(--shadow-glow);
        transform: translateY(-2px);
    }

    .metric-card:hover::before {
        opacity: 1;
    }

    .metric-card.positive::before {
        background: var(--gradient-primary);
    }

    .metric-card.negative::before {
        background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
    }

    .metric-label {
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-muted);
        margin-bottom: 0.5rem;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        line-height: 1.2;
        margin-bottom: 0.25rem;
    }

    .metric-delta {
        font-size: 0.875rem;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 0.25rem;
    }

    .metric-delta.positive { color: var(--accent-primary); }
    .metric-delta.negative { color: var(--accent-danger); }

    .section-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1.5rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid var(--border-color);
    }

    .section-title {
        font-size: 1.25rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .section-title::before {
        content: '';
        width: 4px;
        height: 20px;
        background: var(--gradient-primary);
        border-radius: 2px;
    }

    .strategy-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        padding: 1.25rem;
        margin-bottom: 0.75rem;
        transition: var(--transition);
        cursor: pointer;
    }

    .strategy-card:hover {
        border-color: var(--accent-primary);
        box-shadow: var(--shadow-md);
    }

    .strategy-card.selected {
        border-color: var(--accent-primary);
        background: rgba(16, 185, 129, 0.05);
    }

    .strategy-name {
        font-weight: 600;
        font-size: 1rem;
        margin-bottom: 0.25rem;
    }

    .strategy-desc {
        font-size: 0.8rem;
        color: var(--text-muted);
    }

    .param-group {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        padding: 1.25rem;
        margin-bottom: 1rem;
    }

    .param-label {
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--text-primary);
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .param-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--accent-primary);
    }

    .stButton > button {
        width: 100%;
        background: var(--gradient-primary);
        border: none;
        border-radius: var(--radius-md);
        padding: 0.875rem 1.5rem;
        font-size: 1rem;
        font-weight: 600;
        color: white;
        transition: var(--transition);
        box-shadow: var(--shadow-md);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg), var(--shadow-glow);
    }

    .stButton > button:active {
        transform: translateY(0);
    }

    .stButton > button:focus {
        outline: none;
        box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.3);
    }

    .stSelectbox > div > div {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: var(--radius-md) !important;
        color: var(--text-primary) !important;
    }

    .stSelectbox > div > div:hover {
        border-color: var(--border-light) !important;
    }

    .stSelectbox > div > div > div {
        color: var(--text-primary) !important;
    }

    .stSelectbox [data-baseweb="select"] > div {
        background: var(--bg-card) !important;
        color: var(--text-primary) !important;
    }

    .stSelectbox [data-baseweb="popover"] [data-baseweb="menu"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
    }

    .stSelectbox [data-baseweb="menu"] div[role="option"] {
        background: var(--bg-card) !important;
        color: var(--text-primary) !important;
    }

    .stSelectbox [data-baseweb="menu"] div[role="option"]:hover {
        background: var(--bg-tertiary) !important;
    }

    .stTextInput > div > div > input {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: var(--radius-md) !important;
        color: var(--text-primary) !important;
    }

    .stTextInput > div > div > input::placeholder {
        color: var(--text-muted) !important;
    }

    .stTextInput > div > div > input:focus {
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1) !important;
    }

    .stTextInput label {
        color: var(--text-primary) !important;
    }

    .stSlider [data-testid="stSlider"] > div > div > div[role="slider"] {
        background: var(--accent-primary) !important;
        border-color: var(--accent-primary) !important;
    }

    .stSlider [data-testid="stSlider"] > div > div > div:first-child {
        background: var(--accent-primary) !important;
    }

    .stSpinner > div {
        border-top-color: var(--accent-primary) !important;
    }

    .stSpinner > div > div:last-child {
        background: linear-gradient(135deg, var(--text-primary) 0%, var(--accent-primary) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 600;
    }

    .stAlert {
        border-radius: var(--radius-md) !important;
        border: none !important;
    }

    .stAlert[data-baseweb="notification"] {
        background: var(--bg-card) !important;
    }

    .stSuccess {
        background: rgba(16, 185, 129, 0.1) !important;
        border-left: 4px solid var(--accent-primary) !important;
    }

    .stError {
        background: rgba(239, 68, 68, 0.1) !important;
        border-left: 4px solid var(--accent-danger) !important;
    }

    .stInfo {
        background: rgba(59, 130, 246, 0.1) !important;
        border-left: 4px solid var(--accent-secondary) !important;
    }

    .chart-container {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        padding: 1rem;
        margin-top: 1rem;
    }

    .data-table {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        overflow: hidden;
    }

    .footer {
        margin-top: 3rem;
        padding: 2rem;
        text-align: center;
        color: var(--text-muted);
        font-size: 0.875rem;
        border-top: 1px solid var(--border-color);
    }

    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: var(--radius-md);
        font-size: 0.875rem;
        font-weight: 500;
    }

    .status-indicator.online {
        background: rgba(16, 185, 129, 0.1);
        color: var(--accent-primary);
    }

    .status-indicator.offline {
        background: rgba(239, 68, 68, 0.1);
        color: var(--accent-danger);
    }

    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }

    .status-dot.online { background: var(--accent-primary); }
    .status-dot.offline { background: var(--accent-danger); }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    .api-endpoint {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        background: var(--bg-tertiary);
        padding: 0.25rem 0.5rem;
        border-radius: var(--radius-sm);
        color: var(--text-secondary);
    }

    @media (max-width: 768px) {
        .hero-title { font-size: 1.75rem; }
        .hero-section { padding: 2rem 1.5rem; }
        .metric-value { font-size: 1.5rem; }
        .main .block-container { padding-left: 1rem; padding-right: 1rem; }
    }

    [data-testid="stSidebarNav"] { display: none; }

    /* Chat-specific Styles */
    .chat-container {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        padding: 1.5rem;
        margin-bottom: 2rem;
    }

    .chat-message {
        padding: 0.75rem 1rem;
        border-radius: var(--radius-md);
        margin-bottom: 1rem;
        max-width: 85%;
        line-height: 1.5;
    }

    .chat-message.user {
        background: var(--bg-tertiary);
        color: var(--text-primary);
        margin-left: auto;
        border-bottom-right-radius: 2px;
    }

    .chat-message.bot {
        background: rgba(16, 185, 129, 0.1);
        color: var(--text-primary);
        border: 1px solid rgba(16, 185, 129, 0.2);
        border-bottom-left-radius: 2px;
    }

    .thinking-process {
        background: rgba(59, 130, 246, 0.05);
        border: 1px dashed var(--accent-secondary);
        border-radius: var(--radius-md);
        padding: 1rem;
        margin-bottom: 1.5rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        color: var(--text-secondary);
    }

    .thinking-step {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.25rem;
    }

    .thinking-step.active {
        color: var(--accent-secondary);
        font-weight: 600;
    }

    .thinking-step.completed {
        color: var(--accent-primary);
    }
</style>
"""

def render_hero():
    st.markdown("""
    <div class="hero-section">
        <div style="position: relative; z-index: 1;">
            <h1 class="hero-title">Quantitative Backtesting Engine</h1>
            <p class="hero-subtitle">Algorithmic trading simulation platform for backtesting strategies against historical market data.</p>
            <div class="hero-badges">
                <span class="badge accent">⚡ REST API</span>
                <span class="badge accent">📊 3 Strategies</span>
                <span class="badge accent">🔍 Interactive Charts</span>
                <span class="badge accent">📈 Performance Metrics</span>
                <span class="badge accent">🤖 Quant Assistant AI</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def _sync_slider_to_input(slider_key, input_key):
    st.session_state[input_key] = st.session_state[slider_key]


def _sync_input_to_slider(slider_key, input_key):
    st.session_state[slider_key] = int(st.session_state[input_key])


def param_slider_input(slider_key, input_key, min_val, max_val, default, label, help_text, input_label=None):
    """Render a slider and a number input that stay in sync in both directions."""
    if slider_key not in st.session_state:
        st.session_state[slider_key] = default
    if input_key not in st.session_state:
        st.session_state[input_key] = default

    col_slider, col_input = st.columns([3, 1])
    with col_slider:
        st.slider(label, min_val, max_val, key=slider_key, help=help_text,
                  on_change=_sync_slider_to_input, args=(slider_key, input_key))
    with col_input:
        st.number_input(input_label or label, min_val, max_val, key=input_key, step=1,
                        label_visibility="collapsed",
                        on_change=_sync_input_to_slider, args=(slider_key, input_key))

    return int(st.session_state[input_key])


def get_currency_symbol(data):
    """Currency symbol from the API response, or empty string when unknown."""
    symbol = data.get("currency_symbol") if isinstance(data, dict) else None
    if not symbol:
        return ""
    return str(symbol).strip()


def price_axis_label(data):
    """Y-axis title: 'Price (₹)' when known, neutral 'Price' otherwise."""
    symbol = get_currency_symbol(data)
    return f"Price ({symbol})" if symbol else "Price"


def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="padding: 0.5rem 0 1.5rem 0;">
            <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;">
                <div style="width: 40px; height: 40px; background: var(--gradient-primary); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.25rem;">📈</div>
                <div>
                    <div style="font-weight: 700; font-size: 1.125rem;">Algo Trading API</div>
                    <div style="font-size: 0.75rem; color: var(--text-muted);">v2.0.0 · Production</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-header"><span class="section-title">Configuration</span></div>', unsafe_allow_html=True)

        ticker = st.text_input(
            "Stock Ticker",
            value="",
            placeholder="e.g., RELIANCE.NS, AAPL, TSLA, NVDA",
            help="Enter Yahoo Finance ticker symbol"
        )

        # Period selection for data range
        period_options = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
        period = st.selectbox(
            "Data Period",
            options=period_options,
            index=period_options.index("1y"),
            help="Select how much historical data to fetch"
        )


        st.markdown('<div class="section-header" style="margin-top: 1.5rem;"><span class="section-title">Strategy Selection</span></div>', unsafe_allow_html=True)

        strategy_options = [
            ("SMA Crossover (Trend Following)", "sma", "Trend-following strategy using dual moving average crossovers"),
            ("RSI (Mean Reversion)", "rsi", "Mean reversion strategy using Relative Strength Index"),
            ("Composite (SMA + RSI)", "composite", "Combined strategy with SMA signals filtered by RSI")
        ]

        strategy_choice = st.selectbox(
            "Select Trading Strategy",
            options=[opt[0] for opt in strategy_options],
            format_func=lambda x: x,
            index=0
        )

        strategy_key = next(opt[1] for opt in strategy_options if opt[0] == strategy_choice)
        strategy_desc = next(opt[2] for opt in strategy_options if opt[0] == strategy_choice)

        st.markdown(f"""
        <div class="strategy-card selected">
            <div class="strategy-name">{strategy_choice}</div>
            <div class="strategy-desc">{strategy_desc}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-header" style="margin-top: 1.5rem;"><span class="section-title">Parameters</span></div>', unsafe_allow_html=True)

        params = {}
        if strategy_key == "sma":
            fast_sma = param_slider_input("fast_sma", "fast_sma_input", 1, 500, 50, "Fast Moving Average", "Short-term SMA period", "Fast")
            slow_sma = param_slider_input("slow_sma", "slow_sma_input", 10, 1000, 80, "Slow Moving Average", "Long-term SMA period", "Slow")

            params = {"fast": fast_sma, "slow": slow_sma}
            st.markdown(f"""
            <div class="param-group">
                <div class="param-label">Fast SMA <span class="param-value">{fast_sma}</span></div>
            </div>
            <div class="param-group">
                <div class="param-label">Slow SMA <span class="param-value">{slow_sma}</span></div>
            </div>
            """, unsafe_allow_html=True)
        elif strategy_key == "rsi":
            rsi_period = param_slider_input("rsi_period", "rsi_period_input", 1, 500, 20, "RSI Lookback Period", "RSI calculation period", "Period")

            params = {"period": rsi_period}
            st.markdown(f"""
            <div class="param-group">
                <div class="param-label">RSI Period <span class="param-value">{rsi_period}</span></div>
            </div>
            """, unsafe_allow_html=True)
        else:
            fast_sma = param_slider_input("fast_sma", "fast_sma_input", 1, 500, 50, "Fast Moving Average", "Short-term SMA period", "Fast")
            slow_sma = param_slider_input("slow_sma", "slow_sma_input", 10, 1000, 80, "Slow Moving Average", "Long-term SMA period", "Slow")
            rsi_period = param_slider_input("rsi_period", "rsi_period_input", 1, 500, 20, "RSI Lookback Period", "RSI calculation period", "Period")

            params = {"fast": fast_sma, "slow": slow_sma, "rsi": rsi_period}
            st.markdown(f"""
            <div class="param-group">
                <div class="param-label">Fast SMA <span class="param-value">{fast_sma}</span></div>
            </div>
            <div class="param-group">
                <div class="param-label">Slow SMA <span class="param-value">{slow_sma}</span></div>
            </div>
            <div class="param-group">
                <div class="param-label">RSI Period <span class="param-value">{rsi_period}</span></div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div style="margin-top: 1.5rem;"></div>', unsafe_allow_html=True)
        run_button = st.button("🚀 Run Simulation", type="primary", use_container_width=True)

    return ticker, strategy_choice, strategy_key, params, run_button, period

def render_metrics(data):
    perf = data['performance']
    market_return = perf['market_return_percent']
    strategy_return = perf['strategy_return_percent']
    excess_return = round(strategy_return - market_return, 2)
    total_trades = perf.get('total_trades', 0)
    win_rate = perf.get('win_rate_percent', 0)
    max_drawdown = perf.get('max_drawdown_percent', 0)
    sharpe = perf.get('sharpe_ratio', 0)

    is_positive = excess_return >= 0
    delta_class = "positive" if is_positive else "negative"
    delta_prefix = "+" if is_positive else ""

    # Show analysis window if present
    if "analysis_window" in data:
        aw = data["analysis_window"]
        if aw.get("start_date") and aw.get("end_date"):
            st.markdown(f"""
            <div style="background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 1rem; margin-bottom: 1.5rem;">
                <div style="display: flex; gap: 2rem; flex-wrap: wrap; font-family: 'JetBrains Mono', monospace; font-size: 0.875rem;">
                    <div><strong>Analysis Window:</strong> {aw['start_date']} → {aw['end_date']}</div>
                    <div><strong>Window Days:</strong> {aw.get('window_days', 'N/A')} trading days</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card {'positive' if market_return >= 0 else 'negative'}">
            <div class="metric-label">Market Return (Buy & Hold)</div>
            <div class="metric-value" style="color: {'var(--accent-primary)' if market_return >= 0 else 'var(--accent-danger)'};">{market_return:+.2f}%</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card {'positive' if strategy_return >= 0 else 'negative'}">
            <div class="metric-label">Strategy Return</div>
            <div class="metric-value" style="color: {'var(--accent-primary)' if strategy_return >= 0 else 'var(--accent-danger)'};">{strategy_return:+.2f}%</div>
            <div class="metric-delta {delta_class}">{delta_prefix}{excess_return:.2f}% vs Market</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card {'positive' if win_rate >= 50 else 'negative'}">
            <div class="metric-label">Win Rate</div>
            <div class="metric-value" style="color: {'var(--accent-primary)' if win_rate >= 50 else 'var(--accent-danger)'};">{win_rate:.1f}%</div>
            <div class="metric-delta">From {total_trades} trades</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card {'positive' if max_drawdown <= 15 else 'negative' if max_drawdown <= 25 else 'negative'}">
            <div class="metric-label">Max Drawdown</div>
            <div class="metric-value" style="color: var(--accent-danger);">{max_drawdown:.2f}%</div>
            <div class="metric-delta">Sharpe: {sharpe:.2f}</div>
        </div>
        """, unsafe_allow_html=True)

def render_charts(data, strategy_choice):
    if "chart_data" not in data:
        return

    cd = data['chart_data']
    dates = cd['Date_Str']
    close = cd['Close']

    sym = get_currency_symbol(data)
    axis_label = price_axis_label(data)
    tick_prefix = sym
    h_price = f'%{{x}}<br>Price: {sym}%{{y:.2f}}<extra></extra>' if sym else '%{x}<br>Price: %{y:.2f}<extra></extra>'
    h_sma = f'%{{x}}<br>%{{fullData.name}}: {sym}%{{y:.2f}}<extra></extra>' if sym else '%{x}<br>%{fullData.name}: %{y:.2f}<extra></extra>'

    st.markdown('<div class="section-header" style="margin-top: 2rem;"><span class="section-title">Strategy Visualization</span></div>', unsafe_allow_html=True)

    if strategy_choice == "SMA Crossover (Trend Following)":
        fast_sma = cd['Fast_SMA']
        slow_sma = cd['Slow_SMA']

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates, y=close, name="Stock Price",
            line=dict(color='#9CA3AF', width=1.5),
            hovertemplate=h_price
        ))
        fig.add_trace(go.Scatter(
            x=dates, y=fast_sma, name="Fast SMA",
            line=dict(color='#10B981', width=2),
            hovertemplate=h_sma
        ))
        fig.add_trace(go.Scatter(
            x=dates, y=slow_sma, name="Slow SMA",
            line=dict(color='#EF4444', width=2),
            hovertemplate=h_sma
        ))

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=500,
            margin=dict(l=0, r=20, t=10, b=0),
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor='rgba(15, 23, 42, 0.95)',
                bordercolor='#374151',
                borderwidth=1,
                font=dict(color='#F3F4F6', size=11)
            ),
            xaxis=dict(
                gridcolor='#1F2937',
                zerolinecolor='#1F2937',
                showspikes=True,
                spikecolor='#374151',
                spikethickness=1,
                rangeslider=dict(visible=True, bgcolor='#111827', bordercolor='#374151'),
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label="1M", step="month", stepmode="backward"),
                        dict(count=3, label="3M", step="month", stepmode="backward"),
                        dict(count=6, label="6M", step="month", stepmode="backward"),
                        dict(count=1, label="YTD", step="year", stepmode="todate"),
                        dict(count=1, label="1Y", step="year", stepmode="backward"),
                        dict(step="all", label="All")
                    ]),
                    bgcolor='#1E293B',
                    activecolor='#10B981',
                    bordercolor='#374151',
                    font=dict(color='#F3F4F6', size=11)
                ),
                type="date"
            ),
            yaxis=dict(
                gridcolor='#1F2937',
                zerolinecolor='#1F2937',
                title=axis_label,
                tickprefix=tick_prefix
            )
        )

        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    elif strategy_choice == "RSI (Mean Reversion)":
        rsi = cd['RSI']

        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.04,
            row_heights=[0.7, 0.3],
            subplot_titles=("", "RSI (14)")
        )

        fig.add_trace(go.Scatter(
            x=dates, y=close, name="Stock Price",
            line=dict(color='#9CA3AF', width=1.5),
            hovertemplate=h_price
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=dates, y=rsi, name="RSI",
            line=dict(color='#A855F7', width=2),
            hovertemplate='%{x}<br>RSI: %{y:.1f}<extra></extra>'
        ), row=2, col=1)

        fig.add_hline(y=70, line_dash="dash", line_color="#EF4444", line_width=1, row=2, col=1, opacity=0.6)
        fig.add_hline(y=30, line_dash="dash", line_color="#10B981", line_width=1, row=2, col=1, opacity=0.6)
        fig.add_hline(y=50, line_dash="dot", line_color="#6B7280", line_width=1, row=2, col=1, opacity=0.4)

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=550,
            margin=dict(l=0, r=20, t=10, b=0),
            hovermode="x unified",
            showlegend=False,
            xaxis2=dict(
                gridcolor='#1F2937',
                zerolinecolor='#1F2937',
                showspikes=True,
                spikecolor='#374151',
                spikethickness=1,
                rangeslider=dict(visible=True, bgcolor='#111827', bordercolor='#374151'),
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label="1M", step="month", stepmode="backward"),
                        dict(count=3, label="3M", step="month", stepmode="backward"),
                        dict(count=6, label="6M", step="month", stepmode="backward"),
                        dict(count=1, label="YTD", step="year", stepmode="todate"),
                        dict(count=1, label="1Y", step="year", stepmode="backward"),
                        dict(step="all", label="All")
                    ]),
                    bgcolor='#1E293B',
                    activecolor='#10B981',
                    bordercolor='#374151',
                    font=dict(color='#F3F4F6', size=11)
                ),
                type="date"
            ),
            yaxis=dict(
                gridcolor='#1F2937',
                zerolinecolor='#1F2937',
                title=axis_label,
                tickprefix=tick_prefix
            ),
            yaxis2=dict(
                gridcolor='#1F2937',
                zerolinecolor='#1F2937',
                range=[0, 100],
                title="RSI"
            )
        )

        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    else:
        fast_sma = cd['Fast_SMA']
        slow_sma = cd['Slow_SMA']
        rsi = cd['RSI']

        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.04,
            row_heights=[0.7, 0.3],
            subplot_titles=("", "RSI (14)")
        )

        fig.add_trace(go.Scatter(
            x=dates, y=close, name="Stock Price",
            line=dict(color='#9CA3AF', width=1.5),
            hovertemplate=h_price
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=dates, y=fast_sma, name="Fast SMA",
            line=dict(color='#10B981', width=2),
            hovertemplate=h_sma
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=dates, y=slow_sma, name="Slow SMA",
            line=dict(color='#EF4444', width=2),
            hovertemplate=h_sma
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=dates, y=rsi, name="RSI",
            line=dict(color='#A855F7', width=2),
            hovertemplate='%{x}<br>RSI: %{y:.1f}<extra></extra>'
        ), row=2, col=1)

        fig.add_hline(y=70, line_dash="dash", line_color="#EF4444", line_width=1, row=2, col=1, opacity=0.6)
        fig.add_hline(y=30, line_dash="dash", line_color="#10B981", line_width=1, row=2, col=1, opacity=0.6)
        fig.add_hline(y=50, line_dash="dot", line_color="#6B7280", line_width=1, row=2, col=1, opacity=0.4)

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=600,
            margin=dict(l=0, r=20, t=10, b=0),
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor='rgba(15, 23, 42, 0.95)',
                bordercolor='#374151',
                borderwidth=1,
                font=dict(color='#F3F4F6', size=11)
            ),
            xaxis2=dict(
                gridcolor='#1F2937',
                zerolinecolor='#1F2937',
                showspikes=True,
                spikecolor='#374151',
                spikethickness=1,
                rangeslider=dict(visible=True, bgcolor='#111827', bordercolor='#374151'),
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label="1M", step="month", stepmode="backward"),
                        dict(count=3, label="3M", step="month", stepmode="backward"),
                        dict(count=6, label="6M", step="month", stepmode="backward"),
                        dict(count=1, label="YTD", step="year", stepmode="todate"),
                        dict(count=1, label="1Y", step="year", stepmode="backward"),
                        dict(step="all", label="All")
                    ]),
                    bgcolor='#1E293B',
                    activecolor='#10B981',
                    bordercolor='#374151',
                    font=dict(color='#F3F4F6', size=11)
                ),
                type="date"
            ),
            yaxis=dict(
                gridcolor='#1F2937',
                zerolinecolor='#1F2937',
                title=axis_label,
                tickprefix=tick_prefix
            ),
            yaxis2=dict(
                gridcolor='#1F2937',
                zerolinecolor='#1F2937',
                range=[0, 100],
                title="RSI"
            )
        )

        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

def render_chat():
    st.markdown('<div class="section-header"><span class="section-title">Quant Assistant AI</span></div>', unsafe_allow_html=True)
    st.markdown("""
    <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">
    Chat with our AI to run backtests and analyze stocks using natural language.
    </p>
    """, unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chat_session_id" not in st.session_state:
        st.session_state.chat_session_id = str(uuid.uuid4())

    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            div_class = "chat-message user" if msg["role"] == "user" else "chat-message bot"
            st.markdown(f'<div class="{div_class}">{msg["content"]}</div>', unsafe_allow_html=True)

    if prompt := st.chat_input("e.g., Run a 10/50 SMA backtest for AAPL"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.markdown(f'<div class="chat-message user">{prompt}</div>', unsafe_allow_html=True)

        with st.spinner("Consulting Quant Engine..."):
            try:
                payload = {"session_id": st.session_state.chat_session_id, "message": prompt}

                # Using requests to handle a response from FastAPI
                response = requests.post(f"{FALLBACK_API_BASE}/chat", json=payload, timeout=120)

                if response.status_code == 200:
                    data = response.json()
                    final_response = data.get("response", "")

                    # Render final response
                    st.markdown(f'<div class="chat-message bot">{final_response}</div>', unsafe_allow_html=True)

                    # Update session state
                    st.session_state.messages.append({"role": "bot", "content": final_response})

                    # Render Charts/Metrics if present
                    if data.get("chart_data") and data.get("performance"):
                        strat = data.get("strategy", "")
                        strategy_map = {"SMA": "SMA Crossover (Trend Following)", "RSI": "RSI (Mean Reversion)", "Composite": "Composite (SMA + RSI)"}
                        mapped_strategy = strategy_map.get(strat, strat)
                        render_metrics(data)
                        render_charts(data, mapped_strategy)
                else:
                    st.error(f"AI Error: {response.text}")
            except Exception as e:
                st.error(f"Connection Error: {str(e)}")

def main():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    ticker, strategy_choice, strategy_key, params, run_button, period = render_sidebar()
    render_hero()

    if run_button:
        with st.spinner("Running Backtest..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            for i, (pct, msg) in enumerate([(10, "Connecting..."), (30, "Fetching..."), (50, "Executing..."), (70, "Calculating..."), (90, "Visualizing..."), (100, "Complete!")]):
                progress_bar.progress(pct)
                status_text.markdown(f'<div style="color: var(--text-secondary); font-size: 0.875rem;">{msg}</div>', unsafe_allow_html=True)
                time.sleep(0.1)
            progress_bar.empty()
            status_text.empty()

            try:
                if strategy_key == "sma":
                    api_path = f"/backtest/sma/{ticker}?fast={params['fast']}&slow={params['slow']}&period={period}"
                elif strategy_key == "rsi":
                    api_path = f"/backtest/rsi/{ticker}?rsi={params['period']}&period={period}"
                else:
                    api_path = f"/backtest/composite/{ticker}?fast={params['fast']}&slow={params['slow']}&rsi={params['rsi']}&period={period}"

                response = None
                for base_url, label in [(API_BASE, "Render"), (FALLBACK_API_BASE, "Local")]:
                    try:
                        response = requests.get(f"{base_url}{api_path}", timeout=30)
                        if response.status_code == 200:
                            st.info(f"✅ Used {label} API")
                            break
                    except:
                        continue

                if response and response.status_code == 200:
                    data = response.json()
                    st.success(f"Simulation Complete: {data['strategy']}")
                    render_metrics(data)
                    render_charts(data, strategy_choice)
                else:
                    st.error("🚨 System Error: All APIs failed.")
            except Exception as e:
                st.error(f"🚨 Unexpected Error: {str(e)}")

    st.markdown('<div style="margin-top: 4rem; border-top: 1px solid var(--border-color); padding-top: 2rem;"></div>', unsafe_allow_html=True)
    render_chat()
    st.markdown('<div class="footer"><p>Algo Trading · Quantitative Backtesting Engine</p></div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
