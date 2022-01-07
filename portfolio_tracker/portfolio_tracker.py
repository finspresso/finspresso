# Next plot the growths of dividends per holding
import argparse
import yfinance as yf
import json
import logging
import coloredlogs
import pandas as pd


from pathlib import Path

# Global settings
coloredlogs.install()
logger_name = "portfolio_tracker"
logger = logging.getLogger(logger_name)
logging.basicConfig(level=logging.DEBUG)


class DividendProjector:
    def __init__(self, holdings_file="holdings.json"):
        self.holdings_file = Path(holdings_file)
        self.load_holdings()
        self.download_data_from_yahoo()

    def load_holdings(self):
        with self.holdings_file.open("r") as file:
            self.holdings_dict = json.load(file)

    def download_data_from_yahoo(self):
        for security in self.holdings_dict["securities"]:
            if security.get("yfinance", False):
                logger.info("Downloading data for security {}".format(security["name"]))
                security["dividends"] = yf.Ticker(security["ticker"]).dividends
                security["dividends per year"] = self.get_dividends_per_year(
                    security["dividends"]
                )
                security["dividends per year growth"] = (
                    security["dividends per year"].diff()
                    / security["dividends per year"].shift()
                )
                security["dividends per year growth lp"] = (
                    security["dividends per year growth"].rolling(4).mean()
                )

    @staticmethod
    def get_dividends_per_year(dividends):
        years = range(dividends.index.min().year + 1, dividends.index.max().year + 1)
        dividends_per_year_list = []
        years_list = []
        for year in years:
            years_list.append(year)
            dividends_per_year_list.append(
                dividends[dividends.index.year == year].sum()
            )
        dividends_per_year = pd.Series(dividends_per_year_list, index=years_list)
        return dividends_per_year

    def print(self):
        print(self.holdings_dict)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--holdings_file",
        help="JSON file containing portfolio holdings",
        default="holdings.json",
    )
    args = parser.parse_args()
    dividend_projector = DividendProjector(holdings_file=args.holdings_file)
    dividend_projector.print()


if __name__ == "__main__":
    main()
