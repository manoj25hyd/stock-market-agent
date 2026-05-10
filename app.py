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

if "messages" not in st.session_state:
    st.session_state.messages = []

st.markdown("AI-powered stock market research dashboard with technical analysis")

st.sidebar.header("Stock Controls")

stocks = [
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "TSLA",
    "NVDA",
    "META",
    "NFLX",
    "AMD",
    "INTC"
]

ticker = st.sidebar.selectbox(
    "Select Stock",
    stocks
)

period = st.sidebar.selectbox(
    "Select Time Period",
    ["1mo", "3mo", "6mo", "1y", "5y"],
    index = 2
)

# Download data
data = yf.download(ticker, period=period)

stock = yf.Ticker(ticker)

news = stock.news

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

st.subheader("📰 Latest Stock News")

valid_news = []

for article in news:

    title = article.get("title")

    if title:
        valid_news.append(article)

for article in valid_news[:5]:

    title = article.get("title")

    st.markdown(f"### {title}")

    summary = article.get("summary")

    if summary:
        st.write(summary)

    link = article.get("link")

    if link:
        st.markdown(link)

st.subheader("📈 AI News Sentiment")

news_text = ""

for article in news[:5]:

    title = article.get("title", "")

    news_text += title + "\n"

sentiment_prompt = f"""
Analyze the sentiment of these stock market news headlines.

Stock: {ticker}

News Headlines:
{news_text}

Tell whether sentiment is bullish, bearish, or neutral.

Also explain why in simple language.
"""

sentiment_response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {
            "role": "system",
            "content": "You are a financial news analyst."
        },
        {
            "role": "user",
            "content": sentiment_prompt
        }
    ]
)

sentiment_analysis = sentiment_response.choices[0].message.content

st.write(sentiment_analysis)

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

# Chat Section
st.subheader("💬 Chat With AI Stock Assistant")

user_question = st.chat_input(
    "Ask anything about this stock..."
)

# Display previous messages
for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# When user sends message
if user_question:

    # Store user messages
    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_question
        }
    )

    # Display user message
    with st.chat_message("user"):
        st.markdown(user_question)

    chat_prompt = f"""
    You are an expert stock market analyst.

    Stock: {ticker}

    Current Price: {latest_close}

    MA20: {ma20}

    MA50: {ma50}

    RSI: {latest_rsi}

    User Question:
    {user_question}

    Give a professional but beginner-friendly response.
    """

    # Streaming AI response
    stream = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "You are an expert financial advisor."
            },
            {
                "role": "user",
                "content": chat_prompt
            }
        ],
        stream=True
    )

    # Display streaming response
    with st.chat_message("assistant"):

        response_placeholder = st.empty()

        full_response = ""

        for chunk in stream:

            if chunk.choices[0].delta.content is not None:

                full_response += chunk.choices[0].delta.content

                response_placeholder.markdown(full_response + "▌")

        response_placeholder.markdown(full_response)

    # Save response
    ai_response = full_response

    # Store AI response
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": ai_response
        }
    )