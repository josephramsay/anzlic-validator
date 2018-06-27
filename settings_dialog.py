# -*- coding: utf-8 -*-
"""
/***************************************************************************
Settings_Dialog
                                 A QGIS plugin
 Plugin to provide a LINZ specific metadata editor and uploader.
                             -------------------
        begin                : 2018-04-27
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Ashleigh Ross
        email                : aross@linz.govt.nz
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
from PyQt4 import QtGui, uic
from PyQt4.QtGui import QApplication
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'settings.ui'))


class SettingsDialog(QtGui.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor.
        :param parent: parent.
        """
        super(SettingsDialog, self).__init__(parent)
        self.setupUi(self)
        sg = QApplication.desktop().screenGeometry()
        x = (sg.width()-self.width()) / 2
        y = (sg.height()-self.height()) / 2
        self.move(x, y)
