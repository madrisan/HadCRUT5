#!/usr/bin/env bash

echo "removing .nc files ..."
rm -f HadCRUT.*.nc

for period in "1961-1990" "1850-1900" "1880-1920"; do
    echo "creating plot for period $period ..."
    ./hadcrut5_plot.py \
        --period="${period}" \
        --annotate=2 \
        --outfile plots/HadCRUT5-${period}.png
    ./hadcrut5_plot.py \
        --period="${period}" \
        --smoother 5 \
        --outfile plots/HadCRUT5-${period}-smoother.png
    ./hadcrut5_bars.py \
        --period="${period}" \
        --outfile plots/HadCRUT5-global-${period}.png
done

echo "creating monthly plot ..."
./hadcrut5_plot.py \
    --period "1880-1920" \
    --time-series monthly \
    --global \
    --outfile plots/HadCRUT5-monthly-global-1880-1920.png

echo "creating stripe image ..."
./hadcrut5_stripe.py \
    --region global \
    --outfile plots/HadCRUT5-global-stripe.png

echo "creating plot closing in to 1.5°C ..."
./hadcrut5_close.py \
    --period "1880-1920" \
    --region global \
    --outfile plots/HadCRUT5-global-threshold-1880-1920.png

echo "done."
