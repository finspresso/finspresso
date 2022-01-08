# Next plot the growths of dividends per holding, Add combobox to get the number of years back + add option for geometric mean
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
    def __init__(self, holdings_file="holdings.json", window_size=3):
        self.holdings_file = Path(holdings_file)
        self.window_size = window_size
        self.load_holdings()
        self.download_data_from_yahoo()
        self.tickers = [
            security["ticker"]
            for security in self.holdings_dict.values()
            if security["yfinance"]
        ]
        self.plotting_app = PlottingApp(
            combo_list=self.tickers,
            update_function=self.update_plot_dividend_growth,
            update_average_years_function=self.update_dividend_average_years,
        )
        self.plotting_app.average_years_cb.setCurrentText(str(self.window_size))
        self.update_plot_dividend_growth(self.plotting_app.security_cb.currentText())

    def load_holdings(self):
        with self.holdings_file.open("r") as file:
            holdings_dict_loaded = json.load(file)
            self.holdings_dict = {
                security["ticker"]: security
                for security in holdings_dict_loaded["securities"]
            }

    def download_data_from_yahoo(self):
        for security in self.holdings_dict.values():
            if security.get("yfinance", False):
                logger.info("Downloading data for security {}".format(security["name"]))
                security["dividends"] = yf.Ticker(security["ticker"]).dividends
                security["dividends per year"] = self.get_dividends_per_year(
                    security["dividends"]
                )
        self.compute_dividend_growth_values(self.window_size)

    def compute_dividend_growth_values(self, window_size):
        for security in self.holdings_dict.values():
            if security.get("yfinance", False):
                security["dividends per year growth"] = (
                    security["dividends per year"].diff()
                    / security["dividends per year"].shift()
                )
                security["dividends per year growth lp"] = (
                    security["dividends per year growth"].rolling(window_size).mean()
                )

    def update_dividend_average_years(self, value):
        self.compute_dividend_growth_values(int(value))
        self.update_plot_dividend_growth(self.plotting_app.security_cb.currentText())

    def update_plot_dividend_growth(self, ticker):
        self.plotting_app.plot_widget.clear()
        # from PyQt5.QtCore import pyqtRemoveInputHook
        # pyqtRemoveInputHook()
        # import pdb; pdb.set_trace()
        # if self.plotting_app.plot_widget.plotItem.legend is not None:
        self.plotting_app.plot_widget.plotItem.legend.items = []
        pen = pg.mkPen(color="b", width=4)
        x = self.holdings_dict[ticker]["dividends per year growth lp"].index.values
        y = self.holdings_dict[ticker]["dividends per year growth lp"].values
        self.plot_dividend_growth = self.plotting_app.plot_widget.plot(
            x, y, name="Dividens per year growth lp", pen=pen, symbol="o"
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
    def __init__(
        self, combo_list=[], update_function=None, update_average_years_function=None
    ):
        QtGui.QWidget.__init__(self)
        self.setGeometry(100, 100, 1200, 900)
        self.main_layout = QtGui.QVBoxLayout()
        self.security_cb = QtGui.QComboBox()
        if combo_list:
            combo_list.sort()
            self.security_cb.addItems(combo_list)
        self.average_years_cb = QtGui.QComboBox()
        self.average_years_cb.addItems(["1", "2", "3", "4", "5"])
        if update_average_years_function is not None:
            self.average_years_cb.currentTextChanged.connect(
                update_average_years_function
            )
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.addLegend()
        self.plot_widget.showGrid(x=True, y=True, alpha=0.4)
        if update_function is not None:
            self.security_cb.currentTextChanged.connect(update_function)
        self.main_layout.addWidget(self.security_cb)
        self.main_layout.addWidget(self.average_years_cb)
        self.main_layout.addWidget(self.plot_widget)
        self.setLayout(self.main_layout)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--holdings_file",
        help="JSON file containing portfolio holdings",
        default="holdings.json",
    )
    parser.add_argument(
        "--window_size",
        help="Size of window in year for average of dividend growth",
        default=3,
        type=int,
    )
    args = parser.parse_args()
    app = QtGui.QApplication(sys.argv)
    dividend_projector = DividendProjector(
        holdings_file=args.holdings_file, window_size=args.window_size
    )
    dividend_projector.plotting_app.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
