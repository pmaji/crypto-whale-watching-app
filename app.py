# begin app code, importing necessary modules
# app can be run by executing 'python app.py' in console at the file's location

import gdax
import time
from datetime import datetime as dt
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
import numpy as np

# set up begins
app = dash.Dash()

public_client = gdax.PublicClient() #defines public client for all functions

order_book = public_client.get_product_order_book('ETH-USD', level=3)
ask_tbl = pd.DataFrame(data=order_book['asks'], columns=['price', 'volume', 'address'])
bid_tbl = pd.DataFrame(data=order_book['bids'], columns=['price', 'volume', 'address'])

# building subsetted table for ask data only
ask_tbl['price']=pd.to_numeric(ask_tbl['price'])
ask_tbl['volume']=pd.to_numeric(ask_tbl['volume'])
first_ask = float(ask_tbl.iloc[1,0])
ten_perc_above_first_ask = (1.1 * first_ask)
ask_tbl = ask_tbl[(ask_tbl['price'] <= ten_perc_above_first_ask)]

# building subsetted table for bid data only
bid_tbl['price']=pd.to_numeric(bid_tbl['price'])
bid_tbl['volume']=pd.to_numeric(bid_tbl['volume'])
first_bid = float(bid_tbl.iloc[1,0])
ten_perc_above_first_bid = (0.9 * first_bid)
bid_tbl = bid_tbl[(bid_tbl['price'] >= ten_perc_above_first_bid)]


# actual app layout below
app.layout = html.Div([
html.H4('Whale-Tracking App. ETH donations appreciated: 0x966796A6334EA1302d9Edb03072dB55241145401'),
    html.Div([
        html.Div([
            html.H3('Sell-Side Walls'),
            dcc.Graph(
                id='Sell-Side Walls',
                figure={
                    'data': [
                        go.Scatter(
                            x=ask_tbl['volume'],
                            y=ask_tbl['price'],
                            mode='lines+markers',
                            opacity=0.7,
                            marker={
                                'size': 10,
                                'line': {'width': 0.5, 'color': 'white'},
                                'color': ask_tbl['volume'],  # set color equal to variable
                                'colorscale': 'Magma',
                                'showscale': True
                            },

                        )
                    ],
                    'layout': go.Layout(
                        xaxis={'title': 'Order Size'},
                        yaxis={'title': 'ETH Price'},
                        margin={'b': 0, 'r': 10, 'l': 60, 't': 0},
                        showlegend=False,
                        hovermode='closest'
                    )
                }

            )
        ], className="six columns"),

        html.Div([
            html.H3('Buy-Side Walls'),
            dcc.Graph(
                id='Buy-Side Walls',
                figure={
                    'data': [
                        go.Scatter(
                            x=bid_tbl['volume'],
                            y=bid_tbl['price'],
                            mode='lines+markers',
                            opacity=0.7,
                            marker={
                                'size': 10,
                                'line': {'width': 0.5, 'color': 'white'},
                                'color': bid_tbl['volume'],  # set color equal to variable
                                'colorscale': 'Viridis',
                                'showscale': True
                            },

                        )
                    ],
                    'layout': go.Layout(
                        xaxis={'title': 'Order Size'},
                        yaxis={'title': 'ETH Price'},
                        margin={'b': 0, 'r': 10, 'l': 60, 't': 0},
                        legend={'x': 0, 'y': 1},
                        hovermode='closest'
                    )
                }

            )
        ], className="six columns"),
    ], className="row")
])

app.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
})

if __name__ == '__main__':
    app.run_server(debug=True)