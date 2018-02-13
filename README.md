# eth_python_tracker
Welcome! This is a Python-based Dash app meant to track whale activity in buy / sell walls on GDAX. The present version tracks all major pairings (ETH/USD; ETH/BTC; BTC/USD; LTC/USD) but I can add more upon request. It is set to update every 4 seconds (to optimize load-time now that it is hosted at multiple URLS) but this can be changed easily in the code if you want to make the refreshes faster / slower. 

The idea for this app came to me while looking at buy and sell walls on GDAX. While you can see large walls, you cannot see how much of these are due to individuals vs. group clustering. This difference is quite important, as it impacts how quickly walls can be pulled, etc., so having buy / sell-wall information at the order level can prove quite valuable for traders. This simple app allows you to access just that information, by focusing on individual limit orders that constitute large walls, and particularly emphasizing the largest orders. Hover over any particular price-point to see a tooltip that displays helpful information, including how many unique orders are behind that particular price-point bubble. 

Screenshots of the app's UI are included above. The size of each observation is deteremined by the square root of the volume of all orders at that particular price-point. The color-coding allows for easy identification of price-points where there are at least 5 distinct orders placed. I filter out all orders less than 1 ETH in size, and only pull order book information within 2.5% of the present market price of each currency (to speed up pulls and make the viz. useful). 

Anyone interested with Python 3.6 installed on their computer can download this and run it locally, just check to be sure you have the few required modules installed (see requirements.txt for this). In addition to local hosting, various members of the Ethereum community have volunteered to host versions on their own servers. At the bottom of this README are links to all URLs presently hosting the app.  

This is my first Python / Dash app, and I hope it is of use to many of you! Leave any feedback via the creation of a new issue or a contribution to an open issue. Please support the project if you can by donating to the addresses below and/or leaving a star here on GitHub. I have many ideas for continued improvement, and if enough funds are raised, will migrate to an AWS / Heroku host. Thanks again for reading!

**ETH donations address: 0xDB63E1e60e644cE55563fB62f9F2Fc97B751bc49**

**BTC donations address: 1M2fFerihy68gVJ5gvB7yrnwBbzEPhCbZ2**

Prsently, you can access the app at the links below:

http://whales.cracklord.com/

http://ac.com.au:8050/

