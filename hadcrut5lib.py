#!/usr/bin/python3

# The library functions for parsing the HadCRUT5 temperature datasets
# Copyright (c) 2020-2022 Davide Madrisan <davide.madrisan@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

import argparse
import netCDF4 as nc
import numpy as np
import requests

__author__ = "Davide Madrisan"
__copyright__ = "Copyright (C) 2020-2022 Davide Madrisan"
__license__ = "GNU General Public License v3.0"
__version__ = "2"
__email__ = "davide.madrisan@gmail.com"
__status__ = "stable"

def copyleft(descr):
    """Print the Copyright message and License """
    return ("{} v.{} ({})\n{} <{}>\nLicense: {}"
            .format(descr, __version__, __status__,
                    __copyright__, __email__,
                    __license__))

def argparser(descr, examples):
    """Return a new ArgumentParser object """
    return argparse.ArgumentParser(
               formatter_class = argparse.RawDescriptionHelpFormatter,
               description = copyleft(descr),
               epilog = "examples:\n  " + "\n  ".join(examples))

def dataset_get(dataset_filename, verbose):
    """Download a netCDFv4 HadCRUT5 file if not already found locally"""
    url_datasets = "https://www.metoffice.gov.uk/hadobs"
    url_dataset_hadcrut5 = (
        "{}/hadcrut5/data/current/analysis/diagnostics"
        .format(url_datasets))
    url_dataset = "{}/{}".format(url_dataset_hadcrut5, dataset_filename)

    try:
        with open(dataset_filename) as dataset:
            if verbose:
                print(("Using the local dataset file: {}"
                       .format(dataset_filename)))
    except IOError:
        if verbose:
            print ("Downloading {} ...".format(dataset_filename))

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

    return {
        "dimensions": dimensions,
        "metadata"  : metadata,
        "variables" : variables
    }

def dataset_normalize(tas_mean, period, norm_temp=None):
    """
    Produce the temperature means relative to the given period
    If the norm_temp is not set it's calculated according to the given period.
    Otherwise this value is used as normalization factor.
    """
    if period == "1961-1990":
        # No changes required:
        # the original dataset is based on the reference period 1961-1990
        return (tas_mean, 0)

    if not norm_temp:
        if period == "1850-1900":
            # The dataset starts from 1850-01-01 00:00:00
            norm_temp = np.mean(tas_mean[:50])
        elif period == "1880-1920":
            norm_temp = np.mean(tas_mean[30:41])
        else:
            raise Exception("Unsupported period \"{}\"".format(period))

    tas_mean_normalized = [
        round(t - norm_temp, 8) for t in tas_mean[:]]

    return tas_mean_normalized, norm_temp

def dataset_set_annual(global_temps, northern_temps, southern_temps):
    # List of the HadCRUT.5.0.1.0 datasets we want to plot.
    # Note: We can dump a NetCFG file using the command:
    #       $ ncdump -h <ncfile>
    datasets = {}

    if global_temps:
        datasets["Global"] = {
            "filename": "HadCRUT.5.0.1.0.analysis.summary_series.global.annual.nc"
        }
    if northern_temps:
        datasets["Northern Hemisphere"] = {
            "filename": "HadCRUT.5.0.1.0.analysis.summary_series.northern_hemisphere.annual.nc"
        }
    if southern_temps:
        datasets["Southern Hemisphere"] = {
            "filename": "HadCRUT.5.0.1.0.analysis.summary_series.southern_hemisphere.annual.nc"
        }

    return datasets

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
        np.mean(temperatures[i*chunksize:(i+1)*chunksize]) for i in data_range]
    return subset_years, subset_temperatures
