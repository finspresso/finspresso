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

coloredlogs.install()
logger_name = __name__ if __name__ != "__main__" else "witholding"
logger = logging.getLogger(logger_name)
logging.basicConfig(level=logging.DEBUG)


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
            combo_list=self.steuerfuss_dict,
            update_function=self.update_municipality_input,
        )
        self.update_plot_canton_taxes()
        self.update_municipality_input(self.municipality)
        # import pdb; pdb.set_trace()

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
        if self.plot_canton_taxes is None:
            self.plot_canton_taxes = self.plotting_app.plot_widget.plot(
                self.incomes_samples, self.taxes_canton, name="Tax Canton"
            )
        else:
            self.plot_canton_taxes.setData(self.incomes_samples, self.taxes_canton)

    def update_plot_municipality_taxes(self):
        pen = pg.mkPen(color=(200, 200, 255), width=1)
        if self.plot_municipality_taxes is None:
            self.plot_municipality_taxes = self.plotting_app.plot_widget.plot(
                self.incomes_samples,
                self.taxes_canton,
                name="Municipality tax",
                pen=pen,
            )
        else:
            self.plot_municipality_taxes.setData(
                self.incomes_samples, self.taxes_municipality
            )

    def update_municipality_input(self, value):
        self.municipality = value
        self.taxes_municipality = (
            self.taxes_canton * self.steuerfuss_dict.get(self.municipality) / 100
        )
        self.update_plot_municipality_taxes()


class PlottingApp(QtGui.QWidget):
    def __init__(self, combo_list=[], update_function=None):
        QtGui.QWidget.__init__(self)
        self.setWindowTitle("Taxes")
        self.main_layout = QtGui.QVBoxLayout()
        self.municipality_cb = QtGui.QComboBox()
        if combo_list:
            self.municipality_cb.addItems(combo_list)

        if update_function is not None:
            self.municipality_cb.currentTextChanged.connect(update_function)
        else:
            logger.warning("No update function specified.")

        self.main_layout.addWidget(self.municipality_cb)
        self.setLayout(self.main_layout)
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.addLegend()
        self.plot_widget.setBackground((255, 255, 255))
        self.main_layout.addWidget(self.plot_widget)

    def update_data(self, x, y):
        self.plot_widget.plot(x, y)

    # def municipality_cb_changed(self):
    #    print(str(self.municipality_cb.currentText()))

    #     self.central_layout = QtGui.QVBoxLayout()
    #     self.plot_boxes_layout = QtGui.QHBoxLayout()
    #     self.boxes_layout = QtGui.QVBoxLayout()
    #     self.setLayout(self.central_layout)

    #     # Lets create some widgets inside
    #     self.label = QtGui.QLabel('Taxes plots')

    #     # Here is the plot widget from pyqtgraph
    #     self.plot_widget = pg.PlotWidget()

    #     # Now the Check Boxes (lets make 3 of them)
    #     self.num = 6
    #     self.check_boxes = [QtGui.QCheckBox(f"Box {i+1}") for i in range(self.num)]

    #     # Here will be the data of the plot
    #     self.plot_data = [None for _ in range(self.num)]

    #     # Now we build the entire GUI
    #     self.central_layout.addWidget(self.label)
    #     self.central_layout.addLayout(self.plot_boxes_layout)
    #     self.plot_boxes_layout.addWidget(self.plot_widget)
    #     self.plot_boxes_layout.addLayout(self.boxes_layout)
    #     for i in range(self.num):
    #         self.boxes_layout.addWidget(self.check_boxes[i])
    #         # This will conect each box to the same action
    #         self.check_boxes[i].stateChanged.connect(self.box_changed)

    #     # For optimization let's create a list with the states of the boxes
    #     self.state = [False for _ in range(self.num)]

    #     # Make a list to save the data of each box
    #     self.box_data = [[[0], [0]] for _ in range(self.num)]
    #     x = np.linspace(0, 3.14, 100)
    #     self.add_data(x, np.sin(x), 0)
    #     self.add_data(x, np.cos(x), 1)
    #     self.add_data(x, np.sin(x)+np.cos(x), 2)
    #     self.add_data(x, np.sin(x)**2, 3)
    #     self.add_data(x, np.cos(x)**2, 4)
    #     self.add_data(x, x*0.2, 5)

    # def add_data(self, x, y, ind):
    #     self.box_data[ind] = [x, y]
    #     if self.plot_data[ind] is not None:
    #         self.plot_data[ind].setData(x, y)

    # def box_changed(self):
    #     for i in range(self.num):
    #         if self.check_boxes[i].isChecked() != self.state[i]:
    #             self.state[i] = self.check_boxes[i].isChecked()
    #             if self.state[i]:
    #                 if self.plot_data[i] is not None:
    #                     self.plot_widget.addItem(self.plot_data[i])
    #                 else:
    #                     self.plot_data[i] = self.plot_widget.plot(*self.box_data[i])
    #             else:
    #                 self.plot_widget.removeItem(self.plot_data[i])
    #             break


# if __name__ == "__main__":
#     app = QtGui.QApplication(sys.argv)
#     window = MyApp()
#     window.show()
#     sys.exit(app.exec_())


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

    #
    # pg.QtGui.QApplication.exec_()


if __name__ == "__main__":
    main()
