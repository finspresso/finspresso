import argparse
import json
import logging
import coloredlogs

coloredlogs.install()
logger_name = __name__ if __name__ != "__main__" else "witholding"
logger = logging.getLogger(logger_name)
logging.basicConfig(level=logging.DEBUG)


class TaxWithholder:
    def __init__(self, tax_rates_file="2020/tax_rates.json"):
        self.tax_rates_file = tax_rates_file
        self.load_tax_rates()

    def load_tax_rates(self):
        self.tax_rates_dict = dict()
        with open(self.tax_rates_file, "r") as read_file:
            self.tax_rates_dict = json.load(read_file)
        logger.info(self.tax_rates_dict)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tax_rates_file",
        help="Path to to .json file containing tax rates of cantons and federation",
        default="2020/tax_rates.json",
    )
    args = parser.parse_args()
    tax_withholder = TaxWithholder(tax_rates_file=args.tax_rates_file)
    print(tax_withholder)


if __name__ == "__main__":
    main()
