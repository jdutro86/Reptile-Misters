"""rm_modes.py
Contains all the various modes of the main program.
"""

from PyQt5.QtCore import QTimer, pyqtSignal, QObject

from pin_devices import output_valve, water_detected, rpi_cleanup
from rm_utils import Stopwatch, TimeStampLog

import time
import math

# Still need to clean up, decrease dependencies on parent object (EventLoop) within each mode
# Potential improvement: work solely based off of signals, UI updates triggered by signals
# emitted within each Mode
class AbstractMode(QObject):
    def __init__(self, parent, UPDATE_MS):
        super(AbstractMode, self).__init__()
        self.parent = parent
        self.UPDATE_MS = UPDATE_MS
        self.timer = QTimer(self)
        self.timer.setInterval(UPDATE_MS)
        self.timer.timeout.connect(self.update)

    def activate(self):
        # Called to activate the timer
        self.timer.start()

    def deactivate(self):
        # Called to deactivate the timer
        self.timer.stop()

    def update(self):
        # Called each interval of the timer
        pass

class SensorMode(AbstractMode):
    def __init__(self, parent, UPDATE_MS, label):
        super(SensorMode, self).__init__(parent, UPDATE_MS)
        self.label = label

    def update(self):
        # Loop method for sensor mode
        waterDetected = water_detected()

        if waterDetected and not self.parent.valveWatch.running: # Water Detected and valve off
            self.parent.open_valve()
            self.label.setText("Water Detected\n Valve Open")
        elif not waterDetected and self.parent.valveWatch.running: # No Water Detected and valve on
            self.parent.close_valve()
            self.label.setText("No Water Detected\n Valve Closed")

class TimedMode(AbstractMode):
    def __init__(self, parent, UPDATE_MS, MAX_OPEN_SECONDS, progressBar, signal):
        super(TimedMode, self).__init__(parent, UPDATE_MS)
        self.MAX_OPEN_SECONDS = MAX_OPEN_SECONDS
        self.progressBar = progressBar
        self.signal = signal
        self.timerWatch = Stopwatch()

    def activate(self):
        self.timerWatch.start()
        self.parent.open_valve()
        super(TimedMode, self).activate()

    def deactivate(self):
        self.timerWatch.stop()
        self.timerWatch.reset()
        super(TimedMode, self).deactivate()

    def update(self):
        # Loop method for timed mode
        curTimeOpen = int(self.timerWatch.value())
        self.progressBar.setValue(curTimeOpen)
        # If timer exceeded maximum value, emit signal
        if curTimeOpen >= self.MAX_OPEN_SECONDS:
            self.signal.emit()

class TimeOpenMode(AbstractMode):
    def __init__(self, parent, UPDATE_MS, MAX_OPEN_SECONDS, label, signal):
        super(TimeOpenMode, self).__init__(parent, UPDATE_MS)
        self.MAX_OPEN_SECONDS = MAX_OPEN_SECONDS
        self.timerWatch = Stopwatch()
        self.timerShouldReset = False
        self.label = label
        self.signal = signal

    def update(self):
        # Updates the valve's total time open

        # timerWatch should be reset at midnight
        if time.strftime("%H:%M:%S") == "00:00:00":
            self.timerShouldReset = True

        # If valveTimer is running, the valve should be on, so update notificationLabel and check if time exceeded
        if self.timerWatch.running:
            curTimeOpen = self.timerWatch.value()
            self.label.setText(str(math.floor(curTimeOpen)) + ' seconds open')

            # Emit signal if exceeded maximum time for the day
            if curTimeOpen >= self.MAX_OPEN_SECONDS:
                self.signal.emit()

        # Reset valveTimer if valve is shut off and it should reset
        elif self.timerShouldReset:
            self.timerShouldReset = False
            self.timerWatch.reset()

class ClockMode(AbstractMode):
    def update(self):
        # Updates clockLabel text with current time
        timeDate = time.asctime()
        self.parent.ui.clockLabel.setText(timeDate)

# Inherits QObject to allow for pyqtSignal usage
class EventLoop(QObject):
    # Custom signals for state transitions
    timerFinished = pyqtSignal()
    timeLimitReached = pyqtSignal()

    def __init__(self, ui, UPDATE_MS=10, SLOW_UPDATE_MS=500, MAX_OPEN_SECONDS=300):
        super(EventLoop, self).__init__()
        self.ui = ui
        self.UPDATE_MS = UPDATE_MS
        self.SLOW_UPDATE_MS = SLOW_UPDATE_MS
        self.MAX_OPEN_SECONDS = MAX_OPEN_SECONDS

        self.valveRecord = TimeStampLog()

        # QTimer for valve open time tracking
        self.timeOpenMode = TimeOpenMode(self, self.UPDATE_MS, self.MAX_OPEN_SECONDS, ui.notificationLabel, self.timeLimitReached)
        self.valveWatch = self.timeOpenMode.timerWatch
        self.timeOpenMode.activate()

        # QTimer for clock updates
        self.clockMode = ClockMode(self, self.SLOW_UPDATE_MS)
        self.clockMode.activate()

        # QTimer for sensor mode
        self.sensorMode = SensorMode(self, self.UPDATE_MS, ui.waterLabel)

        # QTimer for timed mode
        self.timedMode = TimedMode(self, self.UPDATE_MS, self.MAX_OPEN_SECONDS, ui.timerProgress, self.timerFinished)

        # State machine-related transition logic
        ui.manualEnabled.entered.connect(self.open_valve)
        ui.manualEnabled.exited.connect(self.close_valve)
        ui.sensorEnabled.entered.connect(self.sensorMode.activate)
        ui.sensorEnabled.exited.connect(self.sensorMode.deactivate)
        ui.timerEnabled.entered.connect(self.timedMode.activate)
        ui.timerEnabled.exited.connect(self.timedMode.deactivate)

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
