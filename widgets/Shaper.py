from PyQt4 import uic
from PyQt4 import QtGui, QtCore
from clt.ramps import ramp_dict
from clt import ramps
from clt import barrierclient
import numpy as np

Ui_Shaper, QWidget = uic.loadUiType("ui/Shaper.ui")

# number of bins to split the waveform into
N_BINS = 25


class Uploader(QtCore.QObject):

    finished = QtCore.pyqtSignal()
    progress = QtCore.pyqtSignal(int)


    def __init__(self, addresses, values):

        self.addresses = np.array(addresses)
        self.values = np.array(values)
        # print('Sending data')
        self.sockobj = barrierclient.upload_points(self.addresses, self.values)
        super(Uploader, self).__init__()

    def longRunning(self):
        for i in range(len(self.addresses)):
            _ = barrierclient.recv_string(self.sockobj)
            self.progress.emit(i)
        # print('revd all data')

        self.sockobj.close()
        self.finished.emit()


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

    finishedUploading = QtCore.pyqtSignal()
    startedUploading = QtCore.pyqtSignal()
    bins_changed = QtCore.pyqtSignal(list)

    def __init__(self, settings, parent):
        super(Shaper, self).__init__(parent=parent)
        self.settings = settings
        self.setupUi(self)

        self.sb_values = [0 for i in range(N_BINS)]

        self.old_ramp = None

        self.addSpinBoxes()
        self.loadSettings()
        self.connectSlots()

        # Fill up comboBox with ramp items
        for key in ramp_dict:
            self.rampListCombo.addItem(key)

        self.interpTypeCombo.addItems(ramps.interp_types)
        self.uploading = False
        self.progressBar.reset()
        # print(self.old_ramp)

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
        self.handleUpload(only_changes=False)

    def handleUploadChanges(self):
        self.handleUpload(only_changes=True)

    def handleResetState(self):
        self.handleFinishedUploading()

    def handleFinishedUploading(self):
        self.progressBar.reset()
        self.uploadAllButton.setEnabled(True)
        self.uploadChangesButton.setEnabled(True)
        self.uploading = False

        # save stuff in case program crashes
        self.saveSettings()
        self.settings.sync()

        # add intentional delay before letting everyone else know
        # that we are done uploading.
        QtCore.QTimer.singleShot(300, self.emitFinishedUploading)

    def emitFinishedUploading(self):
        self.finishedUploading.emit()

    def handleUpload(self, only_changes=False):
        # print('Handle upload. self.uploading=', self.uploading)
        if self.uploading:
            # print('Already uploading, wait until upload is over')
            return

        min_value = self.minVoltageSpinBox.value()
        max_value = self.maxVoltageSpinBox.value()
        interpolation = str(self.interpTypeCombo.currentText())
        # print('Handle upload: making ramps')
        addr, val = ramps.make_full_ramp(self.sb_values, 1000,
                                         minValue=min_value,
                                         maxValue=max_value,
                                         interpolation=interpolation)
        # print('Handle upload: finding changes')
        if only_changes is True and self.old_ramp is not None:
            u_addr = addr
            u_val = val
            old_val = self.old_ramp[1]
            is_different = old_val != val
            n_upload = np.sum(is_different)
            if n_upload == 0:
                # no changes
                self.progressBar.reset()
                self.uploading = False
                QtCore.QTimer.singleShot(300, self.emitFinishedUploading)
                return
            u_addr = np.zeros(n_upload)
            u_val = np.zeros(n_upload)
            index = 0
            for a, v, is_d in zip(addr, val, is_different):
                if is_d:
                    u_addr[index] = a
                    u_val[index] = v
                    index += 1
        else:
            u_addr = addr
            u_val = val

        self.startedUploading.emit()
        self.uploadAllButton.setEnabled(False)
        self.uploadChangesButton.setEnabled(False)
        self.uploading = True

        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(len(u_addr))
        self.progressBar.reset()

        # print('Making thread')
        uploader_thread = QtCore.QThread(parent=self)
        self.uploader = Uploader(u_addr, u_val)
        self.uploader.progress.connect(self.progressBar.setValue)
        self.uploader.moveToThread(uploader_thread)
        self.uploader.finished.connect(uploader_thread.quit)
        uploader_thread.started.connect(self.uploader.longRunning)
        uploader_thread.finished.connect(self.handleFinishedUploading)
        uploader_thread.start()
        self.old_ramp = (addr, val)

    def saveSettings(self):
        self.settings.beginGroup('shaper')
        self.settings.setValue('sb_values', repr(self.sb_values))
        min_voltage = self.minVoltageSpinBox.value()
        max_voltage = self.maxVoltageSpinBox.value()
        self.settings.setValue('min_voltage', min_voltage)
        self.settings.setValue('max_voltage', max_voltage)
        old_ramp_save = [list(self.old_ramp[0]), list(self.old_ramp[1])]
        self.settings.setValue('old_ramp', repr(old_ramp_save))
        self.settings.endGroup()

    def loadSettings(self):
        self.settings.beginGroup('shaper')
        sb_string = str(self.settings.value('sb_values').toString())
        min_voltage = self.settings.value('min_voltage', type=int,
                                          defaultValue=0)
        max_voltage = self.settings.value('max_voltage', type=int,
                                          defaultValue=1000)
        self.minVoltageSpinBox.setValue(min_voltage)
        self.maxVoltageSpinBox.setValue(max_voltage)
        if sb_string is not "":
            self.sb_values = eval(sb_string)
            self.updateSpinBoxes()
        old_ramp_string = str(self.settings.value('old_ramp').toString())
        self.settings.endGroup()
        self.bins_changed.emit(self.sb_values)

        if old_ramp_string is not "":
            old_ramp_load = eval(old_ramp_string)
            self.old_ramp = (np.array(old_ramp_load[0], dtype=int),
                             np.array(old_ramp_load[1], dtype=int))

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

        self.sb_values = all_new_values
        self.bins_changed.emit(self.sb_values)

    def handleResetRamp(self):
        # print('reset ramp')
        ramp_func = ramp_dict[str(self.rampListCombo.currentText())]
        self.sb_values = ramp_func(N_BINS)
        self.disconnectSlots()
        self.updateSpinBoxes()
        self.connectSlots()
        self.bins_changed.emit(self.sb_values)

    def handleSort(self):
        self.sb_values = sorted(self.sb_values)
        self.disconnectSlots()
        self.updateSpinBoxes()
        self.connectSlots()
        self.bins_changed.emit(self.sb_values)

    def changeBins(self, new_bins):
        self.sb_values = list(new_bins)
        # print(len(self.sb_values))
        # print(self.sb_values)
        self.disconnectSlots()
        self.updateSpinBoxes()
        self.connectSlots()
        self.handleUpload(only_changes=True)


    def handleCopy(self):
        infoString = repr(self.sb_values)
        clipboard = QtGui.QApplication.clipboard()
        clipboard.setText(infoString)

    def handlePaste(self):
        clipboard = QtGui.QApplication.clipboard()
        infoString = str(clipboard.text())
        self.sb_values = eval(infoString, {}, {})
        self.disconnectSlots()
        self.updateSpinBoxes()
        self.connectSlots()
        self.bins_changed.emit(self.sb_values)

