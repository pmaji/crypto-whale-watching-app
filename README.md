## Introduction

Welcome! This is a Python-based Dash app meant to track whale activity in buy / sell walls on crypto-currency exchanges (presently just operational for GDAX, but more to come). This document aims to explain the purpose, functionality, and future of this project. Please do share this with your fellow coders / traders, donate via the donation addresses included in the "Support Needed" section below, and contribute to the future of this project by calling out issues, requesting new features, and submitting pull requests to improve the app.


## What's the point of this app?

Presently, GDAX allows users to see the buy and sell limit order volume via the "depth chart" shown below. 

![GDAX Depth Chart](https://raw.githubusercontent.com/pmaji/eth_python_tracker/master/screenshots/gdax_depth_chart.JPG)

The problem with this is that the depth chart does not tell us where the volume behind buy and sell walls is coming from. It could be from a few whales seeking to manipulate the market, or it could be from a large number of individuals who have placed orders around a modal point. In technical terms, there is no way to see how much of present resistance or support levels are due to individuals vs. group clustering. 

This difference is quite important, as it impacts how quickly walls can be pulled, etc., so having buy & sell-wall information at the order level can prove quite valuable for traders. This simple app allows you to access just that information, by focusing on individual limit orders that constitute large walls, and particularly emphasizing the largest orders. As can be seen from the UI screenshot below, for each currency pairing the user can easily examine the largest orders hiding amongst the walls. The algorithm used displays only those orders that make up >= 1% of the volume of the portion of the order book shown in the visualization (+/-5% from present market price). Thanks to the creative coloring algorithm behind the visualization, the brightest colors are those most likely to be whales (i.e. substantial volume at a single price point via a single limit order). The colors become progressively darker as the number of distinct orders at a pricepoint increases, allowing for easy visual identification of whales in the market.

![Main UI](https://raw.githubusercontent.com/pmaji/eth_python_tracker/master/screenshots/main_app_ui.JPG)

In addition to the main views which provide at-a-glance information about the largest orders, users can freeze the live refresh within the app in order to zoom in on particular sections of the order book, or to take better advantage of the tooltip capabilities of the Plotly visualization. Hover over any particular price-point as shown in the screenshot below to see a tooltip that displays helpful information, including how many unique orders are behind that particular price-point bubble. 

![Tooltip UI](https://raw.githubusercontent.com/pmaji/crypto-whale-whatching-app/master/screenshots/ui_tooltip_screenshot.JPG)


## A Few More Technical Details

The present version tracks all major pairings (ETH/USD; ETH/BTC; BTC/USD; LTC/USD) but I can add more upon request. It is set to update every 5 seconds (to optimize load-time) but this can be changed easily in the code if you want to make the refreshes faster / slower. There are also buttons that allow the user to pause the automatic refresh ("Freeze all" / "Unfreeze all"), and hide any of the currency pairings that they do not wish to see displayed. The refresh-pausing functionality allows the user to preserve any zoom or limitation that they have selected via the Plotly viz. 

The size of each observation is determined algorithmically using a transformation of the square root of the volume of all orders at that particular price-point calibrated so that the bubbles never become unreasonably large or small. The color-coding allows for easy identification of whales, as described in the section above. 

Note: all of these limitations--i.e. the volume minimum, the order book limitations, etc., are parameterized within the app.py code and thus can be easily changed if so desired.

Anyone interested with Python 3.6 installed can download the app.py or clone the repo and run the app locally, just check to be sure you have the few required modules installed (see requirements.txt for this). In addition to local hosting, members of the Ethereum community have volunteered to host versions on their own personal servers. A web-hosted version of the app [can be accessed here.](http://whales.cracklord.com/) If for any reason the page does not load, feel free to let us know via an issue, but more than likely it is because we are updating to the newest version of the codebase or performing maintenance.   

## Contribution Rules

All are welcome to contribute issues / pull-requests to the codebase. All I ask is that you include a detailed description of your contribution, that your code is thoroughly-commented, and that you test your contribution locally with the most recent version of the Master branch integrated prior to submitting the PR.

## Support Needed

While this project has grown in popularity a great deal as of late, there is still much to be done. Below is a summary of the main needs that we have presently with which anyone can assist (this is a community project after all!):

1. Donations needed for host-fees and development work (presently raising money for AWS migration):

     1. **ETH donations address: 0xDB63E1e60e644cE55563fB62f9F2Fc97B751bc49**
     
     2. **BTC donations address: 1M2fFerihy68gVJ5gvB7yrnwBbzEPhCbZ2**
     
     3. **LTC donations address: LWaLxgaBveWATqwsYpYfoAqiG2tb2o5awM**
     
2. Overall promotion:

     1. Keep sharing with you friends / fellow traders / coders so that we can get more constructive feedback.
     
     2. Consider starring us on GitHub as a means of sharing this project with the broader community.
     
3. Technical assistance and ideation:

     1. If you have coding experience, check out the code and issues tab and see if you can help with anything or propose new additions.
     
     2. If you want new features integrated or have any other ideas, open a new issue and I'll address them ASAP.








