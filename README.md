# linux-dotfiles

## Openbox/X11

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/MichalTuleja/linux-dotfiles/main/install-openbox.sh)"
```

```bash
bash -c "$(wget https://raw.githubusercontent.com/MichalTuleja/linux-dotfiles/main/install-openbox.sh -O -)"
```

## Wayfire/Wayland

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/MichalTuleja/linux-dotfiles/main/install-wayfire.sh)"
```

```bash
bash -c "$(wget https://raw.githubusercontent.com/MichalTuleja/linux-dotfiles/main/install-wayfire.sh -O -)"
```

## Gnome/Wayland

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/MichalTuleja/linux-dotfiles/main/install-gnome.sh)"
```

```bash
bash -c "$(wget https://raw.githubusercontent.com/MichalTuleja/linux-dotfiles/main/install-gnome.sh -O -)"
```

### Remap keyboard

Disable Print Screen
```
gsettings set org.gnome.settings-daemon.plugins.media-keys screenshot "''"
```

Screenshot area with `Ctrl+Shift+S`
```
gsettings set org.gnome.settings-daemon.plugins.media-keys area-screenshot '<Primary><Shift>s'
```

Screenshot area with `Win+Shift+S`
```
gsettings set org.gnome.settings-daemon.plugins.media-keys area-screenshot '<Super><Shift>s'
```

Revert
```
gsettings reset org.gnome.settings-daemon.plugins.media-keys area-screenshot
```
