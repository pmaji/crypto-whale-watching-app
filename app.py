# Don't forget, if you find this useful please send ETH donations to: 0xDB63E1e60e644cE55563fB62f9F2Fc97B751bc49

# modules

# dash-related libraries for app itself
import dash

from dash.dependencies import Output, Event
from math import log10, floor
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
THRESHOLDS = {"ETH": 1.0, "BTC": 0.25, "LTC": 4.0}
TICKERS = ("ETH-USD", "ETH-BTC", "BTC-USD", "LTC-USD")
GRAPH_IDS = ['live-graph-' + ticker.lower().replace('-', '') for ticker in TICKERS]
TBL_PRICE = 'price'
TBL_VOLUME = 'volume'
tables = {}


# creates a cache to speed up load time and facilitate refreshes
def get_data_cache(ticker):
    return tables[ticker]


public_client = gdax.PublicClient()  # defines public client for all functions; taken from GDAX


# function to get data from GDAX to be referenced in our call-back later
# ticker a string to particular Ticker (e.g. ETH-USD)
# threshold is to limit our view to only orders greater than or equal to the threshold size defined
# uniqueBorder is the border at wich orders are marked differently
# range is the deviation visible from current price
def get_data(ticker, threshold=1.0, uniqueBorder=5, range=0.025):
    # Determine what currencies we're working with to make the tool tip more dynamic.
    currency = ticker.split("-")[0]
    base_currency = ticker.split("-")[1]
    symbol = SYMBOLS.get(base_currency.upper(), "")

    # pulls in the order book data from GDAX; split by ask vs bid
    order_book = public_client.get_product_order_book(ticker, level=3)
    ask_tbl = pd.DataFrame(data=order_book['asks'], columns=[TBL_PRICE, TBL_VOLUME, 'address'])
    bid_tbl = pd.DataFrame(data=order_book['bids'], columns=[TBL_PRICE, TBL_VOLUME, 'address'])

    # building subsetted table for ask data only
    # sell side (would be Magma)
    ask_tbl[TBL_PRICE] = pd.to_numeric(ask_tbl[TBL_PRICE])
    ask_tbl[TBL_VOLUME] = pd.to_numeric(ask_tbl[TBL_VOLUME])
    first_ask = float(ask_tbl.iloc[1, 0])
    perc_above_first_ask = ((1.0 + range) * first_ask)
    # limits the size of the table so that we only look at orders 2.5% above and under market price
    ask_tbl = ask_tbl[(ask_tbl[TBL_PRICE] <= perc_above_first_ask)]

    # building subsetted table for bid data only
    # buy side (would be Viridis)
    bid_tbl[TBL_PRICE] = pd.to_numeric(bid_tbl[TBL_PRICE])
    bid_tbl[TBL_VOLUME] = pd.to_numeric(bid_tbl[TBL_VOLUME])
    first_bid = float(bid_tbl.iloc[1, 0])
    perc_above_first_bid = ((1.0 - range) * first_bid)
    # limits the size of the table so that we only look at orders 2.5% above and under market price
    bid_tbl = bid_tbl[(bid_tbl[TBL_PRICE] >= perc_above_first_bid)]

    # flip the bid table so that the merged full_tbl is in logical order
    bid_tbl = bid_tbl.iloc[::-1]
    # append the buy and sell side tables to create one cohesive table
    fulltbl = bid_tbl.append(ask_tbl)
    # limit our view to only orders greater than or equal to the threshold size defined
    fulltbl = fulltbl[(fulltbl[TBL_VOLUME] >= threshold)]
    # takes the square root of the volume (to be used later on for the purpose of sizing the order bubbles)
    fulltbl['sqrt'] = np.sqrt(fulltbl[TBL_VOLUME])

    # transforms the table for a final time to craft the data view we need for analysis
    final_tbl = fulltbl.groupby([TBL_PRICE])[[TBL_VOLUME]].sum()
    final_tbl['n_unique_orders'] = fulltbl.groupby(TBL_PRICE).address.nunique().astype(float)
    final_tbl[TBL_PRICE] = final_tbl.index
    final_tbl[TBL_PRICE] = final_tbl[TBL_PRICE].apply(round_sig, args=(3, 0, 2))
    final_tbl[TBL_VOLUME] = final_tbl[TBL_VOLUME].apply(round_sig, args=(1, 2))
    final_tbl['n_unique_orders'] = final_tbl['n_unique_orders'].apply(round_sig, args=(0,))
    # print(final_tbl)
    final_tbl['sqrt'] = np.sqrt(final_tbl[TBL_VOLUME])
    # making the tooltip column for our charts
    final_tbl['text'] = (
            "There are " + final_tbl[TBL_VOLUME].map(str) + " " + currency + " available for " + symbol + final_tbl[
        TBL_PRICE].map(str) + " being offered by " + final_tbl['n_unique_orders'].map(
        str) + " " + currency + " orders")

    # get market price; done at the end to correct for any latency in the milliseconds it takes to run this code
    mp = public_client.get_product_ticker(product_id=ticker)
    final_tbl['market price'] = mp['price']
    # makes the type float so that the next set of logical comparisons can take place
    final_tbl['market price'] = final_tbl['market price'].astype(float)

    # determine buys / sells relative to last market price; colors price bubbles based on size
    # buys are green (with default uniqueBorder if there are 5 or more unique orders at a price, the color is bright, else dark)
    # sells are red (with default uniqueBorder if there are 5 or more unique orders at a price, the color is bright, else dark)
    # color map can be found at : https://matplotlib.org/examples/color/named_colors.html

    final_tbl.loc[((final_tbl[TBL_PRICE] > final_tbl['market price']) & (
            final_tbl['n_unique_orders'] >= uniqueBorder)), 'color'] = \
        'red'
    final_tbl.loc[
        ((final_tbl[TBL_PRICE] > final_tbl['market price']) & (final_tbl['n_unique_orders'] < uniqueBorder)), 'color'] = \
        'darkred'
    final_tbl.loc[((final_tbl[TBL_PRICE] <= final_tbl['market price']) & (
            final_tbl['n_unique_orders'] >= uniqueBorder)), 'color'] = \
        'lime'
    final_tbl.loc[((final_tbl[TBL_PRICE] <= final_tbl['market price']) & (
            final_tbl['n_unique_orders'] < uniqueBorder)), 'color'] = \
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
        currency = ticker.split("-")[0]
        thresh = THRESHOLDS.get(currency.upper(), 1.0)
        get_data(ticker, thresh)


# begin building the dash itself
app = dash.Dash()

# simple layout that can be improved with better CSS later, but it does the job for now

div_container = [
    html.H2('CRYPTO WHALE WATCHING APP'),
    html.H3('Donations greatly appreciated; will go towards hosting / development'),
    html.P(['ETH Donations Address: 0xDB63E1e60e644cE55563fB62f9F2Fc97B751bc49', html.Br(),
            'BTC Donations Address: 1BtEBzRxymw6NvtCfoGheLuh2E2iS5mPuo', html.Br(),
            'LTC Donations Address: LWaLxgaBveWATqwsYpYfoAqiG2tb2o5awM'
            ]),
    html.H3(html.A('GitHub Link (Click to support us by giving a star or request new features via "issues" tab)', href="https://github.com/pmaji/eth_python_tracker")),
    html.H3(
        'Legend: Bright colored mark = 5 or more distinct orders at a price-point. Hover over bubbles for more info. Click "Freeze all" button to halt refresh.'),
    html.A(html.Button('Freeze all'),
           href="javascript:var k = setTimeout(function() {for (var i = k; i > 0; i--){ clearInterval(i)}},1);"),
    html.A(html.Button('Un-freeze all'), href="javascript:location.reload();"),
    # This line is for colorblind mode: 1. setInterval function, 2. Loop through all bubbles, 3. Get RGB
    # 4. If Green=0 next bubble, 5. Blue=Green 6. Green = 0, 7. save new color code
    html.A(html.Button('Colorblind mode'), href='javascript:setInterval(function(){var elems=document.getElementsByClassName("point");var amount=elems.length; var x=0;while (x<amount){var nElement=elems[x].style.fill;var rgb=nElement.split("(")[1].split(")")[0].split(",");if(parseInt(rgb[1])!=0){rgb[2]=rgb[1];rgb[1]=" 0";rgb="rgb("+rgb[0]+","+rgb[1]+","+rgb[2]+")";document.getElementsByClassName("point")[x].style.fill=rgb;}x++;}},50);')
]
for graphId in GRAPH_IDS:
    div_container.append(dcc.Graph(id=graphId))

div_container.append(dcc.Interval(
    id='interval-component',
    interval=4 * 1000  # in milliseconds for the automatic refresh; refreshes every 4 seconds
))
app.layout = html.Div(div_container)


def update_data(ticker):
    data = get_data_cache(ticker)
    base_currency = ticker.split("-")[1]
    symbol = SYMBOLS.get(base_currency.upper(), "")
    result = {
        'data': [
            go.Scatter(
                x=data[TBL_VOLUME],
                y=data[TBL_PRICE],
                mode='markers',
                text=data['text'],
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
            title=("The present market price of {} is: {}{}".format(ticker, symbol, str(data['market price'].iloc[0]))),
            xaxis={'title': 'Order Size'},
            yaxis={'title': '{} Price'.format(ticker)},
            hovermode='closest'
        )
    }
    return result


# links up the chart creation to the interval for an auto-refresh
# creates one callback per currency pairing; easy to replicate / add new pairs

# Function generator
def create_cb_func(pGraph):
    def cb():
        return update_data(pGraph)

    return cb


# Loop through graphs and append callback
for ticker in TICKERS:
    graph = 'live-graph-' + ticker.lower().replace('-', '')
    app.callback(Output(graph, 'figure'),
                 events=[Event('interval-component', 'interval')])(create_cb_func(ticker))


def round_sig(x, sig=3, overwrite=0, minimum=0):
    if (x == 0):
        return 0.0
    elif overwrite > 0:
        return round(x, overwrite)
    else:
        digits = -int(floor(log10(abs(x)))) + (sig - 1)
        if digits <= minimum:
            return round(x, minimum)
        else:
            return round(x, digits)


if __name__ == '__main__':
    refreshTickers()
    t = threading.Thread(target=refreshWorker)
    t.daemon = True
    t.start()

app.run_server(host='0.0.0.0')
