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

class EventLoop(QObject):
    timerFinished = pyqtSignal()
    timeLimitReached = pyqtSignal()

    def __init__(self, ui):
        super(EventLoop, self).__init__()
        self.ui = ui

        self.valveRecord = TimeStampLog()

        self.timedValveWatch = Stopwatch()
        self.timedValveTimer = QTimer(ui)
        self.timedValveTimer.timeout.connect(self.timed_valve_open)
        self.timedValveTimer.setInterval(UPDATE_MS)

        self.waterCheckTimer = QTimer(ui)
        self.waterCheckTimer.timeout.connect(self.water_check_mode)
        self.waterCheckTimer.setInterval(UPDATE_MS)

        self.valveWatch = Stopwatch()
        self.valveTimerShouldReset = False
        self.valveTimeOpenTimer = QTimer(ui)
        self.valveTimeOpenTimer.timeout.connect(self.update_valve_timer)
        self.valveTimeOpenTimer.setInterval(UPDATE_MS)
        self.valveTimeOpenTimer.start()

        self.clockTimer = QTimer(ui)
        self.clockTimer.timeout.connect(self.update_clock)
        self.clockTimer.start(SLOW_UPDATE_MS)

        ui.manualEnabled.entered.connect(self.open_valve)
        ui.manualEnabled.exited.connect(self.close_valve)
        ui.sensorEnabled.entered.connect(self.waterCheckTimer.start)
        ui.sensorEnabled.exited.connect(self.waterCheckTimer.stop)
        ui.timerEnabled.entered.connect(self.timedValveTimer.start)

    def open_valve(self): # Open valve
        # logistical stuff only executes if valve is closed
        if not self.valveWatch.running:
            self.valveWatch.start()
            self.valveRecord.open_time(time.time())
            self.ui.lastOpenLabel.setText('Last open: ' + self.valveRecord.get_last_open())
            self.update_log()
        output_valve(1)
    
    def close_valve(self): # Close valve
        # logistical stuff only executes if valve is open
        if self.valveWatch.running:
            self.valveWatch.stop()
            self.valveRecord.close_time(time.time())
            self.ui.lastOpenLabel.setText('Last open: ' + self.valveRecord.get_last_open() + " for " + self.valveRecord.get_time_open() + " seconds")
            self.update_log()
        output_valve(0)

    def update_log(self):
        self.ui.logLabel.setText('Open ' + self.valveRecord.times_open() + ' times(s) today\n' +
        'Closed ' + self.valveRecord.times_closed() + ' time(s) today')

    def water_check_mode(self): # Idle mode that checks for water now that sensor has been activated
        if water_detected() and not self.valveWatch.running: # Water Detected and valve off
            open_valve()
            self.ui.waterLabel.setText("Water Detected\n Valve Open")
        elif not water_detected() and self.valveWatch.running: # No Water Detected and valve on
            close_valve()
            self.ui.waterLabel.setText("No Water Detected\n Valve Closed")

    def deactivate_timer(self): # Deactivates the timer mode
        # stop and reset timer so that timer stops and progress bar resets
        self.timedValveWatch.stop()
        self.timedValveWatch.reset()
        self.timedValveTimer.stop()
        self.timerFinished.emit()

    def timed_valve_open(self): # Idle state to wait for timer to reach time limit
        curTimeOpen = int(self.timedValveWatch.value())
        self.ui.timerProgress.setValue(curTimeOpen)
        # if timer exceeded maximum value, call deactivate_timer
        if curTimeOpen >= MAX_OPEN_SECONDS:
            self.deactivate_timer()

    def update_valve_timer(self): # Updates the valve's total time open
        # indicate valveWatch should be reset at midnight
        if time.strftime("%H:%M:%S") == "00:00:00":
            self.valveTimerShouldReset = True

        # if valveTimer is running, valve is on, so update notificationLabel and check if time exceeded
        if self.valveWatch.running:
            curTimeOpen = self.valveWatch.value()
            self.ui.notificationLabel.setText(str(math.floor(curTimeOpen)) + ' seconds open')

            # stop everything if exceeded maximum time for the day
            if curTimeOpen >= MAX_OPEN_SECONDS:
                self.timeLimitReached.emit()

        # reset valveTimer if valve is shut off and it should reset
        elif self.valveTimerShouldReset:
            self.valveTimerShouldReset = False
            self.valveWatch.reset()

    def update_clock(self): # Updates Clock at top banner every 0.5 second (500 miliseconds)
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
        
        self.machine = QStateMachine()
        
        self.idle = QState()
        self.manualEnabled = QState()
        self.sensorEnabled = QState()
        self.timerEnabled = QState()
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

        self.eventLoop = EventLoop(self)
        self.manualEnabled.addTransition(self.eventLoop.timeLimitReached, self.idle)
        self.sensorEnabled.addTransition(self.eventLoop.timeLimitReached, self.idle)
        self.timerEnabled.addTransition(self.eventLoop.timerFinished, self.idle)
        self.timerEnabled.addTransition(self.eventLoop.timeLimitReached, self.idle)
        
        self.machine.start()
