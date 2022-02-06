# 1. Next make plot that allows
# 2.Next plot the growths of dividends per holding, Add combobox to get the number of years back + add option for geometric mean
import argparse
import datetime
import yfinance as yf
import pyqtgraph as pg
import numpy as np
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
        self.average_years = [1, 2, 3, 4, 5]
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
            update_mouse_function_dividend=self.update_tooltip_dividend,
            average_years=self.average_years,
        )
        self.plotting_app.average_years_checkbox[self.average_years[0]][
            "Checkbox"
        ].setChecked(True)
        self.update_plots(self.plotting_app.security_cb.currentText())

    def update_tooltip_dividend(self, evt):
        mousePoint = self.plotting_app.bar_plot_widget.plotItem.vb.mapSceneToView(evt)
        year, dividend = self.get_closest_point(
            mousePoint.x(),
            self.holdings_dict[self.selected_ticker]["dividends per year"],
        )
        self.plotting_app.bar_plot_widget.setToolTip(
            f"year: {year}, dividend: {dividend}"
        )

    @staticmethod
    def get_closest_point(target_point, data_series):
        diff_series = pd.Series(
            data_series.index.values - target_point, index=data_series.index
        )
        x = diff_series.abs().idxmin()
        y = data_series.loc[x]
        return (x, y)

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
        self.compute_dividend_growth_values()

    def compute_dividend_growth_values(self):
        for security in self.holdings_dict.values():
            if security.get("yfinance", False):
                dividends_per_year = security["dividends per year"][
                    security["dividends per year"].index < self.current_year
                ]
                security["dividends per year growth"] = (
                    dividends_per_year.diff() / dividends_per_year.shift() * 100
                )
                security["dividends per year growth diff"] = security[
                    "dividends per year growth"
                ].diff()
                security["dividends per year growth lp"] = dict()
                for year in self.average_years:
                    security["dividends per year growth lp"][str(year)] = (
                        security["dividends per year growth"].rolling(year).mean()
                    )

    def update_plots(self, ticker):
        self.selected_ticker = ticker
        self.update_plot_dividend_growth(ticker)
        self.update_dividend_bars(ticker)
        self.update_dividend_growth_diff_hist(ticker)

    def update_dividend_average_years(self, value):
        self.update_plot_dividend_growth(self.plotting_app.security_cb.currentText())

    def update_plot_dividend_growth(self, ticker):
        self.plotting_app.plot_widget.clear()
        self.plotting_app.plot_widget.plotItem.legend.items = []
        pen = pg.mkPen(color=[255, 0, 0], width=4)
        # from PyQt5.QtCore import pyqtRemoveInputHook
        # pyqtRemoveInputHook()
        # import pdb; pdb.set_trace()
        # if self.plotting_app.plot_widget.plotItem.legend is not None:
        for year in self.plotting_app.average_years_checkbox.keys():
            if self.plotting_app.average_years_checkbox[year]["Checkbox"].isChecked():
                x = self.holdings_dict[ticker]["dividends per year growth lp"][
                    str(year)
                ].index.values
                y = self.holdings_dict[ticker]["dividends per year growth lp"][
                    str(year)
                ].values
                pen = pg.mkPen(
                    color=self.plotting_app.average_years_checkbox[year]["Color"],
                    width=4,
                )
                self.plot_dividend_growth = self.plotting_app.plot_widget.plot(
                    x,
                    y,
                    name="Dividens per year growth lp: " + str(year),
                    pen=pen,
                    symbol="o",
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
        )  # TODO: Ensure that current year does not show in bar graph
        self.plotting_app.bar_plot_widget.addItem(bargraph)

    def update_dividend_growth_diff_hist(self, ticker):
        self.plotting_app.histogram_variance_widget.clear()
        security = self.holdings_dict[ticker]
        boolean_vec = (
            security["dividends per year growth diff"].index < self.current_year
        ) & (np.isfinite(security["dividends per year growth diff"]))
        vals = security["dividends per year growth diff"][boolean_vec].values
        y, x = np.histogram(vals, bins=len(vals))
        curve = pg.PlotCurveItem(x, y, stepMode=True, fillLevel=0, brush=(255, 100, 0))
        self.plotting_app.histogram_variance_widget.addItem(curve)

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
        self,
        combo_list=[],
        update_function=None,
        update_average_years_function=None,
        update_mouse_function_dividend=None,
        average_years=[1, 2, 3, 4, 5],
    ):
        QtGui.QWidget.__init__(self)
        self.setGeometry(100, 100, 1200, 900)
        self.main_layout = QtGui.QVBoxLayout()
        self.top_layout = QtGui.QFormLayout()
        self.security_cb = QtGui.QComboBox()
        self.second_figure_cb = QtGui.QComboBox()
        self.second_figure_cb.addItems(
            ["Bar chart: Dividens paid", "Histogram: Delta dividend growth rate"]
        )
        self.second_figure_cb.currentTextChanged.connect(self.update_second_figure)
        if combo_list:
            combo_list.sort()
            self.security_cb.addItems(combo_list)
        self.top_layout.addRow("Security:", self.security_cb)
        self.create_average_layout(average_years, update_average_years_function)
        self.top_layout.addRow("Averaging years:", self.average_years_layout)
        self.top_layout.addRow("Second figure:", self.second_figure_cb)
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.addLegend()
        self.plot_widget.setLabel("bottom", "year")
        self.plot_widget.setLabel("left", "dividend growth rate %")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.4)
        self.bar_plot_widget = pg.PlotWidget()
        self.bar_plot_widget.setLabel("bottom", "year")
        self.bar_plot_widget.setLabel(
            "left", "absolute dividend [USD]"
        )  # TODO: Make it adaptive depending on currency
        self.bar_plot_widget.showGrid(x=False, y=True, alpha=0.4)
        if update_function is not None:
            self.security_cb.currentTextChanged.connect(update_function)
        self.main_layout.addLayout(self.top_layout)
        self.main_layout.addWidget(self.plot_widget)
        self.main_layout.addWidget(self.bar_plot_widget)
        if update_mouse_function_dividend is not None:
            self.bar_plot_widget.scene().sigMouseMoved.connect(
                update_mouse_function_dividend
            )
        self.histogram_variance_widget = pg.PlotWidget()
        self.histogram_variance_widget.setLabel(
            "bottom", "delta in dividend growth year by year in %"
        )
        self.histogram_variance_widget.setLabel("left", "#")
        self.histogram_variance_widget.showGrid(x=False, y=True, alpha=0.4)

        self.second_figure_dict = {
            "Bar chart: Dividens paid": self.bar_plot_widget,
            "Histogram: Delta dividend growth rate": self.histogram_variance_widget,
        }
        self.current_second_figure = "Bar chart: Dividens paid"
        self.setLayout(self.main_layout)

    def create_average_layout(self, average_years, update_average_years_function):
        rng = np.random.default_rng(seed=42)

        self.average_years_layout = QtGui.QHBoxLayout()
        self.average_years_checkbox = dict()
        for year in average_years:
            self.average_years_checkbox[year] = dict()
            self.average_years_checkbox[year]["Checkbox"] = QtGui.QCheckBox(str(year))
            self.average_years_layout.addWidget(
                self.average_years_checkbox[year]["Checkbox"]
            )
            self.average_years_checkbox[year]["Checkbox"].stateChanged.connect(
                update_average_years_function
            )
            self.average_years_checkbox[year]["Color"] = rng.integers(
                low=0, high=255, size=3
            ).tolist()

    def update_second_figure(self, desired_plot):
        logger.info(f"Second plot changed to {desired_plot}")
        self.second_figure_dict[self.current_second_figure].setParent(None)
        self.current_second_figure = desired_plot
        self.main_layout.addWidget(self.second_figure_dict[self.current_second_figure])


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
