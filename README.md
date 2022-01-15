# Visualize the HadCRUT5 temperature datasets

> HadCRUT5 is a gridded dataset of global historical surface temperature anomalies relative to a 1961-1990 reference period.
> Data are available for each month from January 1850 to December 2018 (updates will be available in time), on a 5 degree grid.
> The dataset is a collaborative product of the Met Office Hadley Centre and the Climatic Research Unit at the University of East Anglia.
>
> HadCRUT5 data has now been updated to include data to the year 2020 in HadCRUT.5.0.1.0, available from the download page.
>
> &mdash; source: [HadCRUT5 Index](https://www.metoffice.gov.uk/hadobs/hadcrut5/index.html)

> Stations on land are at different elevations, and different countries calculate average monthly temperatures using different methods and formulae.
> To avoid biases that could result from these differences, monthly average temperatures are reduced to anomalies from the period with best coverage (1961-90).
>
> &mdash; source: [HadCRUT5 FAQ-5](https://crudata.uea.ac.uk/cru/data/temperature/#faq5)

Datafiles that are loaded by the Python script:
 * HadCRUT.5.0.1.0.analysis.summary_series.global.annual.nc
 * HadCRUT.5.0.1.0.analysis.summary_series.northern_hemisphere.annual.nc
 * HadCRUT.5.0.1.0.analysis.summary_series.southern_hemisphere.annual.nc

HadCRUT5 data taken from: https://www.metoffice.gov.uk/hadobs/hadcrut5/data/current/download.html

## Plot of the temperature anomalies

The following plots have been generated by the Python scripts `hadcrut5-plot.py` and `hadcrut5-bars.py`.
They require the Python libraries: Matplotlib, netCDF4, NumPy, and Requests.

## hadcrut5-plot.py &mdash; Script usage

```
$ ./hadcrut5-plot.py --help
usage: hadcrut5-plot.py [-h] [-f OUTFILE] [-p PERIOD] [-m SMOOTHER] [-g] [-n] [-s] [-a ANNOTATE] [-v]

Parse and plot the HadCRUT5 temperature datasets v.2 (stable)
Copyright (C) 2020-2021 Davide Madrisan <davide.madrisan@gmail.com>
License: GNU General Public License v3.0

options:
  -h, --help            show this help message and exit
  -f OUTFILE, --outfile OUTFILE
                        name of the output PNG file
  -p PERIOD, --period PERIOD
                        show anomalies related to 1961-1990 (default), 1850-1900, or 1880-1920
  -m SMOOTHER, --smoother SMOOTHER
                        make the lines smoother by using N-year means
  -g, --global          plot the Global Temperatures
  -n, --northern        Northern Hemisphere Temperatures
  -s, --southern        Southern Hemisphere Temperatures
  -a ANNOTATE, --annotate ANNOTATE
                        add temperature annotations (0: no annotations, 1 (default): bottom only, 2: all ones
  -v, --verbose         make the operation more talkative

examples:
  hadcrut5-plot.py
  hadcrut5-plot.py --global
  hadcrut5-plot.py --outfile HadCRUT5.png --annotate=2
  hadcrut5-plot.py --period "1850-1900" --outfile HadCRUT5-1850-1900.png
  hadcrut5-plot.py --period "1880-1920" --outfile HadCRUT5-1880-1920.png
  hadcrut5-plot.py --period "1850-1900" --smoother 5 --outfile HadCRUT-1850-1900-smoother.png
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

## hadcrut5-bars.py &mdash; Script usage

```
usage: hadcrut5-bars.py [-h] [-f OUTFILE] [-p PERIOD] [-v]

Parse and plot the HadCRUT5 temperature datasets v.2 (stable)
Copyright (C) 2020-2021 Davide Madrisan <davide.madrisan@gmail.com>
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
  hadcrut5-bars.py --outfile HadCRUT5-global.png
  hadcrut5-bars.py --period "1850-1900" --outfile HadCRUT5-global-1850-1900.png
  hadcrut5-bars.py --period "1880-1920" --outfile HadCRUT5-global-1880-1920.png
```
The image for to the anomalies related to the period `1880-1920` follows.
```
$ ./hadcrut5-bars.py --period "1880-1920" --outfile plots/HadCRUT5-global-1880-1920.png
```
![HadCRUT5 bar plotting related to 1880-1920](plots/HadCRUT5-global-1880-1920.png)
