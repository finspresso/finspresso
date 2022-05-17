import numpy as np
import datetime


def get_root_mean_square_deviation(x):
    rmsd = np.sqrt((x ** 2).mean())
    return rmsd


def get_geometric_mean(x):
    n = x.shape[0] - 1
    x0 = x.iloc[0]
    x1 = x.iloc[-1]
    geometric_mean = (x1 / x0) ** (1 / n) - 1 if n > 0 else 0
    geometric_mean *= 100
    return geometric_mean


def get_ema(x):
    N_ema = x.shape[0]
    alpha = 2 / (N_ema + 1)
    k = np.array(range(0, N_ema))
    weights = [alpha * (1 - alpha) ** p for p in k]
    weights = np.array(weights[::-1])
    ema = weights * x
    ema = ema.sum()
    return ema


def construct_estimation_dict():
    estimation_dict = {"estimate": dict(), "deviation": dict(), "rmsd": dict()}
    return estimation_dict


def compute_dividend_growth_portfolio(portfolio, data_dict, average_years):
    current_year = datetime.datetime.now().year
    dividend_dict = dict.fromkeys(portfolio, dict())
    for ticker in portfolio:
        dividends_per_year = data_dict[ticker]["dividends per year"][
            data_dict[ticker]["dividends per year"].index < current_year
        ]
        dividend_dict[ticker]["dividends per year growth"] = (
            dividends_per_year.diff() / dividends_per_year.shift() * 100
        )
        dividend_dict[ticker]["dividends per year growth diff"] = dividend_dict[ticker][
            "dividends per year growth"
        ].diff()
        dividend_dict[ticker][
            "rolling average dividend growth per year"
        ] = construct_estimation_dict()
        dividend_dict[ticker][
            "rolling geometric average dividends per year"
        ] = construct_estimation_dict()
        dividend_dict[ticker][
            "rolling ema dividend growth per year"
        ] = construct_estimation_dict()
        for year in average_years:
            dividend_dict[ticker]["rolling average dividend growth per year"][
                "estimate"
            ][str(year)] = (
                dividend_dict[ticker]["dividends per year growth"]
                .rolling(year)
                .mean()
                .shift()
            )
            dividend_dict[ticker]["rolling geometric average dividends per year"][
                "estimate"
            ][str(year)] = (
                dividends_per_year.rolling(year)
                .apply(lambda x: get_geometric_mean(x))
                .shift()
            )
            dividend_dict[ticker]["rolling ema dividend growth per year"]["estimate"][
                str(year)
            ] = (
                dividend_dict[ticker]["dividends per year growth"]
                .rolling(year)
                .apply(lambda x: get_ema(x))
                .shift()
            )
            averaging_names = [
                "rolling average dividend growth per year",
                "rolling geometric average dividends per year",
                "rolling ema dividend growth per year",
            ]
            for averaging_name in averaging_names:
                dividend_dict[ticker][averaging_name]["deviation"][str(year)] = (
                    dividend_dict[ticker][averaging_name]["estimate"][str(year)]
                    - dividend_dict[ticker]["dividends per year growth"]
                )
                dividend_dict[ticker][averaging_name]["rmsd"][
                    str(year)
                ] = get_root_mean_square_deviation(
                    dividend_dict[ticker][averaging_name]["deviation"][str(year)]
                )
    return dividend_dict


def dividend_outlier_rejection(dividends, rejection_threshold):
    dividends_without_outlier = dividends.copy()
    for year in dividends.index[1:]:
        dividends_without_outlier.loc[year] = dividends_without_outlier.loc[year - 1]
        if dividends.loc[year - 1] > 0:
            growth = (
                (dividends.loc[year] - dividends.loc[year - 1])
                / dividends.loc[year - 1]
                * 100
            )
            if np.abs(growth) <= rejection_threshold:
                dividends_without_outlier.loc[year] = dividends.loc[year]
    return dividends_without_outlier
