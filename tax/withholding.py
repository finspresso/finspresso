import argparse
import json
import logging

import coloredlogs

import numpy as np
import pandas as pd
import pyqtgraph as pg

# Next make GUI combobox to select the municipality and then it shows graph for base tax and total tax based on selected municpality and selected data
import sys
from pathlib import Path
from PyQt5.QtCore import Qt
from pyqtgraph.Qt import QtGui

# Global settings
coloredlogs.install()
logger_name = __name__ if __name__ != "__main__" else "witholding"
logger = logging.getLogger(logger_name)
logging.basicConfig(level=logging.DEBUG)

pg.setConfigOption("background", "w")
pg.setConfigOption("foreground", "k")


class TaxWithholder:
    def __init__(
        self,
        tax_rates_file="2020/tax_rates.json",
        steuerfuss_file="2020/steuerfuss.json",
        municipality="Zürich",
        marital_status="single",
        storage_folder="storage_json",
        store_only=False,
    ):
        self.tax_rates_file = tax_rates_file
        self.steuerfuss_file = steuerfuss_file
        self.municipality = municipality
        self.marital_status = marital_status
        self.storage_folder = Path(storage_folder)
        self.plot_canton_taxes = None
        self.plot_municipality_taxes = None
        self.incomes_samples = pd.Series(np.linspace(0, 2.5 * 1e5, 1000))
        self.load_tax_rates()
        self.load_steuerfuss()
        self.taxes_canton = self.compute_taxes(
            self.tax_rates_dict["canton"][self.marital_status], self.incomes_samples
        )
        self.taxes_federal = self.compute_taxes(
            self.tax_rates_dict["federal"][self.marital_status], self.incomes_samples
        )
        if not store_only:
            self.plotting_app = PlottingApp(
                combo_list=[*self.steuerfuss_dict],
                update_function=self.update_municipality_input,
                selected_combobox_list=self.municipality,
                update_mouse_function_upper=self.update_mouse_cursor,
                update_mouse_function_lower=self.update_mouse_cursor_rate,
            )
            self.update_municipality_input(self.municipality)

    def load_tax_rates(self):
        self.tax_rates_dict = dict()
        with open(self.tax_rates_file, "r") as read_file:
            self.tax_rates_dict = json.load(read_file)

    def load_steuerfuss(self):
        self.steuerfuss_dict = dict()
        with open(self.steuerfuss_file, "r") as read_file:
            self.steuerfuss_dict = json.load(read_file)

    def update_plot_canton_taxes(self):
        pen = pg.mkPen(color="g", width=4)
        self.plot_canton_taxes = self.plotting_app.plot_widget.plot(
            self.taxes_canton.index, self.taxes_canton, name="Tax canton", pen=pen
        )
        self.plot_canton_taxes.setCursor(self.plotting_app.cursor)

    def update_plot_federal_taxes(self):
        pen = pg.mkPen(color="b", width=4)
        self.plot_federal_taxes = self.plotting_app.plot_widget.plot(
            self.taxes_federal.index, self.taxes_federal, name="Tax federal", pen=pen
        )

    def update_plot_total_taxes(self):
        pen = pg.mkPen(color="k", width=4)
        self.plot_total_taxes = self.plotting_app.plot_widget.plot(
            self.taxes_total.index, self.taxes_total, name="Tax total", pen=pen
        )

    def update_plot_municipality_taxes(self):
        pen = pg.mkPen(color="r", width=4)
        self.plot_municipality_taxes = self.plotting_app.plot_widget.plot(
            self.taxes_municipality.index,
            self.taxes_municipality,
            name="Tax municipality (Steuerfuss: "
            + str(self.steuerfuss_municipality)
            + ")",
            pen=pen,
        )

    def update_plot_canton_taxes_rate(self):
        pen = pg.mkPen(color="g", width=4)
        self.plot_canton_taxes_rate = self.plotting_app.plot_widget_tax_rate.plot(
            self.taxes_canton_rate.index,
            self.taxes_canton_rate,
            name="Tax canton rate",
            pen=pen,
        )

    def update_plot_federal_taxes_rate(self):
        pen = pg.mkPen(color="b", width=4)
        self.plot_federal_taxes_rate = self.plotting_app.plot_widget_tax_rate.plot(
            self.taxes_federal_rate.index,
            self.taxes_federal_rate,
            name="Tax federal rate",
            pen=pen,
        )

    def update_plot_total_taxes_rate(self):
        pen = pg.mkPen(color="k", width=4)
        self.plot_total_taxes_rate = self.plotting_app.plot_widget_tax_rate.plot(
            self.taxes_total_rate.index,
            self.taxes_total_rate,
            name="Tax total rate",
            pen=pen,
        )

    def update_plot_municipality_taxes_rate(self):
        pen = pg.mkPen(color="r", width=4)
        self.plot_municipality_taxes_rate = self.plotting_app.plot_widget_tax_rate.plot(
            self.taxes_municipality_rate.index,
            self.taxes_municipality_rate,
            name="Tax municipality rate (Steuerfuss: "
            + str(self.steuerfuss_municipality)
            + ")",
            pen=pen,
        )

    def update_tax_values(self):
        self.steuerfuss_municipality = self.steuerfuss_dict.get(self.municipality)
        self.taxes_municipality = self.taxes_canton * self.steuerfuss_municipality / 100
        self.taxes_total = (
            self.taxes_federal + self.taxes_canton + self.taxes_municipality
        )
        self.taxes_canton_rate = self.taxes_canton / self.taxes_canton.index * 100
        self.taxes_municipality_rate = (
            self.taxes_municipality / self.taxes_municipality.index * 100
        )
        self.taxes_federal_rate = self.taxes_federal / self.taxes_federal.index * 100
        self.taxes_total_rate = self.taxes_total / self.taxes_total.index * 100

    def create_storage_folder(self):
        self.storage_folder.mkdir(parents=True, exist_ok=True)

    def store_tax_values(self):
        import pdb

        pdb.set_trace()
        for municipality in self.steuerfuss_dict.keys():
            self.municipality = municipality
            self.update_tax_values()
            file_name = municipality + ".json"
            file_json = self.storage_folder / file_name
            out_dict = {
                "labels": self.taxes_total_rate.index.values.tolist(),
                "datasets": [
                    {"label": "tax rate", "data": self.taxes_total_rate.tolist()}
                ],
            }

            with file_json.open("w") as outfile:
                json.dump(out_dict, outfile, indent=4)

    def store_tax_rates_to_json(self):
        self.create_storage_folder()
        self.store_tax_values()

    def update_municipality_input(self, value):
        self.municipality = value
        self.plotting_app.plot_widget.clear()
        self.plotting_app.plot_widget_tax_rate.clear()
        self.plotting_app.plot_mouse_points = None
        self.plotting_app.plot_mouse_points_rate = None
        self.plotting_app.plot_widget.addItem(self.plotting_app.cursor_label)
        self.plotting_app.plot_widget_tax_rate.addItem(
            self.plotting_app.cursor_rate_label
        )
        self.plotting_app.plot_widget.plotItem.legend.items = []
        self.plotting_app.plot_widget_tax_rate.plotItem.legend.items = []
        self.update_tax_values()
        self.update_plot_municipality_taxes()
        self.update_plot_canton_taxes()
        self.update_plot_federal_taxes()
        self.update_plot_total_taxes()
        self.update_plot_municipality_taxes_rate()
        self.update_plot_canton_taxes_rate()
        self.update_plot_federal_taxes_rate()
        self.update_plot_total_taxes_rate()

    def update_mouse_cursor(self, evt):
        mousePoint = self.plotting_app.plot_widget.plotItem.vb.mapSceneToView(evt)
        if (
            mousePoint.x() <= self.taxes_canton.index[-1]
            and mousePoint.x() >= self.taxes_canton.index[0]
        ):
            x_tax_canton, y_tax_canton = self.get_closest_point(
                mousePoint.x(), self.taxes_canton
            )
            x_tax_municipality, y_tax_municipality = self.get_closest_point(
                mousePoint.x(), self.taxes_municipality
            )
            x_tax_federal, y_tax_federal = self.get_closest_point(
                mousePoint.x(), self.taxes_federal
            )
            x_tax_total, y_tax_total = self.get_closest_point(
                mousePoint.x(), self.taxes_total
            )
            self.plotting_app.mouse_points["x"] = [
                x_tax_canton,
                x_tax_municipality,
                x_tax_federal,
                x_tax_total,
            ]
            self.plotting_app.mouse_points["y"] = [
                y_tax_canton,
                y_tax_municipality,
                y_tax_federal,
                y_tax_total,
            ]
            self.plotting_app.cursor_label_text = (
                f"Taxable income: {np.round(x_tax_canton)}\n"
                + f"Tax municipality: {np.round(y_tax_municipality)}\n"
                + f"Tax canton: {np.round(y_tax_canton)}\n"
                + f"Tax federal: {np.round(y_tax_federal)}\n"
                + f"Tax total: {np.round(y_tax_total)}\n"
            )
            self.plotting_app.update_mouse_points()

    def update_mouse_cursor_rate(self, evt):
        mousePoint = self.plotting_app.plot_widget_tax_rate.plotItem.vb.mapSceneToView(
            evt
        )
        if (
            mousePoint.x() <= self.taxes_canton_rate.index[-1]
            and mousePoint.x() >= self.taxes_canton_rate.index[0]
        ):
            x_tax_canton, y_tax_canton = self.get_closest_point(
                mousePoint.x(), self.taxes_canton_rate
            )
            x_tax_municipality, y_tax_municipality = self.get_closest_point(
                mousePoint.x(), self.taxes_municipality_rate
            )
            x_tax_federal, y_tax_federal = self.get_closest_point(
                mousePoint.x(), self.taxes_federal_rate
            )
            x_tax_total, y_tax_total = self.get_closest_point(
                mousePoint.x(), self.taxes_total_rate
            )
            self.plotting_app.mouse_points_rate["x"] = [
                x_tax_canton,
                x_tax_municipality,
                x_tax_federal,
                x_tax_total,
            ]
            self.plotting_app.mouse_points_rate["y"] = [
                y_tax_canton,
                y_tax_municipality,
                y_tax_federal,
                y_tax_total,
            ]
            self.plotting_app.cursor_rate_label_text = (
                f"Taxable income: {np.round(x_tax_canton, 1)}\n"
                + f"Tax municipality rate: {np.round(y_tax_municipality, 1)}%\n"
                + f"Tax canton rate: {np.round(y_tax_canton, 1)}%\n"
                + f"Tax federal rate: {np.round(y_tax_federal, 1)}%\n"
                + f"Tax total rate: {np.round(y_tax_total, 1)}%\n"
            )
            self.plotting_app.update_mouse_points_rate()

    @staticmethod
    def get_closest_point(target_point, data_series):
        diff_series = pd.Series(
            data_series.index.values - target_point, index=data_series.index
        )
        x = diff_series.abs().idxmin()
        y = data_series.loc[x]
        return (x, y)

    @classmethod
    def compute_taxes(cls, tax_dict, incomes_samples):
        tax_df = pd.DataFrame(
            {
                "taxable income": tax_dict["taxable income"],
                "tax rate": tax_dict["tax rate"],
                "tax": tax_dict["tax"],
            }
        )
        taxes = incomes_samples.map(lambda x: cls.get_tax(x, tax_df))
        taxes.index = incomes_samples
        return taxes

    @classmethod
    def get_tax(self, income, tax_df):
        index_ref = tax_df[tax_df["taxable income"] < income].last_valid_index()
        tax = 0
        if index_ref is not None:
            residual = income - tax_df.loc[index_ref, "taxable income"]
            tax = (
                tax_df.loc[index_ref, "tax"]
                + tax_df.loc[index_ref, "tax rate"] * residual / 1e2
            )
        return tax


class PlottingApp(QtGui.QWidget):
    def __init__(
        self,
        combo_list=[],
        selected_combobox_list=None,
        update_function=None,
        update_mouse_function_upper=None,
        update_mouse_function_lower=None,
    ):
        QtGui.QWidget.__init__(self)
        self.setWindowTitle("Taxes")
        self.setGeometry(100, 100, 1200, 900)
        self.main_layout = QtGui.QVBoxLayout()
        self.municipality_cb = QtGui.QComboBox()
        self.mouse_points = {"x": None, "y": None}
        self.plot_mouse_points = None
        self.mouse_points_rate = {"x": None, "y": None}
        self.plot_mouse_points_rate = None
        if combo_list:
            combo_list.sort()
            self.municipality_cb.addItems(combo_list)
        if selected_combobox_list is not None:
            self.municipality_cb.setCurrentText(selected_combobox_list)

        if update_function is not None:
            self.municipality_cb.currentTextChanged.connect(update_function)
        else:
            logger.warning("No update function specified.")

        self.main_layout.addWidget(self.municipality_cb)
        self.setLayout(self.main_layout)
        self.plot_widget = pg.PlotWidget()
        self.cursor_label = pg.TextItem(anchor=(0, 2))
        self.cursor_label_text = "-"
        self.cursor_label.setText(self.cursor_label_text)
        self.plot_widget.addLegend()
        self.plot_widget.showGrid(x=True, y=True, alpha=0.4)
        self.plot_widget.setLabel("bottom", "taxable income [CHF]")
        self.plot_widget.setLabel("left", "tax [CHF]")
        self.cursor = Qt.CrossCursor
        self.plot_widget.setCursor(self.cursor)
        self.main_layout.addWidget(self.plot_widget)

        self.plot_widget_tax_rate = pg.PlotWidget()
        self.plot_widget_tax_rate.addLegend()
        self.plot_widget_tax_rate.showGrid(x=True, y=True, alpha=0.4)
        self.plot_widget_tax_rate.setLabel("bottom", "taxable income [CHF]")
        self.plot_widget_tax_rate.setLabel("left", "rate %")
        self.cursor_rate = Qt.CrossCursor
        self.cursor_rate_label = pg.TextItem(anchor=(0, 2))
        self.cursor_rate_label_text = "-"
        self.cursor_rate_label.setText(self.cursor_rate_label_text)
        self.plot_widget_tax_rate.setCursor(self.cursor_rate)
        self.main_layout.addWidget(self.plot_widget_tax_rate)

        if update_mouse_function_upper is not None:
            self.plot_widget.scene().sigMouseMoved.connect(update_mouse_function_upper)
        if update_mouse_function_lower is not None:
            self.plot_widget_tax_rate.scene().sigMouseMoved.connect(
                update_mouse_function_lower
            )

    def update_mouse_points(self):
        if self.mouse_points["x"] is not None and self.mouse_points["y"] is not None:
            if self.plot_mouse_points is None:
                self.plot_mouse_points = self.plot_widget.plot(
                    self.mouse_points["x"], self.mouse_points["y"], pen=None, symbol="x"
                )
            else:
                self.plot_mouse_points.setData(
                    self.mouse_points["x"], self.mouse_points["y"]
                )
            self.cursor_label.setText(self.cursor_label_text)

    def update_mouse_points_rate(self):
        if (
            self.mouse_points_rate["x"] is not None
            and self.mouse_points_rate["y"] is not None
        ):
            if self.plot_mouse_points_rate is None:
                self.plot_mouse_points_rate = self.plot_widget_tax_rate.plot(
                    self.mouse_points_rate["x"],
                    self.mouse_points_rate["y"],
                    pen=None,
                    symbol="x",
                )
            else:
                self.plot_mouse_points_rate.setData(
                    self.mouse_points_rate["x"], self.mouse_points_rate["y"]
                )
            self.cursor_rate_label.setText(self.cursor_rate_label_text)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tax_rates_file",
        help="Path to to .json file containing tax rates of cantons and federal",
        default="2020/tax_rates.json",
    )
    parser.add_argument(
        "--municipality",
        help='The municipality for which the "Steuerfuss" is assumed',
        default="Zürich",
    )
    parser.add_argument(
        "--marital_status",
        help="Martial status [single, married]",
        default="single",
        choices=["single", "married"],
    )

    parser.add_argument(
        "--json",
        help="If selected the data will not be visualized but it will store all the relevant tax rates in .json file",
        action="store_true",
    )
    args = parser.parse_args()

    app = QtGui.QApplication(sys.argv)
    tax_withholder = TaxWithholder(
        tax_rates_file=args.tax_rates_file,
        municipality=args.municipality,
        marital_status=args.marital_status,
        store_only=args.json,
    )
    if args.json:
        tax_withholder.store_tax_rates_to_json()
    else:
        tax_withholder.plotting_app.show()
        sys.exit(app.exec_())


if __name__ == "__main__":
    main()
