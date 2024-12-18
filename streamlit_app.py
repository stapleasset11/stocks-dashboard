import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.io as pio
from datetime import datetime
from itertools import islice
from plotly.subplots import make_subplots

#App configuration
st.set_page_config(page_title="Stocks Dashboard", page_icon="💹", layout="wide")
with open("styles.html", "r") as f:
    styles = f.read()

# st.markdown(styles, unsafe_allow_html=True)

pio.templates.default = "plotly_white"

st.title("Stocks Dashboard :tada:")


#load the data
@st.cache_data
def download_data():
    dfs = pd.read_excel("Stock Dashboard.xlsx", sheet_name=None)

    history_dfs = {}
    ticker_df = dfs["ticker"].copy(deep=True)

    for ticker in list(ticker_df["Ticker"]):
        d = dfs[ticker]
        history_dfs[ticker] = d

    return ticker_df, history_dfs

ticker_df, history_dfs = download_data()


#transform_data
@st.cache_data
def transform_data(ticker_df, history_dfs):
    ticker_df["Last Trade time"] = pd.to_datetime(
        ticker_df["Last Trade time"], dayfirst=True
    )

    for c in [
        "Last Price",
        "Previous Day Price",
        "Change",
        "Change Pct",
        "Volume",
        "Volume Avg",
        "Shares",
        "Day High",
        "Day Low",
        "Market Cap",
        "P/E Ratio",
        "EPS",
    ]:
        ticker_df[c] = pd.to_numeric(ticker_df[c], "coerce")

    for ticker in list(ticker_df["Ticker"]):
        history_dfs[ticker]["Date"] = pd.to_datetime(
            history_dfs[ticker]["Date"], dayfirst=True
        )

        for c in ["Open", "High", "Low", "Close", "Volume"]:
            history_dfs[ticker][c] = pd.to_numeric(history_dfs[ticker][c])

    ticker_to_open = [list(history_dfs[t]["Open"]) for t in list(ticker_df["Ticker"])]
    ticker_df["Open"] = ticker_to_open

    return ticker_df, history_dfs

def filter_symbol_widget():
    with st.container():
        left_widget, right_widget, _ = st.columns([1, 1, 3])

    selected_ticker = left_widget.selectbox(
        "📰 Currently Showing", list(history_dfs.keys())
    )
    selected_period = right_widget.selectbox(
        "⌚ Period", ("Week", "Month", "Trimester", "Year"), 2
    )

    return selected_ticker, selected_period


def plot_candlestick(history_df):
    f_candle = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.7, 0.3],
        vertical_spacing=0.1,
    )

    f_candle.add_trace(
        go.Candlestick(
            x=history_df.index,
            open=history_df["Open"],
            high=history_df["High"],
            low=history_df["Low"],
            close=history_df["Close"],
            name="Dollars",
        ),
        row=1,
        col=1,
    )
    f_candle.add_trace(
        go.Bar(x=history_df.index, y=history_df["Volume"], name="Volume Traded"),
        row=2,
        col=1,
    )
    f_candle.update_layout(
        title="Stock Price Trends",
        showlegend=True,
        xaxis_rangeslider_visible=False,
        # xaxis=dict(title="date"),
        yaxis1=dict(title="OHLC"),
        yaxis2=dict(title="Volume"),
        hovermode="x",
    )
    f_candle.update_layout(
        title_font_family="Open Sans",
        title_font_color="#174C4F",
        title_font_size=32,
        font_size=16,
        margin=dict(l=80, r=80, t=100, b=80, pad=0),
        height=500,
    )
    f_candle.update_xaxes(title_text="Date", row=2, col=1)
    f_candle.update_traces(selector=dict(name="Dollars"), showlegend=True)
    return f_candle



@st.fragment
def display_symbol_history(ticker_df, history_dfs):
    selected_ticker, selected_period = filter_symbol_widget()

    history_df = history_dfs[selected_ticker]

    history_df["Date"] = pd.to_datetime(history_df["Date"], dayfirst=True)
    history_df = history_df.set_index("Date")
    mapping_period = {"Week": 7, "Month": 31, "Trimester": 90, "Year": 365}
    today = datetime.today().date()
    history_df = history_df[
        (today - pd.Timedelta(mapping_period[selected_period], unit="d")) : today
    ]

    for c in ["Open", "High", "Low", "Close", "Volume"]:
        history_df[c] = pd.to_numeric(history_df[c])

    left_chart, right_indicator = st.columns([1.5, 1])

    f_candle = plot_candlestick(history_df)

    with left_chart:
        st.html('<span class="column_plotly"></span>')
        st.plotly_chart(f_candle, use_container_width=True)

    with right_indicator:
        st.html('<span class="column_indicator"></span>')
        st.subheader("Period Metrics")
        l, r = st.columns(2)

        with l:
            st.html('<span class="low_indicator"></span>')
            st.metric("Lowest Volume Day Trade", f'{history_df["Volume"].min():,}')
            st.metric("Lowest Close Price", f'$ {history_df["Close"].min():,} ')
        with r:
            st.html('<span class="high_indicator"></span>')
            st.metric("Highest Volume Day Trade", f'{history_df["Volume"].max():,}')
            st.metric("Highest Close Price", f'$ {history_df["Close"].max():,} ')

        with st.container():
            st.html('<span class="bottom_indicator"></span>')
            st.metric("Average Daily Volume", f'{int(history_df["Volume"].mean()):,}')
            st.metric(
                "Current Market Cap",
                "$ {:,} ".format(
                    ticker_df[ticker_df["Ticker"] == selected_ticker][
                        "Market Cap"
                    ].values[0]
                ),
            )



def display_overview(ticker_df):
    def format_currency(val):
        return "$ {:,.2f}".format(val)

    def format_percentage(val):
        return "{:,.2f} %".format(val)

    def format_change(val):
        return "color: red;" if (val < 0) else "color: green;"

    def apply_odd_row_class(row):
        return ["background-color: #FFD700" if row.name % 2 != 0 else "" for _ in row]

    with st.expander("📊 Stocks Preview"):
        styled_dataframe = (
            ticker_df.style.format(
                {
                    "Last Price": format_currency,
                    "Change Pct": format_percentage,
                }
            )
            .apply(apply_odd_row_class, axis=1)
            .map(format_change, subset=["Change Pct"])
        )

        st.dataframe(
            styled_dataframe,
            column_order=[column for column in list(ticker_df.columns)],
            column_config={
                "Open": st.column_config.AreaChartColumn(
                    "Last 12 Months",
                    width="large",
                    help="Open Price for the last 12 Months",
                ),
            },
            hide_index=True,
            height=250,
            use_container_width=True,
        )
display_symbol_history(ticker_df, history_dfs)
display_overview(ticker_df)

st.write(ticker_df)
