import argparse
import pandas as pd
import logging
import coloredlogs
import re

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
        df = pd.read_excel(source_file, index_col=5, sheet_name="LIK2020")

        empty_spaces_list = df.index.map(self.count_empty_spaces)
        df.loc[:, "empty space"] = empty_spaces_list
        return df

    @staticmethod
    def count_empty_spaces(name_raw):
        empty_spaces = 0
        name = str(name_raw)
        mask = "( *)\w"
        match = re.search(mask, name)
        if match:
            empty_spaces = len(match.group(1))
        return empty_spaces


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
