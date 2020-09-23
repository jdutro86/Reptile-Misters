USE_GPIO = False

import tkinter as tk
import tkinter.ttk as ttk
import time
import math

from utils import Stopwatch

if USE_GPIO:
    import RPi.GPIO as GPIO # import RPi.GPIO module
    GPIO.setmode(GPIO.BOARD)
    WATER_SIGNAL_GPIO = 40
    VALVE_SIGNAL_GPIO = 38
    GPIO.setup(WATER_SIGNAL_GPIO, GPIO.IN) # Water Signal In 
    GPIO.setup(VALVE_SIGNAL_GPIO, GPIO.OUT) # Valve Signal Out

MAX_OPEN_SECONDS = 300 # 5 minutes
UPDATE_MS = 10 # time between updates

waterSensorEnabled = False # if water sensor is enabled

valveTimer = Stopwatch()
timedValveTimer = Stopwatch()

def water_Detected():
    if USE_GPIO:
        return GPIO.input(WATER_SIGNAL_GPIO)
    else:
        return 0

def open_Valve():
    valveTimer.start()
    if USE_GPIO:
        GPIO.output(VALVE_SIGNAL_GPIO, 1)
    
def close_Valve():
    valveTimer.stop()
    if USE_GPIO:
        GPIO.output(VALVE_SIGNAL_GPIO, 0)

def update_valve_timer():
    # if valveTimer is running, valve is on, so update notificationLabel and check if time exceeded
    if valveTimer.running:
        curTimeOpen = valveTimer.value()
        notificationLabel.config(text = str(math.floor(curTimeOpen)) + ' seconds open')

        if curTimeOpen >= MAX_OPEN_SECONDS:
            stop_all()
    # reset valveTimer at midnight
    elif time.strftime("%H%:%M:%S") == "00:00:00":
        valveTimer.reset()

    notificationLabel.after(UPDATE_MS, update_valve_timer)

def update_Clock():
    timeDate = time.asctime()
    clockLabel.config(text = timeDate)
    clockLabel.after(500, update_Clock)

def manual_open_Valve():
    valveSwitch.config(text = "Close Valve", command = manual_close_Valve)
    timedSwitch["state"] = "disabled"
    waterSwitch["state"] = "disabled"
    open_Valve()
    
def manual_close_Valve():
    valveSwitch.config(text = "Open Valve", command = manual_open_Valve)
    timedSwitch["state"] = "normal"
    waterSwitch["state"] = "normal"
    close_Valve()
    
def enable_Water_Sensor():
    waterSwitch.config(text = "Disable\n Water Sensor", command = disable_Water_Sensor)
    waterLabel.config(text = "No Water Detected\n Valve Closed")
    valveSwitch["state"] = "disabled"
    timedSwitch["state"] = "disabled"
    global waterSensorEnabled
    waterSensorEnabled = True
    water_Check_Mode()

def disable_Water_Sensor():
    waterSwitch.config(text = "Enable\n Water Sensor", command = enable_Water_Sensor)
    waterLabel.config(text = "Water Sensor Disabled")
    valveSwitch["state"] = "normal"
    timedSwitch["state"] = "normal"
    global waterSensorEnabled
    waterSensorEnabled = False

def water_Check_Mode():
    if water_Detected() and waterSensorEnabled:
        open_Valve()
        waterLabel.config(text = "Water Detected\n Valve Open")
        root.after(UPDATE_MS, water_Check_Mode)
    elif waterSensorEnabled:
        waterLabel.config(text = "No Water Detected\n Valve Closed")
        root.after(UPDATE_MS, water_Check_Mode)
    else:
        return

def activate_Timer():
    valveSwitch["state"] = "disabled"
    timedSwitch["state"] = "disabled"
    waterSwitch["state"] = "disabled"
    timedValveTimer.start()
    timed_Valve_Open()
    open_Valve()

def deactivate_Timer():
    valveSwitch["state"] = "normal"
    timedSwitch["state"] = "normal"
    waterSwitch["state"] = "normal"
    # stop and reset timer so that timer stops and progress bar resets
    timedValveTimer.stop()
    timedValveTimer.reset()
    close_Valve()

def timed_Valve_Open():
    timerProgressBar['value'] = timedValveTimer.value()
    # if timer exceeded maximum value, call deactivate_Timer and return
    if timerProgressBar['value'] >= timerProgressBar['maximum']:
        deactivate_Timer()
        return
    # if timer is not running, the timer is already disabled, so return without calling deactivate_Timer
    elif not timedValveTimer.running:
        return
    root.after(500, timed_Valve_Open)

def stop_all():
    # stops all valve methods and, if max time exceeded, disables buttons
    disable_Water_Sensor()
    deactivate_Timer()
    manual_close_Valve()

    if valveTimer.value() >= MAX_OPEN_SECONDS:
        disable_all()

def reset_all():
    # resets timer before calling stop_all to ensure buttons are not disabled
    valveTimer.reset()
    notificationLabel.config(text = '0 seconds open')
    stop_all()

def disable_all():
    # disables all buttons
    valveSwitch["state"] = "disabled"
    timedSwitch["state"] = "disabled"
    waterSwitch["state"] = "disabled"

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

    emergencyReset = tk.Button(root, text = "EMERGENCY RESET", font = ('calibri', 20, 'bold'), width = 20, height = 3, command = reset_all)
    emergencyReset.pack(side = "top", pady = (10, 0))

    notificationLabel = tk.Label(root, font = ('calibri', 20, 'bold'), text = '0 seconds open')
    notificationLabel.pack(side = "top", pady = (10, 0))

    update_Clock()
    update_valve_timer()
    root.mainloop()

finally:
    if USE_GPIO:
        GPIO.cleanup()
