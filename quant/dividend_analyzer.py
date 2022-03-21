import argparse
import coloredlogs
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
        payload = pd.read_html(
            "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        )
        import pdb

        pdb.set_trace()
        sp500_tickers = payload[0]["Symbol"]
        return sp500_tickers


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
        logger.info(sp_500_tickers)


if __name__ == "__main__":
    main()
