# Visualize the HadCRUT5 temperature datasets

> HadCRUT5 is a gridded dataset of global historical surface temperature anomalies relative to a 1961-1990 reference period.
> Data are available for each month from January 1850 onwards, on a 5 degree grid and as global and regional average time series.
> The dataset is a collaborative product of the Met Office Hadley Centre and the Climatic Research Unit at the University of East Anglia.
>
> The current version of HadCRUT5 is HadCRUT.5.0.2.0, available from the download page.
>
> &mdash; source: [HadCRUT5 Index](https://www.metoffice.gov.uk/hadobs/hadcrut5/index.html)

A detailed description of the datasets can be found in the
[`Answers to Frequently Asked Questions`](https://crudata.uea.ac.uk/cru/data/temperature/).

List of the datafiles that are loaded by the Python script:
 * `HadCRUT.5.0.2.0.analysis.summary_series.global.annual.nc`
 * `HadCRUT.5.0.2.0.analysis.summary_series.northern_hemisphere.annual.nc`
 * `HadCRUT.5.0.2.0.analysis.summary_series.southern_hemisphere.annual.nc`

HadCRUT5 data are downloaded from: https://www.metoffice.gov.uk/hadobs/hadcrut5/data/HadCRUT.5.0.2.0/download.html

## Plot of the temperature anomalies

The following plots have been generated by the Python scripts `hadcrut5-plot.py` and `hadcrut5-bars.py`.
They require the Python libraries: Matplotlib, netCDF4, NumPy, and Requests.

If Python and the required libraries are not installed on your system, you can simply
[install](https://docs.astral.sh/uv/getting-started/installation/) `uv` and run the commands listed below prefixed
with `uv run`. For example `uv run ./hadcrut5-plot.py`.

## hadcrut5-plot.py &mdash; Script usage

```
$ ./hadcrut5-plot.py --help
usage: hadcrut5-plot.py [-h] [-f OUTFILE] [-p PERIOD] [-m SMOOTHER] [-g] [-n] [-s] [-a ANNOTATE] [-v]

Parse and plot the HadCRUT5 temperature datasets v2023.1 (stable)
Copyright (C) 2020-2023 Davide Madrisan <d.madrisan@proton.me>
License: GNU General Public License v3.0

options:
  -h, --help            show this help message and exit
  -a ANNOTATE, --annotate ANNOTATE
                        add temperature annotations (0: no annotations, 1 (default): bottom only, 2: all ones
  -f OUTFILE, --outfile OUTFILE
                        name of the output PNG file
  -g, --global          plot the Global Temperatures
  -m SMOOTHER, --smoother SMOOTHER
                        make the lines smoother by using N-year means
  -n, --northern        Northern Hemisphere Temperatures
  -p PERIOD, --period PERIOD
                        show anomalies related to 1961-1990 (default), 1850-1900, or 1880-1920
  -s, --southern        Southern Hemisphere Temperatures
  -t TIME_SERIES, --time-series TIME_SERIES
                        do plot the "annual" time series (default) or the "monthly" one
  -v, --verbose         make the operation more talkative

examples:
  hadcrut5-plot.py
  hadcrut5-plot.py --global --annotate=2
  hadcrut5-plot.py --period "1850-1900"
  hadcrut5-plot.py --period "1850-1900" --smoother 5
  hadcrut5-plot.py --period "1880-1920" --outfile HadCRUT5-1880-1920.png
  hadcrut5-plot.py --period "1880-1920" --time-series monthly --global
```

`hadcrut5-plot.py` select the period `1961-90` by default but supports (see the command-line switch`--period`) two other base periods found in the literature: `1850-1900`, and `1880-1920`.

```
$ ./hadcrut5-plot.py --annotate=2 --outfile plots/HadCRUT5-1961-1990.png
```
![HadCRUT5 anomalies related to 1961-1990](plots/HadCRUT5-1961-1990.png)

```
$ ./hadcrut5-plot.py --annotate=2 --period "1850-1900" --outfile plots/HadCRUT5-1850-1900.png
```
![HadCRUT5 anomalies related to 1850-1900](plots/HadCRUT5-1850-1900.png)

```
$ ./hadcrut5-plot.py --annotate=2 --period "1880-1920" --outfile plots/HadCRUT5-1880-1920.png
```
![HadCRUT5 anomalies related to 1880-1920](plots/HadCRUT5-1880-1920.png)

### Plots using the N-year mean data

By adding the command-line option `--smoother N` you can create the same three plots, but using the N-year means data.
For instance `--smoother 5` will get you a better idea of the trend lines.

Image generated for the anomalies related to the period `1880-1920`.
```
$ ./hadcrut5-plot.py --period "1880-1920" --smoother 5 --outfile plots/HadCRUT5-1880-1920-smoother.png
```
![HadCRUT5 anomalies related to 1880-1920 with 5-year means](plots/HadCRUT5-1880-1920-smoother.png)

### Plots using the monthly mean data

The command-line option `--time-series monthly` selects the monthly HadCRUT5 datasets (by default the dataset providing the annual means is selected).

Image displying the monthly anomalies related to the period `1880-1920`, for the global temperatures only.
```
$ ./hadcrut5-plot.py --global --period "1880-1920" --time-series monthly
```
![HadCRUT5 monthly global anomalies related to 1880-1920 means](plots/HadCRUT5-monthly-global-1880-1920.png)

## hadcrut5-bars.py &mdash; Script usage

```
usage: hadcrut5-bars.py [-h] [-f OUTFILE] [-p PERIOD] [-v]

Parse and plot the HadCRUT5 temperature datasets v2023.1 (stable)
Copyright (C) 2020-2023 Davide Madrisan <d.madrisan@proton.me>
License: GNU General Public License v3.0

options:
  -h, --help            show this help message and exit
  -f OUTFILE, --outfile OUTFILE
                        name of the output PNG file
  -p PERIOD, --period PERIOD
                        show anomalies related to 1961-1990 (default), 1850-1900, or 1880-1920
  -v, --verbose         make the operation more talkative

examples:
  hadcrut5-bars.py
  hadcrut5-bars.py --period "1850-1900"
  hadcrut5-bars.py --period "1880-1920"
  hadcrut5-bars.py --outfile HadCRUT5-global.png
```
The image for to the anomalies related to the period `1880-1920` follows.
```
$ ./hadcrut5-bars.py --period "1880-1920" --outfile plots/HadCRUT5-global-1880-1920.png
```
![HadCRUT5 bar plotting related to 1880-1920](plots/HadCRUT5-global-1880-1920.png)

## hadcrut5-stripe.py &mdash; Script usage

```
usage: hadcrut5-stripe.py [-h] [-f OUTFILE] [-r {global,northern,southern}] [-v] [-l]

Parse and plot a stripe image of the HadCRUT5 temperature datasets v2023.1 (stable)
Copyright (C) 2020-2023 Davide Madrisan <d.madrisan@proton.me>
License: GNU General Public License v3.0

options:
  -h, --help            show this help message and exit
  -f OUTFILE, --outfile OUTFILE
                        name of the output PNG file
  -r {global,northern,southern}, --region {global,northern,southern}
                        select between Global (default), Northern, or Southern Temperatures
  -v, --verbose         make the operation more talkative
  -l, --no-labels       do not disply the header and footer labels

examples:
  hadcrut5-stripe.py
  hadcrut5-stripe.py --no-labels --region northern
  hadcrut5-stripe.py --region global --outfile HadCRUT5-stripe-global.png
```

Below is a generated striped image for global anomalies.

![HadCRUT5 global warming stripe](plots/HadCRUT5-global-stripe.png)

# License

The Python code of this project is released under the [GPL-3.0 license](https://github.com/madrisan/HadCRUT5/blob/main/LICENSE).
The graphics have a [CC-BY4.0 license](https://creativecommons.org/licenses/by/4.0/), so can be used for any purpose as long as credit is given to Madrisan Davide and a link is provided to this website.
