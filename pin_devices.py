"""pin_devices.py
Contains methods for devices connected to the Pi. i.e Water Sensor, Valve, LED Light, and Speakers
"""

try: # Check if running on Raspi
    import RPi.GPIO as GPIO # import RPi.GPIO module
    import Adafruit_WS2801
    import Adafruit_GPIO.SPI as SPI
    GPIO.setmode(GPIO.BOARD)
    
    WATER_SIGNAL_GPIO = 40
    VALVE_SIGNAL_GPIO = 38
    GPIO.setup(WATER_SIGNAL_GPIO, GPIO.IN) # Water Signal In 
    GPIO.setup(VALVE_SIGNAL_GPIO, GPIO.OUT) # Valve Signal Out
    LED_COUNT = 32
    LED_CLOCK = 18
    LED_DOUT = 23
    pixels = Adafruit_WS2801.WS2801Pixels(LED_COUNT, clk=LED_CLOCK, do=LED_DOUT)
    
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

'''
def lightning():
    if USE_GPIO:
        for led in range(pixels.count()):
            pixels.set_pixels(led, Adafruit_WS2801.RGB_to_color(255,255,255))
        pixels.show()
        
def turnOffLED():
    pixels.clear()
    '''
