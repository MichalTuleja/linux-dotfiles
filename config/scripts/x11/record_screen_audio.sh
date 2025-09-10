#!/bin/sh
MON="$(pactl get-default-sink).monitor"
ffmpeg -video_size $(xdpyinfo | awk '/dimensions/{print $2}') -framerate 30 \
  -f x11grab -i $DISPLAY \
  -f pulse -i "$MON" \
  -vaapi_device /dev/dri/renderD128 -vf "format=nv12,hwupload" \
  -c:v h264_vaapi -profile:v high -qp 22 -g 60 -bf 2 \
  -c:a aac -b:a 128k "$HOME/Videos/screencast-$(date +%F_%H-%M-%S).mkv"
