"""rm_modes.py
Contains all the various modes of the main program.
"""

from PyQt5.QtCore import QTimer, pyqtSignal, QObject

from pin_devices import output_valve, water_detected, rpi_cleanup
#, lightning, turnOffLED
from rm_utils import Stopwatch, TimeStampLog

import time
import math

# Still need to clean up, decrease dependencies on parent object (EventLoop) within a few modes
# Potential improvement for future sems: work solely based off of signals, UI updates triggered
# by signals emitted within each Mode, pass information using these pyqtSignals
class AbstractMode(QObject):
    """
    I know, I know, it's called a 'mode', but it's really a loop.
    Just abstracts looping logic into an object, with decent extendability.
    """

    def __init__(self, parent, updateMs):
        """
        Initializer for the AbstractMode object, creating the QTimer for looping. Add in any custom logic.
        `parent` should be the EventLoop object. A little messy with inter-dependencies, but that's how it is for now.
        `updateMs` is the interval between loops.
        """
        super(AbstractMode, self).__init__()
        self.parent = parent
        self.updateMs = updateMs
        self.timer = QTimer(self)
        self.timer.setInterval(updateMs)
        self.timer.timeout.connect(self.update)

    def activate(self):
        """
        Called to activate the loop. Add in any custom logic.
        """
        self.timer.start()

    def deactivate(self):
        """
        Called to deactivate the loop. Add in any custom logic.
        """
        self.timer.stop()

    def update(self):
        """
        Called each interval of the loop. Add in any custom logic.
        """
        pass

class SensorMode(AbstractMode):
    """
    Object representing the sensor mode of the UI.
    Uses the water sensor for opening/closing the valve.
    """

    def __init__(self, parent, updateMs, label):
        """
        Initializer for the object. Includes a GUI element.
        `label` is the label that should be updated when the sensor state changes.
        """
        super(SensorMode, self).__init__(parent, updateMs)
        self.label = label
        self.previousState = None

    def update(self):
        """
        Turns on/off the valve depending on if water is detected
        """
        waterDetected = water_detected()

        if waterDetected: # Water Detected
            if self.previousState is None or not self.previousState:
                self.parent.open_valve()
                self.label.setText("Water Detected\n Valve Open")
            self.previousState = True
        elif not waterDetected: # No Water Detected
            if self.previousState is None or self.previousState:
                self.parent.close_valve()
                self.label.setText("No Water Detected\n Valve Closed")
            self.previousState = False

class TimedMode(AbstractMode):
    """
    Object representing the timed mode of the UI.
    Turns the valve on for a preset amount of time.
    Simply change maxOpenSeconds for this object if you want to change that amount of time.
    """

    def __init__(self, parent, updateMs, maxOpenSeconds, progressBar, signal):
        """
        Initializer for the object.
        `maxOpenSeconds` is the time to open the valve for.
        `progressBar` is the progress bar to slowly fill.
        `signal` is the pyqtSignal to emit when the timer has finished.
        """
        super(TimedMode, self).__init__(parent, updateMs)
        self.maxOpenSeconds = maxOpenSeconds
        self.progressBar = progressBar
        self.signal = signal
        self.timerWatch = Stopwatch()

    def activate(self):
        """
        Activation method.
        Essentially the same as AbstractMode's, but also starts the watch and opens the valve.
        """
        self.timerWatch.start()
        self.parent.open_valve()
        super(TimedMode, self).activate()

    def deactivate(self):
        """
        Deactivation method.
        Essentially the same as AbstractMode's, but also stops and resets the watch. Closing the valve happens upon transitioning to idle state.
        """
        self.timerWatch.stop()
        self.timerWatch.reset()
        super(TimedMode, self).deactivate()

    def update(self):
        """
        Updates the time and checks if the time has exceeded maxOpenSeconds.
        """
        curTimeOpen = int(self.timerWatch.value())
        self.progressBar.setValue(curTimeOpen)
        # If timer exceeded maximum value, emit signal
        if curTimeOpen >= self.maxOpenSeconds:
            self.signal.emit()

class TimeOpenMode(AbstractMode):
    """
    Object representing the update loop for the time the valve has been open.
    """

    def __init__(self, parent, updateMs, maxOpenSeconds, label, signal):
        """
        Initializer for the object.
        `maxOpenSeconds` is the maximum amount of time the valve should be open for each day.
        `label` is the label to update with the time open.
        `signal` is the signal to emit upon the total time open exceeding maxOpenSeconds.
        """
        super(TimeOpenMode, self).__init__(parent, updateMs)
        self.maxOpenSeconds = maxOpenSeconds
        self.timerWatch = Stopwatch()
        self.timerShouldReset = False
        self.label = label
        self.signal = signal

    def update(self):
        """
        Updates the GUI element and handles time limit-related logic.
        """

        # The time should reset at midnight
        if time.strftime("%H:%M:%S") == "00:00:00":
            self.timerShouldReset = True

        # If timerWatch is running, the valve should be on, so continuously update the label and check if time exceeded
        if self.timerWatch.running:
            curTimeOpen = self.timerWatch.value()
            self.label.setText(str(math.floor(curTimeOpen)) + ' seconds open')

            # Emit signal if exceeded maximum time for the day
            if curTimeOpen >= self.maxOpenSeconds:
                self.signal.emit()

        # Reset valveTimer if valve is shut off (implied above) and it should reset; this fixes the issue of resetting at midnight
        elif self.timerShouldReset:
            self.timerShouldReset = False
            self.timerWatch.reset()

class ClockMode(AbstractMode):
    """
    Object representing the clock label updating.
    """

    def __init__(self, parent, updateMs, label):
        """
        Initializer for the object.
        `label` is the label the time should be displayed onto.
        """
        super(ClockMode, self).__init__(parent, updateMs)
        self.label = label

    def update(self):
        """
        Updates the label with the current time.
        """
        timeDate = time.asctime()
        self.label.setText(timeDate)

# Inherits QObject to allow for pyqtSignal usage
class EventLoop(QObject):
    """
    Handles more of the GUI logic, this time more centered around (surprise) the actual events and loops.
    To be clearer, it creates all the loops that occur actively or passively in the program, and also
    specifies the logic that should be executed upon entering/exiting each state.
    """

    # Custom signals for state transitions
    timerFinished = pyqtSignal() # emitted when timed mode finishes
    timeLimitReached = pyqtSignal() # emitted when time limit for the day reached

    def __init__(self, ui, updateMs=10, slowUpdateMs=500, maxOpenSeconds=300):
        """
        Initializer for the object. Basically everything happens here.
        `updateMs` is the interval between loops.
        `slowUpdateMs` is the interval between slower loops.
        `maxOpenSeconds` is the maximum amount of time the valve should be opened for each day.
        """
        super(EventLoop, self).__init__()
        self.ui = ui
        self.updateMs = updateMs
        self.slowUpdateMs = slowUpdateMs
        self.maxOpenSeconds = maxOpenSeconds

        # Keeps track of the valve opening/closing
        self.valveRecord = TimeStampLog()

        # Loop for tracking the time the valve has been open for
        self.timeOpenMode = TimeOpenMode(self, self.updateMs, self.maxOpenSeconds, ui.notificationLabel, self.timeLimitReached)
        self.valveWatch = self.timeOpenMode.timerWatch
        self.timeOpenMode.activate()

        # Loop for updating the clock
        self.clockMode = ClockMode(self, self.slowUpdateMs, ui.clockLabel)
        self.clockMode.activate()

        # Loop for sensor mode
        self.sensorMode = SensorMode(self, self.updateMs, ui.waterLabel)

        # Loop for timed mode
        self.timedMode = TimedMode(self, self.updateMs, self.maxOpenSeconds, ui.timerProgress, self.timerFinished)

        # State machine-related transition logic
        ui.manualEnabled.entered.connect(self.open_valve)
        ui.manualEnabled.exited.connect(self.close_valve)
        ui.sensorEnabled.entered.connect(self.sensorMode.activate)
        ui.sensorEnabled.exited.connect(self.sensorMode.deactivate)
        ui.timerEnabled.entered.connect(self.timedMode.activate)
        ui.timerEnabled.exited.connect(self.timedMode.deactivate)

        # VERY IMPORTANT, upon entering idle it should always close the valve
        ui.idle.entered.connect(self.close_valve)

    def open_valve(self):
        """
        Method for opening the valve that includes all the logistical stuff.
        """

        # Logistical stuff only executes if valve is closed
        if not self.valveWatch.running:
            self.valveWatch.start()
            self.valveRecord.open_time(time.time())
            self.ui.lastOpenLabel.setText('Last open: ' + self.valveRecord.get_last_open())
            self.update_log()
        #lightning()
        output_valve(1)
    
    def close_valve(self):
        """
        Method for closing the valve that includes all the logistical stuff.
        """

        # Logistical stuff only executes if valve is open
        if self.valveWatch.running:
            self.valveWatch.stop()
            self.valveRecord.close_time(time.time())
            self.ui.lastOpenLabel.setText('Last open: ' + self.valveRecord.get_last_open() + " for " + self.valveRecord.get_time_open() + " seconds")
            self.update_log()
        #turnOffLED()
        output_valve(0)

    def update_log(self):
        """
        Updates the log label with times opened/closed.
        """

        # Update the logging text
        self.ui.logLabel.setText('Open ' + self.valveRecord.times_open() + ' times(s) today\n' +
        'Closed ' + self.valveRecord.times_closed() + ' time(s) today')
