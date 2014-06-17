from PyQt4 import uic
from PyQt4 import QtGui, QtCore
import numpy as np

Ui_Optimizer, QWidget = uic.loadUiType("ui/Optimizer.ui")

# number of bins to split the waveform into
N_BINS = 25


class Optimizer(QWidget, Ui_Optimizer):
    """Widget to handle all uploading to FPGA circuit."""

    def __init__(self, settings, parent):
        super(Optimizer, self).__init__(parent=parent)
        self.settings = settings
        self.setupUi(self)