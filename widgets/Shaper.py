from PyQt4 import uic
from PyQt4 import QtGui

Ui_Shaper, QWidget = uic.loadUiType("ui/Shaper.ui")

# number of bins to split the waveform into
N_BINS = 25


class Shaper(QWidget, Ui_Shaper):
    """Widget to handle all uploading to FPGA circuit."""

    def __init__(self, settings, parent):
        super(Shaper, self).__init__(parent=parent)
        self.settings = settings
        self.setupUi(self)
        self.addSpinBoxes()

    def addSpinBoxes(self):
        self.spin_boxes = [QtGui.QSpinBox(self) for i in range(N_BINS)]
        for sb in self.spin_boxes:
            self.spinBoxLayout.addWidget(sb)

    def handleUploadAll(self):
        print('upload all')

    def saveSettings(self):
        print('shaper save settings')
