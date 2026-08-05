import streamlit as st
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

API_BASE = "http://localhost:8000"

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

    .stSlider > div > div > div > div {
        background: var(--accent-primary) !important;
    }

    .stSlider > div > div > div > div > div {
        background: var(--accent-primary) !important;
        border-color: var(--accent-primary) !important;
    }

    .stSpinner > div {
        border-top-color: var(--accent-primary) !important;
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
</style>
"""

def render_hero():
    st.markdown("""
    <div class="hero-section">
        <div style="position: relative; z-index: 1;">
            <h1 class="hero-title">Quantitative Backtesting Engine</h1>
            <p class="hero-subtitle">Enterprise-grade algorithmic trading simulation platform. Validate strategies against historical data with institutional-quality analytics and visualization.</p>
            <div class="hero-badges">
                <span class="badge accent">⚡ Real-time API</span>
                <span class="badge">📊 3 Strategies</span>
                <span class="badge">🔍 Interactive Charts</span>
                <span class="badge">📈 Performance Metrics</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

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
            value="RELIANCE.NS",
            placeholder="e.g., RELIANCE.NS, AAPL, TSLA",
            help="Enter Yahoo Finance ticker symbol"
        )

        st.markdown('<div class="section-header" style="margin-top: 1.5rem;"><span class="section-title">Strategy Selection</span></div>', unsafe_allow_html=True)

        strategy_options = [
            ("SMA Crossover (Trend Following)", "sma", "Trend-following strategy using dual moving average crossovers"),
            ("RSI (Mean Reversion)", "rsi", "Mean reversion strategy using Relative Strength Index"),
            ("Composite (SMA + RSI Filter)", "composite", "Combined strategy with SMA signals filtered by RSI")
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
            fast_sma = st.slider("Fast Moving Average", 5, 50, 10, help="Short-term SMA period")
            slow_sma = st.slider("Slow Moving Average", 20, 200, 50, help="Long-term SMA period")
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
            rsi_period = st.slider("RSI Lookback Period", 5, 30, 14, help="RSI calculation period")
            params = {"period": rsi_period}
            st.markdown(f"""
            <div class="param-group">
                <div class="param-label">RSI Period <span class="param-value">{rsi_period}</span></div>
            </div>
            """, unsafe_allow_html=True)
        else:
            fast_sma = st.slider("Fast Moving Average", 5, 50, 10, help="Short-term SMA period")
            slow_sma = st.slider("Slow Moving Average", 20, 200, 50, help="Long-term SMA period")
            rsi_period = st.slider("RSI Lookback Period", 5, 30, 14, help="RSI calculation period")
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

    return ticker, strategy_choice, strategy_key, params, run_button

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

    st.markdown('<div class="section-header" style="margin-top: 2rem;"><span class="section-title">Strategy Visualization</span></div>', unsafe_allow_html=True)

    if strategy_choice == "SMA Crossover (Trend Following)":
        fast_sma = cd['Fast_SMA']
        slow_sma = cd['Slow_SMA']

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates, y=close, name="Stock Price",
            line=dict(color='#9CA3AF', width=1.5),
            hovertemplate='%{x}<br>Price: ₹%{y:.2f}<extra></extra>'
        ))
        fig.add_trace(go.Scatter(
            x=dates, y=fast_sma, name="Fast SMA",
            line=dict(color='#10B981', width=2),
            hovertemplate='%{x}<br>Fast SMA: ₹%{y:.2f}<extra></extra>'
        ))
        fig.add_trace(go.Scatter(
            x=dates, y=slow_sma, name="Slow SMA",
            line=dict(color='#EF4444', width=2),
            hovertemplate='%{x}<br>Slow SMA: ₹%{y:.2f}<extra></extra>'
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
                title="Price (₹)",
                tickprefix="₹"
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
            hovertemplate='%{x}<br>Price: ₹%{y:.2f}<extra></extra>'
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
                title="Price (₹)",
                tickprefix="₹"
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
            hovertemplate='%{x}<br>Price: ₹%{y:.2f}<extra></extra>'
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=dates, y=fast_sma, name="Fast SMA",
            line=dict(color='#10B981', width=2),
            hovertemplate='%{x}<br>Fast SMA: ₹%{y:.2f}<extra></extra>'
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=dates, y=slow_sma, name="Slow SMA",
            line=dict(color='#EF4444', width=2),
            hovertemplate='%{x}<br>Slow SMA: ₹%{y:.2f}<extra></extra>'
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
                title="Price (₹)",
                tickprefix="₹"
            ),
            yaxis2=dict(
                gridcolor='#1F2937',
                zerolinecolor='#1F2937',
                range=[0, 100],
                title="RSI"
            )
        )

        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

def main():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    render_hero()

    ticker, strategy_choice, strategy_key, params, run_button = render_sidebar()

    if run_button:
        with st.spinner(""):
            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, (pct, msg) in enumerate([
                (10, "Connecting to API..."),
                (30, "Fetching market data..."),
                (50, "Running backtest engine..."),
                (70, "Calculating performance metrics..."),
                (90, "Generating visualizations..."),
                (100, "Complete!")
            ]):
                progress_bar.progress(pct)
                status_text.markdown(f'<div style="color: var(--text-secondary); font-size: 0.875rem;">{msg}</div>', unsafe_allow_html=True)
                time.sleep(0.15)

            progress_bar.empty()
            status_text.empty()

            try:
                if strategy_key == "sma":
                    api_url = f"{API_BASE}/backtest/{ticker}?fast={params['fast']}&slow={params['slow']}"
                elif strategy_key == "rsi":
                    api_url = f"{API_BASE}/backtest/rsi/{ticker}?period={params['period']}"
                else:
                    api_url = f"{API_BASE}/backtest/composite/{ticker}?fast={params['fast']}&slow={params['slow']}&rsi={params['rsi']}"

                response = requests.get(api_url, timeout=30)

                if response.status_code != 200:
                    st.error(f"🚨 System Error {response.status_code}: The API route is broken.")
                    st.json(response.json())
                else:
                    data = response.json()
                    if "error" in data:
                        st.error(f"API Error: {data['error']}")
                    else:
                        st.success(f"Simulation Complete: {data['strategy']}")

                        render_metrics(data)
                        render_charts(data, strategy_choice)

            except requests.exceptions.Timeout:
                st.error("🚨 Request Timeout: The API took too long to respond. Please try again.")
            except requests.exceptions.ConnectionError:
                st.error("🚨 CRITICAL: Cannot connect to the API. Is your Docker container running?")
            except Exception as e:
                st.error(f"🚨 Unexpected Error: {str(e)}")

    else:
        st.markdown("""
        <div style="text-align: center; padding: 4rem 2rem; color: var(--text-secondary);">
            <div style="font-size: 4rem; margin-bottom: 1rem; opacity: 0.3;">📊</div>
            <h2 style="color: var(--text-primary); margin-bottom: 0.5rem;">Ready to Backtest</h2>
            <p style="max-width: 400px; margin: 0 auto; line-height: 1.6;">Configure your strategy parameters in the sidebar and click <strong>Run Simulation</strong> to see professional-grade backtesting results.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="footer">
        <p>Algo Trading API · Quantitative Backtesting Engine </p>
        <p style="margin-top: 0.5rem; font-size: 0.75rem;">⚠️ This is a simulation tool for educational purposes. Past performance does not guarantee future results.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()