import argparse
import pandas as pd
import logging
import coloredlogs

# Global settings
coloredlogs.install()
logger = logging.getLogger("portfolio_tracker")
logging.basicConfig(level=logging.DEBUG)


class InflationTracker:
    def __init__(self, lik_source):
        self.df_lik = self.get_lik_data(lik_source)
        print(self.df_lik)

    def get_lik_data(self, source_file):
        # Next create dictionary based on subcategory which can be read of from empty spaces
        df = pd.read_excel(source_file, index_col=6, sheet_name="LIK2020")
        return df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--lik_data",
        help="xlsx file containing LIK weights",
        default="data/lik.xlsx",  # ToDo: Automate downlaod of .xlsx file from https://www.bfs.admin.ch/bfs/de/home/statistiken/preise/erhebungen/lik/warenkorb.assetdetail.21484892.html
    )

    args = parser.parse_args()
    inflation_tracker = InflationTracker(args.lik_data)
    print(inflation_tracker.df_lik)


if __name__ == "__main__":
    main()
