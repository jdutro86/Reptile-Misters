"""pin_devices.py
Contains methods for devices connected to the Pi. i.e Water Sensor, Valve, LED Light, Speakers
"""

try: # Check if running on Raspi
    import RPi.GPIO as GPIO # import RPi.GPIO module
    GPIO.setmode(GPIO.BOARD)
    WATER_SIGNAL_GPIO = 40
    VALVE_SIGNAL_GPIO = 38
    GPIO.setup(WATER_SIGNAL_GPIO, GPIO.IN) # Water Signal In 
    GPIO.setup(VALVE_SIGNAL_GPIO, GPIO.OUT) # Valve Signal Out
    USE_GPIO = True
except ImportError: # If not running on Raspi
    USE_GPIO = False
    
def water_detected(): # GPIO signal if water detected
    return GPIO.input(WATER_SIGNAL_GPIO) if USE_GPIO else 0

def output_valve(signal): # Send GPIO signal to valve
    if USE_GPIO:
        GPIO.output(VALVE_SIGNAL_GPIO, signal)

def rpi_cleanup(): # Cleanup RPi.GPIO
    if USE_GPIO:
        GPIO.cleanup()
