# Don't forget, if you find this useful please send ETH donations to: 0xDB63E1e60e644cE55563fB62f9F2Fc97B751bc49

# modules

# dash-related libraries
import dash

from dash.dependencies import Output, Event
from math import log10, floor
from datetime import datetime
from random import randint
import dash_core_components as dcc
import dash_html_components as html

# non-dash-related libraries
import plotly.graph_objs as go
import pandas as pd
import gdax
import numpy as np

# modules added by contributors
import time
import threading
from queue import Queue

# creating variables to reduce hard-coding later on / facilitate later paramterization
serverPort=8050
SYMBOLS = {"USD": "$", "BTC": "₿", "EUR": "€", "GBP": "£"}
TICKERS = ("ETH-USD", "ETH-BTC", "BTC-USD", "LTC-USD", "LTC-BTC", "ETH-EUR", "BTC-EUR", "LTC-EUR")
GRAPH_IDS = ['live-graph-' + ticker.lower().replace('-', '') for ticker in TICKERS]
TBL_PRICE = 'price'
TBL_VOLUME = 'volume'
tables = {}
shape_bid = {}
shape_ask = {}
timeStamps = {}  # For storing timestamp of Data Refresh
sendCache = {}


# creates a cache to speed up load time and facilitate refreshes
def get_data_cache(ticker):
    return tables[ticker]


def get_All_data():
    return tables


def getSendCache():
    return sendCache


public_client = gdax.PublicClient()  # defines public client for all functions; taken from GDAX API


def get_data(ticker, range=0.05, maxSize=32, minVolumePerc=0.01):
    # function to get data from GDAX to be referenced in our call-back later
    # ticker a string to particular Ticker (e.g. ETH-USD)
    # range is the deviation visible from current price
    # maxSize is a parameter to limit the maximum size of the bubbles in the viz
    # minVolumePerc is used to set the minimum volume needed for a price-point to be included in the viz

    global tables, timeStamps, shape_bid, shape_ask
    ob_points = 30  # the Amount of Points (1 time for buy, 1 time for sell) for Order Book Graphic
    # Determine what currencies we're working with to make the tool tip more dynamic.
    currency = ticker.split("-")[0]
    base_currency = ticker.split("-")[1]
    symbol = SYMBOLS.get(base_currency.upper(), "")

    # pulls in the order book data from GDAX; split orders by ask vs. bid
    order_book = public_client.get_product_order_book(ticker, level=3)
    ask_tbl = pd.DataFrame(data=order_book['asks'], columns=[TBL_PRICE, TBL_VOLUME, 'address'])
    bid_tbl = pd.DataFrame(data=order_book['bids'], columns=[TBL_PRICE, TBL_VOLUME, 'address'])

    # building subsetted table for ask data only (sell-side)
    ask_tbl[TBL_PRICE] = pd.to_numeric(ask_tbl[TBL_PRICE])
    ask_tbl[TBL_VOLUME] = pd.to_numeric(ask_tbl[TBL_VOLUME])
    first_ask = float(ask_tbl.iloc[1, 0])
    perc_above_first_ask = ((1.0 + range) * first_ask)
    # building subsetted table for bid data only (buy-side)
    bid_tbl[TBL_PRICE] = pd.to_numeric(bid_tbl[TBL_PRICE])
    bid_tbl[TBL_VOLUME] = pd.to_numeric(bid_tbl[TBL_VOLUME])
    first_bid = float(bid_tbl.iloc[1, 0])
    perc_above_first_bid = ((1.0 - range) * first_bid)

    # limits the size of the table so that we only look at orders 5% above and under market price
    ask_tbl = ask_tbl[(ask_tbl[TBL_PRICE] <= perc_above_first_ask)]
    dif_ask = perc_above_first_ask - first_ask
    # limits the size of the table so that we only look at orders 5% above and under market price
    bid_tbl = bid_tbl[(bid_tbl[TBL_PRICE] >= perc_above_first_bid)]
    dif_bid = first_bid - perc_above_first_bid

    # explanatory comment here to come
    ob_step = dif_ask / ob_points
    ob_ask = pd.DataFrame(columns=[TBL_PRICE, TBL_VOLUME, 'address'])
    # explanatory comment here to come (similar to line 85 comment)
    ob_step = dif_bid / ob_points
    ob_bid = pd.DataFrame(columns=[TBL_PRICE, 'volume', 'address'])

    # Following is creating a new tbl 'ob_bid' which contains the summed volume and adress-count from current price to target price
    i = 1
    while i < ob_points:
        current_border = first_ask + (i * ob_step)
        current_volume = ask_tbl.loc[
            (ask_tbl[TBL_PRICE] >= first_ask) & (ask_tbl[TBL_PRICE] < current_border), TBL_VOLUME].sum()
        current_adresses = ask_tbl.loc[
            (ask_tbl[TBL_PRICE] >= first_ask) & (ask_tbl[TBL_PRICE] < current_border), 'address'].sum()
        ob_ask.loc[i - 1] = [current_border, current_volume, current_adresses]
        i += 1
    # Following is creating a new tbl 'ob_bid' wich contains the summed volume and adresses from current price to target price
    i = 1
    while i < ob_points:
        current_border = first_bid - (i * ob_step)
        current_volume = bid_tbl.loc[
            (bid_tbl[TBL_PRICE] <= first_bid) & (bid_tbl[TBL_PRICE] > current_border), TBL_VOLUME].sum()
        current_adresses = bid_tbl.loc[
            (bid_tbl[TBL_PRICE] <= first_bid) & (bid_tbl[TBL_PRICE] > current_border), 'address'].sum()
        ob_bid.loc[i - 1] = [current_border, current_volume, current_adresses]
        i += 1

    # flip the bid table so that the merged full_tbl is in logical order
    bid_tbl = bid_tbl.iloc[::-1]

    # append the buy and sell side tables to create one cohesive table
    fulltbl = bid_tbl.append(ask_tbl)
    minVolume = fulltbl[TBL_VOLUME].sum() * minVolumePerc
    # limit our view to only orders greater than or equal to the minVolume size
    fulltbl = fulltbl[(fulltbl[TBL_VOLUME] >= minVolume)]
    # takes the square root of the volume (to be used later on for the purpose of sizing the order bubbles)
    fulltbl['sqrt'] = np.sqrt(fulltbl[TBL_VOLUME])
    # transforms the table for a final time to craft the data view we need for analysis
    final_tbl = fulltbl.groupby([TBL_PRICE])[[TBL_VOLUME]].sum()


    final_tbl['n_unique_orders'] = fulltbl.groupby(TBL_PRICE).address.nunique().astype(float)
    final_tbl = final_tbl[(final_tbl['n_unique_orders'] <= 20.0)]
    final_tbl[TBL_PRICE] = final_tbl.index
    final_tbl[TBL_PRICE] = final_tbl[TBL_PRICE].apply(round_sig, args=(3, 0, 2))
    final_tbl[TBL_VOLUME] = final_tbl[TBL_VOLUME].apply(round_sig, args=(1, 2))
    final_tbl['n_unique_orders'] = final_tbl['n_unique_orders'].apply(round_sig, args=(0,))
    final_tbl['sqrt'] = np.sqrt(final_tbl[TBL_VOLUME])

    # Calculation for Volume grouping
    vol_grp_bid = bid_tbl.groupby([TBL_VOLUME]).agg({TBL_PRICE: [np.min, np.max, 'count'], TBL_VOLUME: np.sum}).rename(
        columns={'amin': 'min_Price', 'amax': 'max_Price', 'sum': TBL_VOLUME})
    vol_grp_bid.columns = vol_grp_bid.columns.droplevel(0)
    vol_grp_bid = vol_grp_bid[
        ((vol_grp_bid[TBL_VOLUME] >= minVolume) & (vol_grp_bid['count'] >= 2.0) & (vol_grp_bid['count'] < 70.0))]
    vol_grp_bid['unique'] = vol_grp_bid.index.get_level_values(TBL_VOLUME)
    vol_grp_bid['unique'] = vol_grp_bid['unique'].apply(round_sig, args=(3,))
    vol_grp_bid['text'] = ("There are " + vol_grp_bid['count'].map(str) + " orders " + vol_grp_bid['unique'].map(str) +
                    " each, from " +symbol + vol_grp_bid['min_Price'].map(str) + " to " + symbol + 
                    vol_grp_bid['max_Price'].map(str) + " resulting in a total of " + currency + vol_grp_bid[TBL_VOLUME].map(str))
    shape_bid[ticker] = vol_grp_bid

    vol_grp_ask = ask_tbl.groupby([TBL_VOLUME]).agg({TBL_PRICE: [np.min, np.max, 'count'], TBL_VOLUME: np.sum}).rename(
        columns={'amin': 'min_Price', 'amax': 'max_Price', 'sum': TBL_VOLUME})
    vol_grp_ask.columns = vol_grp_ask.columns.droplevel(0)
    vol_grp_ask = vol_grp_ask[
        ((vol_grp_ask[TBL_VOLUME] >= minVolume) & (vol_grp_ask['count'] >= 2.0) & (vol_grp_ask['count'] < 70.0))]
    vol_grp_ask['unique'] = vol_grp_ask.index.get_level_values(TBL_VOLUME)
    vol_grp_ask['unique'] = vol_grp_ask['unique'].apply(round_sig, args=(3,))
    vol_grp_ask['text'] = ("There are " + vol_grp_ask['count'].map(str) + " orders " + vol_grp_ask['unique'].map(str) +
                    " each, from " +symbol + vol_grp_ask['min_Price'].map(str) + " to " + symbol + 
                    vol_grp_ask['max_Price'].map(str) + " resulting in a total of " + currency + vol_grp_ask[TBL_VOLUME].map(str))
    shape_ask[ticker] = vol_grp_ask
    # Fixing Bubble Size
    cMaxSize = final_tbl['sqrt'].max()
    # nifty way of ensuring the size of the bubbles is proportional and reasonable
    sizeFactor = maxSize / cMaxSize
    final_tbl['sqrt'] = final_tbl['sqrt'] * sizeFactor

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
    # Buys are green, Sells are Red. Probably WHALES are highlighted by being brighter, detected by unqiue order count.
    marketPrice = final_tbl['market price']
    final_tbl['colorintensity'] = final_tbl['n_unique_orders'].apply(calcColor)
    final_tbl.loc[(final_tbl[TBL_PRICE] > marketPrice), 'color'] = \
        'rgb(' + final_tbl.loc[(final_tbl[TBL_PRICE] > marketPrice), 'colorintensity'].map(str) + ',0,0)'
    final_tbl.loc[(final_tbl[TBL_PRICE] <= marketPrice), 'color'] = \
        'rgb(0,' + final_tbl.loc[(final_tbl[TBL_PRICE] <= marketPrice), 'colorintensity'].map(str) + ',0)'
    timeStamps[ticker] = datetime.now().strftime("%H:%M:%S")
    tables[ticker] = final_tbl
    tables[ticker] = prepare_data(ticker)
    return tables[ticker]


def refreshWorker():
    global sendCache
    # establishes a separate refresh schedule for user vs. server makes app resilient to DDOS attacks / refresh crashes
    while True:
        for ticker in TICKERS:
            time.sleep(1)
            currency = ticker.split("-")[0]
            get_data(ticker)
            sendCache = prepare_send()


# begin building the dash itself
app = dash.Dash()

# simple layout that can be improved with better CSS later, but it does the job for now
static_content_before = [
    html.H2('CRYPTO WHALE WATCHING APP'),
    html.H3('Donations greatly appreciated; will go towards hosting / development'),
    html.P(['ETH Donations Address: 0xDB63E1e60e644cE55563fB62f9F2Fc97B751bc49', html.Br(),
            'BTC Donations Address: 1BtEBzRxymw6NvtCfoGheLuh2E2iS5mPuo', html.Br(),
            'LTC Donations Address: LWaLxgaBveWATqwsYpYfoAqiG2tb2o5awM'
            ]),
    html.H3(html.A('GitHub Link (Click to support us by giving a star; request new features via "issues" tab)',
                   href="https://github.com/pmaji/eth_python_tracker")),
    html.H3(
        'Legend: Bright colored mark = likely WHALE '
        '(high volume price point via 1 unique order, or many identical medium-sized orders in a ladder). '
        'Bubbles get darker as the number of unique orders increases. '
        'Hover over bubbles for more info. Volume (x-axis) on log-scale. '
        'Click "Freeze all" button to halt refresh, '
        'and hide/show buttons to pick which currency pairs to display. '
        'Only displays orders greater than or equal to 1% of the volume of the portion of the order book displayed. '
        'If annotations overlap or bubbles cluster click "Freeze all" and then zoom in on the area of interest.'
        ' See GitHub for further details.'),
    html.A(html.Button('Freeze all'),
           href="javascript:var k = setTimeout(function() {for (var i = k; i > 0; i--){ clearInterval(i)}},1);"),
    html.A(html.Button('Un-freeze all'), href="javascript:location.reload();")
]

static_content_after = dcc.Interval(
    id='main-interval-component',
    interval=2 * 1000  # in milliseconds for the automatic refresh; refreshes every 2 seconds
)
app.layout = html.Div(id='main_container', children=[
    html.Div(static_content_before),
    html.Div(id='graphs_Container'),
    html.Div(static_content_after),
])


def prepare_data(ticker):
    data = get_data_cache(ticker)
    base_currency = ticker.split("-")[1]
    symbol = SYMBOLS.get(base_currency.upper(), "")
    x_min = min([shape_bid[ticker]['volume'].min(), shape_ask[ticker]['volume'].min(), data[TBL_VOLUME].min()])
    x_max = max([shape_bid[ticker]['volume'].max(), shape_ask[ticker]['volume'].max(), data[TBL_VOLUME].max()])
    max_unique = max([shape_bid[ticker]['unique'].max(), shape_ask[ticker]['unique'].max()])
    width_factor = 15 / max_unique
    market_price = data['market price'].iloc[0]
    bid_trace = go.Scatter(
       x=[],y=[],
       text=[],
       mode='markers',hoverinfo='text',
       marker=dict(opacity=0,color='rgb(0,255,0)'))
    ask_trace = go.Scatter(
       x=[],y=[],
       text=[],
       mode='markers',hoverinfo='text',
       marker=dict(opacity=0,color='rgb(255,0,0)'))
    shape_arr = [dict(
        # Line Horizontal
        type='line',
        x0=x_min, y0=market_price,
        x1=x_max, y1=market_price,
        line=dict(color='rgb(0, 0, 0)', width=2, dash='dash')
    )]
    annot_arr = [dict(
        x=log10(x_max), y=market_price, xref='x', yref='y',
        text=str(market_price) + symbol,
        showarrow=True, arrowhead=7, ax=20, ay=0,
        bgcolor='rgb(0,0,255)', font={'color': '#ffffff'}
    )]
    for index, row in shape_bid[ticker].iterrows():
        cWidth = row['unique'] * width_factor
        vol = row[TBL_VOLUME]
        posY = (row['min_Price']+row['max_Price'])/2.0
        if cWidth > 15:
            cWidth = 15
        elif cWidth < 2:
            cWidth = 2
        shape_arr.append(dict(type='line',
                              opacity=0.5,
                              x0=vol, y0=row['min_Price'],
                              x1=vol, y1=row['max_Price'],
                              line=dict(color='rgb(0, 255, 0)', width=cWidth)))
        bid_trace['x'].append(vol)
        bid_trace['y'].append(row['min_Price'])
        bid_trace['text'].append(row['text'])
        bid_trace['text'].append(row['text'])
        bid_trace['x'].append(vol)
        bid_trace['y'].append(posY)
        bid_trace['x'].append(vol)
        bid_trace['y'].append(row['max_Price'])
        bid_trace['text'].append(row['text'])
    for index, row in shape_ask[ticker].iterrows():
        cWidth = row['unique'] * width_factor
        vol = row[TBL_VOLUME]
        posY = (row['min_Price']+row['max_Price'])/2.0
        if cWidth > 15:
            cWidth = 15
        elif cWidth < 2:
            cWidth = 2
        shape_arr.append(dict(type='line',
                              opacity=0.5,
                              x0=vol, y0=row['min_Price'],
                              x1=vol, y1=row['max_Price'],
                              line=dict(color='rgb(255, 0, 0)', width=cWidth)))
        ask_trace['x'].append(vol)
        ask_trace['y'].append(row['min_Price'])
        ask_trace['text'].append(row['text'])
        ask_trace['x'].append(vol)
        ask_trace['y'].append(posY)
        ask_trace['text'].append(row['text'])
        ask_trace['x'].append(vol)
        ask_trace['y'].append(row['max_Price'])
        ask_trace['text'].append(row['text'])
    result = {
        'data': [
            go.Scatter(
                x=data[TBL_VOLUME],
                y=data[TBL_PRICE],
                mode='markers',
                text=data['text'],
                opacity=0.95,
                hoverinfo='text',
                marker={
                    'size': data['sqrt'],
                    'line': {'width': 0.5, 'color': 'white'},
                    'color': data['color']
                },
            ),ask_trace, bid_trace
        ],
        'layout': go.Layout(
            # title automatically updates with refreshed market price
            title=("The present market price of {} is: {}{} at {}".format(ticker, symbol,
                                                                          str(data['market price'].iloc[0]),
                                                                          timeStamps[ticker])),
            xaxis=dict(title='Order Size',type='log',autorange=True),
            yaxis={'title': '{} Price'.format(ticker)},
            hovermode='closest',
            # now code to ensure the sizing is right
            margin=go.Margin(
                l=75,r=75,
                b=50,t=50,
                pad=4),
            paper_bgcolor='#c7c7c7',
            plot_bgcolor='#c7c7c7',
            # adding the horizontal reference line at market price
            shapes=shape_arr,
            annotations=annot_arr,
            showlegend=False
        )
    }
    return result


def prepare_send():
    lCache = []
    cData = get_All_data()
    for ticker in TICKERS:
        graph = 'live-graph-' + ticker.lower().replace('-', '')
        lCache.append(html.Br())
        lCache.append(html.Br())
        lCache.append(html.A(html.Button('Hide/ Show ' + ticker),
                             href='javascript:(function(){if(document.getElementById("' + graph + '").style.display==""){document.getElementById("' + graph + '").style.display="none"}else{document.getElementById("' + graph + '").style.display=""}})()'))
        lCache.append(dcc.Graph(
            id=graph,
            figure=cData[ticker]
        ))
    return lCache


# links up the chart creation to the interval for an auto-refresh
# creates one callback per currency pairing; easy to replicate / add new pairs
@app.callback(Output('graphs_Container', 'children'),
              events=[Event('main-interval-component', 'interval')])
def update_Site_data():
    return getSendCache()


# explanatory comment here to come
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


# explanatory comment here to come
def calcColor(x):
    response = round(400 / x)
    if response > 255:
        response = 255
    elif response < 30:
        response = 30
    return response

def watchdog():
   tWorker = threading.Thread(target=refreshWorker)
   tWorker.daemon = True
   tWorker.start()
   tServer = threading.Thread(target=serverThread)
   tServer.daemon = False
   tServer.start()
   while True:
      time.sleep(1)
      if not tWorker.isAlive():
         print("Watchdog detected dead Worker, restarting")
         tWorker = threading.Thread(target=refreshWorker)
         tWorker.daemon = True
         tWorker.start()
      if not tServer.isAlive():
         print("Watchdog detected dead Server, restarting")
         tServer = threading.Thread(target=serverThread)
         tServer.daemon = False
         tServer.start()

def serverThread():
   app.run_server(host='0.0.0.0',port=serverPort)

if __name__ == '__main__':
    # Initial Load of Data
    for ticker in TICKERS:
        print("Initializing " + ticker)
        time.sleep(1)
        currency = ticker.split("-")[0]
        get_data(ticker)
    watchdog()

