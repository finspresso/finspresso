import argparse
import pandas as pd
import logging
import coloredlogs
from pyqtgraph.Qt import QtGui

# Global settings
coloredlogs.install()
logger = logging.getLogger("portfolio_tracker")
logging.basicConfig(level=logging.DEBUG)


class LIK(QtGui.QWidget):
    def __init__(self, lik_source):
        QtGui.QWidget.__init__(self)
        self.main_layout = QtGui.QVBoxLayout()
        self.setLayout(self.main_layout)
        self.main_dict = dict()
        self.main_dict["LIK2020"] = self.get_lik_data(lik_source, "LIK2020")
        self.main_dict["LIK2015"] = self.get_lik_data(lik_source, "LIK2015")

    def get_lik_data(self, source_file, sheet_name):
        # Make interactive plot showing pie for LIK weights in 2015 and 2020. Use matplotlib pyqt integration https://www.pythonguis.com/tutorials/plotting-matplotlib/
        df_raw = pd.read_excel(source_file, index_col=5, sheet_name=sheet_name)
        df = df_raw.iloc[4:, :]
        df.columns = df_raw.iloc[2, :]
        return df


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
    inflation_tracker = InflationTracker(source_lik=args.lik_data)
    print(inflation_tracker)


if __name__ == "__main__":
    main()
