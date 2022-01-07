# Next plot the growths of dividends per holding
import argparse
import yfinance as yf
import pyqtgraph as pg
import json
import logging
import coloredlogs
import sys
import pandas as pd


from pathlib import Path
from pyqtgraph.Qt import QtGui

# Global settings
coloredlogs.install()
logger_name = "portfolio_tracker"
logger = logging.getLogger(logger_name)
logging.basicConfig(level=logging.DEBUG)
pg.setConfigOption("background", "w")
pg.setConfigOption("foreground", "k")


class DividendProjector:
    def __init__(self, holdings_file="holdings.json"):
        self.holdings_file = Path(holdings_file)
        self.load_holdings()
        self.download_data_from_yahoo()
        self.tickers = [
            security["ticker"]
            for security in self.holdings_dict["securities"]
            if security["yfinance"]
        ]
        self.plotting_app = PlottingApp(combo_list=self.tickers)

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


class PlottingApp(QtGui.QWidget):
    def __init__(self, combo_list=[]):
        QtGui.QWidget.__init__(self)
        self.setGeometry(100, 100, 1200, 900)
        self.main_layout = QtGui.QVBoxLayout()
        self.security_cb = QtGui.QComboBox()
        if combo_list:
            combo_list.sort()
            self.security_cb.addItems(combo_list)
        self.plot_widget = pg.PlotWidget()
        import numpy as np

        x = np.linspace(0, 50)
        y = 5 * x
        name = "example"
        self.update_data(x, y, name)
        self.main_layout.addWidget(self.security_cb)
        self.main_layout.addWidget(self.plot_widget)
        self.setLayout(self.main_layout)

    def update_data(self, x, y, name):
        self.plot_widget.clear()
        if self.plot_widget.plotItem.legend is not None:
            self.plot_widget.plotItem.legend.items = []
        self.plot_widget.plot(x, y, name=name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--holdings_file",
        help="JSON file containing portfolio holdings",
        default="holdings.json",
    )
    args = parser.parse_args()
    app = QtGui.QApplication(sys.argv)
    dividend_projector = DividendProjector(holdings_file=args.holdings_file)
    dividend_projector.plotting_app.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
