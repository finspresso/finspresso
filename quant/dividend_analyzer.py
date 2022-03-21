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


class DividendAnalyzer:
    def __init__(self):
        pass

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
        logger.info("Dumping constituents ticker dictionary to %s", file_name)

        with open(file_name, "w") as file:
            json.dump(constituents_dict, file, indent=4)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--download_sp_500",
        help="If set downloads the consitutents of the S&P 500 index from Wikipedia under sp_500_tickers.json",
        action="store_true",
    )
    args = parser.parse_args()
    if args.download_sp_500:
        sp_500_tickers = DividendAnalyzer.get_SP500_constituents()
        DividendAnalyzer.store_constituents_to_json(
            sp_500_tickers, "sp_500_tickers.json"
        )


if __name__ == "__main__":
    main()
