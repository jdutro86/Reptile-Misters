from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import QTimer
import sys
import time
import math

from UI import UI
from rm_utils import Stopwatch
from rm_utils import TimeStampLog

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

# Constants
MAX_OPEN_SECONDS = 300 # 5 minutes
SLOW_UPDATE_MS = 500 # 500 Miliseconds = 1/2 Second
UPDATE_MS = 10 # time between updates

valveTimerShouldReset = False # fix for leaving valve on over midnight

valveTimer = Stopwatch()
timedValveTimer = Stopwatch()
valveRecord = TimeStampLog()

def water_detected(): # GPIO signal if water detected
    return GPIO.input(WATER_SIGNAL_GPIO) if USE_GPIO else 0

def open_valve(): # GPIO signal to open water valve
    # logistical stuff only executes if valve is closed
    if not valveTimer.running:
        valveTimer.start()
        valveRecord.open_time(time.time())
        window.lastOpenLabel.setText('Last open: ' + valveRecord.get_last_open())
        update_log()
    if USE_GPIO:
        GPIO.output(VALVE_SIGNAL_GPIO, 1)
    
def close_valve(): # GPIO signal to close water valve
    # logistical stuff only executes if valve is open
    if valveTimer.running:
        valveTimer.stop()
        valveRecord.close_time(time.time())
        window.lastOpenLabel.setText('Last open: ' + valveRecord.get_last_open() + " for " + valveRecord.get_time_open() + " seconds")
        update_log()
    if USE_GPIO:
        GPIO.output(VALVE_SIGNAL_GPIO, 0)

def update_valve_timer(): # Updates the valve's total time open
    global valveTimerShouldReset

    # indicate valveTimer should be reset at midnight
    if time.strftime("%H:%M:%S") == "00:00:00":
        valveTimerShouldReset = True

    # if valveTimer is running, valve is on, so update notificationLabel and check if time exceeded
    if valveTimer.running:
        curTimeOpen = valveTimer.value()
        window.notificationLabel.setText(str(math.floor(curTimeOpen)) + ' seconds open')

        # stop everything if exceeded maximum time for the day
        if curTimeOpen >= MAX_OPEN_SECONDS:
            stop_all()

    # reset valveTimer if valve is shut off and it should reset
    elif valveTimerShouldReset:
        valveTimerShouldReset = False
        valveTimer.reset()

def manual_open_valve(): # Function to open valve and deactivate other buttons
    disable_button(window.timedSwitch, window.waterSwitch)
    window.valveSwitch.setText("Close Valve")
    window.valveSwitch.clicked.disconnect()
    window.valveSwitch.clicked.connect(manual_close_valve)
    open_valve()
    
def manual_close_valve(): # Function to close valve and activate other buttons
    enable_button(window.timedSwitch, window.waterSwitch)
    window.valveSwitch.setText("Open Valve")
    window.valveSwitch.clicked.disconnect()
    window.valveSwitch.clicked.connect(manual_open_valve)
    close_valve()
    
def enable_water_sensor(): # Activates Check for Water Mode
    window.waterSwitch.setText("Disable\n Water Sensor") 
    window.waterSwitch.clicked.disconnect()
    window.waterSwitch.clicked.connect(disable_water_sensor)
    window.waterLabel.setText("No Water Detected\n Valve Closed")
    disable_button(window.valveSwitch, window.timedSwitch)
    waterCheckTimer.start(UPDATE_MS)

def disable_water_sensor(): # Deactivates Check for Water Mode
    window.waterSwitch.setText("Enable\n Water Sensor")
    window.waterSwitch.clicked.disconnect()
    window.waterSwitch.clicked.connect(enable_water_sensor)
    window.waterLabel.setText("Water Sensor Disabled")
    enable_button(window.valveSwitch, window.timedSwitch)
    waterCheckTimer.stop()

def water_check_mode(): # Idle mode that checks for water now that sensor has been activated

    if water_detected() and not valveTimer.running: # Water Detected and valve off
        open_valve()
        window.waterLabel.setText("Water Detected\n Valve Open")
    elif not water_detected() and valveTimer.running: # No Water Detected and valve on
        close_valve()
        window.waterLabel.setText("No Water Detected\n Valve Closed")

def activate_timer(): # Activates the timer mode
    disable_button(window.valveSwitch, window.waterSwitch, window.timedSwitch)
    timedValveTimer.start()
    timed_valve_open()
    open_valve()
    progressTimer.start(UPDATE_MS)

def deactivate_timer(): # Deactivates the timer mode
    enable_button(window.valveSwitch, window.waterSwitch, window.timedSwitch)
    # stop and reset timer so that timer stops and progress bar resets
    timedValveTimer.stop()
    timedValveTimer.reset()
    close_valve()
    progressTimer.stop()

def timed_valve_open(): # Idle state to wait for timer to reach time limit
    window.timerProgress.setValue(int(timedValveTimer.value()))
    # if timer exceeded maximum value, call deactivate_timer and return
    if window.timerProgress.value() >= MAX_OPEN_SECONDS:
        deactivate_timer()
        return
    # if timer is not running, the timer is already disabled, so return without calling deactivate_timer
    elif not timedValveTimer.running:
        return

def stop_all(): # Stops valve, all GUI methods, and disables buttons if max time exceeded
    disable_water_sensor()
    deactivate_timer()
    manual_close_valve()

    if valveTimer.value() >= MAX_OPEN_SECONDS:
        disable_button(window.valveSwitch, window.waterSwitch, window.timedSwitch)

def reset_all(): # Resets GUI to a 'default state'
    # resets valveTimer before calling stop_all to ensure buttons are not disabled
    valveTimer.reset()
    window.notificationLabel.setText('0 seconds open')
    stop_all()

def disable_button(*buttons): # Disable any number of GUI buttons
    for button in buttons:
        button.setEnabled(False)

def enable_button(*buttons): # Enable any number of GUI buttons
    for button in buttons:
        button.setEnabled(True)

def update_log():
    window.logLabel.setText('Open ' + valveRecord.times_open() + ' times(s) today\n'
                            + 'Closed ' + valveRecord.times_closed() + ' time(s) today')

# Main
try:
    
    app = QApplication([])
    window = UI()

    window.valveSwitch.clicked.connect(manual_open_valve)
    window.waterSwitch.clicked.connect(enable_water_sensor)
    window.timedSwitch.clicked.connect(activate_timer)
    window.stopButton.clicked.connect(stop_all)
    
    window.waterLabel.setText("Water Sensor Disabled")
    window.notificationLabel.setText("0 seconds open")
    window.lastOpenLabel.setText("Not yet open today")
    window.logLabel.setText('Open ' + valveRecord.times_open() + ' times(s) today\n'
                            + 'Closed ' + valveRecord.times_closed() + ' time(s) today')

    window.timerProgress.setMaximum(MAX_OPEN_SECONDS)

    progressTimer = QTimer(window)
    progressTimer.timeout.connect(timed_valve_open)

    waterCheckTimer = QTimer(window)
    waterCheckTimer.timeout.connect(water_check_mode)

    valveTimeOpenTimer = QTimer(window)
    valveTimeOpenTimer.timeout.connect(update_valve_timer)
    valveTimeOpenTimer.start(UPDATE_MS)

    app.exec_()

finally:
    if USE_GPIO:
        GPIO.cleanup()
