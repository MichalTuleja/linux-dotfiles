#!/bin/bash

# Read current and max
CPUFREQ_PATH="/sys/devices/system/cpu/cpu0/cpufreq"
SET_FREQ=$(<"$CPUFREQ_PATH/scaling_max_freq")
MAX_FREQ=$(<"$CPUFREQ_PATH/cpuinfo_max_freq")

# Show average current frequency
avg_freq=$(awk -F: '/cpu MHz/ { sum += $2; n++ } END { printf("%.2f", sum / n / 1000) }' /proc/cpuinfo)

# # Display capped or not
# if [ "$SET_FREQ" -lt "$MAX_FREQ" ]; then
#     echo "✨ ${avg_freq} GHz"
# else
#     echo "🔥 ${avg_freq} GHz"
# fi

# Display capped or not
if [ "$SET_FREQ" -lt "$MAX_FREQ" ]; then
    echo " ${avg_freq} GHz"
else
    echo " ${avg_freq} GHz"
fi
