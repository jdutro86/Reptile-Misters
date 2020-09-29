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

def water_Detected(): # GPIO signal if water detected
    return GPIO.input(WATER_SIGNAL_GPIO) if USE_GPIO else 0

def open_Valve(): # GPIO signal to open water valve
    valveTimer.start()
    if USE_GPIO:
        GPIO.output(VALVE_SIGNAL_GPIO, 1)
    
def close_Valve(): # GPIO signal to close water valve
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

def update_Clock(): # Updates Clock at top banner every 0.5 second (500 miliseconds)
    timeDate = time.asctime()
    clockLabel.config(text = timeDate)
    clockLabel.after(500, update_Clock)

def manual_open_Valve(): # Function to open valve and deactivate other buttons
    valveSwitch.config(text = "Close Valve", command = manual_close_Valve)
    disableButton(timedSwitch, waterSwitch)
    open_Valve()
    
def manual_close_Valve(): # Function to close valve and activate other buttons
    valveSwitch.config(text = "Open Valve", command = manual_open_Valve)
    enableButton(timedSwitch, waterSwitch)
    close_Valve()
    
def enable_Water_Sensor(): # Activates Check for Water Mode
    waterSwitch.config(text = "Disable\n Water Sensor", command = disable_Water_Sensor)
    waterLabel.config(text = "No Water Detected\n Valve Closed")
    disableButton(valveSwitch, timedSwitch)
    global waterSensorEnabled
    waterSensorEnabled = True
    water_Check_Mode()

def disable_Water_Sensor(): # Deactivates Check for Water Mode
    waterSwitch.config(text = "Enable\n Water Sensor", command = enable_Water_Sensor)
    waterLabel.config(text = "Water Sensor Disabled")
    enableButton(valveSwitch, timedSwitch)
    global waterSensorEnabled
    waterSensorEnabled = False

def water_Check_Mode(): # Idle mode that checks for water now that sensor has been activated
    if water_Detected() and waterSensorEnabled: # Water Detected
        open_Valve()
        waterLabel.config(text = "Water Detected\n Valve Open")
        root.after(UPDATE_MS, water_Check_Mode)
    elif waterSensorEnabled: # No Water Detected
        close_Valve()
        waterLabel.config(text = "No Water Detected\n Valve Closed")
        root.after(UPDATE_MS, water_Check_Mode)
    else:
        return

def activate_Timer(): # Activates the timer mode
    disableButton(valveSwitch, waterSwitch, timedSwitch)
    timedValveTimer.start()
    timed_Valve_Open()
    open_Valve()

def deactivate_Timer(): # Deactivates the timer mode
    enableButton(valveSwitch, waterSwitch, timedSwitch)
    # stop and reset timer so that timer stops and progress bar resets
    timedValveTimer.stop()
    timedValveTimer.reset()
    close_Valve()

def timed_Valve_Open(): # Idle state to wait for timer to reach time limit
    timerProgressBar['value'] = timedValveTimer.value()
    # if timer exceeded maximum value, call deactivate_Timer and return
    if timerProgressBar['value'] >= timerProgressBar['maximum']:
        deactivate_Timer()
        return
    # if timer is not running, the timer is already disabled, so return without calling deactivate_Timer
    elif not timedValveTimer.running:
        return
    root.after(500, timed_Valve_Open)

def stop_all(): # Stops valve, all GUI methods, and disables buttons if max time exceeded
    disable_Water_Sensor()
    deactivate_Timer()
    manual_close_Valve()

    if valveTimer.value() >= MAX_OPEN_SECONDS:
        disableButton(valveSwitch, waterSwitch, timedSwitch)

def reset_all(): # Resets GUI to a 'default state'
    # resets valveTimer before calling stop_all to ensure buttons are not disabled
    valveTimer.reset()
    notificationLabel.config(text = '0 seconds open')
    stop_all()

def disableButton(*buttons): # Disable any number of GUI buttons
    for button in buttons:
        button["state"] = "disabled"

def enableButton(*buttons): # Enable any number of GUI buttons
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
                            width = 20, height = 3, command = manual_open_Valve)
    valveSwitch.pack(side = "top", pady = (60, 0))
    
    waterSwitch = tk.Button(root, text = "Enable\n Water Sensor",
                            font = ('calibri', 20, 'bold'),
                            width = 20, height = 3, command = enable_Water_Sensor)
    waterSwitch.pack(side = "top")
    
    waterLabel = tk.Label(root, font = ('calibri', 20, 'bold'),
                          text = "Water Sensor Disabled")
    waterLabel.pack(side = "top", pady = (0, 10))
    
    timerFrame = tk.Frame(root)
    timerFrame.pack()
    
    timedSwitch = tk.Button(timerFrame, text = "Open Valve\n for 5 minutes",
                            font = ('calibri', 20, 'bold'), 
                            width = 20, height = 3, command = activate_Timer)
    timedSwitch.pack(side = "top", pady = (10, 0))
    
    timerProgressBar = ttk.Progressbar(timerFrame, mode = "determinate", orient = "horizontal",
                                       maximum = MAX_OPEN_SECONDS, value = 0)
    timerProgressBar.pack(side = "bottom", pady = (40, 0), fill = 'both')

    emergencyStop = tk.Button(root, text = "EMERGENCY STOP", font = ('calibri', 20, 'bold'), width = 20, height = 3, command = stop_all)
    emergencyStop.pack(side = "top", pady = (10, 0))

    notificationLabel = tk.Label(root, font = ('calibri', 20, 'bold'), text = '0 seconds open')
    notificationLabel.pack(side = "top", pady = (10, 0))

    update_Clock()
    update_valve_timer()
    root.mainloop()

finally:
    if USE_GPIO:
        GPIO.cleanup()