## Introduction

Welcome! This is a Python-based Dash app meant to track whale activity in buy / sell walls on crypto-currency exchanges (presently just operational for GDAX, but more exchanges to come). This document aims to explain the purpose, functionality, and future of this project. Please do share this with your fellow coders / traders / crypto-aficionados, and contribute to the future of this project by calling out issues, requesting new features, and submitting pull requests to improve the app.

While this was previously hosted by a member of the community, the scale and computational intensity of the application have made it too expensive to host long-term in a sustainable manner. If anyone is interested in working with us on web-hosting this application, please reach out via an issue here on GitHub, or feel free to reach out directly [to me via here via Twitter](https://twitter.com/ByPaulJ).

Even absent a web-hosted version of the app, it is quite easy to use. Scroll down to the How-To / User Guide section to learn more about how to run the app yourself. The most recent updates to the app include new features like an improved depth chart (shown in the screenshot below), as well as a side-menu that allows selective hiding / showing of various pairs of interest.

![First UI View](https://raw.githubusercontent.com/pmaji/crypto-whale-watching-app/master/screenshots/improved_new_plots.JPG)

## What's the point of this app?

Presently, GDAX allows users to see the buy and sell limit order volume via the "depth chart" shown below. 

<img src="https://raw.githubusercontent.com/pmaji/eth_python_tracker/master/screenshots/gdax_depth_chart.JPG" width="700" height="300">

The problem with this is that the depth chart does not tell us where the volume behind buy and sell walls is coming from. It could be from a few whales seeking to manipulate the market, or it could be from a large number of individuals who have placed orders around a modal point. In technical terms, there is no way to see how much of present resistance or support levels are due to individuals vs. group clustering. 

This difference is quite important, as it impacts how quickly walls can be pulled, etc., so having buy & sell-wall information at the order level can prove quite valuable for traders. This simple app allows you to access just that information, by focusing on individual limit orders that constitute large walls, and particularly emphasizing the largest orders, enabling the user to spot whales that may be manipulating the present price via various methods. How exactly we define / spot whale activity is the focus of the next section.

## How to spot a whale:

This is perhaps the most important question when it comes to the purpose of this app. We have iterated on this many times, and have arrived at an algorithmic definition that spots 2 types of whales:

* Single Price-Point Whales:
     * Place one large order at a single price-point 
     * Example: 500 ETH for sale at $1000 via 1 unique order
     * Represented via a bubble in the visualization.
     * Tooltip includes order price-point, volume, and number of unique orders
* Ladder Price-Point Whales:
     * Place many medium-sized orders for identical volume increasing in price
     * Example: 500 total ETH for sale starting at $900 and spanning until $1000 via 10 unique 50-ETH orders
     * Represented via a line bar  spanning the range of the ladder
     * Tooltip includes number and volume of orders, price-range of ladder, and total volume

While these two may seem different, their market impacts are often comparable. I think a real world example of this helps illustrate this point:

> Imagine that you are looking to understand if there is any whale activity at your local coffee shop (I know this is silly but I promise it is a good example; stay with me here). You could sit near the ordering area and write down each individual order. If someone comes along and orders 100 lattes, that would get your attention--you have spotted a whale! What if, however, someone was ordering 5 lattes, and then getting in the back of the line again, and ordering another 5 lattes, repeating this until they had purchased a total of 100 lattes? Both of these individuals had a whale-like impact on market movement, but if all you care about is the size of each individual order, you will miss out on the sneaky whales that may be splitting their orders across a ladder of price-points.

> Given that GDAX's API doesn't display ETH addresses (only unique order IDs), we cannot say with 100% certainty that what looks like a "ladder price-point whale" is in fact a unitary actor. We have to make some assumptions. To continue the coffee shop metaphor, we aren't able to actually look at the people in line for coffee; instead, we have a blindfold on and are jotting down what we hear the barista say. We hear "1 order for 5 lattes" once and write it down, but if we hear "1 order for 5 lattes" 100 different times in close succession, then we can make the safe assumption that we are dealing with a whale, as this is analogous to seeing 100 orders for 10 ETH stacked in a ladder of price-points in close succession on GDAX. 

As can be seen from the UI screenshot below, for each currency pairing the user can easily examine the most obvious whales hiding amongst the walls. The algorithm used displays only those orders that make up >= 1% of the volume of the portion of the order book shown in the visualization (which is presently +/-5% from present market price). This methodology makes our analysis robust both in times of price stability--when there is both resistance and support similar in magnitude--as well as during times of large price fluctuation--when there may be very little support or very little resistance. Thanks to the creative coloring algorithm behind the visualization, the brightest colors are those most likely to be whales. The colors become progressively darker as the number of distinct orders at a price-point increases, allowing for easy visual identification of whales in the market.

![Main UI](https://raw.githubusercontent.com/pmaji/crypto-whale-watching-app/master/screenshots/eth_btc_main_view.JPG)

In addition to the main views which provide at-a-glance information about the largest orders, users can freeze the live refresh within the app in order to zoom in on particular sections of the order book, or to take better advantage of the tooltip capabilities of the Plotly visualization. Given that we now track both single price-point and ladder price-point whales, there are often times when bubbles overlap the linebar charts. When this happens, simply freeze the visualization and zoom in on a particular area to separate the two in a more detailed view. An example of the tooltip functionalities for both the ladder and single price-point whales can be seen via the screenshots below.

![Single-Price-Point Whale](https://raw.githubusercontent.com/pmaji/crypto-whale-watching-app/master/screenshots/single_price_point_whale_tooltip.JPG)

In the image above we are looking at a zoom-in on the chart of BTC/USD. The bubble that we have hovered over near the top towards the center of the view is a slightly dark red bubble (as opposed to the brightest red) because there are 2 orders at that exact price price-point; hence, we cannot be 100% confident that it is one whale acting unilaterally. That said, those 2 orders alone constitute almost $1,000,000.00 in sell-side pressure, so they are important to call out, and thus our methodology captures them. We can see additional useful information via the tooltip--namely, that these 2 sell orders together constitute 113.38 BTC in sell-order volume, with each of those orders being placed at a price-point of  $8,352.00. Lastly, we see the count of unique orders at this price point (2), along with the sum total value of those orders ($946,949.76).

![Ladder-Price-Point-Whale](https://raw.githubusercontent.com/pmaji/crypto-whale-watching-app/master/screenshots/ladder_price_point_whale_tooltip.JPG)

In the image above we are looking at the chart for ETH/USD, hovering over a large ladder price-point whale. Here we can see that the tooltip calls out the total number of rungs on the ladder--7 orders of 50 ETH each--as well as the price range in which those orders are found--from $506.99 to $520.00--and the total market value of those orders (in this case $179,051.50). The thickness of the line is also proportional to the size of each rung on the order ladder.

We cannot be as certain that ladder price-point whales are, in fact, individual whales, as it could just be a few people who place similar orders of identical size at different psychological modal points, but in most cases this is unlikely, and we leave it up to the user to make the ultimate determination as to whether or not they believe a particular order or set of orders to be a whale or not. That said, we do recognize that the ladder price-point whale methodology could perhaps be improved with variable controls, and we are actively looking into this along with other improvements. Our app only serves to provide the information, and to ascribe some semblance of a probability to the likelihood that an observation is a whale or not. 

## How-To / User Guide (and a few more technical details)

The present version tracks all major pairings (ETH/USD; ETH/BTC; BTC/USD; LTC/USD) but I can add more upon request. It is set to update every 5 seconds (to optimize load-time) but this can be changed easily in the code if you want to make the refreshes faster / slower. There are also buttons that allow the user to pause the automatic refresh ("Freeze all" / "Unfreeze all"), and hide any of the currency pairings that they do not wish to see displayed. The refresh-pausing functionality allows the user to preserve any zoom or limitation that they have selected via the Plotly viz. 

The size of each observation is determined algorithmically using a transformation of the square root of the volume of all orders at that particular price-point calibrated so that the bubbles never become unreasonably large or small. The color-coding allows for easy identification of whales, as described in the section above. 

Note: all of these limitations--i.e. the volume minimum, the order book limitations, etc., are parameterized within the app.py code and thus can be easily changed if so desired.

Anyone interested with Python 3.6 installed can download the app.py or clone the repo and run the app locally, just check to be sure you have the few required modules installed. Once you have Python 3.6 installed, open up a Terminal and type:

> pip install -r /path/to/requirements.txt

Once its finished type:

> python app.py

Then open up your browser and type in the set of numbers that pop up in terminal, which should look similar to "127.0.0.1:8050".

## Support Needed

Below is a summary of the main needs that we have presently with which anyone can assist (this is a community project after all!):

1. Technical assistance and ideation:

     1. If you have coding experience, check out the code and issues tab and see if you can help with anything or propose new additions.
     
     2. If you want new features integrated or have any other ideas, open a new issue and I'll address it ASAP.

2. Overall promotion:

     1. Keep sharing with you friends / fellow traders / coders so that we can get more constructive feedback.
     
     2. **Consider starring us on GitHub** as a means of sharing this project with the broader community.

## Contribution Rules

All are welcome to contribute issues / pull-requests to the codebase. All I ask is that you include a detailed description of your contribution, that your code is thoroughly-commented, and that you test your contribution locally with the most recent version of the Master branch integrated prior to submitting the PR. We also have a Telegram chat for major contributors, so if you want to be added to that, first submit a contribution and then [reach out to me via Twitter](https://twitter.com/ByPaulJ).






