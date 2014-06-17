from PyQt4 import uic
from PyQt4 import QtGui, QtCore
import numpy as np
import random

Ui_Optimizer, QWidget = uic.loadUiType("ui/Optimizer.ui")


class Optimizer(QWidget, Ui_Optimizer):
    """Widget to handle all uploading to FPGA circuit."""

    change_bins = QtCore.pyqtSignal(list)

    def __init__(self, settings, parent):
        super(Optimizer, self).__init__(parent=parent)
        self.settings = settings
        self.setupUi(self)

        self.image_slice = None
        self.ready_to_upload = True
        self.bin_values = None

    def handleImageChanged(self, new_image_slice):
        new_data = np.array(new_image_slice, dtype=float)
        if self.image_slice is None:
            self.image_slice = new_data
        else:
            try:
                self.image_slice += new_data
            except:
                self.image_slice = new_data

        start_index = self.startPixelSpin.value()
        width = self.widthSpin.value()
        roi_data = new_data[start_index:start_index + width]
        mean_roi_data = np.mean(roi_data)
        max_roi_data = np.max(roi_data)
        sd_roi_data = np.std(roi_data)
        sd_over_mean = sd_roi_data / mean_roi_data

        self.meanSpin.setValue(mean_roi_data)
        self.maxSpin.setValue(max_roi_data)
        self.sdSpin.setValue(sd_roi_data)
        self.sdOverMeanSpin.setValue(sd_over_mean)



    def handleReadyToUpload(self):
        self.ready_to_upload = True
        if self.autoCheckBox.isChecked() is True:
            self.handleIterate()

    def handleNotReadyToUpload(self):
        self.ready_to_upload = False

    def handleBinsChanged(self, new_bin_values):
        self.bin_values = list(new_bin_values)

    def handleIterate(self):
        if self.ready_to_upload:
            print('Uploading')
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
        else:
            print('Not ready to upload')





