import argparse
import coloredlogs
import json
import pandas as pd
import logging
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

# Global settings
coloredlogs.install()
logger_name = "dividend_analyzer"
logger = logging.getLogger(logger_name)
logging.basicConfig(level=logging.DEBUG)
SP_500_TICKER_FILE = "sp_500_tickers.json"


class DividendAnalyzer:
    def __init__(self, tickers, n_security=10, n_portfolio=100):
        self.tickers = tickers
        self.n_security = n_security
        self.n_portfolio = n_portfolio

    @classmethod
    def get_SP500_constituents(self):
        """Downloads S&P 500 constituents from Wikipedia"""
        logger.info("Downloading all S&P 500 ticker from Wikipedia")
        payload = pd.read_html(
            "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        )
        sp500_tickers = payload[0]["Symbol"]
        sp500_tickers_dict = {"tickers": sp500_tickers.tolist()}
        return sp500_tickers_dict

    @classmethod
    def store_constituents_to_json(self, constituents_dict, file_name):
        logger.info("Dumping constituents' ticker dictionary to %s", file_name)

        with open(file_name, "w") as file:
            json.dump(constituents_dict, file, indent=4)

    @classmethod
    def load_constituents_from_json(self, file_name):
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
    args = parser.parse_args()
    if args.download_sp_500:
        sp_500_tickers = DividendAnalyzer.get_SP500_constituents()
        DividendAnalyzer.store_constituents_to_json(sp_500_tickers, SP_500_TICKER_FILE)
    else:
        sp_500_tickers = DividendAnalyzer.load_constituents_from_json(
            SP_500_TICKER_FILE
        )

    DividendAnalyzer(
        sp_500_tickers, n_security=args.n_security, n_portfolio=args.n_portfolio
    )


if __name__ == "__main__":
    main()
