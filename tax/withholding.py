import argparse
import json
import logging

import coloredlogs

import numpy as np
import pandas as pd
import pyqtgraph as pg

# Next make GUI combobox to select the municipality and then it shows graph for base tax and total tax based on selected municpality and selected data
import sys
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
    ):
        self.tax_rates_file = tax_rates_file
        self.steuerfuss_file = steuerfuss_file
        self.municipality = municipality
        self.marital_status = marital_status
        self.plot_canton_taxes = None
        self.plot_municipality_taxes = None
        self.load_tax_rates()
        self.load_steuerfuss()
        self.compute_canton_taxes()
        self.plotting_app = PlottingApp(
            combo_list=[*self.steuerfuss_dict],
            update_function=self.update_municipality_input,
            selected_combobox_list=self.municipality,
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

    def get_tax(self, income, tax_df):
        index_ref = tax_df[tax_df["taxable income"] < income].last_valid_index()
        tax = 0
        if index_ref is not None:
            residual = income - tax_df.loc[index_ref, "taxable income"]
            tax = (
                tax_df.loc[index_ref, "tax"]
                + tax_df.loc[index_ref, "tax_rate"] * residual / 1e2
            )
        return tax

    def compute_canton_taxes(self):
        self.incomes_samples = pd.Series(np.linspace(0, 5 * 1e5, 1000))
        tax_canton_dict = self.tax_rates_dict["canton"][self.marital_status]
        tax_canton_df = pd.DataFrame(
            {
                "taxable income": tax_canton_dict["taxable income"],
                "tax_rate": tax_canton_dict["tax_rate"],
                "tax": tax_canton_dict["tax"],
            }
        )
        self.taxes_canton = self.incomes_samples.map(
            lambda x: self.get_tax(x, tax_canton_df)
        )

    def update_plot_canton_taxes(self):
        pen = pg.mkPen(color="g", width=4)
        self.plot_canton_taxes = self.plotting_app.plot_widget.plot(
            self.incomes_samples, self.taxes_canton, name="Tax canton", pen=pen
        )

    def update_plot_municipality_taxes(self):
        pen = pg.mkPen(color="r", width=4)
        self.plot_municipality_taxes = self.plotting_app.plot_widget.plot(
            self.incomes_samples,
            self.taxes_municipality,
            name="Tax municipality (Steuerfuss: "
            + str(self.steuerfuss_municipality)
            + ")",
            pen=pen,
        )

    def update_municipality_input(self, value):
        self.municipality = value
        self.plotting_app.plot_widget.clear()
        self.plotting_app.plot_widget.plotItem.legend.items = []
        self.steuerfuss_municipality = self.steuerfuss_dict.get(self.municipality)
        self.taxes_municipality = self.taxes_canton * self.steuerfuss_municipality / 100
        self.update_plot_municipality_taxes()
        self.update_plot_canton_taxes()


class PlottingApp(QtGui.QWidget):
    def __init__(
        self, combo_list=[], selected_combobox_list=None, update_function=None
    ):
        QtGui.QWidget.__init__(self)
        self.setWindowTitle("Taxes")
        self.main_layout = QtGui.QVBoxLayout()
        self.municipality_cb = QtGui.QComboBox()
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
        self.plot_widget.addLegend()
        self.plot_widget.showGrid(x=True, y=True, alpha=0.4)
        self.plot_widget.setLabel("bottom", "taxable income [CHF]")
        self.plot_widget.setLabel("left", "tax [CHF]")
        self.main_layout.addWidget(self.plot_widget)

    def update_data(self, x, y):
        self.plot_widget.plot(x, y)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tax_rates_file",
        help="Path to to .json file containing tax rates of cantons and federation",
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
    args = parser.parse_args()

    app = QtGui.QApplication(sys.argv)
    tax_withholder = TaxWithholder(
        tax_rates_file=args.tax_rates_file,
        municipality=args.municipality,
        marital_status=args.marital_status,
    )
    tax_withholder.plotting_app.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
