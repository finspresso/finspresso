# 1: Create new option to select window called "RMSD overall" and add plot 2d histogram of rmsd per security # create example image
# Example:
# img = pg.ImageItem(image=np.eye(3), levels=(0,1) ) # create example image
# plot_widget = pg.PlotWidget()
# plot_widget.addItem(img)

import argparse
import asyncio
import datetime
import yfinance as yf
import pyqtgraph as pg
import numpy as np
import json
import locale
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

NA = "NA"


class TabWindow(QtGui.QTabWidget):
    def __init__(
        self,
        holdings_file="holdings.json",
        parent=None,
        rejection_threshold=50,
        async_download=True,
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
        self.async_download = async_download
        self.load_holdings()
        self.download_data_from_yahoo()
        self.get_portfolio_overview()
        self.compute_dividend_growth_values()
        self.tickers = [security["ticker"] for security in self.holdings_dict.values()]
        self.dividend_history = DividendHistory(
            combo_list_tickers=self.tickers,
            update_function=self.update_plots,
            update_average_years_function=self.update_dividend_average_years,
            update_mouse_function_dividend=self.update_tooltip_dividend,
            average_years=self.average_years,
            averaging_names=self.averaging_names,
        )
        self.portfolio_widget = Portfolio(
            self.holdings_dict, self.portfolio_overview_dict
        )
        self.dividend_history.average_years_checkbox[self.average_years[0]][
            "Checkbox"
        ].setChecked(True)
        self.update_plots()
        self.addTab(self.portfolio_widget, "Portfolio")
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
        self.get_conversion_rates()
        if self.async_download:
            yahoo_data = asyncio.run(self.download_data_from_yahoo_async())
            for (
                ticker,
                dividends,
                dividends_per_year,
                dividends_trailing,
                last_price,
            ) in yahoo_data:
                conversion_rate = 1
                if self.holdings_dict[ticker]["currency"] == "USD":
                    conversion_rate = self.conversion_rate_dict["CHF-USD"].values[0]
                self.holdings_dict[ticker]["dividends"] = dividends * conversion_rate
                self.holdings_dict[ticker]["dividends per year"] = (
                    dividends_per_year * conversion_rate
                )
                self.holdings_dict[ticker]["dividends TTM"] = (
                    dividends_trailing * conversion_rate
                )
                self.holdings_dict[ticker]["last price"] = last_price * conversion_rate
                self.holdings_dict[ticker]["dividend yield TTM"] = (
                    self.holdings_dict[ticker]["dividends TTM"]
                    / self.holdings_dict[ticker]["last price"].values[0]
                )
                self.holdings_dict[ticker]["aggregated dividends TTM"] = (
                    self.holdings_dict[ticker]["dividends TTM"]
                    * self.holdings_dict[ticker]["quantity"]
                    * conversion_rate
                )
                self.holdings_dict[ticker]["market value"] = (
                    last_price
                    * self.holdings_dict[ticker]["quantity"]
                    * conversion_rate
                )
        else:
            self.download_data_from_yahoo_list()

    def get_conversion_rates(self):
        self.conversion_rate_dict = {"CHF-USD": 1}
        self.conversion_rate_dict["CHF-USD"] = self.get_last_price_yahoo("CHFUSD=X")
        self.conversion_rate_dict["EUR-USD"] = self.get_last_price_yahoo("EURUSD=X")

    def get_portfolio_overview(self):
        self.portfolio_overview_dict = {
            "market value": 0,
            "weighted dividend yield (TTM)": 0,
            "aggregated dividends (TTM)": 0,
            "n_holdings": len(self.holdings_dict.keys()),
        }
        for ticker in self.holdings_dict.keys():
            self.portfolio_overview_dict["market value"] += self.holdings_dict[ticker][
                "market value"
            ]
            self.portfolio_overview_dict["weighted dividend yield (TTM)"] += (
                self.holdings_dict[ticker]["market value"]
                * self.holdings_dict[ticker]["dividend yield TTM"]
            )
            self.portfolio_overview_dict[
                "aggregated dividends (TTM)"
            ] += self.holdings_dict[ticker]["aggregated dividends TTM"]
        self.portfolio_overview_dict["weighted dividend yield (TTM)"] = (
            self.portfolio_overview_dict["weighted dividend yield (TTM)"]
            / self.portfolio_overview_dict["market value"]
            * 100
        )

    async def download_data_from_yahoo_async(self):
        tasks = []
        for security in self.holdings_dict.values():
            tasks.append(self.download_data_from_yahoo_single(security["ticker"]))
        yahoo_data = await asyncio.gather(*tasks)
        return yahoo_data

    async def download_data_from_yahoo_single(self, ticker):
        logger.info("Downloading data for ticker {}".format(ticker))
        yf_ticker = yf.Ticker(ticker)
        dividends = yf_ticker.dividends
        dividends_per_year = self.get_dividends_per_year(dividends)
        dividends_trailing = self.get_trailing_dividends(dividends, trailing_days=365)
        last_price = self.get_last_price_yahoo(ticker)
        return (
            ticker,
            dividends,
            dividends_per_year,
            dividends_trailing,
            last_price,
        )

    def download_data_from_yahoo_list(self):
        for security in self.holdings_dict.values():
            conversion_rate = 1
            if security["currency"] == "CHF":
                conversion_rate = self.conversion_rate_dict["CHF-USD"].values[0]
            elif security["currency"] == "EUR":
                conversion_rate = self.conversion_rate_dict["EUR-USD"].values[0]
            logger.info("Downloading data for security {}".format(security["name"]))
            yf_ticker = yf.Ticker(security["ticker"])
            security["dividends"] = yf_ticker.dividends * conversion_rate
            security["dividends per year"] = (
                self.get_dividends_per_year(security["dividends"]) * conversion_rate
            )
            security["dividends TTM"] = (
                self.get_trailing_dividends(security["dividends"], trailing_days=365)
                * conversion_rate
            )
            security["last price"] = (
                self.get_last_price_yahoo(security["ticker"]) * conversion_rate
            )

    def get_last_price_yahoo(self, ticker):
        last_price = yf.Ticker(ticker).history(period="1d")["Close"]
        return last_price

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

    @staticmethod
    def get_growth_zero_crossings(dividends_per_year):
        growth = dividends_per_year.diff() / dividends_per_year.shift() * 100
        growth = growth.iloc[1:]
        growth_diff = growth + growth.diff().shift(-1)
        zero_crossings = growth_diff[growth.values > 0] < 0
        zero_crossings = zero_crossings[zero_crossings]
        zero_crossings[:] = 0.0
        zero_crossings = zero_crossings.astype(float)
        return zero_crossings

    def compute_dividend_growth_values(self):
        for security in self.holdings_dict.values():
            security["rmsd dataframe"] = pd.DataFrame(
                index=self.average_years,
                columns=self.averaging_names,
                data=0,
                dtype=float,
            )
            dividends_per_year = security["dividends per year"][
                security["dividends per year"].index < self.current_year
            ]
            security["zero crossings"] = self.get_growth_zero_crossings(
                dividends_per_year
            )
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
                ] = (security["dividends per year growth"].rolling(year).mean().shift())
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

                security["rolling ema dividend growth per year (outlier rejection)"][
                    "estimate"
                ][str(year)] = (
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
        if not self.holdings_dict[ticker]["zero crossings"].empty:
            self.plot_dividend_growth = self.dividend_history.plot_widget.plot(
                self.holdings_dict[ticker]["zero crossings"].index.values,
                self.holdings_dict[ticker]["zero crossings"].values,
                name="Zero crossings",
                pen=None,
                symbol="x",
                symbolPen="k",
                symbolSize=8,
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
        dividends_per_year = NA
        if not dividends.empty:
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
            dividends_per_year = pd.Series(dividends_per_year_list, index=years_list)
        return dividends_per_year

    @staticmethod
    def get_trailing_dividends(dividends, trailing_days=365):
        last_considered_day = datetime.datetime.now() - datetime.timedelta(
            days=trailing_days
        )
        dividends_trailing = 0
        valid_dates = dividends.index > last_considered_day
        if valid_dates.any():
            dividends_trailing = dividends[dividends.index > last_considered_day].sum()
        return dividends_trailing

    def print(self):
        print(self.holdings_dict)


class Portfolio(QtGui.QTabWidget):
    def __init__(self, holdings_dict, portfolio_overview_dict, parent=None):
        super(Portfolio, self).__init__(parent)
        self.holdings_dict = holdings_dict
        self.portfolio_overview_dict = portfolio_overview_dict
        self.portfolio_widget = PortfolioHoldings(self.holdings_dict)
        self.portfolio_overview = PortfolioOverview(self.portfolio_overview_dict)
        self.addTab(self.portfolio_overview, "Portfolio Overview")
        self.addTab(self.portfolio_widget, "Portfolio Holdings")


class PortfolioOverview(QtGui.QWidget):
    def __init__(self, portfolio_overview_dict):
        QtGui.QWidget.__init__(self)
        self.portfolio_overview_dict = portfolio_overview_dict
        self.create_table_widget_overview()
        self.main_layout_overview = QtGui.QVBoxLayout()
        self.main_layout_overview.addWidget(self.table_widget_overview)
        self.setLayout(self.main_layout_overview)

    def create_table_widget_overview(self):
        self.table_widget_overview = QtGui.QTableWidget(self)
        self.table_widget_overview.setMinimumWidth(2000)
        self.table_widget_overview.setMinimumHeight(500)
        self.table_widget_overview.setRowCount(4)
        self.table_widget_overview.setColumnCount(1)
        self.table_widget_overview.setVerticalHeaderLabels(
            [
                "Number of securities",
                "Market value [USD]",
                "Weighted dividend yield (TTM) [%]",
                "Aggregated dividends (TTM) [USD]",
            ]
        )
        self.table_widget_overview.setItem(
            0,
            0,
            QtGui.QTableWidgetItem(str(self.portfolio_overview_dict["n_holdings"])),
        )
        self.table_widget_overview.setItem(
            1,
            0,
            QtGui.QTableWidgetItem(
                locale.format_string(
                    "%.0f",
                    self.portfolio_overview_dict["market value"].values[0],
                    grouping=True,
                )
            ),
        )
        self.table_widget_overview.setItem(
            2,
            0,
            QtGui.QTableWidgetItem(
                str(
                    round(
                        self.portfolio_overview_dict[
                            "weighted dividend yield (TTM)"
                        ].values[0],
                        2,
                    )
                )
            ),
        )
        self.table_widget_overview.setItem(
            3,
            0,
            QtGui.QTableWidgetItem(
                locale.format_string(
                    "%.0f",
                    self.portfolio_overview_dict["aggregated dividends (TTM)"],
                    grouping=True,
                )
            ),
        )
        self.table_widget_overview.resizeColumnsToContents()
        self.table_widget_overview.resizeRowsToContents()
        self.table_widget_overview.show()


class PortfolioHoldings(QtGui.QWidget):
    def __init__(self, holdings_dict):
        self.holdings_dict = holdings_dict
        QtGui.QWidget.__init__(self)

        self.create_table_widget()
        self.main_layout = QtGui.QVBoxLayout()
        self.main_layout.addWidget(self.table_widget)
        self.setLayout(self.main_layout)

    def create_table_widget(self):
        self.table_widget = QtGui.QTableWidget(self)
        self.table_widget.setMinimumWidth(2000)
        self.table_widget.setMinimumHeight(500)
        self.table_widget.setRowCount(len(self.holdings_dict.keys()))
        self.table_widget.setColumnCount(10)
        self.table_widget.setHorizontalHeaderLabels(
            [
                "Name",
                "Ticker",
                "Currency",
                "Quantity",
                "Last price [USD]",
                "Last trading day",
                "Market value [USD]",
                "Dividend paid/share (TTM) [USD]",
                "Aggregated dividend (TTM) [USD]",
                "Dividend yield (TTM)",
            ]
        )
        row = 0
        for security in self.holdings_dict.values():
            self.table_widget.setItem(row, 0, QtGui.QTableWidgetItem(security["name"]))
            self.table_widget.setItem(
                row, 1, QtGui.QTableWidgetItem(security["ticker"])
            )
            self.table_widget.setItem(
                row, 2, QtGui.QTableWidgetItem(security["currency"])
            )
            self.table_widget.setItem(
                row, 3, QtGui.QTableWidgetItem(str(security["quantity"]))
            )
            self.table_widget.setItem(
                row,
                4,
                QtGui.QTableWidgetItem(str(round(security["last price"].values[0], 2))),
            )
            self.table_widget.setItem(
                row,
                5,
                QtGui.QTableWidgetItem(
                    security["last price"].index[0].strftime("%Y-%m-%d")
                ),
            )
            self.table_widget.setItem(
                row,
                6,
                QtGui.QTableWidgetItem(
                    locale.format_string(
                        "%.0f", security["market value"].values[0], grouping=True
                    )
                ),
            )
            dividend_trailing = security["dividends TTM"]
            dividend_yield_trailing = (
                security["dividends TTM"] / security["last price"].values[0]
            )
            trailing_aggregated_dividend = security["aggregated dividends TTM"]
            self.table_widget.setItem(
                row,
                7,
                QtGui.QTableWidgetItem(str(round(dividend_trailing, 4))),
            )
            self.table_widget.setItem(
                row,
                8,
                QtGui.QTableWidgetItem(
                    locale.format_string(
                        "%.1f", trailing_aggregated_dividend, grouping=True
                    )
                ),
            )
            self.table_widget.setItem(
                row,
                9,
                QtGui.QTableWidgetItem(
                    str(round(dividend_yield_trailing * 100, 2)) + "%"
                ),
            )
            row += 1
        self.table_widget.resizeColumnsToContents()
        self.table_widget.resizeRowsToContents()
        self.table_widget.show()


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

# Next: 1) Add option to include offline dividend inputs value via .json2)Make GUI that shows dividend for portfolio and estimate of next year based on filter technique
