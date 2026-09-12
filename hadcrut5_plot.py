#!/usr/bin/python3
# Copyright (c) 2020-2025 Davide Madrisan <d.madrisan@proton.me>
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Display a plot of the HadCRUT5 temperature dataset.
"""

import argparse
from math import trunc
from typing import List

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from hadcrut5lib import argparser, HadCRUT5


def parse_args() -> argparse.Namespace:
    """This function parses and return arguments passed in"""
    descr = "Parse and plot the HadCRUT5 temperature datasets"
    examples = [
        "%(prog)s",
        "%(prog)s --global --annotate=2",
        '%(prog)s --period "1850-1900"',
        '%(prog)s --period "1850-1900" --smoother 5',
        '%(prog)s --period "1880-1920" --outfile HadCRUT5-1880-1920.png',
        '%(prog)s --period "1880-1920" --time-series monthly --global',
        '%(prog)s --period "1880-1920" --global --trends',
    ]

    parser = argparser(descr, examples)
    parser.add_argument(
        "-a",
        "--annotate",
        action="store",
        dest="annotate",
        default="1",
        help="add temperature annotations (0: no annotations, 1 (default): "
        "bottom only, 2: all ones",
    )
    parser.add_argument(
        "-f",
        "--outfile",
        action="store",
        dest="outfile",
        help="name of the output PNG file",
    )
    parser.add_argument(
        "-g",
        "--global",
        action="store_true",
        dest="plot_global",
        help="plot the Global Temperatures",
    )
    parser.add_argument(
        "-m",
        "--smoother",
        action="store",
        dest="smoother",
        help="make the lines smoother by using N-year means",
    )
    parser.add_argument(
        "-n",
        "--northern",
        action="store_true",
        dest="plot_northern",
        help="Northern Hemisphere Temperatures",
    )
    parser.add_argument(
        "-p",
        "--period",
        action="store",
        dest="period",
        default="1961-1990",
        help="show anomalies related to 1961-1990 (default), 1850-1900, or 1880-1920",
    )
    parser.add_argument(
        "-s",
        "--southern",
        action="store_true",
        dest="plot_southern",
        help="Southern Hemisphere Temperatures",
    )
    parser.add_argument(
        "-r",
        "--trends",
        action="store_true",
        dest="trends",
        help="add linear-fit trend lines for 1970-2010 and 2010-present to "
        "the Global Temperatures, showing the acceleration of global warming",
    )
    parser.add_argument(
        "-t",
        "--time-series",
        action="store",
        default="annual",
        dest="time_series",
        help='do plot the "annual" time series (default) or the "monthly" one',
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        dest="verbose",
        help="make the operation more talkative",
    )

    return parser.parse_args()


def dataset_current_anomaly(temperatures: List[float]) -> float:
    """Return the current anomaly"""
    return temperatures[-1]


def dataset_max_anomaly(temperatures: List[float]) -> float:
    """Return the maximum anomaly with respect to 'temperatures'"""
    return np.max(temperatures)


def dataset_smoother(years: List[int | float], temperatures: List[float], chunksize: int):
    """Make the lines smoother by using {chunksize}-year means"""
    data_range = range((len(years) + chunksize - 1) // chunksize)
    subset_years = [years[i * chunksize] for i in data_range]
    subset_temperatures = [
        np.mean(temperatures[i * chunksize : (i + 1) * chunksize]) for i in data_range
    ]

    return subset_years, subset_temperatures


# Periods used to fit the trend lines showing the acceleration of global
# warming. A None end year means "up to the last available year".
TREND_PERIODS = [(1970, 2010, "black"), (2010, None, "red")]

# How many years to project each trend line into the future
TREND_FORECAST_YEARS = 10


def dataset_linear_fit(
    years: List[int | float], temperatures: List[float], start_year: int, end_year: int
):
    """
    Return the slope and intercept (in °C/year) of the linear fit of
    'temperatures' over 'years' restricted to [start_year, end_year]
    """
    years_arr = np.array(years)
    temperatures_arr = np.array(temperatures)
    mask = (years_arr >= start_year) & (years_arr <= end_year)

    slope, intercept = np.polyfit(years_arr[mask], temperatures_arr[mask], 1)

    return slope, intercept


def plot_trendlines(years: List[int | float], temperatures: List[float]):
    """
    Overlay the linear-fit trend lines defined in TREND_PERIODS, each one
    projected TREND_FORECAST_YEARS into the future so that the accelerating
    departure from the earlier trends is visible
    """
    last_year = trunc(float(np.max(years)))

    for start_year, end_year, color in TREND_PERIODS:
        is_current_trend = end_year is None
        end_year = end_year or last_year
        if end_year <= start_year:
            continue

        slope, intercept = dataset_linear_fit(years, temperatures, start_year, end_year)
        forecast_year = last_year + TREND_FORECAST_YEARS
        x = np.array([start_year, forecast_year])

        label = f"{start_year}-{end_year} trend ({slope * 10:+.2f}°C/decade)"
        if is_current_trend:
            forecast_temp = slope * forecast_year + intercept
            label += f", forecast {forecast_year}: {forecast_temp:+.2f}°C"

        plt.plot(
            x,
            slope * x + intercept,
            color=color,
            linestyle="dotted",
            linewidth=1.4,
            alpha=0.8,
            zorder=1,
            label=label,
        )

        if is_current_trend:
            plt.annotate(
                f"{forecast_temp:.2f}°C",
                xy=(forecast_year - 2, forecast_temp + 0.05),
                fontsize=5,
                horizontalalignment="left",
                bbox={"facecolor": "red", "alpha": 0.3, "pad": 3},
            )


def plotline(hc5: HadCRUT5, chunksize: int, annotate: int, outfile: str, trends: bool):
    """
    Create a plot for the specified period and arguments and diplay it or save
    it to file if outfile is set
    """
    hc5.datasets_download()
    hc5.datasets_load()
    hc5.datasets_normalize()

    mpl.style.use("seaborn-v0_8-notebook")
    anomaly_current = {}
    anomaly_max = {}

    dataset_years = hc5.dataset_years()

    for region in hc5.datasets_regions():
        lower, mean, upper = hc5.dataset_normalized_data(region)
        raw_mean = mean

        if chunksize > 1:
            years, mean = dataset_smoother(dataset_years, mean, chunksize)
            hc5.logging_debug(f"years: \\\n{np.array(years)}")
            hc5.logging_debug(f"temperatures ({region}): \\\n{mean}")
            hc5.logging_debug(f"delta ({years[-1]}): \\\n{mean[-1]}")
        else:
            years = dataset_years
            plt.fill_between(years, lower, upper, color="lightgray")

            anomaly_current[region] = dataset_current_anomaly(mean)
            anomaly_max[region] = dataset_max_anomaly(mean)
            hc5.logging_debug(f"Current anomalies: {anomaly_current[region]}")
            hc5.logging_debug(f"Max anomalies: {anomaly_max[region]}")

            if annotate > 1:
                plt.annotate(
                    f"{anomaly_current[region]:.2f}°C",
                    xy=(years[-1] - 2, anomaly_current[region] - 0.15),
                    fontsize=6,
                    horizontalalignment="left",
                    bbox={"facecolor": "lightgray", "alpha": 0.6, "pad": 3},
                )

        linewidth = 1 if hc5.is_monthly_dataset and chunksize < 2 else 2
        plt.plot(years, mean, linewidth=linewidth, markersize=12, label=region)

        if trends and region == hc5.GLOBAL_REGION:
            plot_trendlines(dataset_years, raw_mean)

    plt.hlines(
        0,
        np.min(dataset_years),
        np.max(dataset_years),
        colors="gray",
        linestyles="dotted",
    )

    plt.title(
        f"HadCRUT5: land and sea temperature anomalies relative to {hc5.dataset_period}",
        pad=20,
    )
    plt.xlabel("year", fontsize=10)

    ylabel = f"{hc5.dataset_datatype.capitalize()} Temperature Anomalies in °C"

    if chunksize > 1:
        ylabel += f" ({chunksize}-year averages)"
    else:
        current = anomaly_current.get(hc5.GLOBAL_REGION)
        maximum = anomaly_max.get(hc5.GLOBAL_REGION)

        if annotate > 0 and current and maximum:
            current_year = trunc(hc5.dataset_years()[-1])
            facecolor = "blue" if current <= 0 else "red"
            plt.annotate(
                (
                    f"current global anomaly ({current_year}): "
                    f"{current:+.2f}°C, max: {maximum:+.2f}°C"
                ),
                xy=(0.98, 0.03),
                xycoords="axes fraction",
                fontsize=8,
                horizontalalignment="right",
                verticalalignment="bottom",
                bbox={
                    "facecolor": facecolor,
                    "alpha": 0.3,
                    "pad": 5,
                },
            )

    plt.annotate(
        f"{hc5.dataset_history} (version {hc5.dataset_version})",
        xy=(0.5, 1.01),
        xycoords="axes fraction",
        fontsize=8,
        horizontalalignment="center",
        verticalalignment="bottom",
    )

    plt.ylabel(ylabel, fontsize=10)
    plt.legend(fontsize=8)

    if outfile:
        plt.savefig(outfile, transparent=False)
    else:
        plt.show()


# pylint: disable=C0116
def main():
    args = parse_args()

    if not (args.plot_global or args.plot_northern or args.plot_southern):
        plot_global = plot_northern = plot_southern = True
    else:
        plot_global = args.plot_global
        plot_northern = args.plot_northern
        plot_southern = args.plot_southern

    regions = (plot_global, plot_northern, plot_southern)
    smoother = int(args.smoother) if args.smoother else 1

    hc5 = HadCRUT5(
        period=args.period,
        datatype=args.time_series,
        regions=regions,
        smoother=smoother,
        verbose=args.verbose,
    )

    plotline(
        hc5,
        smoother,
        int(args.annotate) if args.annotate else 1,
        args.outfile,
        args.trends,
    )


main()
