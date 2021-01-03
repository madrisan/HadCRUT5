#!/usr/bin/python3

# Parse and plot the HadCRUT5 temperature datasets
# Copyright (c) 2020 Davide Madrisan <davide.madrisan@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

import argparse
import json
import matplotlib as mpl
import matplotlib.pyplot as plt
import netCDF4 as nc
import os
import requests

__author__ = "Davide Madrisan"
__copyright__ = "Copyright (C) 2020 Davide Madrisan"
__license__ = "Apache License 2.0 (Apache-2.0)"
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
       "%(prog)s --outfile HadCRUT5.png"]

    parser = argparser(descr, examples)
    parser.add_argument(
        "-f", "--outfile",
        action="store", dest="outfile",
        help="name of the output PNG file")

    return parser.parse_args()

# You can dump a NetCFG file using the command:
# $ ncdump -h <ncfile>

def dataset_load(dataset_filename):
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

    dataset = nc.Dataset(dataset_filename)
    metadata = dataset.__dict__
    dimensions = dataset.dimensions
    variables = dataset.variables

    return (metadata, dimensions, variables)

def plot(datasets, outfile):
    mpl.style.use("seaborn-notebook")

    for item in datasets:
        metadata, dimensions, variables = dataset_load(datasets[item])
        tas_mean = variables['tas_mean'][:]

        years = [y + 1850 for y in range(len(tas_mean))]

        plt.plot(years, tas_mean, linewidth=2, markersize=12, label=item)

    plt.title("HadCRUT5: land and sea temperature anomalies relative to 1961-1990")
    plt.xlabel("Year")
    plt.ylabel("Global Temperatures Anomaly in °C")
    plt.legend()
    plt.axvline(x=2021, color="lightgray", label="2021", linewidth=1,
                linestyle="dotted")

    if outfile:
        plt.savefig(outfile, transparent=False)

    plt.show()

def main():
    datasets = {
        "Global":
             "HadCRUT.5.0.0.0.analysis.summary_series.global.annual.nc",
        "Northern Hemisphere":
            "HadCRUT.5.0.0.0.analysis.summary_series.northern_hemisphere.annual.nc",
        "Southern Hemisphere":
            "HadCRUT.5.0.0.0.analysis.summary_series.southern_hemisphere.annual.nc"
    }

    args = parse_args()
    plot(datasets, args.outfile)

if __name__ == "__main__":
    main()
