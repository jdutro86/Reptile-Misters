"""constant.py
Contains all the constants used in our project.
"""

# Set to False when testing only GUI logic
USE_GPIO = False

# GPIO pin for water sensor
WATER_SIGNAL_GPIO = 40

# GPIO pin for actual valve
VALVE_SIGNAL_GPIO = 38

# Maximum open time of the valve every 24hr
MAX_OPEN_SECONDS = 300

# Milliseconds between GUI updates
UPDATE_MS = 10

# Milliseconds between slower GUI updates
SLOW_UPDATE_MS = 500
