#!/usr/bin/python3

# Parse and plot the HadCRUT5 temperature datasets
# Copyright (c) 2020-2022 Davide Madrisan <davide.madrisan@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

import argparse
import math
import matplotlib.pyplot as plt
import matplotlib.colors

import netCDF4 as nc
import numpy as np
import requests

import hadcrut5lib as hadcrut5

def parse_args():
    """This function parses and return arguments passed in """
    descr = "Parse and plot the HadCRUT5 temperature datasets"
    examples = [
       "%(prog)s",
       "%(prog)s --period \"1850-1900\"",
       "%(prog)s --period \"1880-1920\"",
       "%(prog)s --outfile HadCRUT5-global.png"]

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

def plotbar(dataset, outfile, period, verbose):
    def major_formatter(x, pos):
        return f'{x:.1f}' if x >= 0 else ''

    bar_width = 0.7
    basefont = {
        'family': 'DejaVu Sans',
        'color' : 'white',
        'weight': 'bold',
    }
    fontxl = { **basefont, "size": 20 }
    fontxs = { **basefont, "size": 12 }

    plt.style.use("dark_background")
    fix, ax = plt.subplots()

    tas_mean = dataset["variables"]["tas_mean"][:]
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

    cmap = plt.cm.jet # or plt.cm.bwr
    norm = matplotlib.colors.Normalize(vmin=-1, vmax=max(mean))
    colors = cmap(norm(mean))

    ax.bar(years,
           mean,
           width=bar_width,
           color=colors,
           align="center")

    ax.set_frame_on(False)
    ax.yaxis.tick_right()
    ax.yaxis.set_major_formatter(major_formatter)
    ax.tick_params(axis=u'both', which=u'both',length=0)

    upper, left = .95, .025
    last_year = years[-1]

    text_props = dict(horizontalalignment="left",
                      verticalalignment="top",
                      transform=ax.transAxes)
    plt.text(left, upper,
             '\n'.join((
                 r"Global average temperature difference *",
                 r"1850-{}".format(last_year))),
             fontdict=fontxl,
             linespacing=1.2,
             **text_props)
    plt.text(left, upper - .125,
             '\n'.join((
                 r"(*) Compared to {} pre-industrial levels".format(period),
                 r"Data source - HadCRUT5")),
             fontdict=fontxs,
             linespacing=1.5,
             **text_props)

    fig = plt.gcf()
    fig.set_size_inches(10, 8)   # 1 inch equal to 80pt

    if outfile:
        fig.savefig(outfile, dpi=80, bbox_inches='tight')
        plt.close(fig)

    plt.show()

def main():
    args = parse_args()
    if args.period not in ["1850-1900", "1880-1920", "1961-1990"]:
        raise Exception(("Unsupported reference period: {}"
                         .format(args.period)))

    datasets = hadcrut5.dataset_set_annual(True, False, False)
    global_dataset = datasets["Global"]

    datafile = global_dataset["filename"]
    hadcrut5.dataset_get(datafile, args.verbose)
    data = hadcrut5.dataset_load(datafile)
    global_dataset.update(data)

    plotbar(global_dataset,
            args.outfile,
            args.period,
            args.verbose)

if __name__ == "__main__":
    main()
