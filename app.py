# modules
# dash-related libraries
import dash
from dash.dependencies import Output, Event
from math import log10, floor, isnan
from datetime import datetime
from random import randint
import dash_core_components as dcc
import dash_html_components as html
import colorama
import sys
import getopt

# non-dash-related libraries
import plotly.graph_objs as go
import pandas as pd
import cbpro
import numpy as np

# modules added by contributors
import time
import threading
from queue import Queue

# custom library
from gdax_book import GDaxBook

colorama.init()
# creating variables to facilitate later parameterization
debugLevel = 3
debugLevels = ["Special Debug","Debug","Info","Warnings","Errors"]
debugColors = ['\033[34m','\033[90m','\033[32m','\033[33;1m','\033[31m']
serverPort = 8050
clientRefresh = 1
desiredPairRefresh = 10000  # (in ms) The lower it is, the better is it regarding speed of at least some pairs, the higher it is, the less cpu load it takes.
js_extern = "https://cdn.rawgit.com/pmaji/crypto-whale-watching-app/master/main.js"
noDouble = True  # if activatet each order is in case of beeing part of a ladder just shown once (just as a bubble, not as a ladder)
SYMBOLS = {"USD": "$", "BTC": "₿", "EUR": "€", "GBP": "£"} # used for the tooltip
SIGNIFICANT = {"USD": 2, "BTC": 5, "EUR": 2, "GBP": 2} # used for rounding
TBL_PRICE = 'price'
TBL_VOLUME = 'volume'
tables = {}
depth_ask = {}
depth_bid = {}
marketPrice = {}
prepared = {}
shape_bid = {}
shape_ask = {}
timeStampsGet = {}  # For storing timestamp of Data Refresh
timeStamps = {}  # For storing timestamp from calc start at calc end
sendCache = {}
first_prepare = True
first_pull = True
overallNewData = False


class Exchange:
    ticker = []
    client = ""

    def __init__(self, pName, pTicker, pStamp):
        self.name = pName
        self.ticker.extend(pTicker)
        self.millis = pStamp


class Pair:
    # Class to store a pair with its respective threads
    def __init__(self, pExchange, pTicker):
        self.ob_Inst = {}
        self.threadWebsocket = {}
        self.threadPrepare = {}
        self.threadRecalc = {}
        self.Dataprepared = False
        self.webSocketKill = 1
        self.lastStamp = 0
        self.usedStamp = 0
        self.newData = False
        self.name = pExchange + " " + pTicker
        self.ticker = pTicker
        self.lastUpdate = "0"
        self.exchange = pExchange
        self.prepare = False
        self.websocket = False
        self.combined = pExchange + pTicker


PAIRS = []  # Array containing all pairs
E_GDAX = Exchange("GDAX", [
                           "ETH-USD", "ETH-EUR", "ETH-BTC",
                           "BTC-USD", "BTC-EUR", "BTC-GBP",
                           "LTC-USD", "LTC-EUR", "LTC-BTC",
                           "BCH-USD", "BCH-EUR", "BCH-BTC"], 0)
for ticker in E_GDAX.ticker:
    cObj = Pair(E_GDAX.name, ticker)
    PAIRS.append(cObj)


# creates a cache to speed up load time and facilitate refreshes


def get_data_cache(ticker):
    return tables[ticker]


def get_All_data():
    return prepared


def getSendCache():
    return sendCache


def calc_data(pair, range=0.05, maxSize=32, minVolumePerc=0.01, ob_points=60):
    global tables, timeStamps, shape_bid, shape_ask, E_GDAX, marketPrice, timeStampsGet
    # function to get data from GDAX to be referenced in our call-back later
    # ticker a string to particular Ticker (e.g. ETH-USD)
    # range is the deviation visible from current price
    # maxSize is a parameter to limit the maximum size of the bubbles in the viz
    # minVolumePerc is used to set the minimum volume needed for a price-point to be included in the viz
    ticker = pair.ticker
    exchange = pair.exchange
    combined = exchange + ticker
    if pair.exchange == E_GDAX.name:
        # order_book = gdax.PublicClient().get_product_order_book(ticker, level=3)
        order_book = pair.ob_Inst.get_current_book()
        pair.usedStamp = getStamp()
        ask_tbl = pd.DataFrame(data=order_book['asks'], columns=[
            TBL_PRICE, TBL_VOLUME, 'address'])
        bid_tbl = pd.DataFrame(data=order_book['bids'], columns=[
            TBL_PRICE, TBL_VOLUME, 'address'])

    timeStampsGet[pair.combined] = datetime.now().strftime("%H:%M:%S")  # save timestamp at data pull time

    # Determine what currencies we're working with to make the tool tip more dynamic.
    currency = ticker.split("-")[0]
    base_currency = ticker.split("-")[1]
    sig_use = SIGNIFICANT.get(base_currency.upper(), 2)
    symbol = SYMBOLS.get(base_currency.upper(), "")
    try:
        first_ask = float(ask_tbl.iloc[1, 0])
    except (IndexError):
        log(4,"Empty data for " + combined + " Will wait 3s")
        time.sleep(3)
        return False

    # prepare Price
    ask_tbl[TBL_PRICE] = pd.to_numeric(ask_tbl[TBL_PRICE])
    bid_tbl[TBL_PRICE] = pd.to_numeric(bid_tbl[TBL_PRICE])

    # data from websocket are not sorted yet
    ask_tbl = ask_tbl.sort_values(by=TBL_PRICE, ascending=True)
    bid_tbl = bid_tbl.sort_values(by=TBL_PRICE, ascending=False)

    # get first on each side
    first_ask = float(ask_tbl.iloc[1, 0])

    # get perc for ask/ bid
    perc_above_first_ask = ((1.0 + range) * first_ask)
    perc_above_first_bid = ((1.0 - range) * first_ask)

    # limits the size of the table so that we only look at orders 5% above and under market price
    ask_tbl = ask_tbl[(ask_tbl[TBL_PRICE] <= perc_above_first_ask)]
    bid_tbl = bid_tbl[(bid_tbl[TBL_PRICE] >= perc_above_first_bid)]

    # changing this position after first filter makes calc faster
    bid_tbl[TBL_VOLUME] = pd.to_numeric(bid_tbl[TBL_VOLUME])
    ask_tbl[TBL_VOLUME] = pd.to_numeric(ask_tbl[TBL_VOLUME])

    # prepare everything for depchart
    ob_step = (perc_above_first_ask - first_ask) / ob_points
    ob_ask = pd.DataFrame(columns=[TBL_PRICE, TBL_VOLUME, 'address', 'text'])
    ob_bid = pd.DataFrame(columns=[TBL_PRICE, TBL_VOLUME, 'address', 'text'])

    # Following is creating a new tbl 'ob_bid' which contains the summed volume and adress-count from current price to target price
    i = 1
    last_ask = first_ask
    last_bid = first_ask
    current_ask_volume = 0
    current_bid_volume = 0
    current_ask_adresses = 0
    current_bid_adresses = 0
    while i < ob_points:
        # Get Borders for ask/ bid
        current_ask_border = first_ask + (i * ob_step)
        current_bid_border = first_ask - (i * ob_step)

        # Get Volume
        current_ask_volume += ask_tbl.loc[
            (ask_tbl[TBL_PRICE] >= last_ask) & (ask_tbl[TBL_PRICE] < current_ask_border), TBL_VOLUME].sum()
        current_bid_volume += bid_tbl.loc[
            (bid_tbl[TBL_PRICE] <= last_bid) & (bid_tbl[TBL_PRICE] > current_bid_border), TBL_VOLUME].sum()

        # Get Adresses
        current_ask_adresses += ask_tbl.loc[
            (ask_tbl[TBL_PRICE] >= last_ask) & (ask_tbl[TBL_PRICE] < current_ask_border), 'address'].count()
        current_bid_adresses += bid_tbl.loc[
            (bid_tbl[TBL_PRICE] <= last_bid) & (bid_tbl[TBL_PRICE] > current_bid_border), 'address'].count()

        # Prepare Text
        ask_text = (str(round_sig(current_ask_volume, 3, 0, sig_use)) + currency + " (from " + str(current_ask_adresses) +
                     " orders) up to " + str(round_sig(current_ask_border, 3, 0, sig_use)) + symbol)
        bid_text = (str(round_sig(current_bid_volume, 3, 0, sig_use)) + currency + " (from " + str(current_bid_adresses) +
                     " orders) down to " + str(round_sig(current_bid_border, 3, 0, sig_use)) + symbol)

        # Save Data
        ob_ask.loc[i - 1] = [current_ask_border, current_ask_volume, current_ask_adresses, ask_text]
        ob_bid.loc[i - 1] = [current_bid_border, current_bid_volume, current_bid_adresses, bid_text]
        i += 1
        last_ask = current_ask_border
        last_bid = current_bid_border

    # Get Market Price
    try:
        mp = round_sig((ask_tbl[TBL_PRICE].iloc[0] +
                        bid_tbl[TBL_PRICE].iloc[0]) / 2.0, 3, 0, sig_use)
    except (IndexError):
        log(4,"Empty data for " + combined + " Will wait 3s")
        time.sleep(3)
        return False
    bid_tbl = bid_tbl.iloc[::-1]  # flip the bid table so that the merged full_tbl is in logical order

    fulltbl = bid_tbl.append(ask_tbl)  # append the buy and sell side tables to create one cohesive table

    minVolume = fulltbl[TBL_VOLUME].sum() * minVolumePerc  # Calc minimum Volume for filtering
    fulltbl = fulltbl[
        (fulltbl[TBL_VOLUME] >= minVolume)]  # limit our view to only orders greater than or equal to the minVolume size

    fulltbl['sqrt'] = np.sqrt(fulltbl[
                                  TBL_VOLUME])  # takes the square root of the volume (to be used later on for the purpose of sizing the order bubbles)

    final_tbl = fulltbl.groupby([TBL_PRICE])[
        [TBL_VOLUME]].sum()  # transforms the table for a final time to craft the data view we need for analysis

    final_tbl['n_unique_orders'] = fulltbl.groupby(
        TBL_PRICE).address.nunique().astype(int)

    final_tbl = final_tbl[(final_tbl['n_unique_orders'] <= 20.0)]
    final_tbl[TBL_PRICE] = final_tbl.index
    final_tbl[TBL_PRICE] = final_tbl[TBL_PRICE].apply(round_sig, args=(3, 0, sig_use))
    final_tbl[TBL_VOLUME] = final_tbl[TBL_VOLUME].apply(round_sig, args=(1, 2))
    final_tbl['n_unique_orders'] = final_tbl['n_unique_orders'].apply(round_sig, args=(0,))
    final_tbl['sqrt'] = np.sqrt(final_tbl[TBL_VOLUME])
    final_tbl['total_price'] = (((final_tbl['volume'] * final_tbl['price']).round(2)).apply(lambda x: "{:,}".format(x)))

    # Following lines fix double drawing of orders in case it´s a ladder but bigger than 1%
    if noDouble:
        bid_tbl = bid_tbl[(bid_tbl['volume'] < minVolume)]
        ask_tbl = ask_tbl[(ask_tbl['volume'] < minVolume)]

    bid_tbl['total_price'] = bid_tbl['volume'] * bid_tbl['price']
    ask_tbl['total_price'] = ask_tbl['volume'] * ask_tbl['price']

    # Get Dataset for Volume Grouping
    vol_grp_bid = bid_tbl.groupby([TBL_VOLUME]).agg(
        {TBL_PRICE: [np.min, np.max, 'count'], TBL_VOLUME: np.sum, 'total_price': np.sum})
    vol_grp_ask = ask_tbl.groupby([TBL_VOLUME]).agg(
        {TBL_PRICE: [np.min, np.max, 'count'], TBL_VOLUME: np.sum, 'total_price': np.sum})

    # Rename column names for Volume Grouping
    vol_grp_bid.columns = ['min_Price', 'max_Price', 'count', TBL_VOLUME, 'total_price']
    vol_grp_ask.columns = ['min_Price', 'max_Price', 'count', TBL_VOLUME, 'total_price']

    # Filter data by min Volume, more than 1 (intefere with bubble), less than 70 (mostly 1 or 0.5 ETH humans)
    vol_grp_bid = vol_grp_bid[
        ((vol_grp_bid[TBL_VOLUME] >= minVolume) & (vol_grp_bid['count'] >= 2.0) & (vol_grp_bid['count'] < 70.0))]
    vol_grp_ask = vol_grp_ask[
        ((vol_grp_ask[TBL_VOLUME] >= minVolume) & (vol_grp_ask['count'] >= 2.0) & (vol_grp_ask['count'] < 70.0))]

    # Get the size of each order
    vol_grp_bid['unique'] = vol_grp_bid.index.get_level_values(TBL_VOLUME)
    vol_grp_ask['unique'] = vol_grp_ask.index.get_level_values(TBL_VOLUME)

    # Round the size of order
    vol_grp_bid['unique'] = vol_grp_bid['unique'].apply(round_sig, args=(3, 0, sig_use))
    vol_grp_ask['unique'] = vol_grp_ask['unique'].apply(round_sig, args=(3, 0, sig_use))

    # Round the Volume
    vol_grp_bid[TBL_VOLUME] = vol_grp_bid[TBL_VOLUME].apply(round_sig, args=(1, 0, sig_use))
    vol_grp_ask[TBL_VOLUME] = vol_grp_ask[TBL_VOLUME].apply(round_sig, args=(1, 0, sig_use))

    # Round the Min/ Max Price
    vol_grp_bid['min_Price'] = vol_grp_bid['min_Price'].apply(round_sig, args=(3, 0, sig_use))
    vol_grp_ask['min_Price'] = vol_grp_ask['min_Price'].apply(round_sig, args=(3, 0, sig_use))
    vol_grp_bid['max_Price'] = vol_grp_bid['max_Price'].apply(round_sig, args=(3, 0, sig_use))
    vol_grp_ask['max_Price'] = vol_grp_ask['max_Price'].apply(round_sig, args=(3, 0, sig_use))

    # Round and format the Total Price
    vol_grp_bid['total_price'] = (vol_grp_bid['total_price'].round(sig_use).apply(lambda x: "{:,}".format(x)))
    vol_grp_ask['total_price'] = (vol_grp_ask['total_price'].round(sig_use).apply(lambda x: "{:,}".format(x)))

    # Append individual text to each element
    vol_grp_bid['text'] = ("There are " + vol_grp_bid['count'].map(str) + " orders " + vol_grp_bid['unique'].map(
        str) + " " + currency +
                           " each, from " + symbol + vol_grp_bid['min_Price'].map(str) + " to " + symbol +
                           vol_grp_bid['max_Price'].map(str) + " resulting in a total of " + vol_grp_bid[
                               TBL_VOLUME].map(str) + " " + currency + " worth " + symbol + vol_grp_bid[
                               'total_price'].map(str))
    vol_grp_ask['text'] = ("There are " + vol_grp_ask['count'].map(str) + " orders " + vol_grp_ask['unique'].map(
        str) + " " + currency +
                           " each, from " + symbol + vol_grp_ask['min_Price'].map(str) + " to " + symbol +
                           vol_grp_ask['max_Price'].map(str) + " resulting in a total of " + vol_grp_ask[
                               TBL_VOLUME].map(str) + " " + currency + " worth " + symbol + vol_grp_ask[
                               'total_price'].map(str))

    # Save data global
    shape_ask[combined] = vol_grp_ask
    shape_bid[combined] = vol_grp_bid

    cMaxSize = final_tbl['sqrt'].max()  # Fixing Bubble Size

    # nifty way of ensuring the size of the bubbles is proportional and reasonable
    sizeFactor = maxSize / cMaxSize
    final_tbl['sqrt'] = final_tbl['sqrt'] * sizeFactor

    # making the tooltip column for our charts
    final_tbl['text'] = (
            "There is a " + final_tbl[TBL_VOLUME].map(str) + " " + currency + " order for " + symbol + final_tbl[
        TBL_PRICE].map(str) + " being offered by " + final_tbl['n_unique_orders'].map(
        str) + " unique orders worth " + symbol + final_tbl['total_price'].map(str))

    # determine buys / sells relative to last market price; colors price bubbles based on size
    # Buys are green, Sells are Red. Probably WHALES are highlighted by being brighter, detected by unqiue order count.
    final_tbl['colorintensity'] = final_tbl['n_unique_orders'].apply(calcColor)
    final_tbl.loc[(final_tbl[TBL_PRICE] > mp), 'color'] = \
        'rgb(' + final_tbl.loc[(final_tbl[TBL_PRICE] >
                                mp), 'colorintensity'].map(str) + ',0,0)'
    final_tbl.loc[(final_tbl[TBL_PRICE] <= mp), 'color'] = \
        'rgb(0,' + final_tbl.loc[(final_tbl[TBL_PRICE]
                                  <= mp), 'colorintensity'].map(str) + ',0)'

    timeStamps[combined] = timeStampsGet[combined]  # now save timestamp of calc start in timestamp used for title

    tables[combined] = final_tbl  # save table data

    marketPrice[combined] = mp  # save market price

    depth_ask[combined] = ob_ask
    depth_bid[combined] = ob_bid

    pair.newData = True
    pair.prepare = True  # just used for first enabling of send prepare
    return True


# begin building the dash itself
app = dash.Dash()
app.scripts.append_script({"external_url": js_extern})
# simple layout that can be improved with better CSS/JS later, but it does the job for now
# static_content_before contains all the info we want in our headers that won't be dynamic (for now)
static_content_before = [
    html.H2('CRYPTO WHALE WATCHING APP'),
    html.H3(html.A('GitHub Link Here (Consider supporting us by giving a star; request new features via "issues" tab)',
                   href="https://github.com/pmaji/eth_python_tracker")),
    html.P([
        "Legend: Bright colored mark = likely WHALE ",
        "(high volume price point via 1 unique order, or many identical medium-sized orders in a ladder). ", html.Br(),
        "Bubbles get darker as the number of unique orders increases. " , html.Br(),
        "Hover over bubbles for more info. Note: volume (x-axis) on log-scale. " , html.Br(),
        "Click 'Freeze all' button to halt refresh, "
        "and hide/show buttons to pick which currency pairs to display. " , html.Br(),
        "Only displays orders >= 1% of the volume of the portion of the order book displayed. ", html.Br(),
        "If annotations overlap or bubbles cluster, click 'Freeze all' and then zoom in on the area of interest.", html.Br(),
        "See GitHub link above for further details."
        ])
]
cCache = []
for pair in PAIRS:
    ticker = pair.ticker
    exchange = pair.exchange
    graph = 'live-graph-' + exchange + "-" + ticker
    cCache.append(html.Br())
    cCache.append(html.Div(id=graph))

static_content_after = dcc.Interval(
    id='main-interval-component',
    interval=clientRefresh * 1000
)
app.layout = html.Div(id='main_container', children=[
    html.Div(static_content_before),
    html.Div(id='graphs_Container', children=cCache),
    html.Div(static_content_after),
])


def prepare_data(ticker, exchange):
    combined = exchange + ticker
    data = get_data_cache(combined)
    pair.newData = False
    base_currency = ticker.split("-")[1]
    ob_ask = depth_ask[combined]
    ob_bid = depth_bid[combined]
    #Get Minimum and Maximum
    ladder_Bid_Min = fixNan(shape_bid[combined]['volume'].min())
    ladder_Bid_Max = fixNan(shape_bid[combined]['volume'].max(), False)
    ladder_Ask_Min = fixNan(shape_ask[combined]['volume'].min())
    ladder_Ask_Max = fixNan(shape_ask[combined]['volume'].max(), False)
    data_min = fixNan(data[TBL_VOLUME].min())
    data_max = fixNan(data[TBL_VOLUME].max(), False)
    ob_bid_max = fixNan(ob_bid[TBL_VOLUME].max(), False)
    ob_ask_max = fixNan(ob_ask[TBL_VOLUME].max(), False)

    symbol = SYMBOLS.get(base_currency.upper(), "")
    x_min = min([ladder_Bid_Min, ladder_Ask_Min, data_min])
    x_max = max([ladder_Bid_Max, ladder_Ask_Max, data_max, ob_ask_max, ob_bid_max])
    max_unique = max([fixNan(shape_bid[combined]['unique'].max(), False),
                      fixNan(shape_ask[combined]['unique'].max(), False)])
    width_factor = 15
    if max_unique > 0: width_factor = 15 / max_unique
    market_price = marketPrice[combined]
    bid_trace = go.Scatter(
        x=[], y=[],
        text=[],
        mode='markers', hoverinfo='text',
        marker=dict(opacity=0, color='rgb(0,255,0)'))
    ask_trace = go.Scatter(
        x=[], y=[],
        text=[],
        mode='markers', hoverinfo='text',
        marker=dict(opacity=0, color='rgb(255,0,0)'))
    shape_arr = [dict(
        # Line Horizontal
        type='line',
        x0=x_min * 0.5, y0=market_price,
        x1=x_max * 1.5, y1=market_price,
        line=dict(color='rgb(0, 0, 0)', width=2, dash='dash')
    )]
    annot_arr = [dict(
        x=log10((x_max*0.9)), y=market_price, xref='x', yref='y',
        text=str(market_price) + symbol,
        showarrow=True, arrowhead=7, ax=20, ay=0,
        bgcolor='rgb(0,0,255)', font={'color': '#ffffff'}
    )]
    # delete these 10 lines below if we want to move to a JS-based coloring system in the future
    shape_arr.append(dict(type='rect',
                          x0=x_min, y0=market_price,
                          x1=x_max, y1=market_price * 1.05,
                          line=dict(color='rgb(255, 0, 0)', width=0.01),
                          fillcolor='rgba(255, 0, 0, 0.04)'))
    shape_arr.append(dict(type='rect',
                          x0=x_min, y0=market_price,
                          x1=x_max, y1=market_price * 0.95,
                          line=dict(color='rgb(0, 255, 0)', width=0.01),
                          fillcolor='rgba(0, 255, 0, 0.04)'))
    for index, row in shape_bid[combined].iterrows():
        cWidth = row['unique'] * width_factor
        vol = row[TBL_VOLUME]
        posY = (row['min_Price'] + row['max_Price']) / 2.0
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
    for index, row in shape_ask[combined].iterrows():
        cWidth = row['unique'] * width_factor
        vol = row[TBL_VOLUME]
        posY = (row['min_Price'] + row['max_Price']) / 2.0
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
            ), ask_trace, bid_trace, go.Scatter(
                x=ob_ask[TBL_VOLUME],
                y=ob_ask[TBL_PRICE],
                mode='lines',
                opacity=0.5,
                hoverinfo='text',
                text=ob_ask['text'],
                line = dict(color = ('rgb(255, 0, 0)'),
                        width = 2)
            ),go.Scatter(
                x=ob_bid[TBL_VOLUME],
                y=ob_bid[TBL_PRICE],
                mode='lines',
                opacity=0.5,
                hoverinfo='text',
                text=ob_bid['text'],
                line = dict(color = ('rgb(0, 255, 0)'),
                        width = 2)
            )
        ],
        'layout': go.Layout(
            # title automatically updates with refreshed market price
            title=("The present market price of {} on {} is: {}{} at {}".format(ticker, exchange, symbol,
                                                                                str(
                                                                                    marketPrice[combined]),
                                                                                timeStamps[combined])),
            xaxis=dict(title='Order Size', type='log', autotick=True,range=[log10(x_min*0.95), log10(x_max*1.03)]),
            yaxis={'title': '{} Price'.format(ticker),'range':[market_price*0.94, market_price*1.06]},
            hovermode='closest',
            # now code to ensure the sizing is right
            margin=go.Margin(
                l=75, r=75,
                b=50, t=50,
                pad=4),
            paper_bgcolor='#F5F5F5',
            plot_bgcolor='#F5F5F5',
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
    for pair in PAIRS:
        ticker = pair.ticker
        exchange = pair.exchange
        graph = 'live-graph-' + exchange + "-" + ticker
        lCache.append(html.Br())
        if (pair.Dataprepared):
            lCache.append(dcc.Graph(
                id=graph,
                figure=cData[exchange + ticker]
            ))
        else:
            lCache.append(html.Div(id=graph))
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

def fixNan(x, pMin=True):
    if isnan(x):
      if pMin:
         return 99999
      else:
         return 0
    else:
      return x

def getStamp():
    return int(round(time.time() * 1000))

# watchdog to catch any instances where refresh stops
def watchdog():
    global PAIRS
    tServer = threading.Thread(target=serverThread)
    tServer.daemon = False
    tServer.start()
    time.sleep(3)  # get Server start
    log(2,"Server should be running now")
    tPreparer = threading.Thread(target=sendPrepareThread)
    tPreparer.daemon = False
    tPreparer.start()
    for pair in PAIRS:
        pair.threadWebsocket = threading.Thread(
            target=websockThread, args=(pair,))
        pair.threadWebsocket.daemon = False
        pair.threadWebsocket.start()
        time.sleep(3)
    log(2,"Web sockets up")
    for pair in PAIRS:
        pair.threadRecalc = threading.Thread(target=recalcThread, args=(pair,))
        pair.threadRecalc.daemon = False
        pair.threadRecalc.start()
        time.sleep(2.5)
    log(2,"ReCalc up")
    for pair in PAIRS:
        pair.threadPrepare = threading.Thread(
            target=preparePairThread, args=(pair,))
        pair.threadPrepare.daemon = False
        pair.threadPrepare.start()
    log(2,"Everything should be running now, starting Watchdog, to control the herd")
    while True:
        time.sleep(2)
        alive = True
        for pair in PAIRS:
            if not pair.threadRecalc.isAlive():
                alive = False
                log(2,"Restarting pair Recalc " +
                      pair.exchange + " " + pair.ticker)
                pair.threadRecalc = threading.Thread(
                    target=recalcThread, args=(pair,))
                pair.threadRecalc.daemon = False
                pair.threadRecalc.start()
            if not pair.threadWebsocket.isAlive():
                alive = False
                log(2,"Restarting pair Web socket " +
                      pair.exchange + " " + pair.ticker)
                pair.webSocketKill = 1
                pair.threadWebsocket = threading.Thread(
                    target=websockThread, args=(pair,))
                pair.threadWebsocket.daemon = False
                pair.threadWebsocket.start()
            if not pair.threadPrepare.isAlive():
                alive = False
                log(2,"Restarting pair Prepare worker " +
                      pair.exchange + " " + pair.ticker)
                pair.threadPrepare = threading.Thread(
                    target=preparePairThread, args=(pair,))
                pair.threadPrepare.daemon = False
                pair.threadPrepare.start()
        if not tServer.isAlive():
            alive = False
            log(3,"Watchdog detected dead Server, restarting")
            tServer = threading.Thread(target=serverThread)
            tServer.daemon = False
            tServer.start()
        if not tPreparer.isAlive():
            alive = False
            log(3,"Watchdog detected dead Preparer, restarting")
            tPreparer = threading.Thread(target=sendPrepareThread)
            tPreparer.daemon = False
            tPreparer.start()
        if not alive:
            log(3,"Watchdog got some bad sheeps back to group")


def serverThread():
    app.run_server(host='0.0.0.0', port=serverPort)


def sendPrepareThread():
    global sendCache, first_prepare, overallNewData
    while True:
        sendCache = prepare_send()
        overallNewData = False
        time.sleep(0.5)
        while not overallNewData:
            time.sleep(0.5)


def recalcThread(pair):
    count = 0
    refreshes = 0
    while True:
        if (pair.websocket):
            dif = getStamp() - pair.lastStamp
            if dif > desiredPairRefresh:
                log(1,"Ms Diff for " + pair.ticker + " is " + str(
                    dif) + " Total refreshes for pair " + str(refreshes))
                refreshes += 1
                if not calc_data(pair):
                    count = count + 1
                else:
                    count = 0
                    pair.lastStamp = pair.usedStamp
                if count > 5:
                    log(3,"Going to kill Web socket from " + pair.ticker)
                    count = -5
                    pair.webSocketKill = 0
            else:
                time.sleep((desiredPairRefresh - dif) / 1000)


def websockThread(pair):
    pair.websocket = False
    pair.ob_Inst = GDaxBook(pair.ticker)
    time.sleep(5)
    pair.websocket = True
    while True:
        kill = 5 / pair.webSocketKill
        time.sleep(4)


def preparePairThread(pair):
    global prepared, overallNewData
    ticker = pair.ticker
    exc = pair.exchange
    cbn = exc + ticker
    while True:
        if (pair.prepare):
            prepared[cbn] = prepare_data(ticker, exc)
            overallNewData = True
            pair.Dataprepared = True
        while not pair.newData:
            time.sleep(0.2)

def handleArgs(argv):
    global serverPort, debugLevel, desiredPairRefresh
    try:
        opts, args = getopt.getopt(
            argv, "hp:d:", ["port=","debug=","pRefresh="])
    except getopt.GetoptError:
        print('app.py -h')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('app.py --port 8050 --pRefresh')
            print('--pRefresh indicates the refresh Rate in ms')
            sys.exit()
        elif opt in ("-p", "--port"):
            serverPort = int(arg)
        elif opt in ("-d", "--debug"):
            debugLevel = int(arg)
        elif opt in ("--pRefresh"):
            desiredPairRefresh = int(arg)

    log(4,"Legend: This is an error message")
    log(3,"Legend: This is a warning message")
    log(2,"Legend: This is an info message")
    log(1,"Legend: This is a debug message")
    log(0,"Legend: This is a deep debug message")
    log(1,'Web Interface Port is ' + str(serverPort))
    log(1,'Debug Level is ' + str(debugLevel))

def log(pLevel, pMessage):
    if pLevel >= debugLevel:
        text = (str(datetime.now()) + " [" +
            debugLevels[pLevel] +
            "]: " + str(pMessage))
        open("log.txt","a").write(text + "\n")
        print(debugColors[pLevel] + text + '\033[0m')

if __name__ == '__main__':
    # Initial Load of Data
    handleArgs(sys.argv[1:])
    watchdog()
