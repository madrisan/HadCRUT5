#!/usr/bin/python3
# Copyright (c) 2020-2022 Davide Madrisan <davide.madrisan@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Display a plot of the HadCRUT5 temperature dataset.
"""

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from math import trunc
from hadcrut5lib import argparser, dprint, HadCRUT5


def parse_args():
    """This function parses and return arguments passed in"""
    descr = "Parse and plot the HadCRUT5 temperature datasets"
    examples = [
        "%(prog)s",
        "%(prog)s --global --annotate=2",
        '%(prog)s --period "1850-1900"',
        '%(prog)s --period "1850-1900" --smoother 5',
        '%(prog)s --period "1880-1920" --outfile HadCRUT5-1880-1920.png',
        '%(prog)s --period "1880-1920" --time-series monthly --global',
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


def dataset_current_anomaly(temperatures):
    """Return the current anomaly"""
    return temperatures[-1]


def dataset_max_anomaly(temperatures):
    """Return the maximum anomaly with respect to 'temperatures'"""
    return np.max(temperatures)


def dataset_smoother(years, temperatures, chunksize):
    """Make the lines smoother by using {chunksize}-year means"""
    data_range = range((len(years) + chunksize - 1) // chunksize)
    subset_years = [years[i * chunksize] for i in data_range]
    subset_temperatures = [
        np.mean(temperatures[i * chunksize : (i + 1) * chunksize]) for i in data_range
    ]

    return subset_years, subset_temperatures


def plotline(hc5, chunksize, annotate, outfile, verbose):
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

        if chunksize > 1:
            years, mean = dataset_smoother(dataset_years, mean, chunksize)
            dprint(verbose, "years: \\\n{}".format(np.array(years)))
            dprint(verbose, "temperatures ({}): \\\n{}".format(region, mean))
            dprint(verbose, "delta ({}): \\\n{}".format(years[-1], mean[-1]))
        else:
            years = dataset_years
            plt.fill_between(years, lower, upper, color="lightgray")

            anomaly_current[region] = dataset_current_anomaly(mean)
            anomaly_max[region] = dataset_max_anomaly(mean)
            dprint(verbose, ("Current anomalies: {}".format(anomaly_current[region])))
            dprint(verbose, "Max anomalies: {}".format(anomaly_max[region]))

            if annotate > 1:
                plt.annotate(
                    "{0:.2f}°C".format(anomaly_current[region]),
                    xy=(years[-1] - 5, anomaly_current[region] + 0.05),
                    fontsize=6,
                    horizontalalignment="left",
                    bbox={"facecolor": "lightgray", "alpha": 0.6, "pad": 3},
                )

        linewidth = 1 if hc5.is_monthly_dataset and chunksize < 2 else 2
        plt.plot(years, mean, linewidth=linewidth, markersize=12, label=region)

    plt.hlines(
        0,
        np.min(dataset_years),
        np.max(dataset_years),
        colors="gray",
        linestyles="dotted",
    )

    plt.title(
        (
            "HadCRUT5: land and sea temperature anomalies relative to {}".format(
                hc5.dataset_period
            )
        )
    )
    plt.xlabel("year", fontsize=10)

    ylabel = "{} Temperature Anomalies in °C".format(hc5.dataset_datatype.capitalize())

    if chunksize > 1:
        ylabel += " ({}-year averages)".format(chunksize)
    else:
        current = anomaly_current.get(hc5.GLOBAL_REGION)
        maximum = anomaly_max.get(hc5.GLOBAL_REGION)

        if annotate > 0 and current and maximum:
            current_year = trunc(hc5.dataset_years()[-1])
            plt.annotate(
                (
                    "current global anomaly ({0}): {1:+.2f}°C, max: {2:+.2f}°C".format(
                        current_year, current, maximum
                    )
                ),
                xy=(0.98, 0.03),
                xycoords="axes fraction",
                fontsize=8,
                horizontalalignment="right",
                verticalalignment="bottom",
                bbox={
                    "facecolor": "{}".format("blue" if current <= 0 else "red"),
                    "alpha": 0.3,
                    "pad": 5,
                },
            )

    plt.annotate(
        hc5.dataset_history,
        xy=(0.01, 0.8),
        xycoords="axes fraction",
        fontsize=8,
        horizontalalignment="left",
        verticalalignment="top",
    )

    plt.ylabel(ylabel, fontsize=10)
    plt.legend()

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
        args.verbose,
    )


main()
