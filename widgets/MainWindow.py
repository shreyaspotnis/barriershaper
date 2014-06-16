from PyQt4 import uic
from pyqtgraph.dockarea import DockArea, Dock

from widgets import Shaper

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

    def createDocks(self):
        self.shaper = Shaper(self.settings, self)

        self.dock_shaper = Dock('Shaper', widget=self.shaper)
        self.dock_area.addDock(self.dock_shaper, position='top')


