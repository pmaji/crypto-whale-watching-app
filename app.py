# Don't forget, if you find this useful please send ETH donations to: 0xDB63E1e60e644cE55563fB62f9F2Fc97B751bc49

# modules

# dash-related libraries for app itself
import dash
from dash.dependencies import Output, Event
import dash_core_components as dcc
import dash_html_components as html

# non-dash-related libraries
import plotly.graph_objs as go
import pandas as pd
import gdax
import numpy as np

import time
import threading
from queue import Queue

SYMBOLS = {"USD": "$", "BTC": "₿", "EUR": "€", "GBP": "£"}
TICKERS = ("ETH-USD", "ETH-BTC", "BTC-USD", "LTC-USD")
GRAPH_IDS = ['live-graph-' + ticker.lower().replace('-', '') for ticker in TICKERS]
tables = {}

# creates a cache to speed up load time and facilitate refreshes
def get_data_cache(ticker):
    return tables[ticker]

public_client = gdax.PublicClient()  # defines public client for all functions; taken from GDAX

# function to get data from GDAX to be referenced in our call-back later
def get_data(ticker, threshold=1.0, uniqueBorder=5):

    # Determine what currencies we're working with to make the tool tip more dynamic.
    currency = ticker.split("-")[0]
    base_currency = ticker.split("-")[1]
    symbol = SYMBOLS.get(base_currency.upper(), "")

    # pulls in the order book data from GDAX; split by ask vs bid
    order_book = public_client.get_product_order_book(ticker, level=3)
    ask_tbl = pd.DataFrame(data=order_book['asks'], columns=['price', 'volume', 'address'])
    bid_tbl = pd.DataFrame(data=order_book['bids'], columns=['price', 'volume', 'address'])

    # building subsetted table for ask data only
    # sell side (would be Magma)
    ask_tbl['price'] = pd.to_numeric(ask_tbl['price'])
    ask_tbl['volume'] = pd.to_numeric(ask_tbl['volume'])
    first_ask = float(ask_tbl.iloc[1, 0])
    perc_above_first_ask = (1.025 * first_ask)
    # limits the size of the table so that we only look at orders 2.5% above and under market price
    ask_tbl = ask_tbl[(ask_tbl['price'] <= perc_above_first_ask)]

    # building subsetted table for bid data only
    # buy side (would be Viridis)
    bid_tbl['price'] = pd.to_numeric(bid_tbl['price'])
    bid_tbl['volume'] = pd.to_numeric(bid_tbl['volume'])
    first_bid = float(bid_tbl.iloc[1, 0])
    perc_above_first_bid = (0.975 * first_bid)
    # limits the size of the table so that we only look at orders 2.5% above and under market price
    bid_tbl = bid_tbl[(bid_tbl['price'] >= perc_above_first_bid)]

    # flip the bid table so that the merged full_tbl is in logical order
    bid_tbl = bid_tbl.iloc[::-1]
    # append the buy and sell side tables to create one cohesive table
    fulltbl = bid_tbl.append(ask_tbl)
    # limit our view to only orders greater than or equal to the threshold size defined
    fulltbl = fulltbl[(fulltbl['volume'] >= threshold)]
    # takes the square root of the volume (to be used later on for the purpose of sizing the order bubbles)
    fulltbl['sqrt'] = np.sqrt(fulltbl['volume'])

    # transforms the table for a final time to craft the data view we need for analysis
    final_tbl = fulltbl.groupby(['price'])[['volume']].sum()
    final_tbl['n_unique_orders'] = fulltbl.groupby('price').address.nunique().astype(float)
    final_tbl['price'] = final_tbl.index
    final_tbl['sqrt'] = np.sqrt(final_tbl['volume'])
    # making the tooltip column for our charts
    final_tbl['text'] = ("There are " + final_tbl['volume'].map(str) + " " + currency + " available for " + symbol + final_tbl['price'].map(str) + " being offered by " + final_tbl['n_unique_orders'].map(str) + " " + currency + " orders")

    # get market price; done at the end to correct for any latency in the milliseconds it takes to run this code
    mp = public_client.get_product_ticker(product_id=ticker)
    final_tbl['market price'] = mp['price']
    # makes the type float so that the next set of logical comparisons can take place
    final_tbl['market price'] = final_tbl['market price'].astype(float)

    # determine buys / sells relative to last market price; colors price bubbles based on size
    # buys are green (with default uniqueBorder if there are 5 or more unique orders at a price, the color is bright, else dark)
    # sells are red (with default uniqueBorder if there are 5 or more unique orders at a price, the color is bright, else dark)
    # color map can be found at : https://matplotlib.org/examples/color/named_colors.html

    final_tbl.loc[((final_tbl['price'] > final_tbl['market price']) & (final_tbl['n_unique_orders'] >= uniqueBorder)), 'color'] = \
        'red'
    final_tbl.loc[((final_tbl['price'] > final_tbl['market price']) & (final_tbl['n_unique_orders'] < uniqueBorder)), 'color'] = \
        'darkred'
    final_tbl.loc[((final_tbl['price'] <= final_tbl['market price']) & (final_tbl['n_unique_orders'] >= uniqueBorder)), 'color'] = \
        'lime'
    final_tbl.loc[((final_tbl['price'] <= final_tbl['market price']) & (final_tbl['n_unique_orders'] < uniqueBorder)), 'color'] = \
        'green'

    tables[ticker] = final_tbl
    return tables[ticker]

# establishes a refresh schedule separate from the user's interaction
# these two steps make the app resilient to DDOS attacks / crashes due to too many manual refreshes


def refreshWorker():
    while True:
        refreshTickers()
        time.sleep(5)


def refreshTickers():
    for ticker in TICKERS:
        get_data(ticker)


# begin building the dash itself
app = dash.Dash()

# simple layout that can be improved with better CSS later, but it does the job for now
app.layout = html.Div([
    html.H2('CRYPTO WHALE WATCHING APP (support / donations appreciated)'),
    html.H3('ETH Address: 0xDB63E1e60e644cE55563fB62f9F2Fc97B751bc49' + ' -------------------- '
            'BTC Address: 1BtEBzRxymw6NvtCfoGheLuh2E2iS5mPuo'),
    html.H3('GitHub: https://github.com/pmaji/eth_python_tracker'),
    html.H3('Legend: Bright colored mark = 5 or more distinct orders at a price-point. '
            'Hover over bubbles for more info.'),
    dcc.Graph(id=GRAPH_IDS[0]),
    dcc.Graph(id=GRAPH_IDS[1]),
    dcc.Graph(id=GRAPH_IDS[2]),
    dcc.Graph(id=GRAPH_IDS[3]),
    dcc.Interval(
        id='interval-component',
        interval=1 * 4000  # in milliseconds for the automatic refresh; refreshes every 2 seconds
    )
])


def update_data(ticker, threshold=1.0):
    data = get_data_cache(ticker)
    result = {
        'data': [
            go.Scatter(
                x=data['volume'],
                y=data['price'],
                mode='markers',
                text= data['text'],
                opacity=0.7,
                hoverinfo='text',
                marker={
                    'size': data['sqrt'],
                    'line': {'width': 0.5, 'color': 'white'},
                    'color': data['color']
                },

            )
        ],
        'layout': go.Layout(
            # makes it so that title automatically updates with refreshed market price
            title=("The present market price of {} is: ${}".format(ticker, str(data['market price'].iloc[0]))),
            xaxis={'title': 'Order Size'},
            yaxis={'title': '{} Price'.format(ticker)},
            hovermode='closest'
        )
    }
    return result

# links up the chart creation to the interval for an auto-refresh
# creates one callback per currency pairing; easy to replicate / add new pairs


# ETHUSD #
@app.callback(Output('live-graph-ethusd', 'figure'),
              events=[Event('interval-component', 'interval')])
def update_eth_usd():
    return update_data("ETH-USD")


# ETHBTC #
@app.callback(Output('live-graph-ethbtc', 'figure'),
              events=[Event('interval-component', 'interval')])
def update_eth_btc():
    return update_data("ETH-BTC")


# BTCUSD #
# threshold changed for BTC given higher raw price
@app.callback(Output('live-graph-btcusd', 'figure'),
              events=[Event('interval-component', 'interval')])
def update_btc_usd():
    return update_data("BTC-USD", threshold=0.25)


# LTCUSD #
@app.callback(Output('live-graph-ltcusd', 'figure'),
              events=[Event('interval-component', 'interval')])
def update_ltc_usd():
    return update_data("LTC-USD")


if __name__ == '__main__':
    refreshTickers()
    t = threading.Thread(target=refreshWorker)
    t.daemon = True
    t.start()

app.run_server(host='0.0.0.0')
