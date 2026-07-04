import streamlit as st
import requests

# Set up the page layout
st.set_page_config(page_title="Algo Trading API", layout="wide")
st.title("📈 Quantitative Backtesting Dashboard")
st.markdown("A lightweight UI for our FastAPI Trading Engine.")

# Sidebar for user inputs
st.sidebar.header("Strategy Parameters")
ticker = st.sidebar.text_input("Stock Ticker (e.g., RELIANCE.NS, TCS.NS)", value="RELIANCE.NS")
fast_sma = st.sidebar.slider("Fast Moving Average", min_value=5, max_value=50, value=10)
slow_sma = st.sidebar.slider("Slow Moving Average", min_value=20, max_value=200, value=50)

# The Execution Button
if st.sidebar.button("Run Simulation"):
    with st.spinner(f"Connecting to API and running backtest for {ticker}..."):
        try:
            # 1. Call your Dockerized API
            api_url = f"http://localhost:8000/backtest/{ticker}?fast={fast_sma}&slow={slow_sma}"
            response = requests.get(api_url)
            data = response.json()

            # 2. Handle Errors safely
            if "error" in data:
                st.error(f"API Error: {data['error']}")
            else:
                st.success(f"Simulation Complete: {data['strategy']}")
                
                # 3. Display the core metrics in clean cards
                col1, col2 = st.columns(2)
                market_return = data['performance']['market_return_percent']
                strategy_return = data['performance']['strategy_return_percent']
                
                col1.metric(label="Market Return (Buy & Hold)", value=f"{market_return}%")
                col2.metric(label="Strategy Return (Algorithm)", value=f"{strategy_return}%", delta=f"{round(strategy_return - market_return, 2)}% vs Market")
                
        except requests.exceptions.ConnectionError:
            st.error("🚨 CRITICAL: Cannot connect to the API. Is your Docker container running on port 8000?")