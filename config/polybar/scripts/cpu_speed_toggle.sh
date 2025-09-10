#!/bin/bash

CAP_MHZ=$1

CPUFREQ_PATH="/sys/devices/system/cpu/cpu0/cpufreq"
SET_FREQ=$(<"$CPUFREQ_PATH/scaling_max_freq")
MAX_FREQ=$(<"$CPUFREQ_PATH/cpuinfo_max_freq")

# Determine target frequency in kHz
if [ -z "$CAP_MHZ" ]; then
    # Use full max if no param
    target_khz=$(<"$MAX_FREQ_PATH")
else
    target_khz=$((CAP_MHZ * 1000))
fi

if [ "$SET_FREQ" -ge "$MAX_FREQ" ]; then
    ~/.config/scripts/cpu_speed_limit.sh "$CAP_MHZ" &
else
    ~/.config/scripts/cpu_speed_limit.sh &
fi
