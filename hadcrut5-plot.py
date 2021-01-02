#!/usr/bin/python3

# Parse and plot the HadCRUT5 temperature datasets
# Copyright (c) 2020 Davide Madrisan <davide.madrisan@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

import json
import matplotlib as mpl
import matplotlib.pyplot as plt
import netCDF4 as nc
import os
import requests
import yaml

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

def main():
    datasets = {
        "Global": "HadCRUT.5.0.0.0.analysis.summary_series.global.annual.nc",
        "Northern Hemisphere": "HadCRUT.5.0.0.0.analysis.summary_series.northern_hemisphere.annual.nc",
        "Southern Hemisphere": "HadCRUT.5.0.0.0.analysis.summary_series.southern_hemisphere.annual.nc" 
    }

    mpl.style.use("seaborn-notebook")
    #mpl.style.use("seaborn-muted")

    for item in datasets:
        metadata, dimensions, variables = dataset_load(datasets[item])
        tas_mean = variables['tas_mean'][:]

        years = [y + 1850 for y in range(len(tas_mean))]

        plt.plot(years, tas_mean, linewidth=2, markersize=12, label=item)

    plt.title("HadCRUT5: land and sea temperature anomalies relative to 1961-1990")
    plt.xlabel("Year")
    plt.ylabel("Global Temperatures Anomaly in °C")
    plt.legend()

    plt.savefig("HadCRUT5.png", transparent=False)

    plt.show()

if __name__ == "__main__":
    main()
