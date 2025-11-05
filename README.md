# Desktop Linux Configuration

- Ubuntu-based - tested on Ubuntu 24.04 LTS and Linux Mint 22.1

## Wayfire/Wayland

### Installation

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/MichalTuleja/linux-dotfiles/main/install-wayfire.sh)"
```

or

```bash
bash -c "$(wget https://raw.githubusercontent.com/MichalTuleja/linux-dotfiles/main/install-wayfire.sh -O -)"
```

## Openbox (Legacy, X11-based)

### Installation

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/MichalTuleja/linux-dotfiles/main/install-openbox.sh)"
```

or

```bash
bash -c "$(wget https://raw.githubusercontent.com/MichalTuleja/linux-dotfiles/main/install-openbox.sh -O -)"
```

## Keyboard Shortcuts

### **Applications**
- **Win+Enter**: Launch terminal
- **Win+Shift+Enter or Win+P**: Open app launcher
- **Win+L**: Lock screen
- **Win+Shift+E or Ctrl+Alt+Backspace**: Log out
- **Win+PrintScreen or Win+Ctrl+Shift+S**: Fullscreen screenshot
- **Shift+PrintScreen or Win+Shift+S**: Interactive screenshot
- **Win+Shift+I**: Reset display configuration
- **Win+E**: Open file manager

### **Window Management**
- **Alt+F4 or Win+Q**: Close focused window
- **Win+F**: Toggle fullscreen
- **Win+G**: Toggle sticky (always on top)
- **Win+Tab**: Switch to next window
- **Win+Shift+Tab**: Switch to previous window
- **Alt+Tab**: Activate fast window switcher
- **Win+KP0 or Win+Down**: Restore window to default size

### **Workspace & Output**
- **Ctrl+Win+Left/Right or Win+Comma/Dot**: Switch to left/right workspace
- **Ctrl+Win+Shift+Left/Right or Win+Shift+Comma/Dot**: Move window to left/right workspace
- **Win+1–9**: Direct switch to workspace 1–9
- **Win+O**: Switch to next monitor
- **Win+Shift+O**: Move window to next monitor

### **System Controls**
- **VolumeUp**: Increase audio volume
- **VolumeDown**: Decrease audio volume
- **Mute**: Toggle mute
- **BrightnessUp**: Increase screen brightness
- **BrightnessDown**: Decrease screen brightness

## Gnome/Wayland

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/MichalTuleja/linux-dotfiles/main/install-gnome.sh)"
```

```bash
bash -c "$(wget https://raw.githubusercontent.com/MichalTuleja/linux-dotfiles/main/install-gnome.sh -O -)"
```

### Extra configs for Gnome

#### Remap keyboard

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
