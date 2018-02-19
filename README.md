## Introduction

Welcome! This is a Python-based Dash app meant to track whale activity in buy / sell walls on crpyto-currency exchanges (presently just operational for GDAX, but more to come). This document aims to explain the purpose, functionality, and future of this project. Please do share this with your fellow coders / traders, donate via the donation addresses included in the "Support Needed" section below, and contribute to the future of this project by calling out issues, requesting new features, and submitting pull requests to improve the app.


## What's the point of this app?

Presently, GDAX allows users to see the buy and sell limit order volume via the "depth chart" shown below. 

![GDAX Depth Chart](https://raw.githubusercontent.com/pmaji/eth_python_tracker/master/screenshots/gdax_depth_chart.JPG)

The problem with this is that the depth chart does not tell us where the volume behind buy and sell walls is coming from. It could be from a few whales seeking to manipulate the market, or it could be from a large number of individuals who have placed orders around a modal point. In technical terms, there is no way to see how much of present resistance or support levels are due to individuals vs. group clustering. 

This difference is quite important, as it impacts how quickly walls can be pulled, etc., so having buy & sell-wall information at the order level can prove quite valuable for traders. This simple app allows you to access just that information, by focusing on individual limit orders that constitute large walls, and particularly emphasizing the largest orders. As can be seen from the UI screenshot below, for each currency pairing the user can easily disect the depth chart, checking to see its composition so as to better inform a trading decision. 

![Main UI](https://raw.githubusercontent.com/pmaji/eth_python_tracker/master/screenshots/main_app_ui.JPG)

In addition to the main views which provide at-a-glance information, users can freeze the live refresh within the app in order to zoom in on particular sections of the order book, or to take better advantage of the tooltip capabilities of the Plotly visualization. Hover over any particular price-point as shown in the screenshot below to see a tooltip that displays helpful information, including how many unique orders are behind that particular price-point bubble. 

![Tooltip UI](https://raw.githubusercontent.com/pmaji/crypto-whale-whatching-app/master/screenshots/ui_tooltip_screenshot.JPG)


## A Few Technical Details

The present version tracks all major pairings (ETH/USD; ETH/BTC; BTC/USD; LTC/USD) but I can add more upon request. It is set to update every 4 seconds (to optimize load-time) but this can be changed easily in the code if you want to make the refreshes faster / slower. There are also buttons that allow the user to pause the automatic refresh. This is helpful given that it preserves any zoom or limitation that the user has selected via the Plotly viz. 

The size of each observation is determined by the square root of the volume of all orders at that particular price-point. The color-coding allows for easy identification of price-points where there are at least 5 distinct orders placed. As the legend explains, bright colors (red for sells, green for buys) represent price points with at least 5 distinct limit orders; dark colors are for price points with fewer than 5 distinct orders. I filter out all orders less than 1 in size, and only pull order book information within 2.5% of the present market price of each currency (to speed up pulls and make the viz. useful). 

Note: all of these limitations--i.e. the volume minimum, the order book limitations, etc., are paramterized within the app.py code and thus can be easily changed if so desired.

Anyone interested with Python 3.6 installed can download the app.py or clone the repo and run the app locally, just check to be sure you have the few required modules installed (see requirements.txt for this). In addition to local hosting, members of the Ethereum community have volunteered to host versions on their own personal servers. A web-hosted version of the app [can be accessed here.](http://whales.cracklord.com/) If for any reason the page does not load, feel free to let us know via an issue, but more than likely it is because we are updating to the newest version of the codebase or performing maintenance.   


## Support Needed

While this project has grown in popularity a great deal as of late, there is still much to be done. Below is a summary of the main needs that we have presently with which anyone can assist (this is a community project after all!):

1. Donations for host-fees and development work (presently raising money for AWS migration)

     1. **ETH donations address: 0xDB63E1e60e644cE55563fB62f9F2Fc97B751bc49**
     
     2. **BTC donations address: 1M2fFerihy68gVJ5gvB7yrnwBbzEPhCbZ2**
     
     3. **LTC donations address: LWaLxgaBveWATqwsYpYfoAqiG2tb2o5awM**
     
2. Overall promotion:

     1. Keep sharing with you friends / fellow traders / coders so that we can get more constructive feedback.
     
     2. Consider starring us on GitHub as a means of sharing this project with the broader community.
     
3. Technical assistance and ideation:

     1. If you have coding experience, check out the code and issues tab and see if you can help with anything or propose new additions.
     
     2. If you want new features integrated or have any other ideas, open a new issue and I'll address them ASAP.








