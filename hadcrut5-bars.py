#!/usr/bin/python3

# Parse and plot the HadCRUT5 temperature datasets
# Copyright (c) 2020 Davide Madrisan <davide.madrisan@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

import argparse
import math
import matplotlib as mpl
import matplotlib.pyplot as plt
import netCDF4 as nc
import numpy as np
import requests

import hadcrut5lib as hadcrut5

def parse_args():
    """This function parses and return arguments passed in """
    descr = "Parse and plot the HadCRUT5 temperature datasets"
    examples = [
       "%(prog)s",
       "%(prog)s --outfile HadCRUT5.png",
       "%(prog)s --period \"1850-1900\" --outfile HadCRUT5-1850-1900.png",
       "%(prog)s --period \"1880-1920\" --outfile HadCRUT5-1880-1920.png"]

    parser = hadcrut5.argparser(descr, examples)
    parser.add_argument(
        "-f", "--outfile",
        action="store", dest="outfile",
        help="name of the output PNG file")
    parser.add_argument(
        "-p", "--period",
        action="store", dest="period", default="1961-1990",
        help="show anomalies related to 1961-1990 (default), 1850-1900, or 1880-1920")
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        dest="verbose",
        help="make the operation more talkative")

    return parser.parse_args()

def plotbar(datasets, outfile, period, verbose):
    plt.style.use('dark_background')
    ax = plt.subplot(111)
    bar_width = 0.7

    negative = [
        "#e6eeff", "#ccddff", "#b3ccff",
        "#99bbff", "#80aaff", "#6699ff",
        "#4d88ff", "#3377ff", "#1a66ff",
        "#0055ff", "#004de6", "#0044cc",
        "#003cb3", "#003399", "#002b80"
    ]
    positive = [
        "#fee6e8", "#fdced2", "#fdb5bb",
        "#fc9ca4", "#fb838d", "#fa6b77",
        "#fa5260", "#f93949", "#f82032",
        "#f7091c", "#df0719", "#c60616",
        "#ad0513", "#940511", "#7c040e"
    ]

    fontxl = {
        'family': 'DejaVu Sans',
        'color' : 'white',
        'weight': 'bold',
        'size'  : 16
    }
    fontxs = {
        'family': 'DejaVu Sans',
        'color' : 'white',
        'weight': 'normal',
        'size'  : 10
    }

    for itemnum, item in enumerate(datasets):
        tas_mean = datasets[item]["variables"]["tas_mean"][:]

        years = [y + 1850 for y in range(len(tas_mean))]
        if verbose:
            print("years: \\\n{}".format(np.array(years)))
            print("temperatures: \\\n{}".format(tas_mean))

        mean, norm_temp = hadcrut5.dataset_normalize(tas_mean, period)
        if verbose:
            print(("The mean anomaly in {0} is about: {1:.8f}°C"
                   .format(period, norm_temp)))
            print(("tas_mean relative to {}: \\\n{}"
                   .format(period, np.array(mean))))

        color_deep = lambda x: math.floor(math.fabs(x * 10))
        get_color = lambda x: positive[color_deep(x)] if x > 0 else negative[color_deep(x)]
        colors = [get_color(i) for i in mean]

        ax.bar(years,
               mean,
               width=bar_width,
               color=colors,
               alpha=0.6,
               align='center')

    if outfile:
        plt.savefig(outfile, transparent=False)

    #plt.axis('off')
    ax.yaxis.set_label_position("right")
    ax.yaxis.tick_right()
    ax.set(xticklabels=[])
    ax.axes.get_xaxis().set_visible(False)

    plt.text(1850, 1.20, 'Global average temperature difference *',
             fontdict=fontxl)
    plt.text(1850, 1.10, "1850-2021",
            fontdict=fontxl)
    plt.text(1850, 0.95, "* Compared to {} pre-industrial levels".format(period),
             fontdict=fontxs)
    plt.text(1850, 0.90, "Data source - HadCRUT5",
             fontdict=fontxs)
    #plt.tick_params(labelbottom=True)
    plt.tight_layout()
    plt.show()

def main():
    args = parse_args()
    if args.period not in ["1850-1900", "1880-1920", "1961-1990"]:
        raise Exception(("Unsupported reference period: {}"
                         .format(args.period)))

    datasets = hadcrut5.dataset_set(True, False, False)

    for item in datasets:
        datafile = datasets[item]["filename"]
        hadcrut5.dataset_get(datafile, args.verbose)
        data = hadcrut5.dataset_load(datafile)
        datasets[item].update(data)

    plotbar(datasets,
            args.outfile,
            args.period,
            args.verbose)

if __name__ == "__main__":
    main()
