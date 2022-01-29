# 1. Next make plot that allows
# 2.Next plot the growths of dividends per holding, Add combobox to get the number of years back + add option for geometric mean
import argparse
import datetime
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
    def __init__(
        self, holdings_file="holdings.json", window_size=3, geometric_mean_horizon=5
    ):
        self.holdings_file = Path(holdings_file)
        self.window_size = window_size
        self.geometric_mean_horizon = geometric_mean_horizon
        self.current_year = datetime.datetime.now().year
        self.load_holdings()
        self.download_data_from_yahoo()
        self.tickers = [
            security["ticker"]
            for security in self.holdings_dict.values()
            if security["yfinance"]
        ]
        self.plotting_app = PlottingApp(
            combo_list=self.tickers,
            update_function=self.update_plots,
            update_average_years_function=self.update_dividend_average_years,
        )
        self.plotting_app.average_years_cb.setCurrentText(str(self.window_size))
        self.update_plots(self.plotting_app.security_cb.currentText())

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
                dividends_per_year = security["dividends per year"][
                    security["dividends per year"].index < self.current_year
                ]
                security["dividends per year growth"] = (
                    dividends_per_year.diff() / dividends_per_year.shift() * 100
                )
                security["dividends per year growth lp"] = (
                    security["dividends per year growth"].rolling(window_size).mean()
                )

    def update_plots(self, ticker):
        self.update_plot_dividend_growth(ticker)
        self.update_dividend_bars(ticker)

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

    def update_dividend_bars(self, ticker):
        self.plotting_app.bar_plot_widget.clear()
        security = self.holdings_dict[ticker]
        x = security["dividends per year"][
            security["dividends per year"].index < self.current_year
        ].index.values
        y = security["dividends per year"][
            security["dividends per year"].index < self.current_year
        ].values
        bargraph = pg.BarGraphItem(
            x=x, height=y, width=0.6, brush="g"
        )  # ToDo: Ensure that current year does not show in bar graph
        self.plotting_app.bar_plot_widget.addItem(bargraph)

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
        self.top_layout = QtGui.QFormLayout()
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
        self.top_layout.addRow("Security:", self.security_cb)
        self.top_layout.addRow("Number of years for average:", self.average_years_cb)
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.addLegend()
        self.plot_widget.setLabel("bottom", "year")
        self.plot_widget.setLabel("left", "dividend growth rate %")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.4)
        self.bar_plot_widget = pg.PlotWidget()
        if update_function is not None:
            self.security_cb.currentTextChanged.connect(update_function)
        self.main_layout.addLayout(self.top_layout)
        self.main_layout.addWidget(self.plot_widget)
        self.main_layout.addWidget(self.bar_plot_widget)
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
