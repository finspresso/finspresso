# Portfolio tracker
The goal of the portfolio tracker is to give the user the option enter his/her holdings via a .json file and it outputs different metrics e.g. dividend, dividend growth rate. Enter your holdings in the desired .json file in the same format as in the file `holdings_single.json`. Then to run the portfolio tracker run:

`python portfolio_tracker.py --holdings_file holdings_single.json`

## Installation
In order to be able to run the Python script, run:
Installation of pre-commit hooks

`pip install -r requirements.txt`

`pre-commit install`

## Data source
The financial data in the tool is downloaded from Yahoo Finance via the API Python wrapper [yfinance](https://github.com/ranaroussi/yfinance). Please note, the given scripts are merely educational nature and should only used for personal usage according to the Yahoo terms of use [here](https://policies.yahoo.com/us/en/yahoo/terms/product-atos/apiforydn/index.htm), [here](https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html), [here](https://policies.yahoo.com/us/en/yahoo/terms/index.htm)

## Dividend analyzer
The history of the yearly paid dividend is visible in the lower plot in the form of a bar chart (see below). The upper plot shows the dividend growth rate with different filter methods. For more details on this topic, check out the blog entry [Estimate dividend growth rate in the future part I](https://www.finspresso.com/2022/02/19/estimate-dividend-growth-rate-in-the-future-part-i/) on finspresso.com.

![dividend1](images/dividend1.png)
