#!/bin/bash

set -euo pipefail

# 1. Retrieve repo

sudo apt install -y git

TMP_DIR=$(mktemp -d -t linuxdotflies.XXXXXX)
echo "Created temp dir: $TMP_DIR"

git_download() {
  local repo_url="$1"
  local dest="${2:-}"

  if [[ -z "$repo_url" ]]; then
    echo "Usage: git_download <git-url> [destination]" >&2
    return 1
  fi

  if [[ -n "$dest" ]]; then
    if [[ -d "$dest/.git" ]]; then
      echo "Destination already a git repo → updating with git pull"
      (cd "$dest" && git pull --ff-only)
    else
      echo "Cloning $repo_url into $dest..."
      git clone "$repo_url" "$dest"
    fi
  else
    local folder
    folder="$(basename "$repo_url" .git)"
    if [[ -d "$folder/.git" ]]; then
      echo "Repo '$folder' already exists → updating with git pull"
      (cd "$folder" && git pull --ff-only)
    else
      echo "Cloning $repo_url into default folder..."
      git clone "$repo_url"
    fi
  fi
}

git_download https://github.com/MichalTuleja/linux-dotfiles.git $TMP_DIR

# 2. Install dependencies

PACKAGES=(
  alacritty
  foot
  kanshi
  gammastep
  mako-notifier
  wayfire
  waybar
  swaybg
  swayidle
  swaylock
  gtklock
  grim
  slurp
  wlogout
  wlr-randr
  wofi
  adwaita-icon-theme
  dmz-cursor-theme
  dosfstools
  exfat-fuse
  exfatprogs
  fonts-font-awesome
  fonts-noto
  fonts-noto-mono
  fonts-noto-core
  fonts-noto-color-emoji
  gdm3
  git
  build-essential
  ffmpeg
  zsh
  tmux
  xdg-desktop-portal
  xdg-desktop-portal-gnome
  xdg-desktop-portal-gtk
  vlc
  smplayer
  thunar
  thunar-archive-plugin
  thunar-media-tags-plugin
  thunar-volman
  python3
  python3-pyudev
  iw
  modemmanager
  libmbim-utils
  intel-gpu-tools
  intel-media-va-driver-non-free
  i965-va-driver
  alsa-tools
  pipewire
  pipewire-pulse
  ubuntu-wallpapers
  ubuntu-wallpapers-noble
  brightnessctl
)

# Filter out already installed packages
to_install=()
for pkg in "${PACKAGES[@]}"; do
  if dpkg -s "$pkg" &>/dev/null; then
    echo "Skipping (already installed): $pkg"
  else
    to_install+=("$pkg")
  fi
done

# Install remaining ones in one go
if [[ ${#to_install[@]} -gt 0 ]]; then
  echo "Updating package index..."
  sudo apt-get update -y
  echo "Installing: ${to_install[*]}"
  sudo apt-get install -y "${to_install[@]}"
else
  echo "All packages are already installed."
fi


# 2. Install config files


copy_files() {
  local src_dir="$1"
  local dest_dir="$2"
  shift 2
  local files=("$@")

  echo "Copying files from '$src_dir' to '$dest_dir'."

  # Check source directory
  if [[ ! -d "$src_dir" ]]; then
    echo "Error: source directory '$src_dir' does not exist." >&2
    return 1
  fi

  # Ensure destination directory exists
  mkdir -p "$dest_dir"

  for file in "${files[@]}"; do
    local src="$src_dir/$file"
    local dest="$dest_dir/$file"
    local dest_subdir
    dest_subdir="$(dirname "$dest")"

    if [[ -f "$src" ]]; then
      mkdir -p "$dest_subdir"

      if [[ -e "$dest" ]]; then
        echo "Skipping (already exists): $dest"
      else
        cp -- "$src" "$dest"
      fi
    else
      echo "Warning: missing source file -> $src" >&2
    fi
  done
}

CONFIG_FILES=(
  code-flags.conf
  gtk-3.0/settings.ini
  alacritty/alacritty.toml
  glib-2.0/settings/keyfile
  gtk-4.0/settings.ini
  mako/config
  rofi/apps.rasi
  rofi/wifi.rasi
  rofi/themes/violet-dark.rasi
  rofi/config.rasi
  scripts/cpu_speed_limit.sh
  scripts/modem_read_sms.sh
  scripts/wayland/screenshot-area.sh
  scripts/wayland/screenshot-clipboard.sh
  scripts/wayland/record_screen_intel.sh
  scripts/wayland/monitor_hotplug.py
  scripts/wayland/screenshot-area-clipboard.sh
  scripts/wayland/app_menu.py
  scripts/wayland/pick_best_output.py
  scripts/wayland/switch-audio-sink.sh
  scripts/wayland/monitor_layout_menu.py
  scripts/wayland/screenshot-fullscreen.sh
  wofi/wifi.config
  wofi/apps.config
  wofi/dark.css
  foot/foot.ini
  kanshi/config
  wireplumber/main.lua.d/50-alsa-config.lua
  waybar/config
  waybar/style.css
  waybar/scripts/cpu_speed.sh
  waybar/scripts/bluetooth.sh
  waybar/scripts/awesome-workspaces.sh
  waybar/scripts/cpu_speed_limit.sh
  waybar/scripts/cpu_speed_toggle.sh
  waybar/scripts/awesome-layout.sh
  waybar/scripts/wifi-picker.sh
  waybar/scripts/ob_current_desktop.sh
  waybar/scripts/lte.sh
  waybar/scripts/wifi.sh
  waybar/scripts/awesome-toggle-layout.sh
  pl_de_custom_caps_lock.xkb
  autostart/gammastep-indicator.desktop
  autostart/blueman.desktop
  autostart/xfce-autostart-wm.desktop
  autostart/xfce4-power-manager.desktop
  autostart/im-launch.desktop
  wayfire.ini
)

DOT_FILES=(
  .tmux.conf
  .wallpaper
)

THEME_FILES=(
  ./OpenViolet-Dark/openbox-3/themerc
)

cd $TMP_DIR

DEST_TMP_DIR="$HOME/test$TMP_DIR"
echo "Creating $DEST_TMP_DIR"

mkdir -p "$DEST_TMP_DIR"

copy_files "./dotfiles" "$DEST_TMP_DIR" "${DOT_FILES[@]}"
copy_files "./config" "$DEST_TMP_DIR/.config" "${CONFIG_FILES[@]}"

echo 'All done.'
