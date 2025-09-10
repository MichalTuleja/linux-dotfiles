#!/usr/bin/env bash
set -e

OUTDIR="$HOME/Screen Recordings"
mkdir -p "$OUTDIR"
OUT="$OUTDIR/screencast-$(date +%F_%H-%M-%S).mkv"

wf-recorder \
  --file "$OUT" \
  --framerate=30 \
  --audio --audio-codec=aac \
  --muxer=matroska \
  --codec=h264_vaapi

#  --filter='scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black,format=nv12,hwupload'
#  --filter='format=nv12,hwupload,scale_vaapi=w=1920:h=1080:force_original_aspect_ratio=decrease'

notify-send -a wf-recorder "🎥 Recording saved" "$OUT"
