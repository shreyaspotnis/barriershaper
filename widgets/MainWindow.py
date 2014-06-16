from PyQt4 import uic
from PyQt4 import QtCore
from pyqtgraph.dockarea import DockArea, Dock

from widgets import Shaper, ImageView, RoiEditor
from clt import camera
import time

Ui_MainWindow, QMainWindow = uic.loadUiType("ui/MainWindow.ui")


class FrameGrabber(QtCore.QObject):
    """A background thread that grabs frames and emits them."""

    finished = QtCore.pyqtSignal()
    framegrabbed = QtCore.pyqtSignal(object)

    def __init__(self):
        super(FrameGrabber, self).__init__()
        camera.start_continuous_acquisition()

    def longRunning(self):
        sleep_time = 0.05
        while(1):
            self.framegrabbed.emit(camera.get_image())
            print('frame grabbed')
            time.sleep(sleep_time)

        self.finished.emit()

    def close(self):
        camera.close_everything()
        self.finished.emit()


class MainWindow(QMainWindow, Ui_MainWindow):
    """Where all the action happens."""

    def __init__(self, settings):
        super(MainWindow, self).__init__()
        self.settings = settings
        self.setupUi(self)

        # MainWindow is a collection of widgets in their respective docks.
        # We make DockArea our central widget
        self.dock_area = DockArea()
        self.setCentralWidget(self.dock_area)

        self.createDocks()
        self.loadSettings()
        self.setupAcquisition()

    def setupAcquisition(self):
        camera_thread = QtCore.QThread(parent=self)
        self.frame_grabber = FrameGrabber()
        self.frame_grabber.moveToThread(camera_thread)
        self.frame_grabber.framegrabbed.connect(self.image_view.handleImageChanged)
        self.frame_grabber.finished.connect(camera_thread.quit)
        camera_thread.started.connect(self.frame_grabber.longRunning)
        camera_thread.start()

    def createDocks(self):
        self.shaper = Shaper(self.settings, self)
        self.image_view = ImageView(self.settings, self)
        self.roi_editor = RoiEditor(self.settings, self.image_view, self)

        self.dock_shaper = Dock('Shaper', widget=self.shaper)
        self.dock_image_view = Dock('ImageView', widget=self.image_view)
        self.dock_roi_editor = Dock('RoiEditor', widget=self.roi_editor)
        self.dock_area.addDock(self.dock_image_view, position='top')
        self.dock_area.addDock(self.dock_roi_editor, position='bottom', relativeTo=self.dock_image_view)
        self.dock_area.addDock(self.dock_shaper, position='right', relativeTo=self.dock_image_view)

    def loadSettings(self):
        """Load window state from self.settings"""

        self.settings.beginGroup('mainwindow')
        geometry = self.settings.value('geometry').toByteArray()
        state = self.settings.value('windowstate').toByteArray()
        dock_string = str(self.settings.value('dockstate').toString())
        if dock_string is not "":
            dock_state = eval(dock_string)
            self.dock_area.restoreState(dock_state)
        self.settings.endGroup()

        self.restoreGeometry(geometry)
        self.restoreState(state)

    def saveSettings(self):
        """Save window state to self.settings."""
        self.settings.beginGroup('mainwindow')
        self.settings.setValue('geometry', self.saveGeometry())
        self.settings.setValue('windowstate', self.saveState())
        dock_state = self.dock_area.saveState()
        # dock_state returned here is a python dictionary. Coundn't find a good
        # way to save dicts in QSettings, hence just using representation
        # of it.
        self.settings.setValue('dockstate', repr(dock_state))
        self.settings.endGroup()

    def closeEvent(self, event):
        self.saveSettings()
        self.shaper.saveSettings()
        self.frame_grabber.close()
        super(MainWindow, self).closeEvent(event)
