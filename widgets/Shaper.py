from PyQt4 import uic
from PyQt4 import QtGui, QtCore

Ui_Shaper, QWidget = uic.loadUiType("ui/Shaper.ui")

# number of bins to split the waveform into
N_BINS = 25


class MySpinBox(QtGui.QSpinBox):
    """Selects all text once it receives a focusInEvent."""

    def __init__(self, parent):
        super(MySpinBox, self).__init__()

    def focusInEvent(self, e):
        super(MySpinBox, self).focusInEvent(e)
        QtCore.QTimer.singleShot(100, self.afterFocus)

    def afterFocus(self):
        self.selectAll()


class Shaper(QWidget, Ui_Shaper):
    """Widget to handle all uploading to FPGA circuit."""

    def __init__(self, settings, parent):
        super(Shaper, self).__init__(parent=parent)
        self.settings = settings
        self.setupUi(self)

        self.sb_values = [0 for i in range(N_BINS)]

        self.addSpinBoxes()
        self.loadSettings()
        self.connectSlots()

    def addSpinBoxes(self):
        self.spin_boxes = [MySpinBox(self) for i in range(N_BINS)]
        for sb in self.spin_boxes:
            sb.setMinimum(0)
            sb.setMaximum(100)
            sb.setKeyboardTracking(False)
            self.spinBoxLayout.addWidget(sb)

    def connectSlots(self):
        for sb in self.spin_boxes:
            sb.valueChanged.connect(self.handleSpinBoxValueChanged)

    def disconnectSlots(self):
        for sb in self.spin_boxes:
            sb.valueChanged.disconnect(self.handleSpinBoxValueChanged)

    def handleUploadAll(self):
        print('upload all')

    def saveSettings(self):
        self.settings.beginGroup('shaper')
        self.settings.setValue('sb_values', repr(self.sb_values))
        self.settings.endGroup()

    def loadSettings(self):
        self.settings.beginGroup('shaper')
        sb_string = str(self.settings.value('sb_values').toString())
        if sb_string is not "":
            self.sb_values = eval(sb_string)
            self.updateSpinBoxes()
        self.settings.endGroup()

    def updateSpinBoxes(self):
        for sb, v in zip(self.spin_boxes, self.sb_values):
            sb.setValue(v)

    def handleSpinBoxValueChanged(self, _):
        index_changed = 0
        all_new_values = [sb.value() for sb in self.spin_boxes]
        # find out which spin box was changed
        for i, (new_value, old_value) in enumerate(zip(all_new_values,
                                                       self.sb_values)):
            if new_value is not old_value:
                index_changed = i

        print(index_changed)
        self.sb_values = all_new_values

