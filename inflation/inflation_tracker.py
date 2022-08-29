import argparse
import pandas as pd
import logging
import coloredlogs
import datetime
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
        self.main_dict["LIK2010"] = self.get_lik_data(
            lik_source,
            "LIK2010",
            index_col=3,
            start_row=4,
            column_row=2,
            rename_level_col="Pos",
        )
        self.main_dict["LIK2005"] = self.get_lik_data(
            lik_source,
            "LIK2005",
            index_col=3,
            start_row=4,
            column_row=2,
            rename_level_col="Pos",
        )
        self.create_lik_dict()
        current_year = str(datetime.datetime.now().year)
        self.sc = MplCanvas(self, width=5, height=4, dpi=100)
        self.create_year_combobox(
            sorted(self.lik_dict.keys(), reverse=True), current_year
        )
        self.update_pie_chart(current_year)
        self.main_layout.addWidget(self.year_cb)
        self.main_layout.addWidget(self.sc)

    def create_year_combobox(self, cb_list, current_text):
        self.year_cb = QtGui.QComboBox()
        self.year_cb.addItems(cb_list)
        self.year_cb.currentTextChanged.connect(self.update_pie_chart)
        self.year_cb.setCurrentText(current_text)

    def update_pie_chart(self, text):
        self.current_pie_data = self.lik_dict[text]
        self.sc.axes.cla()
        sizes = self.current_pie_data.values
        labels = self.current_pie_data.index.values
        self.sc.axes.pie(
            sizes, labels=labels, autopct="%1.1f%%", shadow=False, startangle=90
        )
        self.sc.axes.axis("equal")
        self.sc.draw()

    def get_weights(self, df, level, year):
        weights = df[df["Level"] == level][year]
        return weights

    def create_lik_dict(self, level=2):
        self.lik_dict = dict()
        current_year = datetime.datetime.now().year
        for df in self.main_dict.values():
            years = [x for x in df.columns if type(x) is not str]
            for year in years:
                if year <= current_year:
                    self.lik_dict[str(int(year))] = df[df["Level"] == level][year]

    def get_lik_data(
        self,
        source_file,
        sheet_name,
        index_col=5,
        start_row=4,
        column_row=2,
        rename_level_col="Level",
    ):
        # Make interactive plot showing pie for LIK weights in 2015 and 2020. Use matplotlib pyqt integration https://www.pythonguis.com/tutorials/plotting-matplotlib/
        # 2. Make Pie chart's year combobox select between 2015 and 2022
        # 3. Add option to select which change was biggest
        df_raw = pd.read_excel(source_file, index_col=index_col, sheet_name=sheet_name)
        df = df_raw.iloc[start_row:, :]
        df.columns = df_raw.iloc[column_row, :]
        df = df.rename(columns={rename_level_col: "Level"})
        df = df.iloc[: df["Level"].isna().argmax(), :]
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
