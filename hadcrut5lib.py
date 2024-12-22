#!/usr/bin/python3
# Copyright (c) 2020-2024 Davide Madrisan <d.madrisan@proton.me>
# SPDX-License-Identifier: GPL-3.0-or-later

"""
HadCRUT5 class and library functions for parsing the HadCRUT5 temperature
datasets.  See: https://www.metoffice.gov.uk/hadobs/hadcrut5/
"""

import argparse
import json
import logging
import sys

import numpy as np
import requests

# pylint: disable=E0611
from netCDF4 import Dataset as nc_Dataset

# pylint: enable=E0611

__author__ = "Davide Madrisan"
__copyright__ = "Copyright (C) 2020-2024 Davide Madrisan"
__license__ = "GNU General Public License v3.0"
__version__ = "2024.1"
__email__ = "d.madrisan@proton.me"
__status__ = "stable"


def copyleft(descr):
    """Print the Copyright message and License"""
    return (
        f"{descr} v{__version__} ({__status__})\n"
        "{__copyright__} <{__email__}>\nLicense: {__license__}"
    )


def argparser(descr, examples):
    """Return a new ArgumentParser object"""
    return argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=copyleft(descr),
        epilog="examples:\n  " + "\n  ".join(examples),
    )


# pylint: disable=R0902
class HadCRUT5:
    """Class for parsing and plotting HadCRUT5 datasets"""

    # current dataset version
    _DATASET_VERSION = "5.0.2.0"

    # list of all the available data types
    _DEFAULT_DATATYPE = "annual"
    _VALID_DATATYPES = [_DEFAULT_DATATYPE, "monthly"]

    # list of all the valid periods
    _DEFAULT_PERIOD = "1961-1990"
    _VALID_PERIODS = [_DEFAULT_PERIOD, "1850-1900", "1880-1920"]

    GLOBAL_REGION = "Global"
    NORTHERN_REGION = "Northern Hemisphere"
    SOUTHERN_REGION = "Southern Hemisphere"

    def __init__(
        self,
        period=_DEFAULT_PERIOD,
        datatype=_DEFAULT_DATATYPE,
        regions=(True, False, False),
        smoother=1,
        verbose=False,
    ):
        if datatype not in self._VALID_DATATYPES:
            raise ValueError(f'Unsupported time series type "{datatype}"')
        if period not in self._VALID_PERIODS:
            raise ValueError(f'Unsupported reference period: "{period}"')

        # will be populated by datasets_load()
        self._datasets = {}
        # will be populated by datasets_normalize()
        self._datasets_normalized = {}

        self._datatype = datatype

        (self._enable_global, self._enable_northern, self._enable_southern) = regions

        self._period = period
        self._smoother = smoother
        self._verbose = verbose

        self._global_filename = (
            f"HadCRUT.{self._DATASET_VERSION}.analysis.summary_series.global.{datatype}.nc"
        )
        self._northern_hemisphere_filename = (
            f"HadCRUT.{self._DATASET_VERSION}."
            f"analysis.summary_series.northern_hemisphere.{datatype}.nc"
        )
        self._southern_hemisphere_filename = (
            f"HadCRUT.{self._DATASET_VERSION}."
            f"analysis.summary_series.southern_hemisphere.{datatype}.nc"
        )
        self._logging_level = logging.DEBUG if self._verbose else logging.INFO
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
        self._logger = logging.getLogger(__name__)

    def datasets_download(self):
        """Download the required HadCRUT5 datasets"""
        if self._enable_global:
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
                "metadata": dataset.__dict__,
                "variables": dataset.variables,
            }

        def dataset_metadata_dump(dataset_name, dataset):
            metadata = dataset["metadata"]
            self.logging_debug(
                (f'Metadata for "{dataset_name}" dataset:\n{json.dumps(metadata, indent=2)}'),
            )

        if self._enable_global:
            region = self.GLOBAL_REGION
            self._datasets[region] = dataset_load(self._global_filename)
            dataset_metadata_dump(region, self._datasets[region])
        if self._enable_northern:
            region = self.NORTHERN_REGION
            self._datasets[region] = dataset_load(self._northern_hemisphere_filename)
            dataset_metadata_dump(region, self._datasets[region])
        if self._enable_southern:
            region = self.SOUTHERN_REGION
            self._datasets[region] = dataset_load(self._southern_hemisphere_filename)
            dataset_metadata_dump(region, self._datasets[region])

    def datasets_normalize(self):
        """
        Normalize the temperature means to the required time period.
        Set _datasets_normalized with a tuple containing lower, mean, and upper
        temperatures for every enabled region
        """

        def normalization_value(temperatures):
            """
            Return the value to be substracted to temperatures in order to
            obtain a mean-centered dataset for the required period
            """
            if self._period == "1961-1990":
                # No changes required: the original dataset is based on the
                # reference period 1961-1990
                return 0

            factor = 12 if self.is_monthly_dataset else 1

            if self._period == "1850-1900":
                # The dataset starts from 1850-01-01 00:00:00
                # so we calculate the mean of the first 50 years
                norm_temp = np.mean(temperatures[: 50 * factor])
            elif self._period == "1880-1920":
                # We have to skip the first 30 years here
                norm_temp = np.mean(temperatures[30 * factor : 70 * factor + 1])
            else:
                # this should never happen...
                raise ValueError(f'Unsupported period "{self._period}"')

            self.logging_debug("The mean anomaly in {self._period} is about {norm_temp:.8f}°C")
            return norm_temp

        for region, data in self._datasets.items():
            mean = data["variables"]["tas_mean"]
            self.logging_debug(f"dataset ({region}): mean ({len(mean)} entries) \\\n{mean[:]}")

            lower = data["variables"]["tas_lower"]
            upper = data["variables"]["tas_upper"]

            norm_temp = normalization_value(mean)

            self._datasets_normalized[region] = {
                "lower": np.array(lower) - norm_temp,
                "mean": np.array(mean) - norm_temp,
                "upper": np.array(upper) - norm_temp,
            }
            self.logging_debug(
                f"normalized dataset ({region}): mean \\\n{np.array(mean) - norm_temp}"
            )

    def datasets_regions(self):
        """Return the dataset regions set by the user at command-line"""
        return self._datasets.keys()

    def logging(self, message):
        """Print a message"""
        logging.info(message)

    def logging_debug(self, message):
        """Print a message when in verbose mode only"""
        if self._verbose:
            logging.info(message)

    def _hadcrut5_data_url(self, filename):
        site = "https://www.metoffice.gov.uk"
        path = f"/hadobs/hadcrut5/data/HadCRUT.{self._DATASET_VERSION}/analysis/diagnostics/"
        url = f"{site}{path}{filename}"
        return url

    def _wget_dataset_file(self, filename):
        """Download a netCDFv4 HadCRUT5 file if not already found locally"""
        try:
            with open(filename, encoding="utf-8"):
                if self._verbose:
                    logging.info("Using the local dataset file: %s", filename)
        except IOError:
            if self._verbose:
                logging.info("Downloading %s ...", filename)

            url_dataset = self._hadcrut5_data_url(filename)
            try:
                response = requests.get(url_dataset, stream=True, timeout=10)
            except requests.exceptions.RequestException as e:
                logging.error(str(e))
                sys.exit(1)

            # Throw an error for bad status codes
            response.raise_for_status()

            with open(filename, "wb") as handle:
                for block in response.iter_content(1024):
                    handle.write(block)

    @property
    def dataset_datatype(self):
        """Return the datatype string"""
        return self._datatype

    @property
    def dataset_history(self):
        """Return the datatype history from metadata"""
        # The datasets have all the same length so choose the first one
        region = list(self._datasets.keys())[0]
        metadata = self._datasets[region]["metadata"]
        return metadata.get("history")

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
        """
        Return an array of years corresponding of the loaded datasets.
        If the original dataset packages monthly data, the returning vector
        will contain float values (year plus a decimal part for the month).
        """
        # The datasets have all the same length so choose the first one
        region = list(self._datasets.keys())[0]
        mean = self._datasets[region]["variables"]["tas_mean"][:]
        factor = 1 / 12 if self.is_monthly_dataset else 1
        years = [1850 + (y * factor) for y in range(len(mean))]
        self.logging_debug(f"years: \\\n{np.array(years)}")
        return years

    @property
    def is_monthly_dataset(self):
        """
        Return True if the loaded dataset provide monthly data,
        False otherwise
        """
        return self._datatype == "monthly"
