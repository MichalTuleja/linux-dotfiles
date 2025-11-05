# Lenovo Thinkpad T14s Gen2

_Hardware-Specific Instructions_

## PCI-based Hardware

```
00:00.0 Host bridge: Intel Corporation 11th Gen Core Processor Host Bridge/DRAM Registers (rev 01)
00:02.0 VGA compatible controller: Intel Corporation TigerLake-LP GT2 [Iris Xe Graphics] (rev 01)
00:04.0 Signal processing controller: Intel Corporation TigerLake-LP Dynamic Tuning Processor Participant (rev 01)
00:06.0 PCI bridge: Intel Corporation 11th Gen Core Processor PCIe Controller (rev 01)
00:07.0 PCI bridge: Intel Corporation Tiger Lake-LP Thunderbolt 4 PCI Express Root Port #1 (rev 01)
00:07.2 PCI bridge: Intel Corporation Tiger Lake-LP Thunderbolt 4 PCI Express Root Port #2 (rev 01)
00:08.0 System peripheral: Intel Corporation GNA Scoring Accelerator module (rev 01)
00:0d.0 USB controller: Intel Corporation Tiger Lake-LP Thunderbolt 4 USB Controller (rev 01)
00:0d.2 USB controller: Intel Corporation Tiger Lake-LP Thunderbolt 4 NHI #0 (rev 01)
00:0d.3 USB controller: Intel Corporation Tiger Lake-LP Thunderbolt 4 NHI #1 (rev 01)
00:14.0 USB controller: Intel Corporation Tiger Lake-LP USB 3.2 Gen 2x1 xHCI Host Controller (rev 20)
00:14.2 RAM memory: Intel Corporation Tiger Lake-LP Shared SRAM (rev 20)
00:14.3 Network controller: Intel Corporation Wi-Fi 6 AX201 (rev 20)
00:15.0 Serial bus controller: Intel Corporation Tiger Lake-LP Serial IO I2C Controller #0 (rev 20)
00:15.1 Serial bus controller: Intel Corporation Tiger Lake-LP Serial IO I2C Controller #1 (rev 20)
00:16.0 Communication controller: Intel Corporation Tiger Lake-LP Management Engine Interface (rev 20)
00:1c.0 PCI bridge: Intel Corporation Device a0b8 (rev 20)
00:1f.0 ISA bridge: Intel Corporation Tiger Lake-LP LPC Controller (rev 20)
00:1f.3 Audio device: Intel Corporation Tiger Lake-LP Smart Sound Technology Audio Controller (rev 20)
00:1f.4 SMBus: Intel Corporation Tiger Lake-LP SMBus Controller (rev 20)
00:1f.5 Serial bus controller: Intel Corporation Tiger Lake-LP SPI Controller (rev 20)
04:00.0 Non-Volatile memory controller: Sandisk Corp SanDisk Extreme Pro / WD Black SN750 / PC SN730 / Red SN700 NVMe SSD
08:00.0 Unassigned class [ff00]: Quectel Wireless Solutions Co., Ltd. EM120R-GL LTE Modem
```

## Prerequisites

### Windows-specific

It might be beneficial to initialize the LTE Modem with a running Windows instance,due to following reasons:
- Some modems need to be initialized with a vendor-specific software before the first run.
- Firmware updates can be performed only with the vendor-specific software. Depending on the network, it might be beneficial to receive recent firmware updates to the LTE modem.

### Linux-specific

To manage the Thinkpad T14s LTE modem, these packages are required:

- NetworkManager
- ModemManager
- MBIM Utils

Install them with the `apt` command.

```sh
sudo apt install network-manager modemmanager libmbim-utils
```

Then you can attempt to enable the LTE modem.

## Broadband Modem 4G/LTE

To enable broadband modem several steps are required.

Make sure that the modem is enabled by checking the output of the `lspci` command.

```
08:00.0 Unassigned class [ff00]: Quectel Wireless Solutions Co., Ltd. EM120R-GL LTE Modem
```

Based on the official [ModemManager instruction](https://modemmanager.org/docs/modemmanager/fcc-unlock/) you need to go through the FCC unlock procedure to enable the LTE modem.

The command below enables all supported modems on Linux.

```sh
 $ sudo ln -sft /etc/ModemManager/fcc-unlock.d /usr/share/ModemManager/fcc-unlock.available.d/*
```

After running this command reboot the system.

Once this is done, the modem should be visible in the UI. The rest of the configuration steps are common for all types of broadband modems and specific to the network carrier. Check your network carrier website to make sure what APN to use.

### Sleep & Hibernate Resume

This is quite a workaround 

`/usr/lib/systemd/system-sleep/modem-power-cycle`

```sh
#!/bin/bash

NMCLI=/usr/bin/nmcli
RESUME_DELAY=2  # seconds to wait after resume before acting

case "$1" in
  pre)
    logger "Sleep hook: disabling modem before suspend"
    $NMCLI radio wwan off
    ;;
  post)
    notify-send "Sleep hook: re-enabling modem after resume"
    sleep $RESUME_DELAY
    $NMCLI radio wwan off
    $NMCLI radio wwan on
    ;;
esac
```

## Touchpad 

The original hardware database does not contain information about T14s touchpad. It requires a fix in the actual system.

Create a file `/etc/udev/hwdb.d/61-evdev-local.hwdb` and paste the following content:

```
# Lenovo Thinkpad T490 and T14/P14s Gen1/2
evdev:name:SynPS/2 Synaptics TouchPad:dmi:*:svnLENOVO:*pvrThinkPadT490:*
evdev:name:SynPS/2 Synaptics TouchPad:dmi:*:svnLENOVO:*pvrThinkPadT14Gen1:*
evdev:name:SynPS/2 Synaptics TouchPad:dmi:*:svnLENOVO:*pvrThinkPadP14sGen1:*
evdev:name:SynPS/2 Synaptics TouchPad:dmi:*:svnLENOVO:*pvrThinkPadP14sGen2a:*
evdev:name:ELAN0676:00 04F3:3195 Touchpad:dmi:*svnLENOVO:*pvrThinkPadT14sGen2i**
 EVDEV_ABS_00=47:3528:30
 EVDEV_ABS_01=6:1793:29
 EVDEV_ABS_35=47:3528:30
 EVDEV_ABS_36=6:1793:29
```

Then run:

```sh
sudo systemd-hwdb update
```

and reboot the system.
