from PyQt4 import uic
from pyqtgraph.dockarea import DockArea, Dock

from widgets import Shaper, ImageView, RoiEditor

Ui_MainWindow, QMainWindow = uic.loadUiType("ui/MainWindow.ui")


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
        super(MainWindow, self).closeEvent(event)
