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
  dmz-cursor-theme
  dosfstools
  exfat-fuse
  exfatprogs
  fonts-font-awesome
  fonts-noto
  fonts-noto-mono
  fonts-noto-core
  fonts-noto-color-emoji
  git
  build-essential
  ffmpeg
  zsh
  tmux
  vlc
  smplayer
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
  alacritty/alacritty.toml
  foot/foot.ini
  wireplumber/main.lua.d/50-alsa-config.lua
  pl_de_custom_caps_lock.xkb
)

DOT_FILES=(
  .tmux.conf
  .wezterm.lua
  tuleja.zsh-theme
)

THEME_FILES=(
)

cd $TMP_DIR

DEST_TMP_DIR="$HOME/test$TMP_DIR"
echo "Creating $DEST_TMP_DIR"

mkdir -p "$DEST_TMP_DIR"

copy_files "./dotfiles" "$DEST_TMP_DIR" "${DOT_FILES[@]}"
copy_files "./config" "$DEST_TMP_DIR/.config" "${CONFIG_FILES[@]}"

echo 'All done.'
