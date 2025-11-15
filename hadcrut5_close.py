#!/usr/bin/python3
# Copyright (c) 2025 Davide Madrisan <d.madrisan@proton.me>
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Plotting the approach of HadCRUT5 dataset to a threshold temperature.
"""

import argparse

import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import numpy as np

from hadcrut5lib import argparser, HadCRUT5


def parse_args() -> argparse.Namespace:
    """This function parses and return arguments passed in"""
    descr = "Parse and plot the approach of HadCRUT5 dataset to a threshold temperature"
    examples = [
        "%(prog)s",
        '%(prog)s --period "1850-1900" --region global',
        '%(prog)s --period "1880-1920" --outfile "HadCRUT5-1880-1920-threshold.png"',
    ]

    parser = argparser(descr, examples)
    parser.add_argument(
        "-f",
        "--outfile",
        action="store",
        dest="outfile",
        help="name of the output PNG file",
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
        "-r",
        "--region",
        choices=["global", "northern", "southern"],
        action="store",
        dest="region",
        default="global",
        help="select between Global (default), Northern, or Southern Temperatures",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        dest="verbose",
        help="make the operation more talkative",
    )

    return parser.parse_args()


def plotline(hc5: HadCRUT5, region: str, outfile: str, threshold):
    """
    Create a plot for the specified period and arguments and diplay it or save
    it to file if outfile is set
    """
    hc5.datasets_download()
    hc5.datasets_load()
    hc5.datasets_normalize()

    years = hc5.dataset_years()
    ylabel = f"Temperature Anomalies relative to {hc5.dataset_period}"

    regions_switch = {
        "global": hc5.GLOBAL_REGION,
        "northern": hc5.NORTHERN_REGION,
        "southern": hc5.SOUTHERN_REGION,
    }
    _, mean, _ = hc5.dataset_normalized_data(regions_switch[region])

    _, ax = plt.subplots()
    ax.set_frame_on(False)
    ax.tick_params(axis="both", which="both", length=0)
    ax.yaxis.set_major_formatter("{x:.1f}°C")
    ax.yaxis.set_major_locator(MultipleLocator(0.5))

    plt.hlines(
        threshold,
        np.min(years),
        np.max(years),
        colors="white",
        linestyles="dotted",
    )

    ymin = min(mean)
    plt.imshow(
        np.linspace(0, 1, 256).reshape(-1, 1),
        origin="lower",
        aspect="auto",
        cmap="coolwarm",
        extent=(years[0], years[-1], ymin, 2.0),
    )
    plt.fill_between(years, ymin, mean, color="w")

    plt.title(f"HadCRUT5: Closing in to {threshold}°C")
    plt.xlabel("year", fontsize=10)
    plt.ylabel(ylabel, fontsize=10)

    plt.plot(years, mean, "steelblue", linewidth=2)

    if outfile:
        plt.savefig(outfile, transparent=False)
    else:
        plt.show()


# pylint: disable=C0116
def main():
    args = parse_args()

    regions = (args.region == "global", args.region == "northern", args.region == "southern")
    hc5 = HadCRUT5(
        period=args.period,
        regions=regions,
        verbose=args.verbose,
    )

    plotline(hc5, region=args.region, outfile=args.outfile, threshold=1.5)


main()
