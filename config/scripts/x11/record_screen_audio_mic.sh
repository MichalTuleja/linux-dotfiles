#!/bin/sh
MON="$(pactl get-default-sink).monitor"
ffmpeg -video_size $(xdpyinfo | awk '/dimensions/{print $2}') -framerate 30 \
  -f x11grab -i $DISPLAY \
  -f pulse -i "$MON" -f pulse -i default \
  -filter_complex "[1:a][2:a]amix=inputs=2:duration=longest:dropout_transition=0[a]" \
  -map 0:v -map "[a]" \
  -vaapi_device /dev/dri/renderD128 -vf "format=nv12,hwupload" \
  -c:v h264_vaapi -profile:v high -qp 22 -g 60 -bf 2 \
  -c:a aac -b:a 192k "$HOME/Videos/screencast-$(date +%F_%H-%M-%S).mkv"
