import evdev
from evdev import InputDevice, ecodes
from subprocess import call

# Locate your touchpad device. This might require manual specification
device_path = '/dev/input/event6'  # Replace X with your actual event number for the touchpad
device = InputDevice(device_path)

def adjust_scroll_speed(multiplier):
    try:
        # This uses a shell command to set the settings using `libinput`
        # Adjust this command according to your specific needs and path
        call(['libinput', 'debug-events', '--device=' + device_path])
        
        # This is a mock example, you would use libinput's options to change the scroll speed
        # e.g., call(['libinput', 'set-scrolling', '--scroll-speed', str(multiplier)])

        print(f"Scroll speed adjusted by multiplier: {multiplier}")

    except Exception as e:
        print(f"An error occurred: {e}")

# Example of changing scroll speed
adjust_scroll_speed(1.5)  # Increase scroll speed by 50%
