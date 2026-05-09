import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

st.title("📈 AI Stock Research Agent")

ticker = st.text_input("Enter Stock Ticker", "AAPL")

# Download data
data = yf.download(ticker, period="6mo")

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
st.write(data.tail())

# Create chart
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=data["Date"],
        y=data["Close"],
        mode="lines",
        name="Close Price"
    )
)

# MA20 line
fig.add_trace(
    go.Scatter(
        x=data["Date"],
        y=data["MA20"],
        mode="lines",
        name="20-Day MA"
    )
)

# MA50 line
fig.add_trace(
    go.Scatter(
        x=data["Date"],
        y=data["MA50"],
        mode="lines",
        name="50-Day MA"
    )
)

fig.update_layout(
    title=f"{ticker} Stock Price",
    xaxis_title="Date",
    yaxis_title="Price",
    template="plotly_dark",
    height=600
)

# Display chart
st.plotly_chart(fig, use_container_width=True)


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

st.plotly_chart(rsi_fig, use_container_width=True)