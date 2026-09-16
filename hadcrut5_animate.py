#!/usr/bin/python3
# Copyright (c) 2026 Davide Madrisan <d.madrisan@proton.me>
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Create an animated plot of the HadCRUT5 temperature dataset, revealing the
selected regions year by year.
"""

import argparse
from dataclasses import dataclass

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import animation
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.text import Text
import numpy as np

from hadcrut5lib import argparser, HadCRUT5


@dataclass
class SeriesData:
    """Years and per-region (lower, mean, upper) normalized data arrays"""

    years: np.ndarray
    lower: dict
    mean: dict
    upper: dict
    regions: list


@dataclass
class FigureElements:
    """The figure/axes and the per-region artists making up a single frame"""

    fig: Figure
    ax: Axes
    lines: dict
    points: dict
    labels: dict
    year_label: Text


def parse_args() -> argparse.Namespace:
    """This function parses and return arguments passed in"""
    descr = "Create an animated plot of the HadCRUT5 temperature datasets"
    examples = [
        "%(prog)s",
        "%(prog)s --global",
        '%(prog)s --period "1880-1920"',
        '%(prog)s --period "1880-1920" --outfile HadCRUT5-1880-1920-animation.mp4',
        "%(prog)s --fps 30 --hold 5 --outfile HadCRUT5-animation.mp4",
    ]

    parser = argparser(descr, examples)
    parser.add_argument(
        "-b",
        "--bitrate",
        action="store",
        dest="bitrate",
        default=1800,
        type=int,
        help="bitrate (in kbps) of the encoded video (default: 1800)",
    )
    parser.add_argument(
        "-f",
        "--outfile",
        action="store",
        dest="outfile",
        help="name of the output MP4 file; if not set the animation is "
        "displayed interactively instead",
    )
    parser.add_argument(
        "--fps",
        action="store",
        dest="fps",
        default=25,
        type=int,
        help="frames per second of the encoded video (default: 25)",
    )
    parser.add_argument(
        "--hold",
        action="store",
        dest="hold",
        default=2.0,
        type=float,
        help="seconds to hold the last frame at the end of the animation (default: 2.0)",
    )
    parser.add_argument(
        "-g",
        "--global",
        action="store_true",
        dest="plot_global",
        help="plot the Global Temperatures",
    )
    parser.add_argument(
        "-n",
        "--northern",
        action="store_true",
        dest="plot_northern",
        help="Northern Hemisphere Temperatures",
    )
    parser.add_argument(
        "-p",
        "--period",
        action="store",
        dest="period",
        default="1961-1990",
        help="show anomalies related to 1961-1990 (default), 1850-1900, or 1880-1920",
    )
    parser.add_argument(
        "-s",
        "--southern",
        action="store_true",
        dest="plot_southern",
        help="Southern Hemisphere Temperatures",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        dest="verbose",
        help="make the operation more talkative",
    )

    return parser.parse_args()


def load_series(hc5: HadCRUT5, regions: list) -> SeriesData:
    """Return the years and the per-region (lower, mean, upper) normalized arrays"""
    years = np.array(hc5.dataset_years())
    bounds = {region: hc5.dataset_normalized_data(region) for region in regions}
    lower = {region: np.array(bounds[region][0]) for region in regions}
    mean = {region: np.array(bounds[region][1]) for region in regions}
    upper = {region: np.array(bounds[region][2]) for region in regions}
    return SeriesData(years, lower, mean, upper, regions)


def setup_figure(hc5: HadCRUT5, data: SeriesData) -> FigureElements:
    """Create the figure/axes and the per-region line and point artists"""
    mpl.style.use("seaborn-v0_8-notebook")
    fig, ax = plt.subplots(figsize=(8, 5))

    # Plot the full series and error bands first, so that matplotlib
    # autoscales the axes with the same default margins used by the static
    # plots; the axes limits are then frozen, the temporary bands removed,
    # and the lines cleared for the animation start.
    lines, points, labels = {}, {}, {}
    bands = []
    for region in data.regions:
        bands.append(
            ax.fill_between(data.years, data.lower[region], data.upper[region], color="lightgray")
        )
        (line,) = ax.plot(data.years, data.mean[region], linewidth=2, label=region)
        lines[region] = line
        points[region] = ax.scatter([], [], color=line.get_color(), zorder=3)
        labels[region] = ax.text(
            0,
            0,
            "",
            fontsize=6,
            horizontalalignment="left",
            bbox={"facecolor": "lightgray", "alpha": 0.6, "pad": 3},
        )

    ax.autoscale_view()
    ax.set_xlim(ax.get_xlim())
    ax.set_ylim(ax.get_ylim())

    for band in bands:
        band.remove()

    ax.set_title(f"HadCRUT5: land and sea temperature anomalies relative to {hc5.dataset_period}")
    ax.set_xlabel("year", fontsize=10)
    ax.set_ylabel(f"{hc5.dataset_datatype.capitalize()} Temperature Anomalies in °C", fontsize=10)
    ax.hlines(0, data.years.min(), data.years.max(), colors="gray", linestyles="dotted")
    ax.legend(loc="upper left", fontsize=9)
    year_label = ax.text(
        0.98, 0.05, "", transform=ax.transAxes, fontsize=11, horizontalalignment="right"
    )

    for line in lines.values():
        line.set_data([], [])

    return FigureElements(fig, ax, lines, points, labels, year_label)


def animate(hc5: HadCRUT5, fps: int, bitrate: int, hold: float, outfile: str):
    """
    Create an animated plot revealing the selected regions year by year,
    holding the last frame for 'hold' seconds, and diplay it or save it to
    file if outfile is set
    """
    hc5.datasets_download()
    hc5.datasets_load()
    hc5.datasets_normalize()

    regions = list(hc5.datasets_regions())
    data = load_series(hc5, regions)
    elems = setup_figure(hc5, data)

    interval = 40  # milliseconds between frames
    hold_frames = round(hold * 1000 / interval)
    bands = {region: None for region in regions}

    def update(frame):
        artists = [elems.year_label]
        index = min(frame, len(data.years) - 1)
        is_last_year = index == len(data.years) - 1
        x = data.years[: index + 1]
        for region in regions:
            y = data.mean[region][: index + 1]
            elems.lines[region].set_data(x, y)
            elems.points[region].set_offsets([[x[-1], y[-1]]])
            if bands[region] is not None:
                bands[region].remove()
            bands[region] = elems.ax.fill_between(
                x,
                data.lower[region][: index + 1],
                data.upper[region][: index + 1],
                color="lightgray",
            )
            if is_last_year:
                elems.labels[region].set_position((x[-1] - 2, y[-1] - 0.15))
                elems.labels[region].set_text(f"{y[-1]:.2f}°C")
            artists.extend(
                [bands[region], elems.lines[region], elems.points[region], elems.labels[region]]
            )
        elems.year_label.set_text(f"{int(x[-1])}")
        return artists

    ani = animation.FuncAnimation(
        elems.fig, update, frames=len(data.years) + hold_frames, interval=interval, blit=True
    )

    if outfile:
        writer = animation.FFMpegWriter(fps=fps, bitrate=bitrate)
        ani.save(outfile, writer=writer)
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

    hc5 = HadCRUT5(
        period=args.period,
        regions=regions,
        verbose=args.verbose,
    )

    animate(hc5, args.fps, args.bitrate, args.hold, args.outfile)


main()
