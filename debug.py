import tkinter as tk
import tkinter.ttk as ttk
import time
import math

from rm_utils import Stopwatch

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

MAX_OPEN_SECONDS = 300 # 5 minutes
UPDATE_MS = 10 # time between updates

waterSensorEnabled = False # if water sensor is enabled
valveTimerShouldReset = False # fix for leaving valve on over midnight

valveTimer = Stopwatch()
timedValveTimer = Stopwatch()

def water_detected(): # GPIO signal if water detected
    return GPIO.input(WATER_SIGNAL_GPIO) if USE_GPIO else 0

def open_valve(): # GPIO signal to open water valve
    valveTimer.start()
    if USE_GPIO:
        GPIO.output(VALVE_SIGNAL_GPIO, 1)
    
def close_valve(): # GPIO signal to close water valve
    valveTimer.stop()
    if USE_GPIO:
        GPIO.output(VALVE_SIGNAL_GPIO, 0)

def update_valve_timer():
    global valveTimerShouldReset

    # if valveTimer is running, valve is on, so update notificationLabel and check if time exceeded
    if valveTimer.running:
        curTimeOpen = valveTimer.value()
        notificationLabel.config(text = str(math.floor(curTimeOpen)) + ' seconds open')

        # stop everything if exceeded maximum time for the day
        if curTimeOpen >= MAX_OPEN_SECONDS:
            stop_all()
        # indicate valveTimer should be reset after the valve shuts off
        if time.strftime("%H:%M:%S") == "00:00:00":
            valveTimerShouldReset = True
    # reset valveTimer at midnight, or if valve shut off and midnight has passed
    elif time.strftime("%H:%M:%S") == "00:00:00" or valveTimerShouldReset:
        valveTimerShouldReset = False
        valveTimer.reset()

    notificationLabel.after(UPDATE_MS, update_valve_timer)

def update_clock(): # Updates Clock at top banner every 0.5 second (500 miliseconds)
    timeDate = time.asctime()
    clockLabel.config(text = timeDate)
    clockLabel.after(500, update_clock)

def manual_open_valve(): # Function to open valve and deactivate other buttons
    valveSwitch.config(text = "Close Valve", command = manual_close_valve)
    disable_button(timedSwitch, waterSwitch)
    open_valve()
    
def manual_close_valve(): # Function to close valve and activate other buttons
    valveSwitch.config(text = "Open Valve", command = manual_open_valve)
    enable_button(timedSwitch, waterSwitch)
    close_valve()
    
def enable_water_sensor(): # Activates Check for Water Mode
    waterSwitch.config(text = "Disable\n Water Sensor", command = disable_water_sensor)
    waterLabel.config(text = "No Water Detected\n Valve Closed")
    disable_button(valveSwitch, timedSwitch)
    global waterSensorEnabled
    waterSensorEnabled = True
    water_check_mode()

def disable_water_sensor(): # Deactivates Check for Water Mode
    waterSwitch.config(text = "Enable\n Water Sensor", command = enable_water_sensor)
    waterLabel.config(text = "Water Sensor Disabled")
    enable_button(valveSwitch, timedSwitch)
    global waterSensorEnabled
    waterSensorEnabled = False

def water_check_mode(): # Idle mode that checks for water now that sensor has been activated
    if water_detected() and waterSensorEnabled: # Water Detected
        open_valve()
        waterLabel.config(text = "Water Detected\n Valve Open")
        root.after(UPDATE_MS, water_check_mode)
    elif waterSensorEnabled: # No Water Detected
        close_valve()
        waterLabel.config(text = "No Water Detected\n Valve Closed")
        root.after(UPDATE_MS, water_check_mode)
    else:
        return

def activate_timer(): # Activates the timer mode
    disable_button(valveSwitch, waterSwitch, timedSwitch)
    timedValveTimer.start()
    timed_valve_open()
    open_valve()

def deactivate_timer(): # Deactivates the timer mode
    enable_button(valveSwitch, waterSwitch, timedSwitch)
    # stop and reset timer so that timer stops and progress bar resets
    timedValveTimer.stop()
    timedValveTimer.reset()
    close_valve()

def timed_valve_open(): # Idle state to wait for timer to reach time limit
    timerProgressBar['value'] = timedValveTimer.value()
    # if timer exceeded maximum value, call deactivate_Timer and return
    if timerProgressBar['value'] >= timerProgressBar['maximum']:
        deactivate_timer()
        return
    # if timer is not running, the timer is already disabled, so return without calling deactivate_Timer
    elif not timedValveTimer.running:
        return
    root.after(500, timed_valve_open)

def stop_all(): # Stops valve, all GUI methods, and disables buttons if max time exceeded
    disable_water_sensor()
    deactivate_timer()
    manual_close_valve()

    if valveTimer.value() >= MAX_OPEN_SECONDS:
        disable_button(valveSwitch, waterSwitch, timedSwitch)

def reset_all(): # Resets GUI to a 'default state'
    # resets valveTimer before calling stop_all to ensure buttons are not disabled
    valveTimer.reset()
    notificationLabel.config(text = '0 seconds open')
    stop_all()

def disable_button(*buttons): # Disable any number of GUI buttons
    for button in buttons:
        button["state"] = "disabled"

def enable_button(*buttons): # Enable any number of GUI buttons
    for button in buttons:
        button["state"] = "normal"

# Main
try:
    root = tk.Tk()
    root.attributes("-fullscreen", True)

    clockLabel = tk.Label(root, font = ('calibri', 20, 'bold'), padx = 10, pady = 10)
    clockLabel.pack(side = "top", pady = (10, 0))
    
    valveSwitch = tk.Button(root, text = "Open Valve",
                            font = ('calibri', 20, 'bold'),
                            width = 20, height = 3, command = manual_open_valve)
    valveSwitch.pack(side = "top", pady = (60, 0))
    
    waterSwitch = tk.Button(root, text = "Enable\n Water Sensor",
                            font = ('calibri', 20, 'bold'),
                            width = 20, height = 3, command = enable_water_sensor)
    waterSwitch.pack(side = "top")
    
    waterLabel = tk.Label(root, font = ('calibri', 20, 'bold'),
                          text = "Water Sensor Disabled")
    waterLabel.pack(side = "top", pady = (0, 10))
    
    timerFrame = tk.Frame(root)
    timerFrame.pack()
    
    timedSwitch = tk.Button(timerFrame, text = "Open Valve\n for 5 minutes",
                            font = ('calibri', 20, 'bold'), 
                            width = 20, height = 3, command = activate_timer)
    timedSwitch.pack(side = "top", pady = (10, 0))
    
    timerProgressBar = ttk.Progressbar(timerFrame, mode = "determinate", orient = "horizontal",
                                       maximum = MAX_OPEN_SECONDS, value = 0)
    timerProgressBar.pack(side = "bottom", pady = (40, 0), fill = 'both')

    emergencyStop = tk.Button(root, text = "EMERGENCY STOP", font = ('calibri', 20, 'bold'), width = 20, height = 3, command = stop_all)
    emergencyStop.pack(side = "top", pady = (10, 0))

    notificationLabel = tk.Label(root, font = ('calibri', 20, 'bold'), text = '0 seconds open')
    notificationLabel.pack(side = "top", pady = (10, 0))

    update_clock()
    update_valve_timer()
    root.mainloop()

finally:
    if USE_GPIO:
        GPIO.cleanup()
