import streamlit as st
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Algo Trading API", layout="wide")
st.title("📈 Quantitative Backtesting Engine")
st.markdown("Enterprise UI for the FastAPI Trading Microservice.")

st.sidebar.header("Strategy Configuration")
ticker = st.sidebar.text_input("Stock Ticker (e.g., RELIANCE.NS, AAPL)", value="RELIANCE.NS")

# The Dropdown with all 3 options
strategy_choice = st.sidebar.selectbox(
    "Select Trading Strategy",
    ("SMA Crossover (Trend Following)", "RSI (Mean Reversion)", "Composite (SMA + RSI Filter)")
)

# Dynamic Inputs
if strategy_choice == "SMA Crossover (Trend Following)":
    fast_sma = st.sidebar.slider("Fast Moving Average", 5, 50, 10)
    slow_sma = st.sidebar.slider("Slow Moving Average", 20, 200, 50)
elif strategy_choice == "RSI (Mean Reversion)":
    rsi_period = st.sidebar.slider("RSI Lookback Period", 5, 30, 14)
else:
    fast_sma = st.sidebar.slider("Fast Moving Average", 5, 50, 10)
    slow_sma = st.sidebar.slider("Slow Moving Average", 20, 200, 50)
    rsi_period = st.sidebar.slider("RSI Lookback Period", 5, 30, 14)

if st.sidebar.button("Run Simulation"):
    with st.spinner(f"Running {strategy_choice} for {ticker}..."):
        try:
            # Route to the correct endpoint
            if strategy_choice == "SMA Crossover (Trend Following)":
                api_url = f"https://algo-trading-api-mpd1.onrender.com/backtest/{ticker}?fast={fast_sma}&slow={slow_sma}"
            elif strategy_choice == "RSI (Mean Reversion)":
                api_url = f"https://algo-trading-api-mpd1.onrender.com/backtest/rsi/{ticker}?period={rsi_period}"
            else:
                api_url = f"https://algo-trading-api-mpd1.onrender.com/backtest/composite/{ticker}?fast={fast_sma}&slow={slow_sma}&rsi={rsi_period}"
            
            response = requests.get(api_url)
            
            if response.status_code != 200:
                st.error(f"🚨 System Error {response.status_code}: The API route is broken.")
                st.json(response.json())
            else:
                data = response.json()
                if "error" in data:
                    st.error(f"API Error: {data['error']}")
                else:
                   # ... (inside your existing try/except block) ...
                    data = response.json()
                    if "error" in data:
                        st.error(f"API Error: {data['error']}")
                    else:
                        st.success(f"Simulation Complete: {data['strategy']}")
                        
                        # 1. Display Metrics
                        col1, col2 = st.columns(2)
                        market_return = data['performance']['market_return_percent']
                        strategy_return = data['performance']['strategy_return_percent']
                        
                        col1.metric(label="Market Return (Buy & Hold)", value=f"{market_return}%")
                        col2.metric(label="Strategy Return (Algorithm)", value=f"{strategy_return}%", delta=f"{round(strategy_return - market_return, 2)}% vs Market")
                        
                        # 2. --- NEW CODE: Draw the Charts ---
                        if "chart_data" in data:
                            st.markdown("### Strategy Visualization")
                            cd = data['chart_data']
                            
                            # Create a stacked chart (Top: Price, Bottom: RSI)
                            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                                vertical_spacing=0.05, row_heights=[0.7, 0.3])
                            
                            # Top Chart: Price and Moving Averages
                            fig.add_trace(go.Scatter(x=cd['Date_Str'], y=cd['Close'], name="Stock Price", line=dict(color='gray', width=1)), row=1, col=1)
                            fig.add_trace(go.Scatter(x=cd['Date_Str'], y=cd['Fast_SMA'], name="Fast SMA", line=dict(color='green', width=2)), row=1, col=1)
                            fig.add_trace(go.Scatter(x=cd['Date_Str'], y=cd['Slow_SMA'], name="Slow SMA", line=dict(color='red', width=2)), row=1, col=1)
                            
                            # Bottom Chart: RSI
                            fig.add_trace(go.Scatter(x=cd['Date_Str'], y=cd['RSI'], name="RSI", line=dict(color='purple', width=2)), row=2, col=1)
                            # Add the 70 (Overbought) and 30 (Oversold) Danger Lines
                            fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
                            fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
                            
                            fig.update_layout(height=600, margin=dict(l=0, r=0, t=30, b=0), hovermode="x unified")
                            st.plotly_chart(fig, use_container_width=True)
                
        except requests.exceptions.ConnectionError:
            st.error("🚨 CRITICAL: Cannot connect to the API. Is your Docker container running?")