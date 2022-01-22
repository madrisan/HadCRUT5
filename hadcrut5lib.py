#!/usr/bin/python3
# Copyright (c) 2020-2022 Davide Madrisan <davide.madrisan@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

"""
HadCRUT5 class and library functions for parsing the HadCRUT5 temperature
datasets.  See: https://www.metoffice.gov.uk/hadobs/hadcrut5/
"""

import argparse
import numpy as np
import requests

# pylint: disable=E0611
from netCDF4 import Dataset as nc_Dataset
# pylint: enable=E0611

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

def dprint(verbose, message):
    """Print a message when in verbose mode only"""
    if verbose:
        print(message)

# pylint: disable=R0902
class HadCRUT5:
    """Class for parsing and plotting HadCRUT5 datasets"""

    # current dataset version
    _DATASET_VERSION = "5.0.1.0"

    # list of all the available data types
    _DEFAULT_DATATYPE = "annual"
    _VALID_DATATYPES = [_DEFAULT_DATATYPE, "monthly"]

    # list of all the valid periods
    _DEFAULT_PERIOD = "1961-1990"
    _VALID_PERIODS = [_DEFAULT_PERIOD, "1850-1900", "1880-1920"]

    GLOBAL_REGION = "Global"

    def __init__(self,
                 period=_DEFAULT_PERIOD,
                 datatype=_DEFAULT_DATATYPE,
                 regions=(True, False, False),
                 smoother=1,
                 verbose=False):

        enable_global, enable_northern, enable_southern = regions

        if datatype not in self._VALID_DATATYPES:
            raise Exception(("Unsupported time series type \"{}\""
                             .format(datatype)))
        if period not in self._VALID_PERIODS:
            raise Exception(("Unsupported reference period: {}"
                             .format(period)))

        # will be populated by datasets_load()
        self._datasets = {}
        # will be populated by datasets_normalize()
        self._datasets_normalized = {}

        self._datatype = datatype
        self._period = period
        self._smoother = smoother
        self._verbose = verbose

        self._enable_global = enable_global
        self._enable_northern = enable_northern
        self._enable_southern = enable_southern

        self._global_filename = (
            "HadCRUT.{}.analysis.summary_series.global.{}.nc"
            .format(self._DATASET_VERSION, datatype))
        self._northern_hemisphere_filename = (
            "HadCRUT.{}.analysis.summary_series.northern_hemisphere.{}.nc"
            .format(self._DATASET_VERSION, datatype))
        self._southern_hemisphere_filename = (
            "HadCRUT.{}.analysis.summary_series.southern_hemisphere.{}.nc"
            .format(self._DATASET_VERSION, datatype))

    def datasets_download(self):
        """Download the required HadCRUT5 datasets"""
        # The Global dataset need to be always download, because it's used
        # in the temperatures normalization step
        self._wget_dataset_file(self._global_filename)
        if self._enable_northern:
            self._wget_dataset_file(self._northern_hemisphere_filename)
        if self._enable_southern:
            self._wget_dataset_file(self._southern_hemisphere_filename)

    def datasets_load(self):
        """Load all the netCDFv4 datasets"""

        def dataset_load(dataset_filename):
            """Load the data provided by the netCDFv4 file 'dataset_filename'"""
            dataset = nc_Dataset(dataset_filename)
            return {
                "dimensions": dataset.dimensions,
                "metadata"  : dataset.__dict__,
                "variables" : dataset.variables,
            }

        if self._enable_global:
            self._datasets["Global"] = dataset_load(self._global_filename)
        if self._enable_northern:
            self._datasets["Northern Hemisphere"] = \
                dataset_load(self._northern_hemisphere_filename)
        if self._enable_southern:
            self._datasets["Southern Hemisphere"] = \
                dataset_load(self._southern_hemisphere_filename)

    def datasets_normalize(self):
        """
        Normalize the temperature means to the required time period.
        See _VALID_PERIODS.
        Return a tuple containing lower, mean, and upper temperatures.
        """
        for region in self._datasets:
            lower = self._datasets[region]["variables"]["tas_lower"]
            mean = self._datasets[region]["variables"]["tas_mean"]
            upper = self._datasets[region]["variables"]["tas_upper"]

            self._datasets_normalized[region] = {
                "lower": np.array(lower),
                "mean": np.array(mean),
                "upper": np.array(upper)
            }

            dprint(self._verbose,
                   "dataset ({}): mean \\\n{}".format(region, mean))

        if self._period == "1961-1990":
            # No changes required: the original dataset is based on the
            # reference period 1961-1990
            return

        # The Global dataset load can be disabled in the command-line but
        # it's necessary here
        ds_global = nc_Dataset(self._global_filename)
        tas_mean = ds_global.variables["tas_mean"][:]
        factor = 12 if self.is_monthly_dataset else 1

        if self._period == "1850-1900":
            # The dataset starts from 1850-01-01 00:00:00
            # so we calculate the mean of the first 50 years
            norm_temp = np.mean(tas_mean[:50*factor])
        elif self._period == "1880-1920":
            # We have to skip the first 30 years here
            norm_temp = np.mean(tas_mean[30*factor:41*factor])
        else:
            # this should never happen...
            raise Exception(("Unsupported period \"{}\"".format(self._period)))

        dprint(self._verbose, ("The mean anomaly in {0} is about {1:.8f}°C"
                               .format(self._period, norm_temp)))

        for region in self._datasets_normalized:
            lower = self._datasets_normalized[region]["lower"] - norm_temp
            mean = self._datasets_normalized[region]["mean"] - norm_temp
            upper = self._datasets_normalized[region]["upper"] - norm_temp

            self._datasets_normalized[region] = {
                "lower": lower,
                "mean" : mean,
                "upper": upper,
            }

            dprint(self._verbose,
                   "normalized dataset ({}): mean \\\n{}".format(region, mean))

    def datasets_regions(self):
        """Return the dataset regions set by the user at command-line"""
        return self._datasets.keys()

    @staticmethod
    def _hadcrut5_data_url(filename):
        site = "https://www.metoffice.gov.uk"
        path = "/hadobs/hadcrut5/data/current/analysis/diagnostics/"
        url = "{}{}{}".format(site, path, filename)
        return url

    def _wget_dataset_file(self, filename):
        """Download a netCDFv4 HadCRUT5 file if not already found locally"""
        try:
            with open(filename):
                if self._verbose:
                    print("Using the local dataset file: {}".format(filename))
        except IOError:
            if self._verbose:
                print ("Downloading {} ...".format(filename))

            url_dataset = self._hadcrut5_data_url(filename)
            response = requests.get(url_dataset, stream=True)
            # Throw an error for bad status codes
            response.raise_for_status()

            with open(filename, 'wb') as handle:
                for block in response.iter_content(1024):
                    handle.write(block)

    @property
    def dataset_datatype(self):
        """Return the datatype string"""
        return self._datatype

    def dataset_normalized_data(self, region):
        """Return the dataset data normalized for the specified region"""
        lower = self._datasets_normalized[region]["lower"]
        mean = self._datasets_normalized[region]["mean"]
        upper = self._datasets_normalized[region]["upper"]
        return (lower, mean, upper)

    @property
    def dataset_period(self):
        """Return the dataset period as a string"""
        return self._period

    def dataset_years(self):
        """Return an array of years corresponding of the loaded dataset"""
        mean = self._datasets[self.GLOBAL_REGION]["variables"]["tas_mean"][:]
        factor = 1/12 if self.is_monthly_dataset else 1
        years = [1850 + (y * factor) for y in range(len(mean))]
        dprint(self._verbose, "years: \\\n{}".format(np.array(years)))
        return years

    @property
    def is_monthly_dataset(self):
        """
        Return True if the loaded dataset provide monthly data,
        False otherwise
        """
        return self._datatype == "monthly"
