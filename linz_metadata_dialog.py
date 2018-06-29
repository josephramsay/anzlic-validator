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
import qgis
import os
from PyQt4 import QtGui, uic
from PyQt4.QtGui import QApplication, QFont
from PyQt4.QtCore import QDate, QTime

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'linz_metadata_dialog_base.ui'))


class LINZ_MetadataDialog(QtGui.QTabWidget, FORM_CLASS):
    def __init__(self, parent=None):
        """
        Constructor
        :param parent: parent.
        """
        super(LINZ_MetadataDialog, self).__init__(parent)
        self.setupUi(self)
        self.DEFAULTTEMP = r'templates/linz-anzlic-template.xml'
        self.TEMPLATEPATH = self.DEFAULTTEMP
        self.updateDefaults()
        self.check = 0
        self.editMetadata.hide()
        self.home, self.layInfo, self.hideF, self.clear = None, None, None, None
        self.contact, self.idenInfo, self.security = None, None, None
        self.summaryF, self.checked, self.enabled = None, None, None
        self.curDate, self.curIndex, self.curTime = None, None, None

    def closeEvent(self, event):
        """
        Hide and Clear Fields, and reset on close.
        :param event: event.
        :return: None.
        """
        self.hide()
        if os.path.isfile('tempXML.xml'):
            os.remove('tempXML.xml')
        clear = (self.outputFile, self.metadataFile, self.templateFile)
        for i in clear:
            i.clear()
        self.reset_form()
        self.updateDefaults()

    def updateDefaults(self):
        """
        Update Default Fields.
        :return: None.
        """
        sg = QApplication.desktop().screenGeometry()
        x = (sg.width()-self.width()) / 2
        y = (sg.height()-self.height()) / 2
        self.move(x, y)
        self.changeTemplate(self.DEFAULTTEMP)
        self.templateFile.setText(self.TEMPLATEPATH)

    def reset_form(self):
        """
        Reset fields in UI to default.
        :return: None
        """
        self.check = 0
        self.home = [self.loadError, self.autoFillError]
        
        self.layInfo = [self.abs, self.atitle, self.hlName, self.purpose,
                        self.title]
        
        self.contact = [self.city1, self.city2, self.country1, self.country2,
                        self.dadd1, self.dadd2, self.email1, self.email2,
                        self.fas1, self.fas2, self.iName1, self.iName2,
                        self.oName1, self.oName2, self.pName1, self.pName2,
                        self.postCode1, self.postCode2, self.role1, self.role2,
                        self.voice1, self.voice2]
        
        self.idenInfo = [self.date, self.lineage, self.maintenance, self.status,
                         self.spatialrep, self.resolutionText, self.westExtent,
                         self.northExtent, self.southExtent, self.eastExtent,
                         self.topicCategory]
        
        self.security = [self.metSecClass, self.metadataConCopyright,
                         self.metadataConLicense, self.resSecClass,
                         self.resourceConCopyright, self.resourceConLicense]

        self.summaryF = [self.validationLog, self.summary, self.metadataTable]

        self.hideF = [self.iNameError1, self.iNameError2, self.oNameError1,
                      self.oNameError2, self.pNameError1, self.pNameError2,
                      self.voiceError1, self.voiceError2, self.fasError1,
                      self.fasError2, self.dadd1Error, self.cityError1,
                      self.cityError2, self.countryError1, self.postCode2Error,
                      self.emailError1, self.emailError2, self.roleError1,
                      self.roleError2, self.hlNameError, self.titleError,
                      self.purposeError, self.resSecClassError, self.dadd2Error,
                      self.metSecClassError, self.resourceConCopyrightError,
                      self.statusError, self.resourceConLicenseError,
                      self.lineageError, self.metadataConCopyrightError,
                      self.atitleError, self.metadataConLicenseError,
                      self.dONUCheckError, self.geogDesListError, self.absError,
                      self.geoBBNorthLabelError, self.temporalCheckError,
                      self.referenceSysError, self.spatialrepError,
                      self.maintenanceError, self.keywordListError,
                      self.topicCategoryError, self.scaleRadioButtonError,
                      self.postCode1Error, self.resolutionRadioButtonError,
                      self.countryError2, self.resourceCreateCheckError,
                      self.fixError, self.publishMetadata, self.bbError]

        self.clear = (self.layInfo + self.contact + self.idenInfo + self.home +
                      self.security + self.summaryF)

        self.checked = [self.scale, self.endTimeCheck, self.resourceCreateCheck,
                        self.resourcePublishCheck, self.resourceUpdateCheck,
                        self.temporalCheck, self.endDateCheck, self.dONUCheck,
                        self.startTimeCheck]
        
        self.enabled = [self.createMetadata, self.date, self.resolutionText,
                        self.rUnits, self.scaleFrame, self.resourceCreate,
                        self.resourcePublish, self.resourceUpdate, self.endTime,
                        self.startDate, self.startTime, self.endDateCheck,
                        self.startTimeCheck, self.endDate, self.endTimeCheck]
        
        self.curDate = [self.date, self.resourceCreate, self.resourcePublish,
                        self.resourceUpdate, self.startDate, self.endDate]
        
        self.curTime = [self.startTime, self.endTime]
        
        self.curIndex = [self, self.rUnits]
        for field in self.hideF:
            field.hide()

        for field in self.clear:
            field.clear()

        for field in self.curIndex:
            field.setCurrentIndex(0)

        for field in self.enabled:
            field.setEnabled(False)

        for field in self.checked:
            field.setChecked(False)

        for field in self.curDate:
            field.setDate(QDate.currentDate())

        for field in self.curTime:
            field.setTime(QTime.currentTime())

        self.scaleWidget.setScaleString("0")
        
        for i in range(self.keywordList.count()):
            item = self.keywordList.item(i)
            item.setSelected(False)

        for i in range(self.geogDesList.count()):
            item = self.geogDesList.item(i)
            item.setSelected(False)

        for i in range(1, self.count()):
            self.setTabEnabled(i, False)
        
    def changeTemplate(self, tempfile):
        """
        Update template path with tempfile given.
        :param tempfile: tempfile to be changed.
        :return: None.
        """
        self.TEMPLATEPATH = tempfile
