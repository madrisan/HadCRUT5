#!/usr/bin/python3

# Parse and plot the HadCRUT5 temperature datasets
# Copyright (c) 2020-2022 Davide Madrisan <davide.madrisan@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

import argparse
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
       "%(prog)s --annotate=2",
       "%(prog)s --global",
       "%(prog)s --period \"1850-1900\"",
       "%(prog)s --period \"1850-1900\" --smoother 5",
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
        "-m", "--smoother",
        action="store", dest="smoother",
        help="make the lines smoother by using N-year means")
    parser.add_argument(
        "-g", "--global",
        action="store_true",
        dest="global_temps",
        help="plot the Global Temperatures")
    parser.add_argument(
        "-n", "--northern",
        action="store_true",
        dest="northern_temps",
        help="Northern Hemisphere Temperatures")
    parser.add_argument(
        "-s", "--southern",
        action='store_true',
        dest="southern_temps",
        help="Southern Hemisphere Temperatures")
    parser.add_argument(
        "-a", "--annotate",
        action="store", dest="annotate", default="1",
        help="add temperature annotations (0: no annotations, 1 (default): bottom only, 2: all ones")
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        dest="verbose",
        help="make the operation more talkative")

    return parser.parse_args()

def plotline(datasets, outfile, period, chunksize, annotate, verbose):
    mpl.style.use("seaborn-notebook")
    anomaly_current = {}
    anomaly_max = {}

    for item in datasets:
        tas_mean  = datasets[item]["variables"]["tas_mean"][:]
        tas_lower = datasets[item]["variables"]["tas_lower"][:]
        tas_upper = datasets[item]["variables"]["tas_upper"][:]

        years = [y + 1850 for y in range(len(tas_mean))]
        if verbose:
            print("years: \\\n{}".format(np.array(years)))
            print("temperatures ({}): \\\n{}".format(item, tas_mean))

        mean, norm_temp = hadcrut5.dataset_normalize(tas_mean, period)
        if verbose:
            print(("The mean anomaly ({0}) in {1} is about: {2:.8f}°C"
                   .format(item, period, norm_temp)))
            print(("tas_mean ({}) relative to {}: \\\n{}"
                   .format(item, period, np.array(mean))))

        lower, _ = hadcrut5.dataset_normalize(tas_lower, period, norm_temp)
        upper, _ = hadcrut5.dataset_normalize(tas_upper, period, norm_temp)

        if chunksize > 1:
            years, mean = hadcrut5.dataset_smoother(years, mean, chunksize)
            if verbose:
                print("years: \\\n{}".format(np.array(years)))
                print("temperatures ({}): \\\n{}".format(item, mean))
                print("delta ({}): \\\n{}".format(years[-1], mean[-1]))
        else:
            plt.fill_between(years, lower, upper, color="lightgray")

            anomaly_current[item] = hadcrut5.dataset_current_anomaly(mean)
            anomaly_max[item] = hadcrut5.dataset_max_anomaly(mean)
            if verbose:
                print("Current anomalies: {}".format(anomaly_current[item]))
                print("Max anomalies: {}".format(anomaly_max[item]))

            if annotate > 1:
                plt.annotate("{0:.2f}°C".format(anomaly_current[item]),
                             xy=(years[-1]-5, anomaly_current[item]+.05),
                             fontsize=6,
                             horizontalalignment='left',
                             bbox={
                                 "facecolor": "lightgray",
                                 "alpha": 0.6,
                                 "pad": 3
                            }
                )

        plt.plot(years, mean, linewidth=2, markersize=12, label=item)

    plt.hlines(0, np.min(years), np.max(years),
               colors='gray', linestyles='dotted')

    plt.title(
        "HadCRUT5: land and sea temperature anomalies relative to {}".format(period))
    plt.xlabel("year", fontsize=10)

    ylabel = "Temperature Anomalies in °C"
    if chunksize > 1:
        ylabel += " ({}-year averages)".format(chunksize)
    else:
        current = anomaly_current.get('Global')
        maximum = anomaly_max.get('Global')
        if annotate > 0 and current and maximum:
            ax = plt.gca()
            plt.annotate(("current global anomaly: {0:+.2f}°C, max: {1:+.2f}°C"
                          .format(current, maximum)),
                         xy=(0.98, 0.03),
                         xycoords="axes fraction",
                         fontsize=8,
                         horizontalalignment="right",
                         verticalalignment="bottom",
                         bbox={
                             "facecolor": "{}".format(
                                 "blue" if current <= 0 else "red"
                             ),
                             "alpha": 0.3,
                             "pad": 5,
                         })

    plt.ylabel(ylabel, fontsize=10)
    plt.legend()

    if outfile:
        plt.savefig(outfile, transparent=False)
    else:
        plt.show()

def main():
    args = parse_args()
    if args.period not in ["1850-1900", "1880-1920", "1961-1990"]:
        raise Exception("Unsupported reference period: {}".format(args.period))

    if args.global_temps or args.northern_temps or args.southern_temps:
        global_temps = args.global_temps
        northern_temps = args.northern_temps
        southern_temps = args.southern_temps
    else:
        global_temps = northern_temps = southern_temps = True

    datasets = hadcrut5.dataset_set(global_temps,
                                    northern_temps,
                                    southern_temps)

    for item in datasets:
        datafile = datasets[item]["filename"]
        hadcrut5.dataset_get(datafile, args.verbose)
        data = hadcrut5.dataset_load(datafile)
        datasets[item].update(data)

    plotline(datasets,
             args.outfile,
             args.period,
             int(args.smoother) if args.smoother else 1,
             int(args.annotate) if args.annotate else 1,
             args.verbose)

if __name__ == "__main__":
    main()
