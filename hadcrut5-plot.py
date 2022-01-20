#!/usr/bin/python3
# Copyright (c) 2020-2022 Davide Madrisan <davide.madrisan@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Display a plot of the HadCRUT5 temperature dataset.
"""

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

import hadcrut5lib as hadcrut5

def parse_args():
    """This function parses and return arguments passed in"""
    descr = "Parse and plot the HadCRUT5 temperature datasets"
    examples = [
       "%(prog)s",
       "%(prog)s --global --annotate=2",
       "%(prog)s --period \"1850-1900\"",
       "%(prog)s --period \"1850-1900\" --smoother 5",
       "%(prog)s --period \"1880-1920\" --outfile HadCRUT5-1880-1920.png",
       "%(prog)s --period \"1880-1920\" --time-series monthly --global"]

    parser = hadcrut5.argparser(descr, examples)
    parser.add_argument(
        "-a", "--annotate",
        action="store", dest="annotate", default="1",
        help="add temperature annotations (0: no annotations, 1 (default): "
             "bottom only, 2: all ones")
    parser.add_argument(
        "-f", "--outfile",
        action="store",
        dest="outfile",
        help="name of the output PNG file")
    parser.add_argument(
        "-g", "--global",
        action="store_true",
        dest="plot_global",
        help="plot the Global Temperatures")
    parser.add_argument(
        "-m", "--smoother",
        action="store",
        dest="smoother",
        help="make the lines smoother by using N-year means")
    parser.add_argument(
        "-n", "--northern",
        action="store_true",
        dest="plot_northern",
        help="Northern Hemisphere Temperatures")
    parser.add_argument(
        "-p", "--period",
        action="store",
        dest="period",
        default="1961-1990",
        help="show anomalies related to 1961-1990 (default), 1850-1900, or 1880-1920")
    parser.add_argument(
        "-s", "--southern",
        action='store_true',
        dest="plot_southern",
        help="Southern Hemisphere Temperatures")
    parser.add_argument(
        "-t", "--time-series",
        action='store',
        default="annual",
        dest="time_series",
        help="do plot the \"annual\" time series (default) or the \"monthly\" one")
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        dest="verbose",
        help="make the operation more talkative")

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
    subset_years = [years[i*chunksize] for i in data_range]
    subset_temperatures = [
        np.mean(temperatures[i*chunksize:(i+1)*chunksize]) for i in data_range
    ]

    return subset_years, subset_temperatures

def plotline(period,
             time_series,
             regions,
             chunksize,
             annotate,
             outfile,
             verbose):
    """
    Create a plot for the specified period and arguments and diplay it or save
    it to file if outfile is set
    """
    hc5 = hadcrut5.HadCRUT5(period=period,
                            datatype=time_series,
                            regions=regions,
                            verbose=verbose)

    hc5.download_datasets()
    hc5.load_datasets()
    datasets = hc5.datasets

    mpl.style.use("seaborn-notebook")
    anomaly_current = {}
    anomaly_max = {}

    for item in datasets:
        tas_mean = hc5.dataset_mean(item)
        tas_lower, tas_upper = hc5.dataset_range(item)

        is_monthly = hc5.is_monthly_dataset
        factor = 1/12 if is_monthly else 1

        years = [1850 + (y * factor) for y in range(len(tas_mean))]
        if verbose:
            print("years: \\\n{}".format(np.array(years)))
            print("temperatures ({}): \\\n{}".format(item, tas_mean))

        mean, norm_temp = hc5.dataset_normalize(tas_mean)
        if verbose:
            print(("The mean anomaly ({0}) in {1} is about: {2:.8f}°C"
                   .format(item, period, norm_temp)))
            print(("tas_mean ({}) relative to {}: \\\n{}"
                   .format(item, period, np.array(mean))))

        lower, _ = hc5.dataset_normalize(tas_lower, norm_temp)
        upper, _ = hc5.dataset_normalize(tas_upper, norm_temp)

        if chunksize > 1:
            years, mean = dataset_smoother(years, mean, chunksize)
            if verbose:
                print("years: \\\n{}".format(np.array(years)))
                print("temperatures ({}): \\\n{}".format(item, mean))
                print("delta ({}): \\\n{}".format(years[-1], mean[-1]))
        else:
            plt.fill_between(years, lower, upper, color="lightgray")

            anomaly_current[item] = dataset_current_anomaly(mean)
            anomaly_max[item] = dataset_max_anomaly(mean)
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

        plt.plot(years,
                 mean,
                 linewidth=(1 if is_monthly and chunksize < 2 else 2),
                 markersize=12,
                 label=item)

    plt.hlines(0, np.min(years), np.max(years),
               colors='gray', linestyles='dotted')

    plt.title(
        "HadCRUT5: land and sea temperature anomalies relative to {}".format(period))
    plt.xlabel("year", fontsize=10)

    ylabel = ("{} Temperature Anomalies in °C"
              .format("Monthly" if is_monthly else "Annual"))
    if chunksize > 1:
        ylabel += " ({}-year averages)".format(chunksize)
    else:
        current = anomaly_current.get('Global')
        maximum = anomaly_max.get('Global')
        if annotate > 0 and current and maximum:
            plt.gca()
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

    plotline(args.period,
             args.time_series,
             regions,
             int(args.smoother) if args.smoother else 1,
             int(args.annotate) if args.annotate else 1,
             args.outfile,
             args.verbose)

main()
