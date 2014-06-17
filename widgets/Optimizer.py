from PyQt4 import uic
from PyQt4 import QtGui, QtCore
import numpy as np
import random

Ui_Optimizer, QWidget = uic.loadUiType("ui/Optimizer.ui")


class Optimizer(QWidget, Ui_Optimizer):
    """Widget to handle all uploading to FPGA circuit."""

    change_bins = QtCore.pyqtSignal(list)
    plot_optimize_region = QtCore.pyqtSignal(object, object, object)

    def __init__(self, settings, parent):
        super(Optimizer, self).__init__(parent=parent)
        self.settings = settings
        self.setupUi(self)

        self.n_added = 0
        self.image_slice = None
        self.ready_to_upload = True
        self.bin_values = None
        self.loadSettings()

    def handleImageChanged(self, new_image_slice):
        new_data = np.array(new_image_slice, dtype=float)
        if self.image_slice is None:
            self.image_slice = new_data
            self.n_added = 0
        elif self.ready_to_upload:
            try:
                self.image_slice += new_data
                self.n_added += 1
            except:
                self.n_added = 0
                self.image_slice = new_data

        if self.liveUpdateCheck.isChecked():
            start_index = int(self.startPixelSpin.value())
            width = int(self.widthSpin.value())
            end_index = min(start_index + width, len(new_data))
            roi_data = new_data[start_index:end_index]
            mean_roi_data = np.mean(roi_data)
            max_roi_data = np.max(roi_data)
            sd_roi_data = np.std(roi_data)
            sd_over_mean = sd_roi_data / mean_roi_data

            self.meanSpin.setValue(mean_roi_data)
            self.maxSpin.setValue(max_roi_data)
            self.sdSpin.setValue(sd_roi_data)
            self.sdOverMeanSpin.setValue(sd_over_mean)

            self.plot_optimize_region.emit(None, roi_data, None)

    def handleReadyToUpload(self):
        self.ready_to_upload = True
        if self.autoCheckBox.isChecked() is True:
            # give some time to acquire a few images before
            # next iteration
            QtCore.QTimer.singleShot(300, self.handleIterate)

    def handleNotReadyToUpload(self):
        self.ready_to_upload = False

    def handleBinsChanged(self, new_bin_values):
        self.bin_values = list(new_bin_values)

    def handleIterate(self):
        if self.ready_to_upload:
            # take the average of all images picked up until now
            self.image_slice /= self.n_added
            print('ITERATION')
            print('n_added', self.n_added)
            jump_size = self.jumpSizeSpin.value()
            n_bins = len(self.bin_values)
            bin_to_modify = random.randint(0, n_bins - 1)
            curr_value = self.bin_values[bin_to_modify]
            new_value = curr_value + random.randint(-jump_size, jump_size)
            new_value = max(min(new_value, 100), 0)

            self.binNumberSpin.setValue(bin_to_modify)
            self.valueSpin.setValue(new_value)

            self.bin_values[bin_to_modify] = new_value
            self.change_bins.emit(self.bin_values)

            self.image_slice = None
            n_added = 0
        else:
            print('Not ready to upload')

    def loadSettings(self):
        """Load window state from self.settings"""

        self.settings.beginGroup('optimizer')
        start_pixel = self.settings.value('start_pixel', type=int, defaultValue=0)
        width = self.settings.value('width', type=int, defaultValue=0)
        jump_size = self.settings.value('jump_size', type=int, defaultValue=5)
        self.settings.endGroup()

        self.startPixelSpin.setValue(start_pixel)
        self.widthSpin.setValue(width)
        self.jumpSizeSpin.setValue(jump_size)

    def saveSettings(self):
        """Save window state to self.settings."""
        start_pixel = self.startPixelSpin.value()
        width = self.widthSpin.value()
        jump_size = self.jumpSizeSpin.value()
        self.settings.beginGroup('optimizer')
        self.settings.setValue('start_pixel', start_pixel)
        self.settings.setValue('width', width)
        self.settings.setValue('jump_size', jump_size)
        self.settings.endGroup()

