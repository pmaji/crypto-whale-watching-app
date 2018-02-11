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

tables = {}

def get_data_cache(ticker):
    return tables[ticker]

public_client = gdax.PublicClient()  # defines public client for all functions; taken from GDAX

# function to get data from GDAX to be referenced in our call-back later
def get_data(ticker, threshold=1.0):
    # Determine what currencies we're working with to make the tool tip more dynamic.
    currency = ticker.split("-")[0]
    base_currency = ticker.split("-")[1]
    if base_currency.upper() == "USD":
        symbol = "$"
    elif base_currency.upper() == "BTC":
        symbol = "₿"
    elif base_currency.upper() == "EUR":
        symbol = "€"
    elif base_currency.upper() == "GBP":
        symbol = "£"
    else:
        symbol = ""

    order_book = public_client.get_product_order_book(ticker, level=3)
    ask_tbl = pd.DataFrame(data=order_book['asks'], columns=['price', 'volume', 'address'])
    bid_tbl = pd.DataFrame(data=order_book['bids'], columns=['price', 'volume', 'address'])

    # building subsetted table for ask data only
    # sell side (would be Magma)
    ask_tbl['price'] = pd.to_numeric(ask_tbl['price'])
    ask_tbl['volume'] = pd.to_numeric(ask_tbl['volume'])
    first_ask = float(ask_tbl.iloc[1, 0])
    perc_above_first_ask = (1.025 * first_ask)
    ask_tbl = ask_tbl[(ask_tbl['price'] <= perc_above_first_ask)]
    ask_tbl['color'] = 'red'

    # building subsetted table for bid data only
    # buy side (would be Viridis)
    bid_tbl['price'] = pd.to_numeric(bid_tbl['price'])
    bid_tbl['volume'] = pd.to_numeric(bid_tbl['volume'])
    first_bid = float(bid_tbl.iloc[1, 0])
    perc_above_first_bid = (0.975 * first_bid)
    bid_tbl = bid_tbl[(bid_tbl['price'] >= perc_above_first_bid)]
    bid_tbl['color'] = 'green'

    # flip the bid table
    bid_tbl = bid_tbl.iloc[::-1]

    # append the buy and sell side tables to create one cohesive view
    fulltbl = bid_tbl.append(ask_tbl)
    # limit our view to only orders greater than or equal to the threshold defined
    fulltbl = fulltbl[(fulltbl['volume'] >= threshold)]

    # takes the square root of the volume (to be used later on for the purpose of sizing the orders
    fulltbl['sqrt'] = np.sqrt(fulltbl['volume'])

    final_tbl = fulltbl.groupby(['price'])[['volume']].sum()
    final_tbl['n_unique_orders'] = fulltbl.groupby('price').address.nunique().astype(float)
    final_tbl['price'] = final_tbl.index
    final_tbl['sqrt'] = np.sqrt(final_tbl['volume'])
    # making the tooltip
    final_tbl['text'] = ("There are " + final_tbl['volume'].map(str) + " " + currency + " available for " + symbol + final_tbl['price'].map(str) + " being offered by " + final_tbl['n_unique_orders'].map(str) + " " + currency + " addresses")

    # get market price
    mp = public_client.get_product_ticker(product_id=ticker)
    final_tbl['market price'] = mp['price']

    # makes the type float so that the next logical comparison can take place
    final_tbl['market price'] = final_tbl['market price'].astype(float)

    # determine buys / sells relative to last market price
    final_tbl['color'] = np.where(final_tbl['price'] > final_tbl['market price'], 'red', 'green')

    tables[ticker] = final_tbl
    return tables[ticker]

def refreshWorker():
    while True:
        refreshTickers()
        time.sleep(5)

def refreshTickers():
    get_data("ETH-USD")
    get_data("ETH-BTC")
    get_data("BTC-USD")
    get_data("LTC-USD")


# begin building the dash itself
app = dash.Dash()

app.layout = html.Div([
    html.H2('CRYPTO WHALE WATCHING APP (support / donations appreciated)'),
    html.H3('ETH Address: 0xDB63E1e60e644cE55563fB62f9F2Fc97B751bc49'),
    html.H3('BTC Address: 1BtEBzRxymw6NvtCfoGheLuh2E2iS5mPuo'),
    html.H3('GitHub: https://github.com/pmaji/eth_python_tracker'),
    dcc.Graph(
        id='live-graph-ethusd',
    ),
    dcc.Graph(
        id='live-graph-ethbtc',
    ),
    dcc.Graph(
        id='live-graph-btcusd',
    ),
    dcc.Graph(
        id='live-graph-ltcusd',
    ),
    dcc.Interval(
        id='interval-component',
        interval=1 * 2000  # in milliseconds for the automatic refresh
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
                    'color': data['color']  # set color equal to variable
                },

            )
        ],
        'layout': go.Layout(
            # makes it so that title automatically updates with refreshed market price as well
            title=("The present market price of {} is: ${}".format(ticker, str(data['market price'].iloc[0]))),
            xaxis={'title': 'Order Size'},
            yaxis={'title': '{} Price'.format(ticker)},
            hovermode='closest'
        )
    }
    return result

# links up the chart creation to the interval for an auto-refresh
# ETHUSD #
@app.callback(Output('live-graph-ethusd', 'figure'),
              events=[Event('interval-component', 'interval')])
def update_eth_usd():
    return update_data("ETH-USD")


# ETHBTC #
# links up the chart creation to the interval for an auto-refresh

@app.callback(Output('live-graph-ethbtc', 'figure'),
              events=[Event('interval-component', 'interval')])
def update_eth_btc():
    return update_data("ETH-BTC")

# BTCUSD #
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
