import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

st.title("📈 AI Stock Research Agent")
st.markdown("AI-powered stock market research dashboard with technical analysis")

st.sidebar.header("Stock Controls")

ticker = st.sidebar.text_input(
    "Enter Stock Ticker",
    "AAPL"
)

period = st.sidebar.selectbox(
    "Select Time Period",
    ["1mo", "3mo", "6mo", "1y", "5y"],
    index = 2
)

# Download data
data = yf.download(ticker, period=period)

# Fix multi-index issue
if hasattr(data.columns, "levels"):
    data.columns = data.columns.get_level_values(0)

# Reset index
data.reset_index(inplace=True)

# Moving averages
data["MA20"] = data["Close"].rolling(window=20).mean()
data["MA50"] = data["Close"].rolling(window=50).mean()

# RSI Calculation
delta = data["Close"].diff()

gain = delta.where(delta > 0, 0)
loss = -delta.where(delta < 0, 0)

avg_gain = gain.rolling(window = 14).mean()
avg_loss = loss.rolling(window = 14).mean()

rs = avg_gain / avg_loss

data["RSI"] = 100 - (100 / (1 + rs))

# Show data
st.subheader("Stock Data")

latest_close = round(data["Close"].iloc[-1], 2)
highest_price = round(data["High"].max(), 2)
lowest_price = round(data["Low"].min(), 2)
volume = int(data["Volume"].iloc[-1])

col1, col2, col3, col4 = st.columns(4)

col1.metric("Current Price", latest_close)
col2.metric("Highest", highest_price)
col3.metric("Lowest", lowest_price)
col4.metric("Volume", f"{volume:,}")

st.write(data.tail())


fig = go.Figure()

# Candlestick chart
fig.add_trace(
    go.Candlestick(
        x=data["Date"],
        open=data["Open"],
        high=data["High"],
        low=data["Low"],
        close=data["Close"],
        name="Candlestick",
        increasing_line_color="lime",
        decreasing_line_color="tomato"
    )
)

# MA20
fig.add_trace(
    go.Scatter(
        x=data["Date"],
        y=data["MA20"],
        mode="lines",
        name="MA20",
        line=dict(color="orange", width=2)
    )
)

# MA50
fig.add_trace(
    go.Scatter(
        x=data["Date"],
        y=data["MA50"],
        mode="lines",
        name="MA50",
        line=dict(color="cyan", width=2)
    )
)

fig.update_layout(
    title=f"{ticker} Stock Analysis",
    xaxis_title="Date",
    yaxis_title="Price",
    template="plotly_dark",
    height=700
)

st.plotly_chart(fig, width="stretch")

# RSI Chart
rsi_fig = go.Figure()

rsi_fig.add_trace(
    go.Scatter(
        x = data["Date"],
        y = data["RSI"],
        mode = "lines",
        name = "RSI"
    )
)

# Overbought line
rsi_fig.add_hline(y=70)

# Oversold line
rsi_fig.add_hline(y=30)

rsi_fig.update_layout(
    title = "RSI Indicator",
    xaxis_title = "Date",
    yaxis_title = "RSI",
    template = "plotly_dark",
    height = 400
)

st.plotly_chart(rsi_fig, width="stretch")

# AI Stock Analysis
st.subheader("🤖 AI Stock Analysis")

latest_rsi = round(data["RSI"].iloc[-1], 2)
latest_close = round(data["Close"].iloc[-1], 2)
ma20 = round(data["MA20"].iloc[-1], 2)
ma50 = round(data["MA50"].iloc[-1], 2)

prompt = f"""
You are a professional stock market analyst.

Analyze this stock:

Ticker: {ticker}

Current Price: {latest_close}

MA20: {ma20}

MA50: {ma50}

RSI: {latest_rsi}

Give a short professional analysis in simple language.
"""

response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {
            "role": "system",
            "content": "You are an expert financial analyst."
        },
        {
            "role": "user",
            "content": prompt
        }
    ]
)

analysis = response.choices[0].message.content

st.write(analysis)