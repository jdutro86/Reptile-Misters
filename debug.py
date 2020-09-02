import RPi.GPIO as GPIO # import RPi.GPIO module
import tkinter as tk
import tkinter.ttk as ttk
import time

GPIO.setmode(GPIO.BOARD)
WATER_SIGNAL_GPIO = 40
VALVE_SIGNAL_GPIO = 38
GPIO.setup(WATER_SIGNAL_GPIO, GPIO.IN) # Water Signal In 
GPIO.setup(VALVE_SIGNAL_GPIO, GPIO.OUT) # Valve Signal Out

MAX_OPEN_SECONDS = 300 # 5 minutes

timerProgress = 0
waterSensorEnabled = False

def water_Detected():
    return GPIO.input(40)

def signal_Open_Valve():
    GPIO.output(VALVE_SIGNAL_GPIO, 1)
    
def signal_Close_Valve():
    GPIO.output(VALVE_SIGNAL_GPIO, 0)
    
def update_Clock():
    timeDate = time.asctime(time.localtime(time.time()))
    clockLabel.config(text = timeDate)
    clockLabel.after(1000, update_Clock)

def open_Valve():
    valveSwitch.config(text = "Close Valve", command = close_Valve)
    timedSwitch["state"] = "disabled"
    waterSwitch["state"] = "disabled"
    signal_Open_Valve()
    
def close_Valve():
    valveSwitch.config(text = "Open Valve", command = open_Valve)
    timedSwitch["state"] = "normal"
    waterSwitch["state"] = "normal"
    signal_Close_Valve()
    
def enable_Water_Sensor():
    waterSwitch.config(text = "Disable\n Water Sensor", command = disable_Water_Sensor)
    waterLabel.config(text = "No Water Detected\n Valve Closed")
    valveSwitch["state"] = "disabled"
    timedSwitch["state"] = "disabled"
    global waterSensorEnabled
    waterSensorEnabled = True
    water_Check_Mode()
    
def water_Check_Mode():
    if water_Detected() and waterSensorEnabled:
        signal_Open_Valve()
        waterLabel.config(text = "Water Detected\n Valve Open")
        root.after(10, water_Check_Mode)
    elif waterSensorEnabled:
        waterLabel.config(text = "No Water Detected\n Valve Closed")
        root.after(10, water_Check_Mode)
    else:
        return
        
def disable_Water_Sensor():
    waterSwitch.config(text = "Enable\n Water Sensor", command = enable_Water_Sensor)
    waterLabel.config(text = "Water Sensor Disabled")
    valveSwitch["state"] = "normal"
    timedSwitch["state"] = "normal"
    global waterSensorEnabled
    waterSensorEnabled = False
    
def activate_Timer():
    valveSwitch["state"] = "disabled"
    timedSwitch["state"] = "disabled"
    waterSwitch["state"] = "disabled"
    timed_Valve_Open()

def timed_Valve_Open():
    global timerProgress
    timerProgress += 1
    timerProgressBar['value'] = timerProgress
    signal_Open_Valve()
    if timerProgressBar['value'] >= timerProgressBar['maximum']:
        valveSwitch["state"] = "normal"
        timedSwitch["state"] = "normal"
        waterSwitch["state"] = "normal"
        timerProgress = 0
        signal_Close_Valve()
        return    
    root.after(1000, timed_Valve_Open)

# Main
try:
    root = tk.Tk()
    root.attributes("-fullscreen", True)

    clockLabel = tk.Label(root, font = ('calibri', 20, 'bold'), padx = 10, pady = 10)
    clockLabel.pack(side = "top", pady = (10, 0))
    
    valveSwitch = tk.Button(root, text = "Open Valve",
                            font = ('calibri', 20, 'bold'),
                            width = 20, height = 3, command = open_Valve)
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

    update_Clock()
    root.mainloop()

finally: 
    GPIO.cleanup()
