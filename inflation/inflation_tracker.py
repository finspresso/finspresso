import argparse
import pandas as pd
import logging
import coloredlogs
import sys
from pyqtgraph.Qt import QtGui
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

# Global settings
coloredlogs.install()
logger = logging.getLogger("portfolio_tracker")
logging.basicConfig(level=logging.DEBUG)


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class LIK(QtGui.QWidget):
    def __init__(self, lik_source):
        QtGui.QWidget.__init__(self)
        self.main_layout = QtGui.QVBoxLayout()
        self.setLayout(self.main_layout)
        self.main_dict = dict()
        self.main_dict["LIK2020"] = self.get_lik_data(lik_source, "LIK2020")
        self.main_dict["LIK2015"] = self.get_lik_data(lik_source, "LIK2015")
        self.current_pie_data = self.get_weights(self.main_dict["LIK2020"], 2, 2022)
        self.sc = MplCanvas(self, width=5, height=4, dpi=100)
        self.plot_pie_chart()
        # sc.axes.plot([0,1,2,3,4], [10,1,20,3,40])
        self.main_layout.addWidget(self.sc)

    def plot_pie_chart(self):
        sizes = self.current_pie_data.values
        labels = self.current_pie_data.index.values
        self.sc.axes.pie(
            sizes, labels=labels, autopct="%1.1f%%", shadow=True, startangle=90
        )
        # self.sc.axes.axis('equal')

    def get_weights(self, df, level, year):
        weights = df[df["Level"] == level][year]
        return weights

    def get_lik_data(self, source_file, sheet_name):
        # Make interactive plot showing pie for LIK weights in 2015 and 2020. Use matplotlib pyqt integration https://www.pythonguis.com/tutorials/plotting-matplotlib/
        df_raw = pd.read_excel(source_file, index_col=5, sheet_name=sheet_name)
        df = df_raw.iloc[4:, :]
        df.columns = df_raw.iloc[2, :]
        df = df.iloc[: df.index.isna().argmax(), :]
        df.index = df.index.map(self.remove_empty_spaces)
        return df

    @staticmethod
    def remove_empty_spaces(value):
        return_value = value
        if isinstance(value, str):
            return_value = value.strip()
        return return_value


class InflationTracker(QtGui.QTabWidget):
    def __init__(self, parent=None, source_lik=""):
        super(InflationTracker, self).__init__(parent)
        self.lik = LIK(source_lik)
        self.addTab(self.lik, "LIK")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--lik_data",
        help="xlsx file containing LIK weights",
        default="data/lik.xlsx",  # ToDo: Automate downlaod of .xlsx file from https://www.bfs.admin.ch/bfs/de/home/statistiken/preise/erhebungen/lik/warenkorb.assetdetail.21484892.html
    )

    args = parser.parse_args()
    app = QtGui.QApplication(sys.argv)
    inflation_tracker = InflationTracker(source_lik=args.lik_data)
    inflation_tracker.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
