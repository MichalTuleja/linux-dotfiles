#!/bin/bash

layout=$(awesome-client <<'EOF' | sed -n 's/^.*return //p'
return require("awful").layout.getname(require("awful").layout.get(mouse.screen))
EOF
)

case "$layout" in
  tile) echo "🪟 Tiled" ;;
  floating) echo "🌀 Float" ;;
  max) echo "🧱 Max" ;;
  *) echo "$layout" ;;
esac
