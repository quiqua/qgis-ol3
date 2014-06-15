# -*- coding: utf-8 -*-

# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
# Initialize Qt resources from file resources.py
import resources_rc
# Import the code for the dialog
from maindialog import MainDialog


class OL3Plugin:

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface

    def initGui(self):
        self.action = QAction(
            QIcon(":/plugins/qgis2ol/icons/ol.png"),
            u"Create OpenLayers map", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        
        self.iface.addPluginToMenu(u"&Export to Open Layers", self.action)

    def unload(self):
        self.iface.removePluginMenu(u"&Export to Open Layers", self.action)
    
    def run(self):
        dlg = MainDialog()
        dlg.exec_()        
