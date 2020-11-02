"""ui.py
Contains all UI-related stuff and logic.
"""

from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QPushButton, QLabel, QProgressBar
from PyQt5.QtCore import QTimer, QStateMachine, QState, pyqtSignal, QObject
from PyQt5 import uic

from pin_devices import output_valve, water_detected, rpi_cleanup
from rm_utils import Stopwatch, TimeStampLog

import time
import math

MAX_OPEN_SECONDS = 300
SLOW_UPDATE_MS = 500
UPDATE_MS = 10

# Inherits QObject to allow for pyqtSignal usage
class EventLoop(QObject):
    # Custom signals for state transitions
    timerFinished = pyqtSignal()
    timeLimitReached = pyqtSignal()

    def __init__(self, ui):
        super(EventLoop, self).__init__()
        self.ui = ui

        self.valveRecord = TimeStampLog()

        # QTimer for sensor mode
        self.waterCheckTimer = QTimer(ui)
        self.waterCheckTimer.timeout.connect(self.sensor_mode)
        self.waterCheckTimer.setInterval(UPDATE_MS)

        # QTimer for timed mode
        self.timedValveWatch = Stopwatch()
        self.timedValveTimer = QTimer(ui)
        self.timedValveTimer.timeout.connect(self.timed_mode)
        self.timedValveTimer.setInterval(UPDATE_MS)

        # QTimer for valve open time tracking
        self.valveWatch = Stopwatch()
        self.valveTimeShouldReset = False
        self.valveTimeOpenTimer = QTimer(ui)
        self.valveTimeOpenTimer.timeout.connect(self.update_valve_time)
        self.valveTimeOpenTimer.setInterval(UPDATE_MS)
        self.valveTimeOpenTimer.start()

        # QTimer for clock updates
        self.clockTimer = QTimer(ui)
        self.clockTimer.timeout.connect(self.update_clock)
        self.clockTimer.setInterval(SLOW_UPDATE_MS)
        self.clockTimer.start()

        # State machine-related transition logic
        ui.manualEnabled.entered.connect(self.open_valve)
        ui.manualEnabled.exited.connect(self.close_valve)
        ui.sensorEnabled.entered.connect(self.activate_sensor_mode)
        ui.sensorEnabled.exited.connect(self.deactivate_sensor_mode)
        ui.timerEnabled.entered.connect(self.activate_timed_mode)
        ui.timerEnabled.exited.connect(self.deactivate_timed_mode)

        # VERY IMPORTANT
        ui.idle.entered.connect(self.close_valve)

    def open_valve(self):
        # Logistical stuff only executes if valve is closed
        if not self.valveWatch.running:
            self.valveWatch.start()
            self.valveRecord.open_time(time.time())
            self.ui.lastOpenLabel.setText('Last open: ' + self.valveRecord.get_last_open())
            self.update_log()
        output_valve(1)
    
    def close_valve(self):
        # Logistical stuff only executes if valve is open
        if self.valveWatch.running:
            self.valveWatch.stop()
            self.valveRecord.close_time(time.time())
            self.ui.lastOpenLabel.setText('Last open: ' + self.valveRecord.get_last_open() + " for " + self.valveRecord.get_time_open() + " seconds")
            self.update_log()
        output_valve(0)

    def update_log(self):
        # Update the logging text
        self.ui.logLabel.setText('Open ' + self.valveRecord.times_open() + ' times(s) today\n' +
        'Closed ' + self.valveRecord.times_closed() + ' time(s) today')

    def activate_sensor_mode(self):
        # Activate the sensor mode
        self.waterCheckTimer.start()

    def deactivate_sensor_mode(self):
        # Deactivate the sensor mode
        self.waterCheckTimer.start()

    def sensor_mode(self):
        # Loop method for sensor mode
        waterDetected = water_detected()

        if waterDetected and not self.valveWatch.running: # Water Detected and valve off
            self.open_valve()
            self.ui.waterLabel.setText("Water Detected\n Valve Open")
        elif not waterDetected and self.valveWatch.running: # No Water Detected and valve on
            self.close_valve()
            self.ui.waterLabel.setText("No Water Detected\n Valve Closed")

    def activate_timed_mode(self):
        # Activate the timed mode
        self.open_valve()
        self.timedValveWatch.start()
        self.timedValveTimer.start()

    def deactivate_timed_mode(self):
        # Deactivate the timed mode
        self.timedValveWatch.stop()
        self.timedValveWatch.reset()
        self.timedValveTimer.stop()

    def timed_mode(self):
        # Loop method for timed mode
        curTimeOpen = int(self.timedValveWatch.value())
        self.ui.timerProgress.setValue(curTimeOpen)
        # If timer exceeded maximum value, exit timed mode
        if curTimeOpen >= MAX_OPEN_SECONDS:
            self.timerFinished.emit()

    def update_valve_time(self):
        # Updates the valve's total time open

        # valveWatch should be reset at midnight
        if time.strftime("%H:%M:%S") == "00:00:00":
            self.valveTimeShouldReset = True

        # If valveTimer is running, the valve should be on, so update notificationLabel and check if time exceeded
        if self.valveWatch.running:
            curTimeOpen = self.valveWatch.value()
            self.ui.notificationLabel.setText(str(math.floor(curTimeOpen)) + ' seconds open')

            # Stop everything if exceeded maximum time for the day
            if curTimeOpen >= MAX_OPEN_SECONDS:
                self.timeLimitReached.emit()

        # Reset valveTimer if valve is shut off and it should reset
        elif self.valveTimeShouldReset:
            self.valveTimeShouldReset = False
            self.valveWatch.reset()

    def update_clock(self):
        # Updates clockLabel text with current time
        timeDate = time.asctime()
        self.ui.clockLabel.setText(timeDate) 

class UI(QMainWindow):
    
    def __init__(self):
        super(UI, self).__init__()
        uic.loadUi("testUI.ui", self)

        # Find the widgets in the .ui file
 
        self.clockLabel = self.findChild(QLabel, "clockLabel")
        self.lastOpenLabel = self.findChild(QLabel, "lastOpenLabel")
        self.notificationLabel = self.findChild(QLabel, "notificationLabel")

        self.stopButton = self.findChild(QPushButton, "stopButton")
        self.timedSwitch = self.findChild(QPushButton, "timedSwitch")
        self.valveSwitch = self.findChild(QPushButton, "valveSwitch")
        self.sensorSwitch = self.findChild(QPushButton, "sensorSwitch")
        
        self.timerProgress = self.findChild(QProgressBar, "timerProgress")
        self.waterLabel = self.findChild(QLabel, "waterLabel")
        self.logLabel = self.findChild(QLabel, "logLabel")

        self.timerProgress.setMaximum(MAX_OPEN_SECONDS)
        self.showFullScreen()
        
        # This is the start of a state machine for the system. Using this we can change the states and text of buttons easily
        # Connecting the methods that will be moved to pin_devices I haven't figure out yet
        
        # Lot of state creation, transitions, etc.
        self.machine = QStateMachine()
        
        self.idle = QState()
        self.manualEnabled = QState()
        self.sensorEnabled = QState()
        self.timerEnabled = QState()

        # unused for now
        self.timerRunning = QState(self.timerEnabled)
        self.timerFinished = QState(self.timerEnabled)

        self.idle.assignProperty(self.valveSwitch, "text", "Open Valve")
        self.idle.assignProperty(self.valveSwitch, "enabled", True)
        self.idle.assignProperty(self.sensorSwitch, "text", "Enable\n Water Sensor")
        self.idle.assignProperty(self.sensorSwitch, "enabled", True)
        self.idle.assignProperty(self.timedSwitch, "enabled", True)
        self.idle.assignProperty(self.timerProgress, "value", 0)
        self.idle.addTransition(self.valveSwitch.clicked, self.manualEnabled)
        self.idle.addTransition(self.sensorSwitch.clicked, self.sensorEnabled)
        self.idle.addTransition(self.timedSwitch.clicked, self.timerEnabled)

        self.manualEnabled.assignProperty(self.valveSwitch, "text", "Close Valve")
        self.manualEnabled.assignProperty(self.sensorSwitch, "enabled", False)
        self.manualEnabled.assignProperty(self.timedSwitch, "enabled", False)
        self.manualEnabled.addTransition(self.valveSwitch.clicked, self.idle)
        self.manualEnabled.addTransition(self.stopButton.clicked, self.idle)

        self.sensorEnabled.assignProperty(self.valveSwitch, "enabled", False)
        self.sensorEnabled.assignProperty(self.sensorSwitch, "enabled", True)
        self.sensorEnabled.assignProperty(self.sensorSwitch, "text", "Disable\n Water Sensor")
        self.sensorEnabled.assignProperty(self.timedSwitch, "enabled", False)
        self.sensorEnabled.addTransition(self.sensorSwitch.clicked, self.idle)
        self.sensorEnabled.addTransition(self.stopButton.clicked, self.idle)

        self.timerEnabled.setInitialState(self.timerRunning)
        self.timerEnabled.assignProperty(self.valveSwitch, "enabled", False)
        self.timerEnabled.assignProperty(self.sensorSwitch, "enabled", False)
        self.timerEnabled.assignProperty(self.timedSwitch, "enabled", False)
        self.timerEnabled.addTransition(self.stopButton.clicked, self.idle)
        
        self.machine.addState(self.idle)
        self.machine.addState(self.manualEnabled)
        self.machine.addState(self.sensorEnabled)
        self.machine.addState(self.timerEnabled)
        self.machine.setInitialState(self.idle)
        self.machine.setErrorState(self.idle)

        # Create the EventLoop down here since there are some overlapping dependencies between these two objects
        self.eventLoop = EventLoop(self)
        self.manualEnabled.addTransition(self.eventLoop.timeLimitReached, self.idle)
        self.sensorEnabled.addTransition(self.eventLoop.timeLimitReached, self.idle)
        self.timerEnabled.addTransition(self.eventLoop.timerFinished, self.idle)
        self.timerEnabled.addTransition(self.eventLoop.timeLimitReached, self.idle)
        
        self.machine.start()
