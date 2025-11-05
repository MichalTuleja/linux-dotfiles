#!/bin/sh
osascript <<'EOT'
tell application "System Events"
  if (exists process "Finder") then
    tell application "Finder" to activate
  end if
end tell

tell application "Finder"
  set newWindow to make new Finder window
  set target of newWindow to (POSIX file (do shell script "echo $HOME")) as alias
end tell
EOT
