import argparse
import coloredlogs
import datetime
import json
from multiprocessing import Pool
import numpy as np
import pandas as pd

import logging


import yfinance as yf

# import ssl # ToDo: Add enabling to optional arguments
# ssl._create_default_https_context = ssl._create_unverified_context

# Global settings
coloredlogs.install()
logger_name = "dividend_analyzer"
logger = logging.getLogger(logger_name)
logging.basicConfig(level=logging.DEBUG)
SP_500_TICKER_FILE = "sp_500_tickers.json"
DATA_DICT_FILE = "data_dict.json"


class DividendAnalyzer:
    def __init__(self, tickers, n_security=10, n_portfolio=100, n_processes=None):
        self.yf_object = yf.Tickers(tickers)
        self.n_processes = n_processes
        self.data_dict = dict.fromkeys(tickers, dict())
        self.n_security = n_security
        self.n_portfolio = n_portfolio

    def randomize_portfolios(self):
        logger.info(
            "Randomizing %s portfolios with each %s securities",
            self.n_portfolio,
            self.n_security,
        )
        tickers = pd.Series(self.yf_object.tickers.keys())
        n_tickers = tickers.shape[0]

        self.portfolios = []
        while len(self.portfolios) < self.n_portfolio:
            selected_tickers = tuple(
                tickers[
                    np.floor(np.random.rand(self.n_security) * n_tickers).tolist()
                ].values.tolist()
            )
            self.portfolios.append(selected_tickers)

    def download_dividend_history_single(self):
        for ticker in self.yf_object.tickers.keys():
            logger.info("Downloading data for security {}".format(ticker))
            self.data_dict[ticker]["dividends"] = self.yf_object.tickers[
                ticker
            ].dividends
            self.data_dict[ticker]["dividends per year"] = self.get_dividends_per_year(
                self.data_dict[ticker]["dividends"]
            )

    def get_dividend_history(self, ticker):
        logger.info("Downloading data for security {}".format(ticker))
        dividend_history = dict()
        dividend_history["dividends"] = pd.Series(dtype=np.float64)
        dividend_history["dividends per year"] = pd.Series(dtype=np.float64)
        dividends = self.yf_object.tickers[ticker].dividends
        if len(dividends) > 0:
            dividend_history["dividends"] = self.yf_object.tickers[ticker].dividends
            dividend_history["dividends per year"] = self.get_dividends_per_year(
                dividend_history["dividends"]
            )
        return dividend_history

    def download_dividend_history_multi(self):
        logger.info("Starting multiprocessing to downloading dividend data")
        tickers = list(self.yf_object.tickers.keys())
        with Pool(processes=self.n_processes) as pool:
            result_list = pool.map(self.get_dividend_history, tickers)
        for ticker, dividend_history in zip(tickers, result_list):
            self.data_dict[ticker] = dividend_history

    def store_data_dict_to_json(self):
        file_name = DATA_DICT_FILE
        logger.info("Storing data_dict to %s", file_name)
        data_to_json = {
            key: {
                "dividends": value["dividends"].to_json(date_format="iso")
                if "dividends" in value.keys()
                else None,
                "dividends per year": value["dividends per year"].to_json(
                    date_format="iso"
                )
                if "dividends per year" in value.keys()
                else None,
            }
            for key, value in self.data_dict.items()
        }

        with open(file_name, "w") as file:
            json.dump(data_to_json, file, indent=4)

    def load_data_dict_from_json(self):
        file_name = DATA_DICT_FILE
        logger.info("loading data_dict to %s", file_name)
        with open(file_name, "r") as file:
            self.loaded_dict = json.load(file)
        self.data_dict = {key: dict() for key in self.loaded_dict}
        for key in self.data_dict.keys():
            self.data_dict[key]["dividends"] = pd.Series(
                eval(self.loaded_dict[key]["dividends"]), dtype=np.float64
            )
            self.data_dict[key]["dividends"].index = self.data_dict[key][
                "dividends"
            ].index.map(lambda x: datetime.datetime.strptime(x[:10], "%Y-%M-%d"))
            self.data_dict[key]["dividends per year"] = pd.Series(
                eval(self.loaded_dict[key]["dividends per year"]), dtype=np.float64
            )

    @classmethod
    def get_dividends_per_year(cls, dividends):
        dividends_per_year = pd.Series(dtype=np.float64)
        if len(dividends) > 0:
            years = range(
                dividends.index.min().year + 1, dividends.index.max().year + 1
            )
            dividends_per_year_list = []
            years_list = []
            for year in years:
                years_list.append(year)
                dividends_per_year_list.append(
                    dividends[dividends.index.year == year].sum()
                )
            if len(dividends_per_year_list) > 0:
                dividends_per_year = pd.Series(
                    dividends_per_year_list, index=years_list
                )
        return dividends_per_year

    @classmethod
    def get_SP500_constituents(cls):
        """Downloads S&P 500 constituents from Wikipedia"""
        logger.info("Downloading all S&P 500 ticker from Wikipedia")
        payload = pd.read_html(
            "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        )
        sp500_tickers = payload[0]["Symbol"]
        sp500_tickers_dict = {"tickers": sp500_tickers.tolist()}
        return sp500_tickers_dict

    @classmethod
    def store_constituents_to_json(cls, constituents_dict, file_name):
        logger.info("Dumping constituents' ticker dictionary to %s", file_name)

        with open(file_name, "w") as file:
            json.dump(constituents_dict, file, indent=4)

    @classmethod
    def load_constituents_from_json(cls, file_name):
        logger.info("Loading constituents' ticker from %s", file_name)

        with open(file_name, "r") as file:
            constituents_dict = json.load(file)
        return constituents_dict


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--download_sp_500",
        help="If set downloads the consitutents of the S&P 500 index from Wikipedia under "
        + SP_500_TICKER_FILE,
        action="store_true",
    )
    parser.add_argument(
        "--n_security", help="Number of securities per portfolio", type=int, default=10
    )
    parser.add_argument(
        "--n_portfolio",
        help="Number of considered portfolios for analysis",
        type=int,
        default=100,
    )
    parser.add_argument(
        "-j",
        help="Number of allowed parallel processes for downloading",
        type=int,
        default=None,
    )
    parser.add_argument(
        "--update_dividends",
        help="If set, re-downloads all the dividends of the desired tickers and \
              stores them under data_dict.json. Otherwise loads the data_dict \
              from data_dict.json ",
        action="store_true",
    )
    args = parser.parse_args()
    if args.download_sp_500:
        sp_500_tickers = DividendAnalyzer.get_SP500_constituents()
        DividendAnalyzer.store_constituents_to_json(sp_500_tickers, SP_500_TICKER_FILE)
    else:
        sp_500_tickers = DividendAnalyzer.load_constituents_from_json(
            SP_500_TICKER_FILE
        )

    dividend_analyzer = DividendAnalyzer(
        sp_500_tickers["tickers"],
        n_security=args.n_security,
        n_portfolio=args.n_portfolio,
        n_processes=args.j,
    )
    if args.update_dividends:
        dividend_analyzer.download_dividend_history_multi()
        dividend_analyzer.store_data_dict_to_json()
    else:
        dividend_analyzer.load_data_dict_from_json()

    dividend_analyzer.randomize_portfolios()


if __name__ == "__main__":
    main()
