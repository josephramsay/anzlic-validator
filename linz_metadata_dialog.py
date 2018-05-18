# -*- coding: utf-8 -*-
"""
/***************************************************************************
 LINZ_MetadataDialog
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
from PyQt4 import QtGui, uic, QtCore
from PyQt4.QtGui import QApplication
from PyQt4.QtCore import QDate

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'linz_metadata_dialog_base.ui'))


class LINZ_MetadataDialog(QtGui.QTabWidget, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(LINZ_MetadataDialog, self).__init__(parent)
        self.setupUi(self)
        self.DEFAULTTEMP = r'templates/linz-anzlic-template.xml'
        self.TEMPLATEPATH = self.DEFAULTTEMP
        self.updateDefaults()


    def closeEvent(self, event):
        self.hide()
        self.reset_form()
        self.updateDefaults()

    def updateDefaults(self):
        sg = QApplication.desktop().screenGeometry()
        x = (sg.width()-self.width()) / 2
        y = (sg.height()-self.height()) / 2
        self.move(x, y)
        self.changeTemplate(self.DEFAULTTEMP)
        self.templateFile.setText(self.TEMPLATEPATH)

        

    def reset_form(self):
        self.layerInfoFields = [self.abs, self.atitle, self.hlName,            \
                                self.purpose, self.title]
        
        self.contactFields = [self.city1, self.city2, self.country1,           \
                              self.country2, self.dadd1, self.dadd2,           \
                              self.email1, self.email2, self.fas1, self.fas2,  \
                              self.iName1, self.iName2, self.oName1,           \
                              self.oName2, self.pName1,self.pName2,            \
                              self.postCode1, self.postCode2, self.role1,      \
                              self.role2, self.voice1, self.voice2]
        
        self.identInfoFields = [self.date, self.lineage, self.maintenance,     \
                                self.spatialrep, self.status,     \
                                self.topicCategory, self.geoDescCombo]
        
        self.securityFields = [self.metSecClass, self.metadataConCopyright,    \
                               self.metadataConLicense, self.resSecClass,      \
                               self.resourceConCopyright,                      \
                               self.resourceConLicense]

        self.summaryFields = [self.validationLog, self.summary, self.metadataTable]
        for field in (self.layerInfoFields + self.contactFields + self.identInfoFields + self.securityFields + self.summaryFields):
            field.clear()
        # Del temp file
        # self.extentFields
        # self.otherFields
        self.createMetadata.setEnabled(False)
        self.setCurrentIndex(0)
        self.date.setEnabled(False)
        self.dONUCheck.setChecked(False)
        self.resolutionText.setEnabled(False)
        self.resolutionUnits.setEnabled(False)
        self.scaleFrame.setEnabled(False)
        self.resolutionUnits.setCurrentIndex(0)
        self.resolutionText.clear()
        self.scale.setChecked(False)
        self.scaleWidget.setScaleString("0")
        self.date.setDate(QDate.currentDate())
        self.resourceCreate.setDate(QDate.currentDate())
        self.resourceCreate.setEnabled(False)
        self.resourcePublish.setDate(QDate.currentDate())
        self.resourcePublish.setEnabled(False)
        self.resourceUpdate.setDate(QDate.currentDate())
        self.resourceUpdate.setEnabled(False)
        self.resourceCreateCheck.setChecked(False)
        self.resourcePublishCheck.setChecked(False)
        self.resourceUpdateCheck.setChecked(False)
        for i in range(self.keywordList.count()):
            item = self.keywordList.item(i)
            self.keywordList.setItemSelected(item, False)
        c = self.count()
        for i in range(1, c):
            self.setTabEnabled(i, False)
        
    def changeTemplate(self, file):
        self.TEMPLATEPATH = file
        
