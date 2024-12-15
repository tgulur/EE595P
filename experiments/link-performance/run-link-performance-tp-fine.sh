#!/bin/bash
#
# This script runs the link-performance example with varying transmit power
# and zooms in on the threshold region to plot PER vs. transmit power between -5 dBm and 5 dBm.

set -e
set -o errexit

control_c()
{
  echo "exiting"
  exit $?
}

trap control_c SIGINT

dirname=link-performance
if test ! -f ../../../../ns3 ; then
    echo "please run this program from within the directory `dirname $0`, like this:"
    echo "cd `dirname $0`"
    echo "./`basename $0`"
    exit 1
fi

resultsDir=`pwd`/results/$dirname-`date +%Y%m%d-%H%M%S`
experimentDir=`pwd`

# need this as otherwise waf won't find the executables
cd ../../../../

# Avoid accidentally overwriting existing trace files; confirm deletion first
if [ -e link-performance-rssi.dat ]; then
    echo "Remove existing file link-performance-rssi.dat from top-level directory?"
    select yn in "Yes" "No"; do
        case $yn in
            Yes ) echo "Removing..."; rm -rf link-performance-rssi.dat; break;;
            No ) echo "Exiting..."; exit;;
        esac
    done
fi

if [ -e link-performance-summary.dat ]; then
    echo "Removing existing file link-performance-summary.dat from top-level directory?"
    select yn in "Yes" "No"; do
        case $yn in
            Yes ) echo "Removing..."; rm -rf link-performance-summary.dat; break;;
            No ) echo "Exiting..."; exit;;
        esac
    done
fi

# Random number generator run number
RngRun=1

# Set the name and title for the new plot
plotName='link-performance-per-vs-transmit-power-threshold.pdf'
plotTitle='PER vs. Transmit Power (Zoomed into Threshold Region)'

# Vary the number of packets per trial here
maxPackets=1000
# Distance between devices (keep fixed)
distance=50
# Noise power is fixed in dBm (decibels relative to 1 mW)
noisePower=-90

# Set the range of transmit power (in dBm) focusing on the threshold region
minTransmitPower=-5  # Starting at -5 dBm
maxTransmitPower=5   # Up to 5 dBm
stepSize=0.5         # Use a finer step size of 0.5 dBm for better resolution

# Echo remaining commands to standard output, to track progress
set -x
for transmitPower in `seq $minTransmitPower $stepSize $maxTransmitPower`; do
  ./ns3 run "link-performance --maxPackets=${maxPackets} --transmitPower=${transmitPower} --noisePower=${noisePower} --distance=${distance} --metadata=${transmitPower} --RngRun=${RngRun}"
done

# Move files from top level directory to the experiments directory
mv link-performance-summary.dat ${experimentDir} 
mv link-performance-rssi.dat ${experimentDir}

cd ${experimentDir}

if [[ ! -f ../utils/plot-lines-with-error-bars.py ]]; then
  echo 'plot file not found, exiting...'
  exit
fi

# Specify where the columns of data are to plot.  Here, the xcolumn data
# (transmit power) is in column 5, the y column data (PER) in column 3, and the
# length of the error bar is in column 4 
/usr/bin/python3 ../utils/plot-lines-with-error-bars.py --title="${plotTitle}" --xlabel='Transmit Power (dBm)' --ylabel='Packet Error Ratio (PER)' --xcol=5 --ycol=3 --yerror=4 --fileName=link-performance-summary.dat --plotName=${plotName}

# If script has succeeded to this point, create the results directory
mkdir -p ${resultsDir}
# Move and copy files to the results directory
mv $plotName ${resultsDir} 
mv link-performance-summary.dat ${resultsDir} 
mv link-performance-rssi.dat ${resultsDir} 
cp $0 ${resultsDir}
cp ../utils/plot-lines-with-error-bars.py ${resultsDir}
git show --name-only > ${resultsDir}/git-commit.txt
