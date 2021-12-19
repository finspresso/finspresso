import argparse
import json
import logging

import coloredlogs

# import numpy as np
# import pandas as pd
# import pyqtgraph as pg
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
        municipality="Zürich",
        marital_status="single",
    ):
        self.tax_rates_file = tax_rates_file
        self.municipality = municipality
        self.marital_status = marital_status
        self.load_tax_rates()
        self.plotting_app = PlottingApp()

    def load_tax_rates(self):
        self.tax_rates_dict = dict()
        with open(self.tax_rates_file, "r") as read_file:
            self.tax_rates_dict = json.load(read_file)

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

    def plot_tax_per_income(self):
        self.plotting_app.show()
        # incomes_samples = pd.Series(np.linspace(0, 5 * 1e5, 1000))
        # tax_canton_dict = self.tax_rates_dict["canton"][self.marital_status]
        # tax_canton_df = pd.DataFrame(
        #     {
        #         "taxable income": tax_canton_dict["taxable income"],
        #         "tax_rate": tax_canton_dict["tax_rate"],
        #         "tax": tax_canton_dict["tax"],
        #     }
        # )

        # taxes_canton = incomes_samples.map(lambda x: self.get_tax(x, tax_canton_df))

        # # create plot
        # plt = pg.plot()
        # plt.showGrid(x=True, y=True)
        # plt.addLegend()

        # # set properties
        # plt.setLabel("left", "taxable income [CHF]")
        # plt.setLabel("bottom", "tax [CHF]")
        # plt.setWindowTitle("pyqtgraph plot")

        # # plot
        # plt.plot(
        #     incomes_samples,
        #     taxes_canton,
        #     pen=pg.mkPen("b", width=5),
        #     name="Base tax canton",
        # )


class PlottingApp(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.setWindowTitle("Taxes")
        self.main_layout = QtGui.QVBoxLayout()
        self.canton_cb = QtGui.QComboBox()
        self.canton_cb.addItems(["Java", "C#", "Python"])

        self.main_layout.addWidget(self.canton_cb)
        self.setLayout(self.main_layout)

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
    tax_withholder.plot_tax_per_income()
    sys.exit(app.exec_())

    #
    # pg.QtGui.QApplication.exec_()


if __name__ == "__main__":
    main()
