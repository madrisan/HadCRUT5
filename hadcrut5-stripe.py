#!/usr/bin/python3
# Copyright (c) 2023 Davide Madrisan <davide.madrisan@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Display a stripe image of the HadCRUT5 Global temperature dataset.
"""

import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.colors import ListedColormap
from matplotlib.patches import Rectangle

from hadcrut5lib import argparser, HadCRUT5


def parse_args():
    """This function parses and return arguments passed in"""
    descr = "Parse and plot a stripe image of the HadCRUT5 temperature datasets"
    examples = [
        "%(prog)s",
        "%(prog)s --no-labels --region northern",
        "%(prog)s --region global --outfile HadCRUT5-stripe-global.png",
    ]

    parser = argparser(descr, examples)
    parser.add_argument(
        "-f",
        "--outfile",
        action="store",
        dest="outfile",
        help="name of the output PNG file",
    )
    parser.add_argument(
        "-r",
        "--region",
        choices=["global", "northern", "southern"],
        action="store",
        dest="region",
        default="global",
        help="select between Global (default), Northern, or Southern Temperatures",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        dest="verbose",
        help="make the operation more talkative",
    )
    parser.add_argument(
        "-l",
        "--no-labels",
        action="store_false",
        dest="labels",
        help="do not disply the header and footer labels",
    )
    parser.set_defaults(labels=True)

    return parser.parse_args()


def plotstripe(region, outfile, labels, verbose):
    """
    Create a stripe plot for the specified period and diplay it or save it to
    file if outfile is set
    """
    hc5 = HadCRUT5(
        regions=(region == "global", region == "northern", region == "southern"),
        verbose=verbose,
    )
    hc5.datasets_download()
    hc5.datasets_load()
    hc5.datasets_normalize()

    years = hc5.dataset_years()
    yfirst, ylast = years[0], years[-1]
    yrange = ylast - yfirst

    regions_switch = {
        "global": hc5.GLOBAL_REGION,
        "northern": hc5.NORTHERN_REGION,
        "southern": hc5.SOUTHERN_REGION,
    }
    _, mean, _ = hc5.dataset_normalized_data(regions_switch[region])

    plt.style.use("dark_background")
    _, ax = plt.subplots()

    # the colors in this colormap come from http://colorbrewer2.org
    # (the 8 more saturated colors from the 9 blues / 9 reds)
    cmap = ListedColormap(
        [
            "#08306b",
            "#08519c",
            "#2171b5",
            "#4292c6",
            "#6baed6",
            "#9ecae1",
            "#c6dbef",
            "#deebf7",
            "#fee0d2",
            "#fcbba1",
            "#fc9272",
            "#fb6a4a",
            "#ef3b2c",
            "#cb181d",
            "#a50f15",
            "#67000d",
        ]
    )

    # create a collection with a rectangle for each year
    collection = PatchCollection(
        [Rectangle((x / yrange, 0), x + 1 / yrange, 1) for x in range(1 + yrange)]
    )
    # set data and colormap
    collection.set_array(mean)
    collection.set_cmap(cmap)
    # collection.set_clim(,)

    ax.add_collection(collection)
    ax.get_yaxis().set_visible(False)
    ax.set_frame_on(False)

    if labels:
        ax.tick_params(axis="both", which="both", length=0)
        # pylint: disable=consider-using-f-string
        plt.title(
            (
                "{} Temperature Change ({}-{})".format(
                    regions_switch[region], yfirst, ylast
                )
            ),
            fontsize=16,
            loc="left",
            fontweight="bold",
            family="DejaVu Sans",
        )

        ticks = [0, 0.2, 0.4, 0.6, 0.8, 1]
        xlabels = [round(yfirst + x * yrange) for x in ticks]
        plt.xticks(ticks, xlabels, fontweight="bold", fontsize=12)
    else:
        ax.get_xaxis().set_visible(False)

    fig = plt.gcf()
    fig.set_size_inches(10, 4)  # 1 inch equal to 80pt

    if outfile:
        fig.savefig(outfile, dpi=80, bbox_inches="tight")
        plt.close(fig)
    else:
        plt.show()


# pylint: disable=C0116
def main():
    args = parse_args()
    plotstripe(args.region, args.outfile, args.labels, args.verbose)


main()
