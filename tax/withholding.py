import argparse
import json
import logging
import coloredlogs
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

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
        incomes_samples = pd.Series(np.linspace(0, 5 * 1e5, 1000))
        tax_canton_dict = self.tax_rates_dict["canton"][self.marital_status]
        tax_canton_df = pd.DataFrame(
            {
                "taxable income": tax_canton_dict["taxable income"],
                "tax_rate": tax_canton_dict["tax_rate"],
                "tax": tax_canton_dict["tax"],
            }
        )

        taxes_canton = incomes_samples.map(lambda x: self.get_tax(x, tax_canton_df))
        fig = plt.figure(figsize=(20, 15))
        ax = fig.add_subplot(111)
        ax.plot(incomes_samples, taxes_canton, label="Base tax canton")
        ax.set_title("Tax")
        ax.set_xlabel("taxable income [CHF]")
        ax.set_ylabel("tax [CHF]")
        ax.legend()
        ax.grid()
        plt.show()


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
    tax_withholder = TaxWithholder(
        tax_rates_file=args.tax_rates_file,
        municipality=args.municipality,
        marital_status=args.marital_status,
    )
    tax_withholder.plot_tax_per_income()


if __name__ == "__main__":
    main()
