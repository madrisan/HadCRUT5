#!/usr/bin/python3

# Parse and plot the HadCRUT5 temperature datasets
# Copyright (c) 2020 Davide Madrisan <davide.madrisan@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

import argparse
import json
import matplotlib as mpl
import matplotlib.pyplot as plt
import netCDF4 as nc
import numpy as np
import os
import requests

__author__ = "Davide Madrisan"
__copyright__ = "Copyright (C) 2020 Davide Madrisan"
__license__ = "GNU General Public License v3.0"
__version__ = "1"
__email__ = "davide.madrisan@gmail.com"
__status__ = "beta"

def copyleft(descr):
    """Print the Copyright message and License """
    return ("{} v.{} ({})\n{} <{}>\nLicense: {}"
            .format(
                descr, __version__, __status__,
                __copyright__, __email__,
                __license__))

def argparser(descr, examples):
    """Return a new ArgumentParser object """
    return argparse.ArgumentParser(
               formatter_class = argparse.RawDescriptionHelpFormatter,
               description = copyleft(descr),
               epilog = "examples:\n  " + "\n  ".join(examples))

def parse_args():
    """This function parses and return arguments passed in """
    descr = "Parse and plot the HadCRUT5 temperature datasets"
    examples = [
       "%(prog)s",
       "%(prog)s --outfile HadCRUT5.png",
       "%(prog)s --period \"1850-1900\" --outfile HadCRUT5-1850-1900.png"]

    parser = argparser(descr, examples)
    parser.add_argument(
        "-f", "--outfile",
        action="store", dest="outfile",
        help="name of the output PNG file")
    parser.add_argument(
        "-p", "--period",
        action="store", dest="period", default="1961-1990",
        help="show anomalies related to 1961-1990 (default) or 1850-1900")

    return parser.parse_args()

def dataset_get(dataset_filename):
    """Download a netCDFv4 HadCRUT5 file if not already found locally"""
    url_datasets = "https://www.metoffice.gov.uk/hadobs"
    url_dataset_hadcrut5 = (
        "{}/hadcrut5/data/current/analysis/diagnostics"
        .format(url_datasets))
    url_dataset = "{}/{}".format(url_dataset_hadcrut5, dataset_filename)

    try:
        with open(dataset_filename) as dataset:
            print ("Using the local dataset file {}".format(dataset_filename))
    except IOError:
        print ("Downloading the file {}".format(dataset_filename))
        response = requests.get(url_dataset, stream=True)
        # Throw an error for bad status codes
        response.raise_for_status()

        with open(dataset_filename, 'wb') as handle:
            for block in response.iter_content(1024):
                handle.write(block)

def dataset_load(dataset_filename):
    """Load the data provided by the netCDFv4 file 'dataset_filename'"""
    dataset = nc.Dataset(dataset_filename)
    metadata = dataset.__dict__
    dimensions = dataset.dimensions
    variables = dataset.variables

    return (metadata, dimensions, variables)

def normalize(tas_mean, period):
    if period == "1961-1990":
        # the original dataset is based on the reference period 1961-1990
        return tas_mean

    # The dataset starts from 1850-01-01 00:00:00
    mean_temp_1850_1900 = np.mean(tas_mean[:50])
    print(("The mean anomaly in {0} is about {1:.8f}°C"
           .format(period,
                   mean_temp_1850_1900)))
    return [round(t - mean_temp_1850_1900, 8) for t in tas_mean[:]]

def plot(datasets, outfile, period):
    mpl.style.use("seaborn-notebook")

    for item in datasets:
        tas_mean = datasets[item]["variables"]["tas_mean"][:]
        tas_mean_normalized = normalize(tas_mean, period)
        years = [y + 1850 for y in range(len(tas_mean_normalized))]
        plt.plot(years, tas_mean_normalized, linewidth=2, markersize=12, label=item)

    plt.title(
        "HadCRUT5: land and sea temperature anomalies relative to {}" .format(period))
    plt.xlabel("Year")
    plt.ylabel("Global Temperatures Anomaly in °C")
    plt.legend()
    plt.axvline(x=2021, color="lightgray", label="2021", linewidth=1,
                linestyle="dotted")

    if outfile:
        plt.savefig(outfile, transparent=False)

    plt.show()

def main():
    args = parse_args()
    if args.period not in ["1850-1900", "1961-1990"]:
        raise Exception("Unsupported reference period: {}".format(args.period))

    # List of the HadCRUT.5.0.0.0 datasets we want to plot.
    # Note: We can dump a NetCFG file using the command:
    #       $ ncdump -h <ncfile>
    datasets = {
        "Global": {
            "filename": "HadCRUT.5.0.0.0.analysis.summary_series.global.annual.nc"
        },
        "Northern Hemisphere": {
            "filename": "HadCRUT.5.0.0.0.analysis.summary_series.northern_hemisphere.annual.nc"
        },
        "Southern Hemisphere": {
            "filename": "HadCRUT.5.0.0.0.analysis.summary_series.southern_hemisphere.annual.nc"
        }
    }

    for item in datasets:
        datafile = datasets[item]["filename"]
        dataset_get(datafile)
        metadata, dimensions, variables = dataset_load(datafile)
        datasets[item].update({
            "metadata": metadata,
            "dimensions": dimensions,
            "variables": variables
        })

    plot(datasets, args.outfile, args.period)

if __name__ == "__main__":
    main()
