"""ui.py
Contains all UI-related stuff and logic.
"""

from PyQt5.QtWidgets import QMainWindow, QPushButton, QLabel, QProgressBar, QRadioButton
from PyQt5.QtCore import QStateMachine, QState
from PyQt5 import uic
from rm_modes import EventLoop

class UI(QMainWindow):
    """
    The UI object contains all GUI objects, such as labels and buttons.
    Also contains the state machine used for the GUI logic.
    """
    
    def __init__(self, updateMs, slowUpdateMs, maxOpenSeconds):
        """
        Initializer for the GUI. Loads the ui file and creates the state machine.
        `updateMs` is the interval between loops.
        `slowUpdateMs` is the interval between slower loops, i.e. updating the clock label.
        `maxOpenSeconds` is the maximum amount of time the valve should be opened for each day.
        """
        super(UI, self).__init__()
        uic.loadUi("newUI.ui", self)


        # Find the widgets in the .ui file
        self.clockLabel = self.findChild(QLabel, "clockLabel")
        #self.lastOpenLabel = self.findChild(QLabel, "lastOpenLabel")
        self.notificationLabel = self.findChild(QLabel, "notificationLabel")

        self.stopButton = self.findChild(QPushButton, "stopButton")
        #self.timedSwitch = self.findChild(QPushButton, "timedSwitch")
        self.demoSwitch = self.findChild(QPushButton, "demoSwitch")
        #self.sensorSwitch = self.findChild(QPushButton, "sensorSwitch")
        
        self.timerProgress = self.findChild(QProgressBar, "timerProgress")
        self.waterStatusLabel = self.findChild(QLabel, "waterStatusLabel")
        #self.logLabel = self.findChild(QLabel, "logLabel")

        self.detectRainModeSelect = self.findChild(QRadioButton, "detectRainModeSelect")
        self.scheduleModeSelect = self.findChild(QRadioButton, "scheduleModeSelect")
        
        self.timerProgress.setMaximum(maxOpenSeconds)
        self.showFullScreen()
        
        # Creates the state machine
        self.machine = QStateMachine()
        
        self.idle = QState()
        self.manualEnabled = QState()
        self.sensorEnabled = QState()
        self.timerEnabled = QState()

        # unused for now
        self.timerRunning = QState(self.timerEnabled)
        self.timerFinished = QState(self.timerEnabled)

        # Assign all state properties + transitions
        #self.idle.assignProperty(self.valveSwitch, "text", "Open Valve")
        self.idle.assignProperty(self.demoSwitch, "enabled", True)
        self.timerEnabled.assignProperty(self.scheduleModeSelect, "enabled", True)
        self.timerEnabled.assignProperty(self.detectRainModeSelect, "enabled", True)
        #self.idle.assignProperty(self.sensorSwitch, "text", "Enable\n Water Sensor")
        #self.idle.assignProperty(self.sensorSwitch, "enabled", True)
        #self.idle.assignProperty(self.timedSwitch, "enabled", True)
        self.idle.assignProperty(self.timerProgress, "value", 0)
        self.idle.addTransition(self.demoSwitch.clicked, self.manualEnabled)
        #self.idle.addTransition(self.sensorSwitch.clicked, self.sensorEnabled)
        #self.idle.addTransition(self.timedSwitch.clicked, self.timerEnabled)
        self.idle.addTransition(self.scheduleModeSelect.clicked, self.timerEnabled)
        self.idle.addTransition(self.detectRainModeSelect.clicked, self.sensorEnabled)

        self.manualEnabled.assignProperty(self.demoSwitch, "text", "Stop Demo")
        #self.manualEnabled.assignProperty(self.sensorSwitch, "enabled", False)
        #self.manualEnabled.assignProperty(self.timedSwitch, "enabled", False)
        self.manualEnabled.addTransition(self.demoSwitch.clicked, self.idle)
        self.manualEnabled.addTransition(self.stopButton.clicked, self.idle)

        self.sensorEnabled.assignProperty(self.demoSwitch, "enabled", False)
        #self.sensorEnabled.assignProperty(self.sensorSwitch, "enabled", True)
        #self.sensorEnabled.assignProperty(self.sensorSwitch, "text", "Disable\n Water Sensor")
        #self.sensorEnabled.assignProperty(self.timedSwitch, "enabled", False)
        #self.sensorEnabled.addTransition(self.sensorSwitch.clicked, self.idle)
        self.sensorEnabled.addTransition(self.scheduleModeSelect.clicked, self.timerEnabled)
        self.sensorEnabled.addTransition(self.stopButton.clicked, self.idle)

        self.timerEnabled.setInitialState(self.timerRunning)
        self.timerEnabled.assignProperty(self.demoSwitch, "enabled", False)
        self.timerEnabled.assignProperty(self.scheduleModeSelect, "enabled", False)
        self.timerEnabled.assignProperty(self.detectRainModeSelect, "enabled", False)
        #self.timerEnabled.assignProperty(self.sensorSwitch, "enabled", False)
        #self.timerEnabled.assignProperty(self.timedSwitch, "enabled", False)
        self.timerEnabled.addTransition(self.stopButton.clicked, self.idle)
        
        # Adds all states to the state machine
        self.machine.addState(self.idle)
        self.machine.addState(self.manualEnabled)
        self.machine.addState(self.sensorEnabled)
        self.machine.addState(self.timerEnabled)
        self.machine.setInitialState(self.idle)
        self.machine.setErrorState(self.idle)

        # Create the EventLoop down here since there are some overlapping dependencies between these two objects
        self.eventLoop = EventLoop(self, updateMs, slowUpdateMs, maxOpenSeconds)

        # Further transitions based on EventLoop pyqtSignals
        self.manualEnabled.addTransition(self.eventLoop.timeLimitReached, self.idle)
        self.sensorEnabled.addTransition(self.eventLoop.timeLimitReached, self.idle)
        self.timerEnabled.addTransition(self.eventLoop.timerFinished, self.idle)
        self.timerEnabled.addTransition(self.eventLoop.timeLimitReached, self.idle)
        
        # Start the state machine (and thus all GUI logic)
        self.machine.start()
