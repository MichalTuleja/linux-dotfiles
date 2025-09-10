#!/bin/bash

# Optional override in MHz; default is full max
CAP_MHZ=$1

CPUFREQ_PATH="/sys/devices/system/cpu/cpu0/cpufreq"
MAX_FREQ_PATH="$CPUFREQ_PATH/cpuinfo_max_freq"
SET_FREQ_PATH="$CPUFREQ_PATH/scaling_max_freq"

# Determine target frequency in kHz
if [ -z "$CAP_MHZ" ]; then
    # Use full max if no param
    target_khz=$(<"$MAX_FREQ_PATH")
else
    target_khz=$((CAP_MHZ * 1000))
fi

# Explicitly apply to all CPUs
for cpu in /sys/devices/system/cpu/cpu[0-9]*; do
    echo "$target_khz" | sudo tee "$cpu/cpufreq/scaling_max_freq" > /dev/null
done
