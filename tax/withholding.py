import argparse
import json
import logging

import coloredlogs

import numpy as np
import pandas as pd
import pyqtgraph as pg

# Next make GUI combobox to select the municipality and then it shows graph for base tax and total tax based on selected municpality and selected data
import sys
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
    ):
        self.tax_rates_file = tax_rates_file
        self.steuerfuss_file = steuerfuss_file
        self.municipality = municipality
        self.marital_status = marital_status
        self.plot_canton_taxes = None
        self.plot_municipality_taxes = None
        self.incomes_samples = pd.Series(np.linspace(0, 5 * 1e5, 1000))
        self.load_tax_rates()
        self.load_steuerfuss()
        self.taxes_canton = self.compute_taxes(
            self.tax_rates_dict["canton"][self.marital_status], self.incomes_samples
        )
        self.taxes_federal = self.compute_taxes(
            self.tax_rates_dict["federal"][self.marital_status], self.incomes_samples
        )
        self.plotting_app = PlottingApp(
            combo_list=[*self.steuerfuss_dict],
            update_function=self.update_municipality_input,
            selected_combobox_list=self.municipality,
            update_mouse_function=self.update_mouse_cursor,
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

    def update_municipality_input(self, value):
        self.municipality = value
        self.plotting_app.plot_widget.clear()
        self.plotting_app.plot_mouse_points = None
        self.plotting_app.plot_widget.addItem(self.plotting_app.cursorlabel)
        self.plotting_app.plot_widget.plotItem.legend.items = []
        self.steuerfuss_municipality = self.steuerfuss_dict.get(self.municipality)
        self.taxes_municipality = self.taxes_canton * self.steuerfuss_municipality / 100
        self.update_plot_municipality_taxes()
        self.update_plot_canton_taxes()
        self.update_plot_federal_taxes()

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
            self.plotting_app.mouse_points["x"] = [
                x_tax_canton,
                x_tax_municipality,
                x_tax_federal,
            ]
            self.plotting_app.mouse_points["y"] = [
                y_tax_canton,
                y_tax_municipality,
                y_tax_federal,
            ]
            self.plotting_app.update_mouse_points()

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
        update_mouse_function=None,
    ):
        QtGui.QWidget.__init__(self)
        self.setWindowTitle("Taxes")
        self.main_layout = QtGui.QVBoxLayout()
        self.municipality_cb = QtGui.QComboBox()
        self.mouse_points = {"x": None, "y": None}
        self.plot_mouse_points = None
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
        self.cursorlabel = pg.TextItem(anchor=(-1, 10))
        self.cursorlabel.setText("test")
        self.plot_widget.addLegend()
        self.plot_widget.showGrid(x=True, y=True, alpha=0.4)
        self.plot_widget.setLabel("bottom", "taxable income [CHF]")
        self.plot_widget.setLabel("left", "tax [CHF]")
        self.main_layout.addWidget(self.plot_widget)

        self.cursor = Qt.CrossCursor
        self.plot_widget.setCursor(self.cursor)
        # self.plot_widget.scene().sigMouseMoved.connect(self.mouse_moved)
        if update_mouse_function is not None:
            self.plot_widget.scene().sigMouseMoved.connect(update_mouse_function)

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

    def mouse_moved(self, evt):
        # from PyQt5.QtCore import pyqtRemoveInputHook
        # from pdb import set_trace
        # pyqtRemoveInputHook()
        # set_trace()
        mousePoint = self.plot_widget.plotItem.vb.mapSceneToView(evt)
        self.mouse_points["x"] = mousePoint.x()
        self.mouse_points["y"] = mousePoint.y()
        self.update_mouse_points()

        # print(mousePoint.x(), mousePoint.y())
        # self.plot_widget.plot([mousePoint.x()],[mousePoint.y()], pen=None, symbol='x')
        # pos = evt[0]  ## using signal proxy turns original arguments into a tuple
        # if self.plotWidget.sceneBoundingRect().contains(pos):
        # mousePoint = self.plotWidget.vb.mapSceneToView(pos)
        # print('x: {}, y: {}'.format(mousePoint.x(), mousePoint.y()))
        # index = int(mousePoint.x())
        # #if index > 0 and index < len(data1):
        # if index > 0 and index < self.MFmax:
        #     self.cursorlabel.setText("<span style='font-size: 12pt'>x=%0.1f,   <span style='color: red'>y=%0.1f</span>" % (
        #     mousePoint.x(), mousePoint.y()))
        # self.vLine.setPos(mousePoint.x())
        # self.hLine.setPos(mousePoint.y())


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
