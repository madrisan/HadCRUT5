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


class HadCRUT5(object):
    """Class for parsing and plotting HadCRUT5 datasets"""

    """current dataset version"""
    _DATASET_VERSION = "5.0.1.0"

    """list of all the valid periods"""
    _DEFAULT_PERIOD = "1961-1990"
    _VALID_PERIODS = [_DEFAULT_PERIOD, "1850-1900", "1880-1920"]

    """list of all the available data types"""
    _DEFAULT_DATATYPE = "annual"
    _VALID_DATATYPES = [_DEFAULT_DATATYPE, "monthly"]

    def __init__(self,
                 period = _DEFAULT_PERIOD,
                 datatype = _DEFAULT_DATATYPE,
                 enable_global = True,
                 enable_northern = True,
                 enable_southern = True,
                 verbose = False):

        if datatype not in self._VALID_DATATYPES:
            raise Exception(("Unsupported time series type \"{}\""
                             .format(datatype)))
        if period not in self._VALID_PERIODS:
            raise Exception(("Unsupported reference period: {}"
                             .format(period)))

        # will be populated by load_datasets()
        self._datasets = {}

        self._datatype = datatype
        self._period = period
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

    def download_datasets(self):
        if self._enable_global:
            self._wget_dataset_file(self._global_filename)
        if self._enable_northern:
            self._wget_dataset_file(self._northern_hemisphere_filename)
        if self._enable_southern:
            self._wget_dataset_file(self._southern_hemisphere_filename)

    def load_datasets(self):
        """Load all the netCDFv4 datasets"""

        def dataset_load(dataset_filename):
            """Load the data provided by the netCDFv4 file 'dataset_filename'"""
            dataset = nc.Dataset(dataset_filename)
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

    @staticmethod
    def _hadcrut5_data_url(filename):
        site = "https://www.metoffice.gov.uk"
        path = "/hadobs/hadcrut5/data/current/analysis/diagnostics/"
        url = "{}{}{}".format(site, path, filename)
        return url

    def _wget_dataset_file(self, filename):
        """Download a netCDFv4 HadCRUT5 file if not already found locally"""
        try:
            with open(filename) as dataset:
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
    def datasets(self):
        return self._datasets

    def dataset_mean(self, datatype):
        return self._datasets[datatype]["variables"]["tas_mean"][:]

    def dataset_normalize(self, tas_mean, norm_temp=None):
        """
        Produce the temperature means relative to the given period
        If the norm_temp is not set it's calculated according to the given
        period. Otherwise the value is used as normalization factor.
        """
        if self._period == "1961-1990":
            # No changes required:
            # the original dataset is based on the reference period 1961-1990
            return (tas_mean, 0)

        m = 12 if self.is_monthly_dataset else 1

        if not norm_temp:
            if self._period == "1850-1900":
                # The dataset starts from 1850-01-01 00:00:00
                # so we calculate the mean of the first 50 years
                norm_temp = np.mean(tas_mean[:50*m])
            elif self._period == "1880-1920":
                # We have to skip the first 30 years here
                norm_temp = np.mean(tas_mean[30*m:41*m])
            else:
                # should never happen...
                raise Exception(("Unsupported period \"{}\""
                                 .format(self._period)))

        tas_mean_normalized = [
            round(t - norm_temp, 8) for t in tas_mean[:]]

        return tas_mean_normalized, norm_temp

    def dataset_range(self, datatype):
        tas_lower = self._datasets[datatype]["variables"]["tas_lower"][:]
        tas_upper = self._datasets[datatype]["variables"]["tas_upper"][:]
        return (tas_lower, tas_upper)

    @property
    def is_monthly_dataset(self):
        return False if self._datatype == "annual" else True

    @property
    def global_filename(self):
        return self._global_filename
    @property
    def northern_hemisphere_filename(self):
        return self._northern_hemisphere_filename
    @property
    def southern_hemisphere_filename(self):
        return self._southern_hemisphere_filename

    @property
    def verbose(self):
        """Return the verbosity status"""
        return self._verbose
