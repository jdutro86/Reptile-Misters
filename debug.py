import tkinter as tk
import tkinter.ttk as ttk
import time
import math

import constant
from rm_utils import Stopwatch

if constant.USE_GPIO:
    import RPi.GPIO as GPIO # import RPi.GPIO module
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(constant.WATER_SIGNAL_GPIO, GPIO.IN) # Water Signal In 
    GPIO.setup(constant.VALVE_SIGNAL_GPIO, GPIO.OUT) # Valve Signal Out

waterSensorEnabled = False # if water sensor is enabled
valveTimerShouldReset = False # fix for leaving valve on over midnight

valveTimer = Stopwatch()
timedValveTimer = Stopwatch()

def water_Detected(): # GPIO signal if water detected
    if constant.USE_GPIO:
        return GPIO.input(constant.WATER_SIGNAL_GPIO)
    else:
        return 0

def open_Valve(): # GPIO signal to open water valve
    valveTimer.start()
    if constant.USE_GPIO:
        GPIO.output(constant.VALVE_SIGNAL_GPIO, 1)
    
def close_Valve(): # GPIO signal to close water valve
    valveTimer.stop()
    if constant.USE_GPIO:
        GPIO.output(constant.VALVE_SIGNAL_GPIO, 0)

def update_valve_timer(): # Updates the valve's total time open
    global valveTimerShouldReset

    # indicate valveTimer should be reset at midnight
    if time.strftime("%H%:%M:%S") == "00:00:00":
        valveTimerShouldReset = True

    # if valveTimer is running, valve is on, so update notificationLabel and check if time exceeded
    if valveTimer.running:
        curTimeOpen = valveTimer.value()
        notificationLabel.config(text = str(math.floor(curTimeOpen)) + ' seconds open')

        # stop everything if exceeded maximum time for the day
        if curTimeOpen >= constant.MAX_OPEN_SECONDS:
            stop_all()

    # reset valveTimer if valve is shut off and it should reset
    elif valveTimerShouldReset:
        valveTimerShouldReset = False
        valveTimer.reset()

    notificationLabel.after(constant.UPDATE_MS, update_valve_timer)

def update_Clock(): # Updates Clock at top banner every SLOW_UPDATE_MS
    timeDate = time.asctime()
    clockLabel.config(text = timeDate)
    clockLabel.after(constant.SLOW_UPDATE_MS, update_Clock)

def manual_open_Valve(): # Function to open valve and deactivate other buttons
    disable_all()
    valveSwitch.config(text = "Close Valve", command = manual_close_Valve)
    valveSwitch["state"] = "normal"
    open_Valve()
    
def manual_close_Valve(): # Function to close valve and activate other buttons
    enable_all()
    valveSwitch.config(text = "Open Valve", command = manual_open_Valve)
    close_Valve()
    
def enable_Water_Sensor(): # Activates Check for Water Mode
    disable_all()
    waterSwitch.config(text = "Disable\n Water Sensor", command = disable_Water_Sensor)
    waterLabel.config(text = "No Water Detected\n Valve Closed")
    waterSwitch["state"] = "normal"
    global waterSensorEnabled
    waterSensorEnabled = True
    water_Check_Mode()

def disable_Water_Sensor(): # Deactivates Check for Water Mode
    enable_all()
    waterSwitch.config(text = "Enable\n Water Sensor", command = enable_Water_Sensor)
    waterLabel.config(text = "Water Sensor Disabled")
    global waterSensorEnabled
    waterSensorEnabled = False

def water_Check_Mode(): # Idle mode that checks for water now that sensor has been activated
    if water_Detected() and waterSensorEnabled: # Water Detected
        open_Valve()
        waterLabel.config(text = "Water Detected\n Valve Open")
    elif waterSensorEnabled: # No Water Detected
        close_Valve()
        waterLabel.config(text = "No Water Detected\n Valve Closed")
    else:
        return
    root.after(constant.UPDATE_MS, water_Check_Mode)

def activate_Timer(): # Activates the timer mode
    disable_all()
    timedValveTimer.start()
    timed_Valve_Open()
    open_Valve()

def deactivate_Timer(): # Deactivates the timer mode
    enable_all()
    # stop and reset timer so that progress bar resets
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
    root.after(constant.SLOW_UPDATE_MS, timed_Valve_Open)

def stop_all(): # Stops valve, all GUI methods, and disables buttons if max time exceeded
    disable_Water_Sensor()
    deactivate_Timer()
    manual_close_Valve()

    if valveTimer.value() >= constant.MAX_OPEN_SECONDS:
        disable_all()

def reset_all(): # Resets GUI to a 'default state'
    # resets valveTimer before calling stop_all to ensure buttons are not disabled
    valveTimer.reset()
    notificationLabel.config(text = '0 seconds open')
    stop_all()

def disable_all(): # Disables all GUI buttons
    valveSwitch["state"] = "disabled"
    timedSwitch["state"] = "disabled"
    waterSwitch["state"] = "disabled"

def enable_all(): # Enables all GUI buttons
    valveSwitch["state"] = "normal"
    timedSwitch["state"] = "normal"
    waterSwitch["state"] = "normal"

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
                                       maximum = constant.MAX_OPEN_SECONDS, value = 0)
    timerProgressBar.pack(side = "bottom", pady = (40, 0), fill = 'both')

    emergencyStop = tk.Button(root, text = "EMERGENCY STOP", font = ('calibri', 20, 'bold'), width = 20, height = 3, command = stop_all)
    emergencyStop.pack(side = "top", pady = (10, 0))

    notificationLabel = tk.Label(root, font = ('calibri', 20, 'bold'), text = '0 seconds open')
    notificationLabel.pack(side = "top", pady = (10, 0))

    update_Clock()
    update_valve_timer()
    root.mainloop()

finally:
    if constant.USE_GPIO:
        GPIO.cleanup()
