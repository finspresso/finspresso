import argparse
import coloredlogs
import datetime
import json
import matplotlib.pyplot as plt

from multiprocessing import Pool
import numpy as np
import pandas as pd
import logging
import yfinance as yf

from portfolio_math import portfolio_math
from mpl_toolkits.axes_grid1 import make_axes_locatable

# import ssl # ToDo: Add enabling to optional arguments
# ssl._create_default_https_context = ssl._create_unverified_context

# Global settings
coloredlogs.install()
logger_name = "dividend_analyzer"
logger = logging.getLogger(logger_name)
logging.basicConfig(level=logging.DEBUG)
SP_500_TICKER_FILE = "sp_500_tickers.json"
DATA_DICT_FILE = "data_dict.json"


# ToDo: Add this function to portfolio_math library
def get_dividend_payer_tickers(tickers, data_dict, n_min, current_year):
    dividend_payer = []
    for ticker in tickers:
        if not data_dict[ticker]["dividends per year"].empty:
            dividends_per_year = data_dict[ticker]["dividends per year"][
                data_dict[ticker]["dividends per year"] > 0
            ]
            if (np.diff(dividends_per_year.index) == 1).all():
                if (
                    len(dividends_per_year[dividends_per_year.index < current_year])
                    > n_min
                ):
                    dividend_payer.append(ticker)
    return dividend_payer


def compute_dividend_growth(
    ticker,
    data_dict,
    average_years,
    averaging_names,
    rejection_threshold,
    mixed_names,
):
    logger.info("Compute growth estimates for ticker %s", ticker)
    current_year = datetime.datetime.now().year
    dividend_dict = dict()
    dividend_dict["rmsd_df"] = pd.DataFrame(
        index=average_years, columns=averaging_names, data=0, dtype=float
    )
    dividend_dict["rmsd_df_mixed"] = pd.DataFrame(
        index=average_years, columns=mixed_names, data=0, dtype=float
    )
    dividends_per_year = data_dict[ticker]["dividends per year"][
        (data_dict[ticker]["dividends per year"].index < current_year)
        & (data_dict[ticker]["dividends per year"] > 0)
    ]
    dividend_dict["dividends per year"] = dividends_per_year
    dividend_dict["dividends per year growth"] = (
        dividends_per_year.diff() / dividends_per_year.shift() * 100
    )
    dividend_dict["dividends per year growth"] = dividend_dict[
        "dividends per year growth"
    ].iloc[1:]
    dividend_dict[
        "dividends per year (outlier rejection)"
    ] = portfolio_math.dividend_outlier_rejection(
        dividends_per_year, rejection_threshold
    )
    dividend_dict["dividends per year growth (outlier rejection)"] = (
        dividend_dict["dividends per year (outlier rejection)"].diff()
        / dividend_dict["dividends per year (outlier rejection)"].shift()
        * 100
    )
    dividend_dict["dividends per year growth (outlier rejection)"] = dividend_dict[
        "dividends per year growth (outlier rejection)"
    ].iloc[1:]
    dividend_dict["dividends per year growth diff"] = dividend_dict[
        "dividends per year growth"
    ].diff()

    for averaging_name in averaging_names:
        dividend_dict[averaging_name] = portfolio_math.construct_estimation_dict()
    for year in average_years:
        dividend_dict["rolling average dividend growth per year"]["estimate"][
            str(year)
        ] = (dividend_dict["dividends per year growth"].rolling(year).mean().shift())
        dividend_dict["rolling average dividend growth per year (outlier rejection)"][
            "estimate"
        ][str(year)] = (
            dividend_dict["dividends per year growth (outlier rejection)"]
            .rolling(year)
            .mean()
            .shift()
        )
        dividend_dict["rolling geometric average dividends growth per year"][
            "estimate"
        ][str(year)] = (
            dividends_per_year.rolling(year)
            .apply(lambda x: portfolio_math.get_geometric_mean(x))
            .shift()
        )
        dividend_dict[
            "rolling geometric average dividends growth per year (outlier rejection)"
        ]["estimate"][str(year)] = (
            dividend_dict["dividends per year (outlier rejection)"]
            .rolling(year)
            .apply(lambda x: portfolio_math.get_geometric_mean(x))
            .shift()
        )
        dividend_dict["rolling ema dividend growth per year"]["estimate"][str(year)] = (
            dividend_dict["dividends per year growth"]
            .rolling(year)
            .apply(lambda x: portfolio_math.get_ema(x))
            .shift()
        )

        dividend_dict["rolling ema dividend growth per year (outlier rejection)"][
            "estimate"
        ][str(year)] = (
            dividend_dict["dividends per year growth (outlier rejection)"]
            .rolling(year)
            .apply(lambda x: portfolio_math.get_ema(x))
            .shift()
        )

        for averaging_name in averaging_names:
            dividend_dict[averaging_name]["deviation"][str(year)] = (
                dividend_dict[averaging_name]["estimate"][str(year)]
                - dividend_dict["dividends per year growth"]
            )
            rmsd = portfolio_math.get_root_mean_square_deviation(
                dividend_dict[averaging_name]["deviation"][str(year)]
            )
            dividend_dict["rmsd_df"].loc[year, averaging_name] = rmsd
            dividend_dict[averaging_name]["rmsd"][str(year)] = rmsd
        dividend_dict["rmsd_df_mixed"] = get_rmsd_mixed(
            dividend_dict["rmsd_df"], mixed_names
        )

    return dividend_dict


def get_rmsd_portfolio(
    portfolio, dividend_growth_dict, average_years, averaging_names, mixed_names
):
    logger.info("Computing rmsd for portfolio %s", portfolio)
    rmsd_averaging_df = pd.DataFrame(
        index=average_years, columns=averaging_names, data=0, dtype=float
    )
    rmsd_dict = dict()
    for ticker in portfolio:
        rmsd_averaging_df = rmsd_averaging_df + dividend_growth_dict[ticker]["rmsd_df"]

    rmsd_dict["rmsd portfolio"] = rmsd_averaging_df
    rmsd_dict["rmsd portfolio mixed"] = get_rmsd_mixed(
        rmsd_dict["rmsd portfolio"], mixed_names
    )

    return rmsd_dict


def get_rmsd_mixed(rmsd, mixed_names):
    rmsd_mixed = pd.DataFrame(columns=mixed_names, index=rmsd.index, data=0)
    pairs = {name: [] for name in mixed_names}
    for name in mixed_names:
        for column in rmsd.columns:
            if name in column:
                pairs[name].append(column)
    for key, pair_names in pairs.items():
        rmsd_mixed.loc[:, key] = rmsd[pair_names].min(axis=1)

    return rmsd_mixed


class DividendAnalyzer:
    def __init__(
        self,
        tickers,
        average_years=[1, 2, 3, 4, 5],
        n_security=10,
        n_portfolio=100,
        n_processes=None,
        averaging_names=[
            "rolling average dividend growth per year",
            "rolling average dividend growth per year (outlier rejection)",
            "rolling geometric average dividends growth per year",
            "rolling geometric average dividends growth per year (outlier rejection)",
            "rolling ema dividend growth per year",
            "rolling ema dividend growth per year (outlier rejection)",
        ],
        rejection_threshold=50,
    ):
        self.n_min = len(average_years) + 1
        self.n_processes = n_processes
        self.data_dict = {ticker: dict() for ticker in tickers}
        self.n_security = n_security
        self.n_portfolio = n_portfolio
        self.average_years = average_years
        self.averaging_names = averaging_names
        self.mixed_names = [
            name for name in self.averaging_names if "outlier" not in name
        ]
        self.rejection_threshold = rejection_threshold

    def compare_growth_estimates(self):
        if self.n_processes == 1:
            self.compare_growth_estimates_single()
        else:
            self.compare_growth_estimates_single()  # Single processing is here faster
            # self.compare_growth_estimates_multi()

    def compare_growth_estimates_single(self):
        logger.info("Running growth comparison with in single processing mode.")
        self.rmsd_dict_portfolios = []
        for portfolio in self.portfolios:
            rmsd_dict = get_rmsd_portfolio(
                portfolio,
                self.dividend_growth_dict,
                self.average_years,
                self.averaging_names,
                self.mixed_names,
            )
            self.rmsd_dict_portfolios.append(rmsd_dict)
        self.compute_histograms()

    def compare_growth_estimates_multi(self):
        logger.info("Running growth comparison with multiprocessing.")
        input_tuples = [
            (
                portfolio,
                self.dividend_growth_dict,
                self.average_years,
                self.averaging_names,
                self.mixed_names,
            )
            for portfolio in self.portfolios
        ]

        with Pool(processes=self.n_processes) as pool:
            self.rmsd_dict_portfolios = pool.starmap(get_rmsd_portfolio, input_tuples)
        self.compute_histograms()

    def plot_count_arrays(self, save_figures=False):
        logger.info("Plotting count arrays")
        figures = [
            plt.figure(figsize=(17, 8)),
            plt.figure(figsize=(17, 8)),
            plt.figure(figsize=(17, 8)),
            plt.figure(figsize=(17, 8)),
        ]
        figure_names = [
            "portfolio.png",
            "single.png",
            "portfolio_mixed.png",
            "single_mixed.png",
        ]
        axes = [
            figures[0].add_subplot(1, 1, 1),
            figures[1].add_subplot(1, 1, 1),
            figures[2].add_subplot(1, 1, 1),
            figures[3].add_subplot(1, 1, 1),
        ]
        count_arrays = [
            self.count_arrays["portfolios"]["all"].transpose(),
            self.count_arrays["single"]["all"].transpose(),
            self.count_arrays["portfolios"]["mixed"].transpose(),
            self.count_arrays["single"]["mixed"].transpose(),
        ]
        n_single = self.count_arrays["single"]["all"].sum()
        titles = [
            (
                "Best averaging technique (portfolio)"
                + f"\nnumber of portfolios: {self.n_portfolio}"
                + f"\nsecurities per portfolio: {self.n_security}"
            ),
            (
                "Best averaging technique (single)"
                + f"\nnumber of securities: {n_single}"
            ),
            (
                "Best averaging mixed technique (portfolio)"
                + f"\nnumber of portfolios: {self.n_portfolio}"
                + f"\nsecurities per portfolio: {self.n_security}"
            ),
            (
                "Best averaging mixed technique (single)"
                + f"\nnumber of securities: {n_single}"
            ),
        ]
        ylabel_tick_names = [
            [
                " ".join(x.split()[:2])
                + "\n"
                + " ".join(x.split()[2:4])
                + "\n"
                + " ".join(x.split()[4:])
                for x in self.averaging_names
            ]
        ]
        ylabel_tick_names.append(ylabel_tick_names[0])
        ylabel_tick_names_mixed = [
            " ".join(x.split()[:2])
            + "\n"
            + " ".join(x.split()[2:4])
            + "\n"
            + " ".join(x.split()[4:])
            for x in self.mixed_names
        ]
        ylabel_tick_names.extend([ylabel_tick_names_mixed, ylabel_tick_names_mixed])
        xlabel_tick_names = [str(name) + "y" for name in self.average_years]
        for i in range(4):
            divider = make_axes_locatable(axes[i])
            nx = len(xlabel_tick_names)
            ny = len(ylabel_tick_names[i])
            lx = nx - 1
            ly = ny - 1
            xlabel_tick_positions = [x * lx / (2 * nx) for x in np.arange(1, 2 * nx, 2)]
            ylabel_tick_positions = [y * ly / (2 * ny) for y in np.arange(1, 2 * ny, 2)]

            img = axes[i].imshow(
                count_arrays[i],
                origin="lower",
                interpolation="nearest",
                aspect="equal",
                alpha=0.6,
                cmap="plasma",
                extent=[0, lx, 0, ly],
            )
            cax = divider.append_axes("right", size="5%", pad=0.05)
            plt.colorbar(img, cax=cax)
            axes[i].set_xticks(xlabel_tick_positions)
            axes[i].set_xticklabels(xlabel_tick_names)
            axes[i].set_yticks(ylabel_tick_positions)
            axes[i].set_yticklabels(ylabel_tick_names[i])
            axes[i].set_title(titles[i])
            if save_figures:
                figures[i].savefig(figure_names[i])

        plt.show()

    def compute_histograms(self):
        self.count_arrays = {"portfolios": dict(), "single": dict()}
        self.count_arrays["portfolios"]["all"] = np.zeros(
            (len(self.average_years), len(self.averaging_names))
        )
        self.count_arrays["single"]["all"] = np.zeros(
            (len(self.average_years), len(self.averaging_names))
        )
        self.count_arrays["portfolios"]["mixed"] = np.zeros(
            (len(self.average_years), len(self.mixed_names))
        )
        self.count_arrays["single"]["mixed"] = np.zeros(
            (len(self.average_years), len(self.mixed_names))
        )

        for rmsd_dict in self.rmsd_dict_portfolios:
            array = np.array(rmsd_dict["rmsd portfolio"])
            ind = np.unravel_index(np.argmin(array, axis=None), array.shape)
            self.count_arrays["portfolios"]["all"][ind] += 1
            array = np.array(rmsd_dict["rmsd portfolio mixed"])
            ind = np.unravel_index(np.argmin(array, axis=None), array.shape)
            self.count_arrays["portfolios"]["mixed"][ind] += 1

        for ticker in self.tickers_included:
            array = np.array(self.dividend_growth_dict[ticker]["rmsd_df"])
            ind = np.unravel_index(np.argmin(array, axis=None), array.shape)
            self.count_arrays["single"]["all"][ind] += 1
            array = np.array(self.dividend_growth_dict[ticker]["rmsd_df_mixed"])
            ind = np.unravel_index(np.argmin(array, axis=None), array.shape)
            self.count_arrays["single"]["mixed"][ind] += 1

    def randomize_portfolios(self):
        logger.info(
            "Randomizing %s portfolios with each %s securities",
            self.n_portfolio,
            self.n_security,
        )
        tickers = pd.Series(self.yf_object.tickers.keys())
        n_tickers = tickers.shape[0]

        self.portfolios = []
        tickers_included = []
        while len(self.portfolios) < self.n_portfolio:
            selected_tickers = tuple(
                tickers[
                    np.floor(np.random.rand(self.n_security) * n_tickers).tolist()
                ].values.tolist()
            )
            self.portfolios.append(selected_tickers)
            tickers_included.extend(selected_tickers)
        self.tickers_included = set(tickers_included)

    def download_dividend_history_single(self):
        for ticker in self.yf_object.tickers.keys():
            logger.info("Downloading data for security {}".format(ticker))
            self.data_dict[ticker]["dividends"] = self.yf_object.tickers[
                ticker
            ].dividends
            self.data_dict[ticker]["dividends per year"] = self.get_dividends_per_year(
                self.data_dict[ticker]["dividends"]
            )

    def get_dividend_history(self, ticker):
        logger.info("Downloading data for security {}".format(ticker))
        dividend_history = dict()
        dividend_history["dividends"] = pd.Series(dtype=np.float64)
        dividend_history["dividends per year"] = pd.Series(dtype=np.float64)
        dividends = self.yf_object.tickers[ticker].dividends
        if len(dividends) > 0:
            dividend_history["dividends"] = self.yf_object.tickers[ticker].dividends
            dividend_history["dividends per year"] = self.get_dividends_per_year(
                dividend_history["dividends"]
            )
        return dividend_history

    def download_dividend_history_multi(self):
        logger.info("Starting multiprocessing to downloading dividend data")
        tickers = list(self.yf_object.tickers.keys())
        with Pool(processes=self.n_processes) as pool:
            result_list = pool.map(self.get_dividend_history, tickers)
        for ticker, dividend_history in zip(tickers, result_list):
            self.data_dict[ticker] = dividend_history

    def store_data_dict_to_json(self):
        file_name = DATA_DICT_FILE
        logger.info("Storing data_dict to %s", file_name)
        data_to_json = {
            key: {
                "dividends": value["dividends"].to_json(date_format="iso")
                if "dividends" in value.keys()
                else None,
                "dividends per year": value["dividends per year"].to_json(
                    date_format="iso"
                )
                if "dividends per year" in value.keys()
                else None,
            }
            for key, value in self.data_dict.items()
        }

        with open(file_name, "w") as file:
            json.dump(data_to_json, file, indent=4)

    def load_data_dict_from_json(self):
        file_name = DATA_DICT_FILE
        logger.info("loading data_dict to %s", file_name)
        with open(file_name, "r") as file:
            self.loaded_dict = json.load(file)
        self.data_dict = {key: dict() for key in self.loaded_dict}
        for key in self.data_dict.keys():
            self.data_dict[key]["dividends"] = pd.Series(
                eval(self.loaded_dict[key]["dividends"]), dtype=np.float64
            )
            self.data_dict[key]["dividends"].index = self.data_dict[key][
                "dividends"
            ].index.map(lambda x: datetime.datetime.strptime(x[:10], "%Y-%M-%d"))
            self.data_dict[key]["dividends per year"] = pd.Series(
                eval(self.loaded_dict[key]["dividends per year"]), dtype=np.float64
            )
            self.data_dict[key]["dividends per year"].index = self.data_dict[key][
                "dividends per year"
            ].index.map(int)

    def presort_stocks(self):
        current_year = datetime.datetime.now().year
        self.dividend_payer = get_dividend_payer_tickers(
            self.data_dict.keys(), self.data_dict, self.n_min, current_year
        )
        self.yf_object = yf.Tickers(self.dividend_payer)

    def compute_dividend_growth(self):
        if self.n_processes == 1:
            self.compute_dividend_growth_single()
        else:
            self.compute_dividend_growth_multi()

    def compute_dividend_growth_multi(self):
        logger.info("Computing dividend growth values with multiprocessing")
        input_tuples = [
            (
                ticker,
                self.data_dict,
                self.average_years,
                self.averaging_names,
                self.rejection_threshold,
                self.mixed_names,
            )
            for ticker in self.tickers_included
        ]
        with Pool(processes=self.n_processes) as pool:
            computed_dividend_list = pool.starmap(compute_dividend_growth, input_tuples)
        self.dividend_growth_dict = {
            ticker: dividend_dict
            for ticker, dividend_dict in zip(
                self.tickers_included, computed_dividend_list
            )
        }

    def compute_dividend_growth_single(self):
        logger.info("Computing dividend growth values")
        self.dividend_growth_dict = dict()
        for ticker in self.tickers_included:
            self.dividend_growth_dict[ticker] = compute_dividend_growth(
                ticker,
                self.data_dict,
                self.average_years,
                self.averaging_names,
                self.rejection_threshold,
                self.mixed_names,
            )

    @classmethod
    def get_dividends_per_year(cls, dividends):
        dividends_per_year = pd.Series(dtype=np.float64)
        if len(dividends) > 0:
            years = range(
                dividends.index.min().year + 1, dividends.index.max().year + 1
            )
            dividends_per_year_list = []
            years_list = []
            for year in years:
                years_list.append(year)
                dividends_per_year_list.append(
                    dividends[dividends.index.year == year].sum()
                )
            if len(dividends_per_year_list) > 0:
                dividends_per_year = pd.Series(
                    dividends_per_year_list, index=years_list
                )
        return dividends_per_year

    @classmethod
    def get_SP500_constituents(cls):
        """Downloads S&P 500 constituents from Wikipedia"""
        logger.info("Downloading all S&P 500 ticker from Wikipedia")
        payload = pd.read_html(
            "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        )
        sp500_tickers = payload[0]["Symbol"]
        sp500_tickers_dict = {"tickers": sp500_tickers.tolist()}
        return sp500_tickers_dict

    @classmethod
    def store_constituents_to_json(cls, constituents_dict, file_name):
        logger.info("Dumping constituents' ticker dictionary to %s", file_name)

        with open(file_name, "w") as file:
            json.dump(constituents_dict, file, indent=4)

    @classmethod
    def load_constituents_from_json(cls, file_name):
        logger.info("Loading constituents' ticker from %s", file_name)

        with open(file_name, "r") as file:
            constituents_dict = json.load(file)
        return constituents_dict


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--download_sp_500",
        help="If set downloads the consitutents of the S&P 500 index from Wikipedia under "
        + SP_500_TICKER_FILE,
        action="store_true",
    )
    parser.add_argument(
        "--n_security", help="Number of securities per portfolio", type=int, default=10
    )
    parser.add_argument(
        "--n_portfolio",
        help="Number of considered portfolios for analysis.",
        type=int,
        default=100,
    )
    parser.add_argument(
        "-j",
        help="Number of allowed parallel processes for multiprocessing steps",
        type=int,
        default=None,
    )
    parser.add_argument(
        "--update_dividends",
        help="If set, re-downloads all the dividends of the desired tickers and \
              stores them under data_dict.json. Otherwise loads the data_dict \
              from data_dict.json ",
        action="store_true",
    )
    parser.add_argument(
        "--save_figures",
        help="If set, saves the figures in the current directory with portfolio.png and single.png",
        action="store_true",
    )
    args = parser.parse_args()
    if args.download_sp_500:
        sp_500_tickers = DividendAnalyzer.get_SP500_constituents()
        DividendAnalyzer.store_constituents_to_json(sp_500_tickers, SP_500_TICKER_FILE)
    else:
        sp_500_tickers = DividendAnalyzer.load_constituents_from_json(
            SP_500_TICKER_FILE
        )

    dividend_analyzer = DividendAnalyzer(
        sp_500_tickers["tickers"],
        n_security=args.n_security,
        n_portfolio=args.n_portfolio,
        n_processes=args.j,
    )
    if args.update_dividends:
        dividend_analyzer.download_dividend_history_multi()
        dividend_analyzer.store_data_dict_to_json()
    else:
        dividend_analyzer.load_data_dict_from_json()

    dividend_analyzer.presort_stocks()
    dividend_analyzer.randomize_portfolios()
    dividend_analyzer.compute_dividend_growth()

    dividend_analyzer.compare_growth_estimates()
    dividend_analyzer.plot_count_arrays(save_figures=args.save_figures)


# Next:
# 1) Make alternative computation that considers single tickes instead of randomized portfolio to see whether the 1y zero growth (geometric growth estiamte) is still the best
# 2 ) If a different one is the best
if __name__ == "__main__":
    main()
