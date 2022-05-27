# 1: Create new option to select window called "RMSD overall" and add plot 2d histogram of rmsd per security # create example image
# Example:
# img = pg.ImageItem(image=np.eye(3), levels=(0,1) ) # create example image
# plot_widget = pg.PlotWidget()
# plot_widget.addItem(img)

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
from portfolio_math import portfolio_math

from pathlib import Path
from pyqtgraph.Qt import QtGui, QtCore

# Global settings
coloredlogs.install()
logger = logging.getLogger("portfolio_tracker")
logging.basicConfig(level=logging.DEBUG)
pg.setConfigOption("background", "w")
pg.setConfigOption("foreground", "k")


class TabWindow(QtGui.QTabWidget):
    def __init__(
        self, holdings_file="holdings.json", parent=None, rejection_threshold=50
    ):
        super(TabWindow, self).__init__(parent)
        self.averaging_names = [
            "rolling average dividend growth per year",
            "rolling average dividend growth per year (outlier rejection)",
            "rolling geometric average dividends growth per year",
            "rolling geometric average dividends growth per year (outlier rejection)",
            "rolling ema dividend growth per year",
            "rolling ema dividend growth per year (outlier rejection)",
        ]
        self.holdings_file = Path(holdings_file)
        self.rejection_threshold = rejection_threshold
        self.current_year = datetime.datetime.now().year
        self.average_years = [1, 2, 3, 4, 5]
        self.colorbar = None
        self.load_holdings()
        self.download_data_from_yahoo()
        self.tickers = [
            security["ticker"]
            for security in self.holdings_dict.values()
            if security["yfinance"]
        ]
        self.dividend_history = DividendHistory(
            combo_list_tickers=self.tickers,
            update_function=self.update_plots,
            update_average_years_function=self.update_dividend_average_years,
            update_mouse_function_dividend=self.update_tooltip_dividend,
            average_years=self.average_years,
            averaging_names=self.averaging_names,
        )
        self.dividend_history.average_years_checkbox[self.average_years[0]][
            "Checkbox"
        ].setChecked(True)
        self.update_plots()
        self.addTab(self.dividend_history, "Dividend history")

    def update_tooltip_dividend(self, evt):
        mousePoint = self.dividend_history.bar_plot_widget.plotItem.vb.mapSceneToView(
            evt
        )
        selected_ticker = self.dividend_history.security_cb.currentText()
        year, dividend = self.get_closest_point(
            mousePoint.x(),
            self.holdings_dict[selected_ticker]["dividends per year"],
        )
        self.dividend_history.bar_plot_widget.setToolTip(
            f"year: {year}, dividend: {round(dividend,2)}"
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

    @staticmethod
    def construct_estimation_dict():
        estimation_dict = {
            "estimate": dict(),
            "deviation": dict(),
            "rmsd": dict(),
        }
        return estimation_dict

    @staticmethod
    def dividend_outlier_rejection(dividends, rejection_threshold):
        dividends_without_outlier = dividends.copy()
        for year in dividends.index[1:]:
            dividends_without_outlier.loc[year] = dividends_without_outlier.loc[
                year - 1
            ]
            if dividends.loc[year - 1] > 0:
                growth = (
                    (dividends.loc[year] - dividends.loc[year - 1])
                    / dividends.loc[year - 1]
                    * 100
                )
                if np.abs(growth) <= rejection_threshold:
                    dividends_without_outlier.loc[year] = dividends.loc[year]
        return dividends_without_outlier

    def compute_dividend_growth_values(self):
        for security in self.holdings_dict.values():
            security["rmsd dataframe"] = pd.DataFrame(
                index=self.average_years,
                columns=self.averaging_names,
                data=0,
                dtype=float,
            )
            if security.get("yfinance", False):
                dividends_per_year = security["dividends per year"][
                    security["dividends per year"].index < self.current_year
                ]
                security["dividends per year growth"] = (
                    dividends_per_year.diff() / dividends_per_year.shift() * 100
                )
                security[
                    "dividends per year (outlier rejection)"
                ] = self.dividend_outlier_rejection(
                    dividends_per_year, self.rejection_threshold
                )
                security["dividends per year growth (outlier rejection)"] = (
                    security["dividends per year (outlier rejection)"].diff()
                    / security["dividends per year (outlier rejection)"].shift()
                    * 100
                )
                security["dividends per year growth diff"] = security[
                    "dividends per year growth"
                ].diff()

                for averaging_name in self.averaging_names:
                    security[averaging_name] = self.construct_estimation_dict()
                for year in self.average_years:
                    security["rolling average dividend growth per year"]["estimate"][
                        str(year)
                    ] = (
                        security["dividends per year growth"]
                        .rolling(year)
                        .mean()
                        .shift()
                    )
                    security[
                        "rolling average dividend growth per year (outlier rejection)"
                    ]["estimate"][str(year)] = (
                        security["dividends per year growth (outlier rejection)"]
                        .rolling(year)
                        .mean()
                        .shift()
                    )

                    security["rolling geometric average dividends growth per year"][
                        "estimate"
                    ][str(year)] = (
                        dividends_per_year.rolling(year)
                        .apply(lambda x: portfolio_math.get_geometric_mean(x))
                        .shift()
                    )
                    security[
                        "rolling geometric average dividends growth per year (outlier rejection)"
                    ]["estimate"][str(year)] = (
                        security["dividends per year (outlier rejection)"]
                        .rolling(year)
                        .apply(lambda x: portfolio_math.get_geometric_mean(x))
                        .shift()
                    )
                    security["rolling ema dividend growth per year"]["estimate"][
                        str(year)
                    ] = (
                        security["dividends per year growth"]
                        .rolling(year)
                        .apply(lambda x: portfolio_math.get_ema(x))
                        .shift()
                    )

                    security[
                        "rolling ema dividend growth per year (outlier rejection)"
                    ]["estimate"][str(year)] = (
                        security["dividends per year growth (outlier rejection)"]
                        .rolling(year)
                        .apply(lambda x: portfolio_math.get_ema(x))
                        .shift()
                    )
                    # Next
                    # 3) Add this quant to check whether this rmsd would be the beset
                    for averaging_name in self.averaging_names:
                        security[averaging_name]["deviation"][str(year)] = (
                            security[averaging_name]["estimate"][str(year)]
                            - security["dividends per year growth"]
                        )
                        security[averaging_name]["rmsd"][
                            str(year)
                        ] = portfolio_math.get_root_mean_square_deviation(
                            security[averaging_name]["deviation"][str(year)]
                        )
                        security[averaging_name]["deviation"][str(year)] = (
                            security[averaging_name]["estimate"][str(year)]
                            - security["dividends per year growth"]
                        )
                        security[averaging_name]["rmsd"][
                            str(year)
                        ] = portfolio_math.get_root_mean_square_deviation(
                            security[averaging_name]["deviation"][str(year)]
                        )
                        security["rmsd dataframe"].loc[year, averaging_name] = security[
                            averaging_name
                        ]["rmsd"][str(year)]

    @staticmethod
    def get_root_mean_square_deviation(x):
        rmsd = np.sqrt((x ** 2).mean())
        return rmsd

    @staticmethod
    def get_geometric_mean(x):
        n = x.shape[0] - 1
        x0 = x.iloc[0]
        x1 = x.iloc[-1]
        geometric_mean = (x1 / x0) ** (1 / n) - 1 if n > 0 else 0
        geometric_mean *= 100
        return geometric_mean

    @staticmethod
    def get_ema(x):
        N_ema = x.shape[0]
        alpha = 2 / (N_ema + 1)
        k = np.array(range(0, N_ema))
        weights = [alpha * (1 - alpha) ** p for p in k]
        weights = np.array(weights[::-1])
        ema = weights * x
        ema = ema.sum()
        return ema

    def update_plots(self):
        self.dividend_history.reenable_autoscale()
        self.update_plot_dividend_growth()
        self.update_dividend_bars()
        self.update_dividend_growth_diff_hist()
        self.update_rmsd_image()

    def update_dividend_average_years(self):
        self.update_plot_dividend_growth()

    def update_plot_dividend_growth(self):
        ticker = self.dividend_history.security_cb.currentText()
        self.dividend_history.plot_widget.clear()
        self.dividend_history.plot_widget.plotItem.legend.items = []
        self.dividend_history.plot_widget_diff.clear()
        self.dividend_history.plot_widget_diff.plotItem.legend.items = []
        # self.dividend_history.bar_plot_widget.clear()
        # self.dividend_history.bar_plot_widget.plotItem.legend.items = []
        # from PyQt5.QtCore import pyqtRemoveInputHook
        # pyqtRemoveInputHook()
        # import pdb; pdb.set_trace()
        pen = pg.mkPen(
            color="red",
            width=4,
        )
        self.plot_dividend_growth = self.dividend_history.plot_widget.plot(
            self.holdings_dict[ticker]["dividends per year growth"].index.values,
            self.holdings_dict[ticker]["dividends per year growth"].values,
            name="Real dividend growth",
            pen=pen,
            symbol="o",
            symbolSize=6,
        )
        if self.dividend_history.outlier_rejection_checkbox.isChecked():
            pen = pg.mkPen(color="red", width=2, style=QtCore.Qt.DotLine)
            self.dividend_history.plot_widget.plot(
                self.holdings_dict[ticker][
                    "dividends per year growth (outlier rejection)"
                ].index.values,
                self.holdings_dict[ticker][
                    "dividends per year growth (outlier rejection)"
                ].values,
                name="Real dividend growth (outlier rejection)",
                pen=pen,
                symbol="o",
                symbolSize=6,
            )

        if self.dividend_history.averaging_cb.currentText() == "Simple averaging":
            visible_averaging_values_key = "rolling average dividend growth per year"
        elif self.dividend_history.averaging_cb.currentText() == "Geometric averaging":
            visible_averaging_values_key = (
                "rolling geometric average dividends growth per year"
            )
        elif (
            self.dividend_history.averaging_cb.currentText()
            == "Exponential weighted averaging"
        ):
            visible_averaging_values_key = "rolling ema dividend growth per year"
        for year in self.dividend_history.average_years_checkbox.keys():
            if self.dividend_history.average_years_checkbox[year][
                "Checkbox"
            ].isChecked():

                x = self.holdings_dict[ticker][visible_averaging_values_key][
                    "estimate"
                ][str(year)].index.values
                y = self.holdings_dict[ticker][visible_averaging_values_key][
                    "estimate"
                ][str(year)].values
                pen = pg.mkPen(
                    color=self.dividend_history.average_years_checkbox[year]["Color"],
                    width=4,
                )
                self.dividend_history.plot_widget.plot(
                    x,
                    y,
                    name="Estimate: " + str(year) + " years window size",
                    pen=pen,
                    symbol="o",
                    symbolSize=6,
                )
                if self.dividend_history.outlier_rejection_checkbox.isChecked():
                    x = self.holdings_dict[ticker][
                        visible_averaging_values_key + " (outlier rejection)"
                    ]["estimate"][str(year)].index.values
                    y = self.holdings_dict[ticker][
                        visible_averaging_values_key + " (outlier rejection)"
                    ]["estimate"][str(year)].values
                    pen = pg.mkPen(
                        color=self.dividend_history.average_years_checkbox[year][
                            "Color"
                        ],
                        width=2,
                        style=QtCore.Qt.DotLine,
                    )
                    self.dividend_history.plot_widget.plot(
                        x,
                        y,
                        name="Estimate (outlier rejection): "
                        + str(year)
                        + " years window size",
                        pen=pen,
                        symbol="o",
                        symbolSize=6,
                    )
                x = self.holdings_dict[ticker][visible_averaging_values_key][
                    "deviation"
                ][str(year)].index.values
                y_diff = self.holdings_dict[ticker][visible_averaging_values_key][
                    "deviation"
                ][str(year)].values
                self.dividend_history.plot_widget_diff.plot(
                    x,
                    y_diff,
                    name="Estimate - Real: " + str(year) + " years window size",
                    pen=pen,
                    symbol="o",
                    symbolSize=6,
                )
        self.update_rmsd_bars(visible_averaging_values_key, ticker)

    def update_dividend_bars(self):
        ticker = self.dividend_history.security_cb.currentText()
        self.dividend_history.bar_plot_widget.clear()
        security = self.holdings_dict[ticker]
        desired_width = 0.6
        if self.dividend_history.outlier_rejection_checkbox.isChecked():
            desired_width = 0.3
        x = security["dividends per year"][
            security["dividends per year"].index < self.current_year
        ].index.values
        y = security["dividends per year"][
            security["dividends per year"].index < self.current_year
        ].values
        bargraph = pg.BarGraphItem(
            x=x, height=y, width=desired_width, brush="g", name="Dividends"
        )  # TODO: Ensure that current year does not show in bar graph
        self.dividend_history.bar_plot_widget.addItem(bargraph)
        if self.dividend_history.outlier_rejection_checkbox.isChecked():
            x = security["dividends per year (outlier rejection)"][
                security["dividends per year (outlier rejection)"].index
                < self.current_year
            ].index.values
            x = x + 0.33
            y = security["dividends per year (outlier rejection)"][
                security["dividends per year (outlier rejection)"].index
                < self.current_year
            ].values
            bargraph2 = pg.BarGraphItem(
                x=x,
                height=y,
                width=desired_width,
                brush="r",
                name="Dividends (outlier rejection)",
            )  # TODO: Ensure that current year does not show in bar graph
            self.dividend_history.bar_plot_widget.addItem(bargraph2)

    def update_rmsd_image(self):
        self.dividend_history.plot_widget_rmsd_overall.clear()
        ticker = self.dividend_history.security_cb.currentText()
        security = self.holdings_dict[ticker]
        self.dividend_history.rmsd_plot_widget.clear()
        considered_names = security["rmsd dataframe"].columns
        if not self.dividend_history.outlier_rejection_checkbox.isChecked():
            considered_names = [
                col
                for col in security["rmsd dataframe"].columns
                if "outlier" not in col
            ]
        rmsd_overall = security["rmsd dataframe"][considered_names]
        self.dividend_history.setup_rmsd_overall_plot(considered_names)
        img = pg.ImageItem(image=rmsd_overall.values)
        self.dividend_history.plot_widget_rmsd_overall.addItem(img)
        max_val = rmsd_overall.replace([np.inf, -np.inf], np.nan).max().max()
        min_val = rmsd_overall.replace([np.inf, -np.inf], np.nan).min().min()
        if not np.isnan(max_val) and not np.isnan(
            min_val
        ):  # Next improve color to match the one from quant + axis description as in quant
            if self.colorbar is None:
                cm = pg.colormap.get("plasma")
                cm.reverse()
                self.colorbar = pg.ColorBarItem(cmap=cm)
            self.colorbar.setImageItem(
                img,
                insert_in=self.dividend_history.plot_widget_rmsd_overall.getPlotItem(),
            )
            self.colorbar.setLevels(low=min_val, high=max_val)

    def update_rmsd_bars(self, visible_averaging_values_key, ticker):
        self.dividend_history.rmsd_plot_widget.clear()
        if self.dividend_history.rmsd_plot_widget.plotItem.legend is not None:
            self.dividend_history.rmsd_plot_widget.plotItem.legend.items = []
        x = [
            int(key)
            for key in self.holdings_dict[ticker][visible_averaging_values_key][
                "rmsd"
            ].keys()
        ]
        y = list(
            self.holdings_dict[ticker][visible_averaging_values_key]["rmsd"].values()
        )
        bargraph_rmsd = pg.BarGraphItem(x=x, height=y, width=0.6, brush="g")
        self.dividend_history.rmsd_plot_widget.addItem(bargraph_rmsd)

    def update_dividend_growth_diff_hist(self):
        ticker = self.dividend_history.security_cb.currentText()
        self.dividend_history.histogram_variance_widget.clear()
        security = self.holdings_dict[ticker]
        boolean_vec = (
            security["dividends per year growth diff"].index < self.current_year
        ) & (np.isfinite(security["dividends per year growth diff"]))
        vals = security["dividends per year growth diff"][boolean_vec].values
        y, x = np.histogram(vals, bins=len(vals))
        curve = pg.PlotCurveItem(x, y, stepMode=True, fillLevel=0, brush=(255, 100, 0))
        self.dividend_history.histogram_variance_widget.addItem(curve)

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


class DividendHistory(QtGui.QWidget):
    def __init__(
        self,
        combo_list_tickers=[],
        update_function=None,
        update_average_years_function=None,
        update_mouse_function_dividend=None,
        average_years=[1, 2, 3, 4, 5],
        averaging_names=[""],
    ):
        QtGui.QWidget.__init__(self)
        self.setGeometry(100, 100, 1200, 900)
        self.main_layout = QtGui.QVBoxLayout()
        self.top_layout = QtGui.QFormLayout()
        self.security_cb = QtGui.QComboBox()
        self.averaging_cb = QtGui.QComboBox()
        self.averaging_cb.addItems(
            [
                "Simple averaging",
                "Geometric averaging",
                "Exponential weighted averaging",
            ]
        )
        self.second_figure_cb = QtGui.QComboBox()
        self.second_figure_cb.addItems(
            [
                "Bar chart: Dividends paid",
                "Histogram: Delta dividend growth rate",
                "Difference: Estimate - Real",
                "Bar chart: Root-mean-square deviation",
                "RMSD overall",
                "None",
            ]
        )
        self.outlier_rejection_checkbox = QtGui.QCheckBox("Show outlier rejection")
        self.second_figure_cb.currentTextChanged.connect(self.update_second_figure)
        self.average_years = average_years
        self.averaging_names = averaging_names
        if combo_list_tickers:
            self.security_cb.addItems(combo_list_tickers)
        self.top_layout.addRow("Security:", self.security_cb)
        self.top_layout.addRow("Averaging method:", self.averaging_cb)
        self.create_average_layout(average_years, update_average_years_function)
        self.top_layout.addRow("Averaging years:", self.average_years_layout)
        self.top_layout.addRow("Outlier Rejection:", self.outlier_rejection_checkbox)
        self.top_layout.addRow("Second figure:", self.second_figure_cb)
        self.plot_widget = pg.PlotWidget()
        label_style = {"font-size": "20px"}
        self.plot_widget.addLegend(labelTextSize="14pt", offset=(10, 10))
        self.plot_widget.setLabel("bottom", "Year", **label_style)
        self.plot_widget.setLabel("left", "dividend growth rate %", **label_style)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.4)
        self.plot_widget_diff = pg.PlotWidget()
        self.plot_widget_diff.addLegend(labelTextSize="14pt", offset=(10, 10))
        self.plot_widget_diff.setLabel("bottom", "Year", **label_style)
        self.plot_widget_diff.setLabel(
            "left", "Deviation dividend growth rate %", **label_style
        )
        self.plot_widget_diff.showGrid(x=True, y=True, alpha=0.4)
        self.bar_plot_widget = pg.PlotWidget()
        self.bar_plot_widget.setLabel("bottom", "Year", **label_style)
        self.bar_plot_widget.setLabel(
            "left", "[USD]", **label_style
        )  # TODO: Make it adaptive depending on currency
        self.bar_plot_widget.addLegend(labelTextSize="14pt", offset=(10, 10))
        self.bar_plot_widget.showGrid(x=False, y=True, alpha=0.4)
        self.rmsd_plot_widget = pg.PlotWidget()
        self.rmsd_plot_widget.setLabel("bottom", "Averaging Years", **label_style)
        self.rmsd_plot_widget.setLabel(
            "left", "Root-mean-square deviation %", **label_style
        )
        self.rmsd_plot_widget.showGrid(x=False, y=True, alpha=0.4)
        if update_function is not None:
            self.security_cb.currentTextChanged.connect(update_function)
            self.averaging_cb.currentTextChanged.connect(update_function)
            self.outlier_rejection_checkbox.stateChanged.connect(update_function)
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

        self.plot_widget_rmsd_overall = pg.PlotWidget()

        self.second_figure_dict = {
            "Bar chart: Dividends paid": self.bar_plot_widget,
            "Histogram: Delta dividend growth rate": self.histogram_variance_widget,
            "Difference: Estimate - Real": self.plot_widget_diff,
            "Bar chart: Root-mean-square deviation": self.rmsd_plot_widget,
            "RMSD overall": self.plot_widget_rmsd_overall,
            "None": None,
        }
        self.current_second_figure = "Bar chart: Dividends paid"
        self.setLayout(self.main_layout)

    def setup_rmsd_overall_plot(self, considered_names):
        ax = self.plot_widget_rmsd_overall.getAxis("bottom")
        ay = self.plot_widget_rmsd_overall.getAxis("left")
        xlabel_tick_names = [str(name) + "y" for name in self.average_years]
        ylabel_tick_names = [
            " ".join(x.split()[:2])
            + "\n"
            + " ".join(x.split()[2:4])
            + "\n"
            + " ".join(x.split()[4:])
            for x in considered_names
        ]
        nx = len(xlabel_tick_names)
        ny = len(ylabel_tick_names)
        xlabel_tick_positions = [x + 0.5 for x in np.arange(nx)]
        ylabel_tick_positions = [y + 0.5 for y in np.arange(ny)]
        ax.setTicks(
            [
                [
                    (pos, name)
                    for pos, name in zip(xlabel_tick_positions, xlabel_tick_names)
                ]
            ]
        )
        ay.setTicks(
            [
                [
                    (pos, name)
                    for pos, name in zip(ylabel_tick_positions, ylabel_tick_names)
                ]
            ]
        )
        self.plot_widget_rmsd_overall.getPlotItem().setTitle(
            "Root mean square deviation (RMSD)"
        )

    def reenable_autoscale(self):
        self.plot_widget.enableAutoRange()
        self.plot_widget.setAutoVisible(x=True, y=True)
        self.plot_widget_diff.enableAutoRange()
        self.plot_widget_diff.setAutoVisible(x=True, y=True)

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
        logger.debug(f"Second plot changed to {desired_plot}")
        if self.second_figure_dict[self.current_second_figure] is not None:
            self.second_figure_dict[self.current_second_figure].setParent(None)
        self.current_second_figure = desired_plot
        if desired_plot != "None":
            self.main_layout.addWidget(
                self.second_figure_dict[self.current_second_figure]
            )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--holdings_file",
        help="JSON file containing portfolio holdings",
        default="holdings.json",
    )
    args = parser.parse_args()
    app = QtGui.QApplication(sys.argv)
    tab_window = TabWindow(holdings_file=args.holdings_file)
    tab_window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
