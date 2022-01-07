# Next load holdings and compute projected dividends
import argparse
import json


from pathlib import Path


class DividendProjector:
    def __init__(self, holdings_file="holdings.json"):
        self.holdings_file = Path(holdings_file)
        self.load_holdings()

    def load_holdings(self):
        with self.holdings_file.open("r") as file:
            self.holdings_dict = json.load(file)

    def print(self):
        print(self.holdings_dict)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--holdings_file",
        help="JSON file containing portfolio holdings",
        default="holdings.json",
    )
    args = parser.parse_args()
    dividend_projector = DividendProjector(holdings_file=args.holdings_file)
    dividend_projector.print()


if __name__ == "__main__":
    main()
