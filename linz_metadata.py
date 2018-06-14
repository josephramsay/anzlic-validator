# -*- coding: utf-8 -*-
"""
/***************************************************************************
 LINZ_Metadata
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

# Import the code for the dialog
import qgis
import yaml
import re
import os
import uuid
import koordinates
import sys
import traceback
import scripts.resources
import urllib2 as UR
from qgis.core import QgsCoordinateReferenceSystem as QCRS
from PyQt4.QtCore import QSettings, QCoreApplication, QDate, QTime, Qt, \
    QTranslator, qVersion, QObject
from PyQt4.QtGui import QIcon, QAction, QFileDialog, QItemSelectionModel, \
    QTextCursor, QFont, QTableWidgetItem as QTWI, QComboBox, QPalette, QColor, \
    QLabel, QWhatsThis
from linz_metadata_dialog import LINZ_MetadataDialog
from scripts.codeList import codeList as CL
from lxml.etree import parse as PS, SubElement as SE, QName as QN, \
    Element as EL, tostring as TS, ElementTree as ELT, XMLSyntaxError
from shutil import copyfile
from scripts.validate import Combined, ValidatorException, KEY
from scripts.errorChecker import runChecks, InvalidConfigException
from collections import OrderedDict as OD
from publish_metadata_dialog import Publish_MetadataDialog
from scripts.lds_metadata_updater.metadata_updater.metadata_updater import \
    set_metadata

# Set Namespaces
NSX = {'xlink': 'http://www.w3.org/1999/xlink',
       'gco': 'http://www.isotc211.org/2005/gco',
       'gmd': 'http://www.isotc211.org/2005/gmd',
       'gts': 'http://www.isotc211.org/2005/gts',
       'gml': 'http://www.opengis.net/gml'}

# Set Metadata Tags
MD = '/gmd:MD_Metadata'
CONTACT = MD + '/gmd:contact/gmd:CI_ResponsibleParty'
CINFO = CONTACT + '/gmd:contactInfo/gmd:CI_Contact'
PHONE = CINFO + '/gmd:phone/gmd:CI_Telephone'
ADDRESS = CINFO + '/gmd:address/gmd:CI_Address'
ID = MD + '/gmd:identificationInfo/gmd:MD_DataIdentification'
CITATION = ID + '/gmd:citation/gmd:CI_Citation'
POC = ID + '/gmd:pointOfContact/gmd:CI_ResponsibleParty'
POCINFO = POC + '/gmd:contactInfo/gmd:CI_Contact'
POCPHONE = POCINFO + '/gmd:phone/gmd:CI_Telephone'
POCADDRESS = POCINFO + '/gmd:address/gmd:CI_Address'
SECURITYCODE = '/gmd:MD_SecurityConstraints/gmd:classification/gmd:MD_' + \
               'ClassificationCode'
USELIMIT = '/gmd:MD_LegalConstraints/gmd:useLimitation/gco:CharacterString'
USECONST = '/gmd:MD_LegalConstraints/gmd:useConstraints/gmd:MD_RestrictionCode'
DQ = MD + '/gmd:dataQualityInfo/gmd:DQ_DataQuality'
SC = DQ + '/gmd:scope/gmd:DQ_Scope'
EXTENT = ID + '/gmd:extent/gmd:EX_Extent'
EXTENTBB = EXTENT + '/gmd:geographicElement/gmd:EX_GeographicBoundingBox'
RMAINT = '/gmd:resourceMaintenance/gmd:MD_MaintenanceInformation'

CS = '/gco:CharacterString'
MDCSC = '/gmd:MD_CharacterSetCode'
MDSC = '/gmd:MD_ScopeCode'
CIRC = '/gmd:CI_RoleCode'
DT = '/gco:Date'
CIDTC = '/gmd:CI_DateTypeCode'
MDPC = '/gmd:MD_ProgressCode'
MDMFC = '/gmd:MD_MaintenanceFrequencyCode'
MDKTC = '/gmd:MD_KeywordTypeCode'
DE = '/gco:Decimal'

FID = MD + '/gmd:fileIdentifier' + CS
LAN = MD + '/gmd:language' + CS
CHSET = MD + '/gmd:characterSet' + MDCSC
HLEVEL = MD + '/gmd:hierarchyLevel' + MDSC
HLEVELNAME = MD + '/gmd:hierarchyLevelName' + CS

INAME = CONTACT + '/gmd:individualName' + CS
ONAME = CONTACT + '/gmd:organisationName' + CS
PNAME = CONTACT + '/gmd:positionName' + CS
VOICE = PHONE + '/gmd:voice' + CS
FACS = PHONE + '/gmd:facsimile' + CS
DELIVERYPOINT = ADDRESS + '/gmd:deliveryPoint' + CS
CITY = ADDRESS + '/gmd:city' + CS
POSTALCODE = ADDRESS + '/gmd:postalCode' + CS
COUNTRY = ADDRESS + '/gmd:country' + CS
EMAIL = ADDRESS + '/gmd:electronicMailAddress' + CS
ROLE = CONTACT + '/gmd:role' + CIRC

DSTAMP = MD + '/gmd:dateStamp' + DT
MSN = MD + '/gmd:metadataStandardName' + CS
MSV = MD + '/gmd:metadataStandardVersion' + CS
RS = MD + '/gmd:referenceSystemInfo/gmd:MD_ReferenceSystem/gmd:reference' + \
     'SystemIdentifier/gmd:RS_Identifier/gmd:code' + CS

TITLE = CITATION + '/gmd:title' + CS
ALTTITLE = CITATION + '/gmd:alternateTitle' + CS
CITDATE = CITATION + '/gmd:date/gmd:CI_Date/gmd:date' + DT
CITDATETYPE = CITATION + '/gmd:date/gmd:CI_Date/gmd:dateType' + CIDTC
ABSTRACT = ID + '/gmd:abstract' + CS
PURPOSE = ID + '/gmd:purpose' + CS
STATUS = ID + '/gmd:status' + MDPC

POCINAME = POC + '/gmd:individualName' + CS
POCONAME = POC + '/gmd:organisationName' + CS
POCPNAME = POC + '/gmd:positionName' + CS
POCVOICE = POCPHONE + '/gmd:voice' + CS
POCFACS = POCPHONE + '/gmd:facsimile' + CS
POCDELIVERYPOINT = POCADDRESS + '/gmd:deliveryPoint' + CS
POCCITY = POCADDRESS + '/gmd:city' + CS
POCPOSTALCODE = POCADDRESS + '/gmd:postalCode' + CS
POCCOUNTRY = POCADDRESS + '/gmd:country' + CS
POCEMAIL = POCADDRESS + '/gmd:electronicMailAddress' + CS
POCROLE = POC + '/gmd:role' + CIRC

RMAINTCODE = ID + RMAINT + '/gmd:maintenanceAndUpdateFrequency' + MDMFC
RMAINTDATE = ID + RMAINT + '/gmd:dateOfNextUpdate' + DT
RFORMATN = ID + '/gmd:resourceFormat/gmd:MD_Format/gmd:name' + CS
RFORMATV = ID + '/gmd:resourceFormat/gmd:MD_Format/gmd:version' + CS

KEYWORDS = ID + '/gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:keyword' + CS
KEYWORDSTYPE = ID + '/gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:type' + MDKTC
CLASSIFCODE = ID + '/gmd:resourceConstraints' + SECURITYCODE
RESOURCELIMIT = ID + '/gmd:resourceConstraints' + USELIMIT
RESOURCEUSE = ID + '/gmd:resourceConstraints' + USECONST

SPATIALREP = ID + '/gmd:spatialRepresentationType/gmd:MD_Spatial' + \
             'RepresentationTypeCode'
SCALE = ID + '/gmd:spatialResolution/gmd:MD_Resolution/gmd:equivalentScale' + \
        '/gmd:MD_RepresentativeFraction/gmd:denominator/gco:Integer'

RESOLUTION = ID + '/gmd:spatialResolution/gmd:MD_Resolution/gmd:distance/' + \
             'gco:Distance'

IDENTLAN = ID + '/gmd:language' + CS
IDENTCS = ID + '/gmd:characterSet' + MDCSC

TOPIC = ID + '/gmd:topicCategory/gmd:MD_TopicCategoryCode'

EXTENTDES = EXTENT + '/gmd:geographicElement/gmd:EX_GeographicDescription/' + \
            'gmd:geographicIdentifier/gmd:MD_Identifier/gmd:code' + CS

EXTENTBBW = EXTENTBB + '/gmd:westBoundLongitude' + DE
EXTENTBBE = EXTENTBB + '/gmd:eastBoundLongitude' + DE
EXTENTBBN = EXTENTBB + '/gmd:northBoundLatitude' + DE
EXTENTBBS = EXTENTBB + '/gmd:southBoundLatitude' + DE

TSINGLE = EXTENT + '/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/' + \
          'gml:TimeInstant/gml:timePosition'
TBEGIN = EXTENT + '/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/' + \
         'gml:TimePeriod/gml:beginPosition'
TEND = EXTENT + '/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml:' + \
       'TimePeriod/gml:endPosition'

LINKAGE = MD + '/gmd:distributionInfo/gmd:MD_Distribution/gmd:transfer' + \
          'Options/gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_Online' + \
          'Resource/gmd:linkage/gmd:URL'

SCOPE = SC + '/gmd:level' + MDSC
SCOPEDESC = SC + '/gmd:levelDescription/gmd:MD_ScopeDescription/gmd:other' + CS
LINEAGE = DQ + '/gmd:lineage/gmd:LI_Lineage/gmd:statement' + CS

MCLASSIFCODE = MD + '/gmd:metadataConstraints' + SECURITYCODE
METALIMIT = MD + '/gmd:metadataConstraints' + USELIMIT
METAUSE = MD + '/gmd:metadataConstraints' + USECONST

# FIELDS, all metadata fields in order.
FIELDS = (FID, LAN, CHSET, HLEVEL, HLEVELNAME, INAME, ONAME, PNAME, VOICE, FACS,
          DELIVERYPOINT, CITY, POSTALCODE, COUNTRY, EMAIL, ROLE, DSTAMP, MSN,
          MSV, RS, TITLE, ALTTITLE, CITDATE, CITDATETYPE, ABSTRACT, PURPOSE,
          STATUS, POCINAME, POCONAME, POCPNAME, POCVOICE, POCFACS,
          POCDELIVERYPOINT, POCCITY, POCPOSTALCODE, POCCOUNTRY, POCEMAIL,
          POCROLE, RMAINTCODE, RMAINTDATE, RFORMATN, RFORMATV, KEYWORDS,
          KEYWORDSTYPE, CLASSIFCODE, RESOURCELIMIT, RESOURCEUSE, SPATIALREP,
          SCALE, RESOLUTION, IDENTLAN, IDENTCS, TOPIC, EXTENTDES, EXTENTBBW,
          EXTENTBBE, EXTENTBBS, EXTENTBBN, TSINGLE, TBEGIN, TEND, LINKAGE,
          SCOPE, SCOPEDESC, LINEAGE, MCLASSIFCODE, METALIMIT, METAUSE)

TEMPFILE = 'tempXML.xml'

DEFAULTTEXT = {CHSET: 'utf8',
               LAN: 'eng',
               MSN: 'ANZLIC Metadata Profile: An Australian/New Zealand ' +
                    'Profile of AS/NZS ISO 19115:2005, Geographic Information' +
                    '- Metadata',
               MSV: '1.1',
               RFORMATN: '*.xml',
               RFORMATV: 'Unknown',
               IDENTLAN: 'eng',
               IDENTCS: 'utf8'}


class LINZ_Metadata:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.
        :param iface: An interface instance that will be passed to this class
            which provides the hook to manipulate the QGIS application at run
            time.
        :type iface: QgisInterface
        """
        self.dlg = LINZ_MetadataDialog()
        self.publishDialog = Publish_MetadataDialog(self.dlg)
        noneVar = ('tF', 'cF', 'cFS', 'palette', 'rcode', 'widget', 'use',
                   'client', 'lidpub', 'layer', 'resCC', 'configfile', 'title',
                   'rcopyright', 'metaCL', 'resCL', 'metaCC', 'lid', 'rlicense',
                   'mcopyright', 'mlicense')
        for var in noneVar:
            setattr(self, var, None)
        self.MDTEXT, self.iface, self.actions = {}, iface, []
        self.plugin_dir = os.path.dirname(__file__)
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(self.plugin_dir, 'i18n',
                                   'LINZ_Metadata_{}.qm'.format(locale))
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)
        self.menu = self.tr(u'&LINZ Metadata')
        self.toolbar = self.iface.addToolBar(u'LINZ_Metadata')
        self.toolbar.setObjectName(u'LINZ_Metadata')

    def tr(self, message):
        """Get the translation for a string using Qt translation API.
        :param message: String for translation.
        :type message: str, QString
        :returns: Translated version of message.
        :rtype: QString
        """
        return QCoreApplication.translate('LINZ_Metadata', message)

    def add_action(self, icon_path, text, callback, enabled_flag=True,
                   add_to_menu=True, add_to_toolbar=True, status_tip=None,
                   whats_this=None, parent=None):
        """Add a toolbar icon to the toolbar.
        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str
        :param text: Text that should be shown in menu items for this action.
        :type text: str
        :param callback: Function to be called when the action is triggered.
        :type callback: function
        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool
        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool
        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool
        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str
        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget
        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.
        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """
        self.dlg.changeTemplate(r'templates/linz-anzlic-template.xml')
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        if status_tip is not None:
            action.setStatusTip(status_tip)
        if whats_this is not None:
            action.setWhatsThis(whats_this)
        if add_to_toolbar:
            self.toolbar.addAction(action)
        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)
        self.actions.append(action)
        return action

    def initGui(self):
        """
        Create the menu entries and toolbar icons inside the QGIS GUI.
        :return: None.
        """
        icon_path = ':/plugins/LINZ_Metadata/icon.png'
        self.add_action(icon_path, text=self.tr(u''), callback=self.run,
                        parent=self.iface.mainWindow())
        c = self.dlg.count()
        for i in range(1, c):
            self.dlg.setTabEnabled(i, False)
        self.dlg.templateFile.setText(self.dlg.TEMPLATEPATH)
        self.dlg.OUTPUTFILE = TEMPFILE
        self.dlg.loadError.hide()
        # Set Text Fields
        self.tF = {TITLE: self.dlg.title,
                   ALTTITLE: self.dlg.atitle,
                   ABSTRACT: self.dlg.abs,
                   PURPOSE: self.dlg.purpose,
                   LINEAGE: self.dlg.lineage}

        # Set Combo Fields
        self.cF = {ROLE: [self.dlg.role2, CL('CI_RoleCode')],
                   POCROLE: [self.dlg.role1, CL('CI_RoleCode')],
                   HLEVEL: [self.dlg.hlName, CL('MD_ScopeCode')],
                   STATUS: [self.dlg.status, CL('MD_ProgressCode')],
                   RMAINTCODE: [self.dlg.maintenance,
                                CL('MD_MaintenanceFrequencyCode')],
                   SPATIALREP: [self.dlg.spatialrep,
                                CL('MD_SpatialRepresentationTypeCode')],
                   CLASSIFCODE: [self.dlg.resSecClass,
                                 CL('MD_ClassificationCode')],
                   MCLASSIFCODE: [self.dlg.metSecClass,
                                  CL('MD_ClassificationCode')]}

        self.cFS = {VOICE: self.dlg.voice2,
                    ONAME: self.dlg.oName2,
                    INAME: self.dlg.iName2,
                    POCVOICE: self.dlg.voice1,
                    POCONAME: self.dlg.oName1,
                    POCINAME: self.dlg.iName1,
                    POCDELIVERYPOINT: self.dlg.dadd1,
                    DELIVERYPOINT: self.dlg.dadd2,
                    POCCITY: self.dlg.city1,
                    CITY: self.dlg.city2,
                    POCEMAIL: self.dlg.email1,
                    EMAIL: self.dlg.email2,
                    POCPOSTALCODE: self.dlg.postCode1,
                    POSTALCODE: self.dlg.postCode2,
                    POCCOUNTRY: self.dlg.country1,
                    COUNTRY: self.dlg.country2,
                    FACS: self.dlg.fas2,
                    POCFACS: self.dlg.fas1,
                    POCPNAME: self.dlg.pName1,
                    PNAME: self.dlg.pName2}

        # Set Resolution Code -> Units
        self.rcode = {'m': 'metre',
                      'km': 'kilometre',
                      'deg': 'degree',
                      'ft': 'foot',
                      'fath': 'fathom',
                      'mile': 'mile',
                      'nm': 'nautical mile',
                      'yd': 'yard',
                      'rad': 'radian',
                      'u': 'unknown'}

        self.MDTEXT = {}
        # Select Template Clicked
        self.dlg.selectTemplate.clicked.connect(lambda: self.setFile(1))
        self.dlg.selectOutputFile.clicked.connect(lambda: self.setFile(2))
        self.dlg.selectMetadata.clicked.connect(lambda: self.setFile(3))
        # Default Template Clicked
        self.dlg.defaultButton.clicked.connect(self.updateFileText)
        # Load Metadata Clicked
        self.dlg.loadTemplate.clicked.connect(lambda: self.loadMetadata(1))
        self.dlg.loadMetadata.clicked.connect(lambda: self.loadMetadata(2))

        # State Changed Of Date of Next Update Check Box
        self.dlg.dONUCheck.stateChanged.connect(self.toggleDate)
        self.dlg.scale.stateChanged.connect(self.toggleState)
        self.dlg.scaleRadioButton.toggled.connect(self.toggleRadio)

        self.dlg.temporalCheck.stateChanged.connect(self.temporal)
        self.dlg.startTimeCheck.stateChanged.connect(self.startTime)
        self.dlg.endDateCheck.stateChanged.connect(self.endDate)
        self.dlg.endTimeCheck.stateChanged.connect(self.endTime)

        self.dlg.resourceCreateCheck.stateChanged.connect(self.createDate)
        self.dlg.resourcePublishCheck.stateChanged.connect(self.publishDate)
        self.dlg.resourceUpdateCheck.stateChanged.connect(self.updateDate)

        # Create Metadata Clicked
        self.dlg.createMetadata.clicked.connect(self.createMeta)
        # Validate/ Error Check Clicked 
        self.dlg.validateErrorCheck.clicked.connect(self.check)

        self.dlg.autofillResource.clicked.connect(lambda: self.autoFill(1))
        self.dlg.autofillMetadata.clicked.connect(lambda: self.autoFill(2))

        self.dlg.boldText.clicked.connect(lambda: self.textStyle(1))
        self.dlg.italicText.clicked.connect(lambda: self.textStyle(2))
        self.dlg.linkText.clicked.connect(lambda: self.textStyle(3))

        self.dlg.fixError.clicked.connect(self.fixError)

        self.dlg.loadExtent.clicked.connect(self.loadExtent)

        self.dlg.publishMetadata.clicked.connect(self.publishMeta)

        self.publishDialog.layerButton.clicked.connect(self.updatePublishDlg)
        self.publishDialog.publishBox.accepted.connect(self.publish)

        self.dlg.fillLegal.clicked.connect(self.autoFillLegal)
        self.dlg.undoFill.clicked.connect(self.autoFillLegalUndo)

        self.dlg.loadMetadataID.clicked.connect(self.selectLayer)

        self.dlg.iName2.editTextChanged.connect(lambda: self.test(self.dlg.iName2))
        self.dlg.iName1.editTextChanged.connect(lambda: self.test(self.dlg.iName1))
        self.dlg.oName2.editTextChanged.connect(lambda: self.test(self.dlg.oName2))
        self.dlg.oName1.editTextChanged.connect(lambda: self.test(self.dlg.oName1))
        self.dlg.pName2.editTextChanged.connect(lambda: self.test(self.dlg.pName2))
        self.dlg.pName1.editTextChanged.connect(lambda: self.test(self.dlg.pName1))
        self.dlg.dadd2.editTextChanged.connect(lambda: self.test(self.dlg.dadd2))
        self.dlg.dadd1.editTextChanged.connect(lambda: self.test(self.dlg.dadd1))
        self.dlg.city2.editTextChanged.connect(lambda: self.test(self.dlg.city2))
        self.dlg.city1.editTextChanged.connect(lambda: self.test(self.dlg.city1))
        self.dlg.postCode2.editTextChanged.connect(lambda: self.test(self.dlg.postCode2))
        self.dlg.postCode1.editTextChanged.connect(lambda: self.test(self.dlg.postCode1))
        self.dlg.email2.editTextChanged.connect(lambda: self.test(self.dlg.email2))
        self.dlg.email1.editTextChanged.connect(lambda: self.test(self.dlg.email1))
        self.dlg.voice2.editTextChanged.connect(lambda: self.test(self.dlg.voice2))
        self.dlg.voice1.editTextChanged.connect(lambda: self.test(self.dlg.voice1))
        self.dlg.fas2.editTextChanged.connect(lambda: self.test(self.dlg.fas2))
        self.dlg.fas1.editTextChanged.connect(lambda: self.test(self.dlg.fas1))
        self.dlg.role2.editTextChanged.connect(lambda: self.test(self.dlg.role2))
        self.dlg.role1.editTextChanged.connect(lambda: self.test(self.dlg.role1))
        self.dlg.referenceSys.crsChanged.connect(lambda: self.test2(self.dlg.referenceSys))



    def test(self, sender):
        font = QFont('Noto Sans', 11)
        sender.setFont(font)
        if sender.isEditable:
            sender.lineEdit().setFont(font)

    def test2(self, sender):
        font = QFont('Noto Sans', 11)
        sender.setFont(font)

    def selectLayer(self):
        self.dlg.loadError.hide()
        if self.dlg.loadLayerID.text() != '':
            self.lid = self.dlg.loadLayerID.text()
            md_name = 'https://data.linz.govt.nz/layer/{lid}/metadata/iso/xml/'
            try:
                md_handle = UR.urlopen(md_name.format(lid=self.lid))
                if not os.path.exists(
                        '{}/downloads'.format(os.path.dirname(__file__))):
                    os.makedirs(
                        '{}/downloads'.format(os.path.dirname(__file__)))
                filename = '{}/downloads/{}'.format(
                    os.path.dirname(__file__),
                    md_handle.info()['content-disposition'].split(
                        "filename*=UTF-8''")[1])
                with open(filename, 'wb') as file:
                    file.write(md_handle.read())
                self.dlg.OUTPUTFILE = filename
                self.dlg.changeTemplate(filename)
                self.dlg.metadataFile.setText(self.dlg.OUTPUTFILE)
                self.loadMetadata(2)
            except XMLSyntaxError as xse:
                # Private layers are inaccessible
                if 'https://id.koordinates.com/login' in md_handle.url:
                    self.dlg.loadError.setText(
                        'Private layer {}.\n{}'.format(self.lid, xse))
                else:
                    self.dlg.loadError.setText(
                        'Metadata parse error {}.\n{}'.format(self.lid, xse))
                self.dlg.loadError.show()
            except UR.HTTPError as he:
                self.dlg.loadError.setText(
                    'Metadata unavailable {}.\n{}'.format(self.lid, he))
                self.dlg.loadError.show()
            except Exception as e:
                # catch any other error and continue, may not be what is wanted
                self.dlg.loadError.setText(
                    'Processing error {}.\n{}'.format(self.lid, e))
                self.dlg.loadError.show()
        else:
            self.dlg.loadError.setText('Input Layer ID')
            self.dlg.loadError.show()

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(u'&LINZ Metadata'), action)
            self.iface.removeToolBarIcon(action)
        del self.toolbar

    def loadMetadata(self, button):
        """
        Load Selectable Combo/List Items from Codelists.
        Load Selectable Contact Items from Config (if given)
        Load metadata template or existing metadata file into associated fields.
        :param button: which button clicked to load the metadata.
        (1 - Load Template Metadata), (2 - Load Existing Metadata)
        :return: None.
        """
        try:
            lice, copy, metlice, metcopy, = None, None, None, None
            meta, res = None, None
            crsList = {'NZGD2000/New Zealand Transverse Mercator 2000': 2193,
                       'WGS 84': 4326}
            topicCategoryValues = CL('MD_TopicCategoryCode')
            self.MDTEXT = {}
            if button == 1:
                if self.dlg.templateFile.text() == '' or \
                        self.dlg.outputFile.text() == '':
                    raise Exception("Metadata Load Error, No File Selected")
                self.dlg.changeTemplate(self.dlg.templateFile.text())
                self.dlg.OUTPUTFILE = self.dlg.outputFile.text()
            elif button == 2:
                if self.dlg.metadataFile.text() == '':
                    raise Exception("Metadata Load Error, No File Selected")
                self.dlg.changeTemplate(self.dlg.metadataFile.text())
                self.dlg.OUTPUTFILE = self.dlg.metadataFile.text()
            try:
                md = PS(os.path.abspath(os.path.join(
                    os.path.dirname(__file__), self.dlg.TEMPLATEPATH)))
            except Exception as e:
                raise Exception("Metadata Load Error: {}".format(str(e)))
            self.configfile = r'{}/{}'.format(os.path.abspath(os.path.join(
                __file__, '../config')), self.dlg.configSelector.currentText())
            if not os.path.exists(self.configfile):
                raise Exception("Cannot Find Config File {}".format(
                    self.configfile))
            with open(self.configfile, 'r') as f:
                config = yaml.load(f)
            if 'Metadata' not in md.getroot().tag:
                raise Exception('Metadata Load Error, not ISO Metadata')

            self.dlg.reset_form()
            self.dlg.referenceSys.setCrs(QCRS())
            # Read through metadata file and set path, text in MDTEXT
            for m in md.iter():
                if m.text:
                    key = re.sub('\[+.+?\]', '', md.getpath(m))
                    if key in self.MDTEXT:
                        if type(self.MDTEXT[key]) == tuple:
                            self.MDTEXT[key] = self.MDTEXT[key] + (m.text,)
                        else:
                            self.MDTEXT[key] = (self.MDTEXT[key], m.text)
                    else:
                        self.MDTEXT[key] = m.text

            # Add Topic Category Selection Values to UI List.
            for val in topicCategoryValues:
                self.dlg.topicCategory.addItem(val.strip())
            self.dlg.topicCategory.sortItems()

            configDict = {VOICE: 'VOICE1',
                          POCVOICE: 'VOICE2',
                          ONAME: 'ORGANISATIONNAME1',
                          POCONAME: 'ORGANISATIONNAME2',
                          INAME: 'INDIVIDUALNAME1',
                          POCINAME: 'INDIVIDUALNAME2',
                          DELIVERYPOINT: 'DELIVERYADDRESS1',
                          POCDELIVERYPOINT: 'DELIVERYADDRESS2',
                          CITY: 'CITY1',
                          POCCITY: 'CITY2',
                          POSTALCODE: 'POSTALCODE1',
                          POCPOSTALCODE: 'POSTALCODE2',
                          COUNTRY: 'COUNTRY1',
                          POCCOUNTRY: 'COUNTRY2',
                          EMAIL: 'EMAIL1',
                          POCEMAIL: 'EMAIL2',
                          FACS: 'FACSIMILE1',
                          POCFACS: 'FACSIMILE2',
                          PNAME: 'POSITIONNAME1',
                          POCPNAME: 'POSITIONNAME2',
                          HLEVEL: 'HIERARCHYLEVEL',
                          CLASSIFCODE: 'SECURITYCLASSRES',
                          MCLASSIFCODE: 'SECURITYCLASSMET',
                          STATUS: 'STATUS',
                          RMAINTCODE: 'MAINTENANCE',
                          SPATIALREP: 'SPATIALREPRESENTATION',
                          ROLE: 'ROLE1',
                          POCROLE: 'ROLE2'}

            constraints = ('RCOPYRIGHT', 'RLICENSE', 'MCOPYRIGHT', 'MLICENSE')
            font = QFont('Noto Sans', 11)
            for vals in constraints:
                text = ''
                if vals in config:
                    text = config[vals]
                if vals == 'RCOPYRIGHT':
                    self.rcopyright = text
                elif vals == 'RLICENSE':
                    self.rlicense = text
                elif vals == 'MCOPYRIGHT':
                    self.mcopyright = text
                else:
                    self.mlicense = text

            trueFalseVals = ()
            for i in FIELDS:
                if i in self.cFS:
                    if i in configDict:
                        self.cFS[i].addItem('')
                        if configDict[i] in config and \
                                type(config[configDict[i]]) == list:
                            self.cFS[i].addItems(config[configDict[i]])
                            for v in range(self.cFS[i].count()):
                                if self.cFS[i].itemText(v) == 'NONE' or \
                                        self.cFS[i].itemText(v) == 'EMPTY':
                                    self.cFS[i].removeItem(v)
                        elif configDict[i] in config and \
                                type(config[configDict[i]]) == str:
                            self.cFS[i].addItem(config[configDict[i]])
                        else:
                            trueFalseVals += (i,)

                if i in self.cF:
                    self.cF[i][0].addItem('')
                    items = self.cF[i][1]
                    if i in configDict and configDict[i] in config:
                        if type(config[configDict[i]]) == list:
                            values = ()
                            for v in config[configDict[i]]:
                                values += (v,)
                        elif type(config[configDict[i]]) == str and \
                                config[configDict[i]] in items:
                                    values = (config[configDict[i]],)
                        else:
                            values = self.cF[i][1]
                    else:
                        values = self.cF[i][1]
                    self.cF[i][0].addItems(values)

            # Update UI Fields based on fields found in Metadata
            for i in FIELDS:
                if i in self.MDTEXT:

                    # Load Scale
                    if i == SCALE:
                        self.dlg.scale.setChecked(True)
                        self.dlg.scaleRadioButton.setChecked(True)
                        if ':' in self.MDTEXT[i]:
                            self.MDTEXT[i] = self.MDTEXT[i].split(':')[1]
                        self.dlg.scaleWidget.setScaleString("1:" +
                                                            self.MDTEXT[i])

                    # Load Temporal (Single or Range)
                    elif i == TSINGLE or i == TBEGIN or i == TEND:
                        self.dlg.temporalCheck.setChecked(True)
                        date, time = self.MDTEXT[i], None
                        y, M, d = None, None, None
                        h, m, s = None, None, None
                        if self.MDTEXT[i].find('T') != -1:
                            date = self.MDTEXT[i].split('T')[0]
                            time = self.MDTEXT[i].split('T')[1]

                        date = date.split('-')
                        if len(date) == 1:
                            y = date[0]
                        elif len(date) == 2:
                            y, M = date[0], date[1]
                        else:
                            y, M, d = date[0], date[1], date[2]
                        if time is not None:
                            time = time.split(':')
                            if len(time) == 1:
                                h = time[0]
                            elif len(time) == 2:
                                h, m = time[0], time[1]
                            else:
                                h, m, s = time[0], time[1], time[2]
                        if M is None:
                            M = 1
                        if d is None:
                            d = 1
                        date = QDate(int(y), int(M), int(d))

                        if i == TSINGLE or i == TBEGIN:
                            self.dlg.startDate.setDate(date)
                        else:
                            self.dlg.endDateCheck.setChecked(True)
                            self.dlg.endDate.setDate(date)
                        if time is not None:
                            if m is None:
                                m = 1
                            if s is None:
                                s = 0
                            time = QTime(int(h), int(m), int(s))
                            if i == TSINGLE or i == TBEGIN:
                                self.dlg.startTimeCheck.setChecked(True)
                                self.dlg.startTime.setTime(time)
                            if i == TEND:
                                self.dlg.endTimeCheck.setChecked(True)
                                self.dlg.endTime.setTime(time)

                    # Load Keywords
                    elif i == KEYWORDS:
                        if type(self.MDTEXT[i]) != tuple:
                            valList = [self.MDTEXT[i]]
                        else:
                            valList = self.MDTEXT[i]
                        for val in valList:
                            val = val.replace('-', ' ')
                            if 'non specific' in val:
                                val = val.replace('non specific',
                                                  'non-specific')
                            if val[1].isupper():
                                found = self.dlg.keywordList.findItems(
                                    val, Qt.MatchExactly)
                                if len(found) > 0:
                                    self.dlg.keywordList.setCurrentRow(
                                        self.dlg.keywordList.row(found[0]),
                                        QItemSelectionModel.Select)
                                else:
                                    print("WARNING: Invalid Keyword Ignored "
                                          + val)

                    # Load Resolution
                    elif i == RESOLUTION:
                        ms = md.find(RESOLUTION[16:],
                                     namespaces=NSX).attrib['uom']
                        self.dlg.scale.setChecked(True)
                        self.dlg.scaleRadioButton.setChecked(False)
                        self.dlg.resolutionRadioButton.setChecked(True)
                        self.dlg.resolutionText.setText(self.MDTEXT[i])
                        self.dlg.rUnits.setCurrentIndex(
                            self.dlg.rUnits.findText(self.rcode[ms]))

                    # Load Citation Date
                    elif i == CITDATE:
                        dates = {'creation': (self.dlg.resourceCreate,
                                              self.dlg.resourceCreateCheck),
                                 'publication': (self.dlg.resourcePublish,
                                                 self.dlg.resourcePublishCheck),
                                 'revision': (self.dlg.resourceUpdate,
                                              self.dlg.resourceUpdateCheck)}
                        if type(self.MDTEXT[i]) == tuple:
                            valList = self.MDTEXT[i]
                        else:
                            valList = [self.MDTEXT[i]]
                        for num, el in enumerate(valList):
                            dt = el.split('-')
                            if len(dt) == 1:
                                dt = (dt[0], 1, 1)
                            elif len(dt) == 2:
                                dt = (dt[0], dt[1], 1)
                            if type(self.MDTEXT[i]) == tuple:
                                dates[self.MDTEXT[
                                    CITDATETYPE][num]][0].setEnabled(True)
                                dates[self.MDTEXT[CITDATETYPE][num]][0].setDate(
                                    QDate(int(dt[0]), int(dt[1]), int(dt[2])))
                                dates[self.MDTEXT[
                                    CITDATETYPE][num]][1].setChecked(True)
                            else:
                                dates[self.MDTEXT[
                                    CITDATETYPE]][0].setEnabled(True)
                                dates[self.MDTEXT[CITDATETYPE]][0].setDate(
                                    QDate(int(dt[0]), int(dt[1]), int(dt[2])))
                                dates[self.MDTEXT[
                                    CITDATETYPE]][1].setChecked(True)

                    # Load Reference System
                    elif i == RS:
                        if self.MDTEXT[i].isdigit():
                            crs = QCRS(int(self.MDTEXT[i]))
                            self.dlg.referenceSys.setCrs(crs)
                        elif 'urn:ogc:def:crs:EPSG::' in self.MDTEXT[i]:
                            crs = QCRS(int(self.MDTEXT[i].split(
                                'urn:ogc:def:crs:EPSG::')[1]))
                            self.dlg.referenceSys.setCrs(crs)
                        elif 'EPSG::' in self.MDTEXT[i]:
                            crs = QCRS(int(self.MDTEXT[i].split('EPSG::')[1]))
                            self.dlg.referenceSys.setCrs(crs)
                        else:
                            if self.MDTEXT[i] in crsList:
                                crs = QCRS(crsList[self.MDTEXT[i]])
                                self.dlg.referenceSys.setCrs(crs)
                            else:
                                print("WARNING unknown CRS " + self.MDTEXT[i])

                    # Load Resource Maintenance Date
                    elif i in RMAINTDATE:
                        if self.MDTEXT[i] != '':
                            dt, val, d = ['year', 'month', 'day'], 0, ()
                            while val < len(self.MDTEXT[i].split('-')):
                                dt[val] = (dt[val],
                                           self.MDTEXT[i].split('-')[val])
                                val += 1
                            for val in dt:
                                if type(val) == tuple:
                                    d += (int(val[1]),)
                                else:
                                    d += (1,)
                            self.dlg.date.setDate(QDate(d[0], d[1], d[2]))
                            self.dlg.dONUCheck.setChecked(True)
                            self.dlg.date.setEnabled(True)

                    # Load Any Other Text/Combo Fields
                    elif i in self.tF or i in self.cFS or i in self.cF:
                        # Select Only First Value If Multiple
                        # - Should only be one if correct.
                        if type(self.MDTEXT[i]) == tuple:
                            print("WARNING found " +
                                  "{} when loading {}, only using '{}'.".format(
                                      self.MDTEXT[i], i, self.MDTEXT[i][0]))
                            val = self.MDTEXT[i][0]
                        else:
                            val = self.MDTEXT[i]

                        if i in self.tF:
                            self.tF[i].setText(val)
                        elif i in self.cF:
                            if self.cF[i][0].findText(val) == -1:
                                self.cF[i][0].addItem(val)
                            self.cF[i][0].setCurrentIndex(
                                self.cF[i][0].findText(val))
                        else:
                            if self.cFS[i].findText(val) == -1:
                                self.cFS[i].addItem(val)
                            self.cFS[i].setCurrentIndex(
                                self.cFS[i].findText(val))

                    # Else if is Topic Category or Resource or
                    # Bounding Box Value(s)
                    else:
                        if type(self.MDTEXT[i]) == tuple:
                            val = self.MDTEXT[i]
                        else:
                            val = [self.MDTEXT[i]]

                        if i == TOPIC:
                            for item in val:
                                found = self.dlg.topicCategory.findItems(
                                    item.strip(), Qt.MatchExactly)
                                if len(found) > 0:
                                    self.dlg.topicCategory.setCurrentRow(
                                        self.dlg.topicCategory.row(found[0]),
                                        QItemSelectionModel.Select)

                        if i == EXTENTDES:
                            for item in val:
                                found = self.dlg.geogDesList.findItems(
                                    item.strip(), Qt.MatchExactly)
                                if len(found) > 0:
                                    self.dlg.geogDesList.setCurrentRow(
                                        self.dlg.geogDesList.row(found[0]),
                                        QItemSelectionModel.Select)

                        elif i == RESOURCELIMIT:
                                res = val

                        elif i == RESOURCEUSE:
                            for k, value in enumerate(val):
                                if value == 'copyright':
                                    copy = k
                                elif value == 'license':
                                    lice = k

                        elif i == METALIMIT:
                            meta = val

                        elif i == METAUSE:
                            for k, value in enumerate(val):
                                if value == 'copyright':
                                    metcopy = k
                                elif value == 'license':
                                    metlice = k

                        elif i == EXTENTBBE:
                            self.dlg.eastExtent.setText(val[0])
                        elif i == EXTENTBBW:
                            self.dlg.westExtent.setText(val[0])
                        elif i == EXTENTBBS:
                            self.dlg.southExtent.setText(val[0])
                        elif i == EXTENTBBN:
                            self.dlg.northExtent.setText(val[0])

            if lice is not None and res is not None and lice < len(res):
                self.dlg.resourceConLicense.setText(res[lice])
            if copy is not None and res is not None and copy < len(res):
                self.dlg.resourceConCopyright.setText(res[copy])
            if metlice is not None and meta is not None and metlice < len(meta):
                self.dlg.metadataConLicense.setText(meta[metlice])
            if metcopy is not None and meta is not None and metcopy < len(meta):
                self.dlg.metadataConCopyright.setText(meta[metcopy])
        except Exception as e:
            self.dlg.reset_form()
            self.dlg.loadError.setText(str(e))
            self.dlg.loadError.show()
            return

        self.dlg.loadError.hide()
        self.dlg.loadError.clear()
        # Update window name and reset fields.
        fname = self.dlg.OUTPUTFILE[self.dlg.OUTPUTFILE.rfind('/') + 1:]
        self.dlg.setWindowTitle("ANZLIC METADATA - " + fname)
        self.dlg.setCurrentIndex(1)
        for i in range(self.dlg.count()):
            self.dlg.setTabEnabled(i, True)

    def formatSummary(self, tree):
        """
        Write Update XML Metadata fields to the formatted summary tab.
        :param tree: XML tree to write information from.
        :return: None.
        """
        general = (FID, LAN, CHSET, HLEVEL, DSTAMP, MSN, MSV, RFORMATN,
                   RFORMATV)
        metAdd = (INAME, ONAME, PNAME, VOICE, FACS, DELIVERYPOINT, CITY, ROLE,
                  POSTALCODE, COUNTRY, EMAIL)
        resAdd = (POCINAME, POCONAME, POCPNAME, POCVOICE, POCFACS, POCEMAIL,
                  POCDELIVERYPOINT, POCCITY, POCPOSTALCODE, POCCOUNTRY, POCROLE)
        resFields = (TITLE, ALTTITLE, ABSTRACT, PURPOSE, CITDATE, CITDATETYPE,
                     LINEAGE, LINKAGE, KEYWORDS, TOPIC)
        systemInfo = (RS, STATUS, RMAINTCODE, RMAINTDATE, SPATIALREP, SCALE,
                      RESOLUTION, EXTENTDES, EXTENTBBW, EXTENTBBE, EXTENTBBN,
                      EXTENTBBS, TSINGLE, TBEGIN, TEND)
        rconstraints = (CLASSIFCODE, RESOURCELIMIT, RESOURCEUSE)
        mconstraints = (MCLASSIFCODE, METALIMIT, METAUSE)
        j, k = 0, 0
        li = {general: (),
              metAdd: (),
              resAdd: (),
              resFields: (),
              systemInfo: (),
              rconstraints: (),
              mconstraints: ()}

        # Iterate through tree getting text and text 'title'
        for el in tree.iter():
            if el.text is not None:
                t1 = el.getparent().tag[el.getparent().tag.rfind('}') + 1:]
                t2 = el.text
                for l in li:
                    if re.sub('\[+.+?\]', '', tree.getpath(el)) in l:
                        li[l] += ([re.sub('([A-Z])', r' \1', t1).title(), t2],)
                        break

        # Set default values for formatted table
        vals = OD([('General', li[general]),
                   ('Metadata Address', li[metAdd]),
                   ('Resource Address', li[resAdd]),
                   ('Resource Fields', li[resFields]),
                   ('System Info', li[systemInfo]),
                   ('Resource Constraints', li[rconstraints]),
                   ('Metadata Constraints', li[mconstraints])])
        for i in vals:
            j += len(vals[i]) + 1
            for w in vals[i]:
                if w[0] == 'Date Type' or w[0] == 'Use Constraints':
                    j -= 1
                elif w[0] == 'West Bound Longitude':
                    j += 1
        self.dlg.metadataTable.clear()
        self.dlg.metadataTable.setColumnCount(2)
        self.dlg.metadataTable.setRowCount(j)
        self.dlg.metadataTable.setColumnWidth(0, 210)
        self.dlg.metadataTable.setWordWrap(True)
        font = QFont('Noto Sans', 15, QFont.Bold, True)
        font2 = QFont('Noto Sans', 11)
        changeVals = {'Code'                 : 'Extent Description',
                      'Classification'       : 'Security Classification',
                      'Denominator'          : 'Scale',
                      'Distance'             : 'Resolution',
                      'Statement'            : 'History',
                      'East Bound Longitude' : '        East Bound Longitude',
                      'West Bound Longitude' : '        West Bound Longitude',
                      'South Bound Latitude' : '        South Bound Latitude',
                      'North Bound Latitude' : '        North Bound Latitude',
                      'Date'                 : ' Date - ',
                      'Use Limitation'       : ' Use Limitation - '}
        # Update formatted table to include text and text 'title' values.
        for i in vals:
            self.dlg.metadataTable.setItem(k, 0, QTWI(i))
            self.dlg.metadataTable.item(k, 0).setFont(font)
            k += 1
            for num, j in enumerate(vals[i]):
                add, item0, item1 = False, j[0], j[1]
                if j[0] in changeVals:
                    if j[0] == 'West Bound Longitude':
                        self.dlg.metadataTable.setItem(
                            k, 0, QTWI('Extent Bounding Box'))
                        k += 1
                    if j[0] == 'Code' and j[1].isdigit():
                        item0 = 'Reference System'
                        item1 += ' - ' + \
                                 self.dlg.referenceSys.crs().description()
                    elif j[0] == 'Date':
                        item0 = changeVals[j[0]] + vals[i][num+1][1].title()
                    elif j[0] == 'Use Limitation':
                        item0 = changeVals[j[0]] + vals[i][num+1][1].title()
                    else:
                        item0 = changeVals[j[0]]
                if j[0] != 'Date Type' and j[0] != 'Use Constraints':
                    if j[0] == 'Abstract':
                        text = item1
                        start = -1
                        while text.find('**') != -1 and text.find(
                                '**') != start and text.find(
                                '**') != text.rfind('**'):
                            start = text.find('**')
                            text = text.replace('**', '<b>', 1)
                            text = text.replace('**', '</b>', 1)
                        start = -1
                        while text.find('*') != -1 and \
                                text.find('*') != start and \
                                text.find('*') != text.rfind('*'):
                            start = text.find('*')
                            text = text.replace('*', '<i>', 1)
                            text = text.replace('*', '</i>', 1)
                        for m in re.finditer(
                                "(\[{1}[^\[\]]+\]{1}\({1}[^\(\)\[\]]+\){1})",
                                text):
                            org = m.group(0)
                            new = org
                            name = re.search("(\[{1}.+\]{1})", new).group(0)
                            link = re.search("(\({1}.+\){1})", new).group(0)
                            name = name[1:len(name) - 1]
                            link = link[1:len(link) - 1]
                            new = ('<a href="' + link + '">' + name + '</a>')
                            text = text.replace(org, new)
                        textnew = ""
                        for n in text.split("\n"):
                            textnew += n + '<br>'
                        if textnew == '':
                            textnew = text
                        text = textnew
                        abst = QLabel(text)
                        abst.setFont(font2)
                        abst.setWordWrap(True)
                        abst.setTextInteractionFlags(Qt.TextBrowserInteraction)
                        self.dlg.metadataTable.setCellWidget(k, 1, abst)
                        self.dlg.metadataTable.setItem(k, 0, QTWI(item0))
                    else:
                        self.dlg.metadataTable.setItem(k, 1, QTWI(item1))
                        self.dlg.metadataTable.setItem(k, 0, QTWI(item0))
                    k += 1
        self.dlg.metadataTable.resizeRowsToContents()

    def write(self, i, tree, text, many=None, con=None):
        """
        Write text value to the xml tree, tree, with a given path.
        Determines if the path (or part of) already exists and enters all
        required remaining path to the xml tree.
        If the tag for the text value doesn't contain 'gco' or additional
        selected options the default codeURL Codelist will be added.
        :param i: xml path to the text to be inserted.
        :param tree: tree for the text to be inserted.
        :param text: text to be inserted into the tree.
        :param many: xml path to be inserted if many fields allowed and full
        path already exists.
        :param con: constraint 'license' or 'copyright'
        :return: tree.
        """
        base, found = '', None
        codeUrl = 'http://standards.iso.org/ittf/PubliclyAvailableStandards' + \
                  '/ISO_19139_Schemas/resources/Codelist/gmxCodelists.xml#'

        # Is a template field, so don't add.
        if text[0] == '[' and text[len(text) - 1] == ']':
            return tree

        # Find tag that exists in the tree already. (Found)
        for val in i[17:].split('/'):
            if tree.find(base + val, namespaces=NSX) is not None:
                found = base + val
            base += (val + '/')

        # If none of the tag can be found in the tree, insert from the
        # root, else insert from the point found.
        if found is None:
            found = base[:len(base) - 1]
            insert, f = found, tree.getroot()
        else:
            insert = (i[17:].split(found)[1][1:])
            f = tree.find(found, namespaces=NSX)

        if insert == "" and many is not None or \
                many is not None and 'extent' in i and 'Bounding' not in i or \
                many is not None and 'extent' in i and 'west' in i or \
                many is not None and 'LegalConstraints' in i and \
                insert != tree.getroot():

            if many == tree.getroot():
                insert, f = i[17:], tree.getroot()
            else:
                insert = base.split(many)[1].lstrip('/').rstrip('/')
                f = tree.find(many, namespaces=NSX)

        # Add elements to be inserted to the xml tree one by one.
        # If is a use Limitation add restriction and use constraints, else if
        # is not a 'gco' field add codelist values.
        for k in insert.split('/'):
            j = (k.split(':'))
            element = SE(f, QN(NSX[str(j[0])], str(j[1])))
            f = element
            if con is not None and j[1] == 'useLimitation':
                sib = EL(QN(NSX['gmd'], 'useConstraints'))
                code = SE(sib, QN(NSX['gmd'], 'MD_RestrictionCode'))
                code.attrib['codeList'] = codeUrl + 'MD_RestrictionCode'
                code.attrib['codeListValue'] = con
                code.text = con
                f.addnext(sib)
            elif 'temporal' in i and j[1] == 'TimePeriod':
                f.attrib['{' + NSX['gml'] + '}id'] = 'TP1'
            elif 'temporal' in i and j[1] == 'TimeInstant':
                f.attrib['{' + NSX['gml'] + '}id'] = 'TI1'

        if 'gco' not in f.tag and 'URL' not in f.tag and 'Position' \
                not in f.tag and 'Topic' not in f.tag:
            f.attrib['codeList'] = codeUrl + f.tag[f.tag.rfind('}') + 1:]
            f.attrib['codeListValue'] = text
        f.text = text
        return tree

    def writeXML(self):
        """
        Iterate through XML fields and if they contain text/ are selected,
        or multiple are selected. Write them to the xml tree using the write()
        method.
        :return: None.
        """
        extentDesc = OD(
            [('/gmd:title' + CS, (
                'ANZLIC Geographic Extent Name Register',
                'gmd:identificationInfo/gmd:MD_DataIdentification')),
             ('/gmd:date/gmd:CI_Date/gmd:date' + DT, ('2006-10-10', None)),
             ('/gmd:date/gmd:CI_Date/gmd:dateType/gmd:CI_DateTypeCode',
              ('publication', None)),
             ('/gmd:edition' + CS, ('Version 2', None)),
             ('/gmd:editionDate' + DT, ('2001-02', None)),
             ('/gmd:identifier/gmd:MD_Identifier/gmd:code' + CS,
              ('http://asdd.ga.gov.au/asdd/profileinfo/anzlic-allgens.xml' +
               '#new_zealand', None)),
             ('/gmd:citedResponsibleParty/gmd:CI_ResponsibleParty/gmd:' +
              'organisationName' + CS,
              ('ANZLIC the Spatial Information Council', None)),
             ('/gmd:citedResponsibleParty/gmd:CI_ResponsibleParty/gmd:role/' +
              'gmd:CI_RoleCode', ('custodian', None))])
        extentDesv1 = OD(
            [('/gmd:title' + CS, (
                'ANZMet Lite Country codelist',
                'gmd:identificationInfo/gmd:MD_DataIdentification')),
             ('/gmd:date/gmd:CI_Date/gmd:date' + DT, ('2009-03-31', None)),
             ('/gmd:date/gmd:CI_Date/gmd:dateType/gmd:CI_DateTypeCode',
              ('publication', None)),
             ('/gmd:edition' + CS, ('Version 1.0', None)),
             ('/gmd:editionDate' + DT, ('2009-03-31', None)),
             ('/gmd:identifier/gmd:MD_Identifier/gmd:code' + CS,
              ('http://asdd.ga.gov.au/asdd/profileinfo/anzlic-country.xml' +
               '#Country', None)),
             ('/gmd:citedResponsibleParty/gmd:CI_ResponsibleParty/gmd:' +
              'organisationName' + CS,
              ('ANZLIC the Spatial Information Council', None)),
             ('/gmd:citedResponsibleParty/gmd:CI_ResponsibleParty/gmd:role/' +
              'gmd:CI_RoleCode', ('custodian', None))])
        keywordDict = OD(
            [('/gmd:title' + CS, ('ANZLIC Jursidictions', None)),
             ('/gmd:date/gmd:CI_Date/gmd:date' + DT, ('2008-10-29', None)),
             ('/gmd:date/gmd:CI_Date/gmd:dateType/gmd:CI_DateTypeCode',
              ('revision', None)),
             ('/gmd:edition' + CS, ('Version 2.1', None)),
             ('/gmd:editionDate' + DT, ('2008-10-29', None)),
             ('/gmd:identifier/gmd:MD_Identifier/gmd:code' + CS,
              ('http://asdd.ga.gov.au/asdd/profileinfo/anzlic-jurisdic.xml#' +
               'anzlic-jurisdic', None)),
             ('/gmd:citedResponsibleParty/gmd:CI_ResponsibleParty/gmd:' +
              'organisationName' + CS,
              ('ANZLIC the Spatial Information Council', None)),
             ('/gmd:citedResponsibleParty/gmd:CI_ResponsibleParty/gmd:role/' +
              'gmd:CI_RoleCode', ('custodian', None))])
        iD = ID.split(MD+'/')[1]
        url = 'http://standards.iso.org/ittf/PubliclyAvailableStandards/' + \
              'ISO_19139_Schemas/resources/Codelist/gmxCodelists.xml#'
        try:
            md = EL('{http://www.isotc211.org/2005/gmd}MD_Metadata', nsmap=NSX)
            tree = ELT(md)
            for i in FIELDS:

                # File Identifier
                if i == FID and self.dlg.outputFile.text() != '':
                    tree = self.write(i, tree, str(uuid.uuid4()))

                # Date Stamp
                elif i == DSTAMP and self.dlg.outputFile.text() != '':
                    date = QDate.currentDate().toString('yyyy-MM-dd')
                    tree = self.write(i, tree, date, iD)

                # Scale
                elif i == SCALE:
                    if self.dlg.scale.isChecked() and \
                            self.dlg.scaleRadioButton.isChecked() and \
                            self.dlg.scaleWidget.scaleString() != '0':
                        tx = self.dlg.scaleWidget.scaleString().replace(',', '')
                        tree = self.write(i, tree, tx.split('1:')[1])

                # Resolution
                elif i == RESOLUTION:
                    if self.dlg.scale.isChecked() and \
                            self.dlg.resolutionRadioButton.isChecked():
                        if self.dlg.rUnits.currentText() == '' or \
                                self.dlg.resolutionText.text() == '':
                            raise Exception('Write Warning: Resolution not ' +
                                            'written to XML as missing fields.')
                        else:
                            text = self.dlg.resolutionText.text()
                            tree = self.write(i, tree, text)
                            for j in self.rcode:
                                if self.rcode[j] == self.dlg.rUnits.currentText(
                                ):
                                    res = tree.find(RESOLUTION[16:],
                                                    namespaces=NSX)
                                    res.attrib['uom'] = j

                # Extent Description
                elif i == EXTENTDES:
                    ex = 'gmd:EX_Extent/gmd:geographicElement/gmd:EX_' + \
                         'GeographicDescription/gmd:geographicIdentifier/' + \
                         'gmd:MD_Identifier/gmd:authority/gmd:CI_Citation'
                    idn = md.find('gmd:identificationInfo/gmd:MD_Data' +
                                  'Identification', namespaces=NSX)
                    if idn is None:
                        idn = SE(md, QN(NSX['gmd'], 'identificationInfo'))
                        idn = SE(idn, QN(NSX['gmd'], 'MD_DataIdentification'))
                    for s in self.dlg.geogDesList.selectedItems():
                        exDesc = extentDesc
                        if s.text() == 'nzl':
                            exDesc = extentDesv1
                        extent = SE(idn, QN(NSX['gmd'], 'extent'))
                        for value in exDesc:
                            base, found = '', None
                            for val in (ex+value).split('/'):
                                if extent.find(
                                        base + val, namespaces=NSX) is not None:
                                    found = base + val
                                base += (val + '/')
                            if found:
                                f = extent.find(found, namespaces=NSX)
                                search = (ex+value).split(found)[1]
                            else:
                                search = (ex+value)
                                f = extent
                            splitb = search.split('/')
                            for sb in splitb:
                                if sb != '':
                                    splitn = sb.split(':')
                                    for num, j in enumerate(
                                            splitn[:len(splitn) / 2]):
                                        element = SE(
                                            f, QN(NSX[j], splitn[num + 1]))
                                        f = element
                                        if splitn[num+1] == 'authority':
                                            el = EL(QN(NSX['gmd'], 'code'))
                                            sel = SE(el, QN(
                                                NSX['gco'], 'CharacterString'))
                                            sel.text = s.text()
                                            f.addnext(el)
                                        num += 1
                            f.text = exDesc[value][0]
                            if 'gco' not in f.tag:
                                f.attrib['codeList'] = url + f.tag[f.tag.rfind(
                                    '}') + 1:]
                                f.attrib['codeListValue'] = exDesc[value][0]

                # Reference System
                elif i == RS:
                    if self.dlg.referenceSys.crs().authid() != "":
                        text = self.dlg.referenceSys.crs().authid()
                        tree = self.write(i, tree, text.split(':')[1])

                # Other Text Fields
                elif i in self.tF:
                    if self.tF[i].toPlainText() != '':
                        tree = self.write(i, tree, self.tF[i].toPlainText())

                # Other Combo - Contact Fields
                elif i in self.cFS:
                    if self.cFS[i].currentText() != '':
                        tree = self.write(i, tree, self.cFS[i].currentText())

                # Other Combo Fields
                elif i in self.cF:
                    if self.cF[i][0].currentText() != '':
                        tree = self.write(i, tree, self.cF[i][0].currentText())

                # Hierarchy Level Description/ Scope/ Scope Description
                elif i == HLEVELNAME or i == SCOPE or i == SCOPEDESC:
                    if self.cF[HLEVEL][0].currentText() != '':
                        text = self.cF[HLEVEL][0].currentText()
                        tree = self.write(i, tree, text)

                # Topic Category
                elif i == TOPIC:
                    for j in self.dlg.topicCategory.selectedItems():
                        tree = self.write(i, tree, j.text(), iD)

                # Resource Maintenance Date
                elif i == RMAINTDATE:
                    if self.dlg.date.isEnabled():
                        date = self.dlg.date.date().toString('yyyy-MM')
                        tree = self.write(i, tree, date)

                # Resource Limitation
                elif i == RESOURCELIMIT:
                    if self.dlg.resourceConLicense.toPlainText() != '':
                        tx = self.dlg.resourceConLicense.toPlainText()
                        tree = self.write(i, tree, tx, iD, con='license')
                    if self.dlg.resourceConCopyright.toPlainText() != '':
                        tx = self.dlg.resourceConCopyright.toPlainText()
                        tree = self.write(i, tree, tx, iD, con='copyright')

                # Metadata Limitaiton
                elif i == METALIMIT:
                    if self.dlg.metadataConLicense.toPlainText() != '':
                        tx = self.dlg.metadataConLicense.toPlainText()
                        tree = self.write(i, tree, tx, tree.getroot(),
                                          con='license')
                    if self.dlg.metadataConCopyright.toPlainText() != '':
                        tx = self.dlg.metadataConCopyright.toPlainText()
                        tree = self.write(i, tree, tx, tree.getroot(),
                                          con='copyright')

                # Temporal Single/ Begin Range
                elif i == TSINGLE or i == TBEGIN:
                    if i == TSINGLE and not \
                            self.dlg.endDateCheck.isChecked() or i == TBEGIN \
                            and self.dlg.endDateCheck.isChecked():
                        if self.dlg.temporalCheck.isChecked():
                            date = self.dlg.startDate.date().toString(
                                'yyyy-MM-dd')
                            if self.dlg.startTimeCheck.isChecked():
                                date += 'T' + self.dlg.startTime.time(
                                ).toString('hh:mm:ss')
                            tree = self.write(i, tree, date, iD)

                # Temporal End Range
                elif i == TEND:
                    tend = None
                    if self.dlg.temporalCheck.isChecked() and \
                            self.dlg.endDateCheck.isChecked():
                        date = self.dlg.endDate.date().toString('yyyy-MM-dd')
                        if self.dlg.endTimeCheck.isChecked():
                            date += 'T' + self.dlg.endTime.time().toString(
                                'hh:mm:ss')
                            tend = TEND.split('/gml:endPosition')[
                                0].split(MD+'/')[1]
                        tree = self.write(i, tree, date, tend)

                # Keywords/ Keyword Type
                elif i == KEYWORDS or i == KEYWORDSTYPE:
                    mdk = None
                    if i == KEYWORDS:
                        keywordUrl = url + 'MD_KeywordTypeCode'
                        mt = KEYWORDS.split('/gmd:keyword')[0].split(MD)[1]
                        tree = self.write(i, tree, 'New Zealand', mt[1:])

                        kt = EL(QN(NSX['gmd'], 'type'))
                        ktc = SE(kt, QN(NSX['gmd'], 'MD_KeywordTypeCode'))
                        ktc.attrib['codeList'] = keywordUrl
                        ktc.attrib['codeListValue'] = 'theme'
                        h = tree.find(i[17:], namespaces=NSX)
                        h.getparent().addnext(kt)

                        path = MD + mt + '/gmd:thesaurusName/gmd:CI_Citation'

                        for k in keywordDict:
                            tree = self.write(path + k, tree,
                                              keywordDict[k][0],
                                              keywordDict[k][1])
                        found = False
                        if len(self.dlg.keywordList.selectedItems()) > 0:
                            desc = tree.find(iD + '/gmd:descriptiveKeywords',
                                             namespaces=NSX)
                            desckey = EL(QN(NSX['gmd'], 'descriptiveKeywords'))
                            desc.addnext(desckey)
                            mdk = SE(desckey, QN(NSX['gmd'], 'MD_Keywords'))
                        for j in self.dlg.keywordList.selectedItems():
                            found = True
                            key = EL(QN(NSX['gmd'], 'keyword'))
                            cs = SE(key, QN(NSX['gco'], 'CharacterString'))
                            cs.text = j.text().replace(' ', '-')
                            mdk.append(key)

                        if found:
                            kt = EL(QN(NSX['gmd'], 'type'))
                            ktc = SE(kt, QN(NSX['gmd'], 'MD_KeywordTypeCode'))
                            ktc.attrib['codeList'] = keywordUrl
                            ktc.attrib['codeListValue'] = 'theme'
                            t = tree.findall(i[17:], namespaces=NSX)
                            t = t[len(tree.findall(i[17:], namespaces=NSX)) - 1]
                            t.getparent().addnext(kt)

                # Key Resource Date & Type
                elif i == CITDATE or i == CITDATETYPE:
                    if i == CITDATE:
                        dateUrl = url + 'CI_DateTypeCode'

                        codeListVal = {self.dlg.resourceCreateCheck: (
                            'creation', self.dlg.resourceCreate),
                                       self.dlg.resourceUpdateCheck: (
                                           'revision', self.dlg.resourceUpdate),
                                       self.dlg.resourcePublishCheck: (
                                           'publication',
                                           self.dlg.resourcePublish)}

                        for val in (self.dlg.resourceCreateCheck,
                                    self.dlg.resourcePublishCheck,
                                    self.dlg.resourceUpdateCheck):
                            if val.isChecked():
                                date = codeListVal[val][1].date()
                                date = date.toString('yyyy-MM-dd')
                                tree = self.write(
                                    i, tree, date,
                                    iD + '/gmd:citation/gmd:CI_Citation')
                                citD = EL(QN(NSX['gmd'], 'dateType'))
                                citDCode = SE(citD, QN(NSX['gmd'],
                                                       'CI_DateTypeCode'))
                                citDCode.attrib['codeList'] = dateUrl
                                citDCode.attrib['codeListValue'] = codeListVal[
                                    val][0]
                                citDCode.text = codeListVal[val][0]
                                t = tree.findall(i[17:], namespaces=NSX)
                                t = t[len(tree.findall(
                                    i[17:], namespaces=NSX)) - 1]
                                t.getparent().addnext(citD)

                elif EXTENTBB in i:
                    if self.dlg.northExtent.displayText() != '' and \
                       self.dlg.southExtent.displayText() != '' and \
                       self.dlg.eastExtent.displayText() != '' and \
                       self.dlg.westExtent.displayText() != '':
                        if 'north' in i:
                            tree = self.write(
                                i, tree, self.dlg.northExtent.displayText())
                        elif 'south' in i:
                            tree = self.write(
                                i, tree, self.dlg.southExtent.displayText())
                        elif 'east' in i:
                            tree = self.write(
                                i, tree, self.dlg.eastExtent.displayText())
                        elif 'west' in i:
                            tree = self.write(
                                i, tree, self.dlg.westExtent.displayText(), iD)

                # Default Values
                elif i in DEFAULTTEXT:
                    tree = self.write(i, tree, DEFAULTTEXT[i])

                elif i in self.MDTEXT and (i == FID or i == DSTAMP or
                                           'extent' in i or 'URL' in i):
                    # Update Any other fields that are not empty.
                    if type(self.MDTEXT[i]) == tuple:
                        val = self.MDTEXT[i][0]
                    else:
                        val = self.MDTEXT[i]
                    if val != '':
                        if 'extent' in i:
                            tree = self.write(i, tree, self.MDTEXT[i], iD)
                        else:
                            tree = self.write(i, tree, self.MDTEXT[i])

            # Create New Metadata File
            md_text = TS(md, pretty_print=True, xml_declaration=True,
                         encoding='utf-8')

            # Write to Temp File & Create XML Summary & Formatted Summary
            with open(TEMPFILE, 'wb') as f:
                f.write(md_text)
            self.dlg.summary.setText(md_text)
            self.formatSummary(tree)

        except Exception as e:
            raise Exception("Write Error: " + str(e))

    def createMeta(self):
        """
        Create metadata Clicked.
        Copies the temp file to the selected output file, removes the temp file,
        and allows the user to click publish metadata.
        :return: None.
        """
        # Clear validation and update output file.
        self.dlg.validationLog.clear()
        try:
            copyfile(TEMPFILE, self.dlg.OUTPUTFILE)
            os.remove(TEMPFILE)
        except Exception as e:
            self.dlg.validationLog.setText("XML Creation Error: " + str(e))
            return
        if self.dlg.OUTPUTFILE == self.dlg.TEMPLATEPATH:
            self.dlg.validationLog.setText('Metadata "{}" Edited'.format(
                self.dlg.OUTPUTFILE))
        else:
            self.dlg.validationLog.setText('Metadata "{}" Created'.format(
                self.dlg.OUTPUTFILE))
        self.dlg.publishMetadata.show()
        self.dlg.createMetadata.setEnabled(False)

    def publishMeta(self):
        """
        Publish metadata Clicked.
        Sets the koordinates client, clears any previous information in the
        publish dialog and diplays.
        :return: None.
        """
        try:
            domain = 'data.linz.govt.nz'
            self.client = koordinates.Client(domain, KEY)
            self.publishDialog.errorText.clear()
            self.publishDialog.titleBox.clear()
            self.publishDialog.layerId.clear()
            self.publishDialog.publishBox.setEnabled(False)
            self.publishDialog.show()
            if self.lid:
                self.publishDialog.layerId.setText(self.lid)
        except Exception as e:
            self.dlg.validationLog.setText('Publication Error: ' + str(e))

    def updatePublishDlg(self):
        """
        Enter is clicked on the Publish dialog, the layer associated to the
        layer ID is searched if valid, enabled the user to continue with
        publishing, otherwise writes the error to the dialog.
        :return: None.
        """
        try:
            self.publishDialog.errorText.clear()
            self.publishDialog.titleBox.clear()
            self.lidpub = self.publishDialog.layerId.toPlainText()
            if self.lidpub != '':
                self.layer = self.client.layers.get(self.lidpub)
                self.title = self.layer.title
                self.publishDialog.titleBox.setText(self.title)
                self.publishDialog.publishBox.setEnabled(True)
            else:
                self.publishDialog.errorText.setText('Enter Layer ID to Update')
        except Exception as e:
            self.publishDialog.errorText.setText(str(e))
            self.publishDialog.publishBox.setEnabled(False)

    def publish(self):
        """
        Okay is clicked on the Publish dialog, the saved xml metadata file is
        published to the layer associated to the ID given using set_metadata
        from lds_metadata_updater.
        :return: None
        """
        publish = '''
        try:
            xmlfile = self.dlg.OUTPUTFILE
            publisher = koordinates.Publish()
            res = set_metadata(self.layer, xmlfile, publisher)
            if res:
                #r = self.client.publishing.create(publisher)
                self.dlg.validationLog.setText('Publication Complete - ' + 
                                               self.lidpub + ' - ' + self.title)
            else:
                raise Exception('Error Getting Draft Metadata')
        except Exception as e:
            self.dlg.validationLog.setText('Publication Failure: ' + str(e))
        '''
        print (publish)
        xmlfile = self.dlg.OUTPUTFILE
        layerID = self.lidpub
        print (xmlfile, layerID)
        text = 'Publication Complete - ' + self.lidpub + ' - ' + self.title
        self.dlg.validationLog.setText(text)

    def toggleDate(self, state):
        """
        Date of next update check box state changed. Enable/Disable Date field
        depending on state.
        :param state: Check box state.
        :return: None.
        """
        if state > 0:
            self.dlg.date.setEnabled(True)
        else:
            self.dlg.date.setEnabled(False)

    def toggleState(self, state):
        """
        Scale check box state changed. Enable/Disable Scale Frame depending on
        state.
        :param state: Check box state.
        :return: None.
        """
        if state > 0:
            self.dlg.scaleFrame.setEnabled(True)
        else:
            self.dlg.scaleFrame.setEnabled(False)

    def toggleRadio(self, checked):
        """
        Scale/ Resolution radio buttons state changed. Enable/Disable Scale -
        (Scale Widget)/ Resolution - (Resolution Text, R Units) depending on
        checked.
        :param checked: Radio button state.
        :return: None.
        """
        if checked:
            self.dlg.scaleWidget.setEnabled(True)
            self.dlg.resolutionText.setEnabled(False)
            self.dlg.rUnits.setEnabled(False)
        else:
            self.dlg.scaleWidget.setEnabled(False)
            self.dlg.resolutionText.setEnabled(True)
            self.dlg.rUnits.setEnabled(True)

    def toggleRadioRes(self, checked):
        """
        Resolution radio button state changed. Enable/Disable Scale -
        (Scale Widget)/ Resolution - (Resolution Text, R Units) depending on
        checked.
        :param checked: Radio button state.
        :return: None.
        """
        if checked:
            self.dlg.scaleWidget.setEnabled(False)
            self.dlg.resolutionText.setEnabled(True)
            self.dlg.rUnits.setEnabled(True)
        else:
            self.dlg.scaleWidget.setEnabled(True)
            self.dlg.resolutionText.setEnabled(False)
            self.dlg.rUnits.setEnabled(False)

    def temporal(self, state):
        """
        Temporal check box state changed. Enable/Disable and Uncheck/Check All
        Temporal Date fields depending on state.
        :param state: Check box state.
        :return: None.
        """
        if state > 0:
            self.dlg.startDate.setEnabled(True)
            self.dlg.startTimeCheck.setEnabled(True)
            self.dlg.endDateCheck.setEnabled(True)
        else:
            self.dlg.startDate.setEnabled(False)
            self.dlg.startTimeCheck.setChecked(False)
            self.dlg.startTimeCheck.setEnabled(False)
            self.dlg.endDateCheck.setChecked(False)
            self.dlg.endDateCheck.setEnabled(False)

    def startTime(self, state):
        """
        Start time check box state changed. Enable/Disable Temporal Start Time
        depending on state.
        :param state: Check box state.
        :return: None.
        """
        if state > 0:
            self.dlg.startTime.setEnabled(True)
        else:
            self.dlg.startTime.setEnabled(False)

    def endTime(self, state):
        """
        End time check box state changed. Enable/Disable Temporal End Time
        depending on state.
        :param state: Check box state.
        :return: None.
        """
        if state > 0:
            self.dlg.endTime.setEnabled(True)
        else:
            self.dlg.endTime.setEnabled(False)

    def endDate(self, state):
        """
        End date check box state changed. Enable/Disable and Check/Uncheck
        Temporal End Date
        :param state: Check box state.
        :return: None.
        """
        if state > 0:
            self.dlg.endDate.setEnabled(True)
            self.dlg.endTimeCheck.setEnabled(True)
        else:
            self.dlg.endDate.setEnabled(False)
            self.dlg.endTimeCheck.setEnabled(False)
            self.dlg.endTimeCheck.setChecked(False)

    def createDate(self, state):
        """
        Creation date check box state changed. Enable/Disable Resource Creation
        Key Date, depending on state.
        :param state: Check box state.
        :return: None.
        """
        if state > 0:
            self.dlg.resourceCreate.setEnabled(True)
        else:
            self.dlg.resourceCreate.setEnabled(False)

    def publishDate(self, state):
        """
        Publish date check box state changed. Enable/Disable Resource Publish
        Key Date, depending on state.
        :param state: Check box state.
        :return: None.
        """
        if state > 0:
            self.dlg.resourcePublish.setEnabled(True)
        else:
            self.dlg.resourcePublish.setEnabled(False)

    def updateDate(self, state):
        """
        Update date check box state changed. Enabled/Disable Resource Update
        Key Date, depending on state.
        :param state: Check box state.
        :return: None.
        """
        if state > 0:
            self.dlg.resourceUpdate.setEnabled(True)
        else:
            self.dlg.resourceUpdate.setEnabled(False)

    def loadExtent(self):
        """
        Load Extent clicked.
        Load the extent of the current layer into the extent bounding box fields
        shows error label if no layer selected.
        :return: None
        """
        canvas = self.iface.mapCanvas()
        layer = canvas.currentLayer()
        if layer is not None:
            try:
                self.dlg.bbError.hide()
                extent = layer.extent()
                self.dlg.northExtent.setText(str(extent.yMaximum()))
                self.dlg.southExtent.setText(str(extent.yMinimum()))
                self.dlg.eastExtent.setText(str(extent.xMaximum()))
                self.dlg.westExtent.setText(str(extent.xMinimum()))
            except Exception as e:
                self.dlg.bbError.setText('Error: ', str(e))
                self.dlg.bbError.show()
        else:
            self.dlg.bbError.show()

    def check(self):
        """
        Validate/ Error Check Clicked.
        Perform Error Checks from errorChecker.py - If error found and contains
        text 'Expected is' then will show fix error button which will link to
        to the tab that contains the error, along with an asterisks showing
        which field.
        Perform Validation Checks from validate.py
        All Validation/ Error checks will be displayed in the validation log.
        If no validation or error checker errors are found, allow the user to
        create the metadata.
        :return: None
        """
        contact = ('INDIVIDUALNAME', 'ORGANISATIONNAME', 'POSITIONNAME', 'ROLE',
                   'VOICE', 'FACSIMILE', 'DELIVERYADDRESS', 'CITY', 'COUNTRY',
                   'POSTALCODE', 'EMAIL')
        basic = ('HIERARCHYLEVEL', 'TITLE', 'ALTTITLE', 'ABSTRACT', 'PURPOSE')
        security = ('SECURITYCLASSRES', 'SECURITYCLASSMET', 'RESTRICCODERES',
                    'RESTRICCODEMET', 'RESOURCECON', 'METADATACON')
        extent = ('EXTENTDESCRIPTION', 'EXTENTBOUNDINGBOX', 'EXTENTTEMPORAL',
                  'EXTENTVERTICAL')
        ident = ('REFERENCESYS1', 'STATUS', 'LINEAGE', 'SPATIALREPRESENTATION',
                 'MAINTENANCE', 'MAINTNEXTUPDATE', 'SCALE', 'RESOLUTION')
        other = ('KEYWORD', 'KEYDATE', 'TOPICCATEGORY')

        tabDict = {'INDIVIDUALNAME'       : (self.dlg.iNameError1,
                                             self.dlg.iNameError2),
                   'ORGANISATIONNAME'     : (self.dlg.oNameError1,
                                             self.dlg.oNameError2),
                   'POSITIONNAME'         : (self.dlg.pNameError1,
                                             self.dlg.pNameError2),
                   'VOICE'                : (self.dlg.voiceError1,
                                             self.dlg.voiceError2),
                   'FACSIMILE'            : (self.dlg.fasError1,
                                             self.dlg.fasError2),
                   'DELIVERYADDRESS'      : (self.dlg.dadd1Error,
                                             self.dlg.dadd2Error),
                   'CITY'                 : (self.dlg.cityError1,
                                             self.dlg.cityError2),
                   'COUNTRY'              : (self.dlg.countryError1,
                                             self.dlg.countryError2),
                   'POSTALCODE'           : (self.dlg.postCode1Error,
                                             self.dlg.postCode2Error),
                   'EMAIL'                : (self.dlg.emailError1,
                                             self.dlg.emailError2),
                   'ROLE'                 : (self.dlg.roleError1,
                                             self.dlg.roleError2),
                   'HIERARCHYLEVEL'       : self.dlg.hlNameError,
                   'TITLE'                : self.dlg.titleError,
                   'ABSTRACT'             : self.dlg.absError,
                   'PURPOSE'              : self.dlg.purposeError,
                   'SECURITYCLASSRES'     : self.dlg.resSecClassError,
                   'SECURITYCLASSMET'     : self.dlg.metSecClassError,
                   'RESTRICCODERES'       : (self.dlg.resourceConCopyrightError,
                                             self.dlg.resourceConLicenseError),
                   'RESTRICCODEMET'       : (self.dlg.metadataConCopyrightError,
                                             self.dlg.metadataConLicenseError),
                   'EXTENTDESCRIPTION'    : self.dlg.geogDesListError,
                   'EXTENTBOUNDINGBOX'    : self.dlg.geoBBNorthLabelError,
                   'EXTENTTEMPORAL'       : self.dlg.temporalCheckError,
                   'REFERENCESYS1'        : self.dlg.referenceSysError,
                   'STATUS'               : self.dlg.statusError,
                   'LINEAGE'              : self.dlg.lineageError,
                   'SPATIALREPRESENTATION': self.dlg.spatialrepError,
                   'MAINTENANCE'          : self.dlg.maintenanceError,
                   'KEYWORD'              : self.dlg.keywordListError,
                   'TOPICCATEGORY'        : self.dlg.topicCategoryError,
                   'ALTTITLE'             : self.dlg.atitleError,
                   'SCALE'                : self.dlg.scaleRadioButtonError,
                   'RESOLUTION'           : self.dlg.resolutionRadioButtonError,
                   'KEYDATE'              : self.dlg.resourceCreateCheckError,
                   'MAINTNEXTUPDATE'      : self.dlg.dONUCheckError}

        self.dlg.validationLog.clear()
        vdtr = None
        # Write input to xml tree.
        try:
            self.writeXML()
        except Exception as e:
            self.dlg.validationLog.setText(str(e))
            return
        try:
            metafile, vdtr = r'{}/{}'.format(os.getcwd(), TEMPFILE), Combined()
            meta = vdtr.metadata(name=metafile)
            if self.dlg.check != 0 and self.use:
                self.use.hide()

            # Run Error Checks
            runChecks(meta, self.lid, con=self.configfile)

            self.dlg.fixError.hide()
            self.dlg.validationLog.setText('Error Checks Complete')

            # Run Validation
            vdtr.setschema()
            vdtr.validate(meta)
            vdtr.conditional(meta)

            self.dlg.validationLog.setText(
                'Error Checks Complete\nValidation Checks Complete')
            self.dlg.createMetadata.setEnabled(True)

        except ValidatorException as ve:
            text = ""
            if vdtr:
                if 'Expected is (' in str(vdtr.sch.error_log):
                    errorLog = str(vdtr.sch.error_log)
                    eL = errorLog[str(vdtr.sch.error_log).rfind('}')+1:len(
                        str(vdtr.sch.error_log))-3]
                    text = ' - Missing: ' + eL
                self.dlg.validationLog.setText(
                    'Validation Error: ' + str(ve) + text + '\n' + str(
                        vdtr.sch.error_log))
            else:
                self.dlg.validationLog.setText('Validation Error: ' + str(ve))
            self.dlg.createMetadata.setEnabled(False)
        except InvalidConfigException as ice:
            self.dlg.validationLog.setText(
                'Checker Error, Invalid Config: {}'.format(str(ice)))
            self.dlg.createMetadata.setEnabled(False)
        except Exception as e:
            try:
                self.dlg.check += 1
                self.widget = self.dlg.widget(7)
                valFound = None
                self.dlg.fixError.show()
                self.dlg.validationLog.setText('Checker Error: {}'.format(
                    str(e)))

                dt = {contact   : self.dlg.widget(2),
                      basic     : self.dlg.widget(1),
                      security  : self.dlg.widget(6),
                      extent    : self.dlg.widget(5),
                      ident     : self.dlg.widget(3),
                      other     : self.dlg.widget(4)}

                for val in contact, basic, security, extent, ident, other:
                    for v in val:
                        if v in str(e):
                            self.widget, valFound = dt[val], v
                            break
                widget = None
                if valFound is None:
                    self.dlg.fixError.hide()
                elif valFound not in tabDict:
                    pass
                elif type(tabDict[valFound]) == tuple:
                    if 'copyright' in str(e):
                        self.use = tabDict[valFound][0]
                        attr = self.use.objectName().replace('Error', '')
                        if hasattr(self.dlg, attr):
                            widget = getattr(self.dlg, attr)
                    elif 'license' in str(e):
                        self.use = tabDict[valFound][1]
                        attr = self.use.objectName().replace('Error', '')
                        if hasattr(self.dlg, attr):
                            widget = getattr(self.dlg, attr)
                    elif valFound + '2' in str(e):
                        self.use = tabDict[valFound][0]
                        attr = self.use.objectName().replace('Error', '')
                        if hasattr(self.dlg, attr):
                            widget = getattr(self.dlg, attr)
                    else:
                        self.use = tabDict[valFound][1]
                        attr = self.use.objectName().replace('Error', '')
                        if hasattr(self.dlg, attr):
                            widget = getattr(self.dlg, attr)
                else:
                    self.use = tabDict[valFound]
                    attr = self.use.objectName().replace('Error', '')
                    if hasattr(self.dlg, attr):
                        widget = getattr(self.dlg, attr)
                if widget:
                    widget.setFocus()
                self.use.show()
            except Exception as e:
                self.dlg.validationLog.setText('Checker Error: {}'.format(
                    str(e)))
                traceback.print_exc()
                self.dlg.fixError.hide()
                self.dlg.createMetadata.setEnabled(False)
            self.dlg.createMetadata.setEnabled(False)

    def fixError(self):
        """
        Fix error button clicked.
        Hide the fix error button again, and switch to tab with the recorded
        error.
        :return: None.
        """
        self.dlg.fixError.hide()
        self.dlg.setCurrentWidget(self.widget)

    def setFile(self, i):
        """
        Select file clicked.
        Open File Dialog and Update Selection (Template, Output, Existing
        Metadata File)
        :param i: Button clicked to set the file.
        (1 - Template Select, 2 - Output Select, 3 - Existing Select)
        :return: None.
        """
        try:
            self.dlg.loadError.hide()
            self.dlg.metadataFile.clear()
            if i == 1:
                filename = QFileDialog.getOpenFileName(
                    None, 'Open File', os.getenv('HOME'),
                    "XML Template File (*xml)")
            elif i == 2:
                filename = QFileDialog.getOpenFileName(
                    None, 'Open File', os.getenv('HOME'),
                    "XML Output File (*xml)")
            else:
                filename = QFileDialog.getOpenFileName(
                    None, 'Open File', os.getenv('HOME'),
                    "XML Metadata File (*xml)")
            if filename:
                if type(filename) == list:
                    filename = filename[0]
                self.dlg.reset_form()
                if i == 1:
                    self.dlg.changeTemplate(filename)
                    self.dlg.templateFile.setText(self.dlg.TEMPLATEPATH)
                    self.dlg.outputFile.setText(self.dlg.TEMPLATEPATH)
                elif i == 2:
                    self.dlg.OUTPUTFILE = filename
                    self.dlg.outputFile.setText(self.dlg.OUTPUTFILE)
                else:
                    self.dlg.OUTPUTFILE = filename
                    self.dlg.changeTemplate(filename)
                    self.dlg.metadataFile.setText(self.dlg.OUTPUTFILE)
        except Exception as e:
            self.dlg.loadError.setText("File Selection Error: " + str(e))
            self.dlg.loadError.show()

    def updateFileText(self):
        """
        Default template clicked.
        Update the template field to the default template location.
        :return: None.
        """
        self.dlg.changeTemplate(self.dlg.DEFAULTTEMP)
        self.dlg.templateFile.setText(self.dlg.TEMPLATEPATH)

    def autoFillLegal(self):
        """
        Auto Fill Clicked on the Legal Tab.
        Auto fill resource/metadata constraint values with default values, and
        update the original values for undo operation.
        :return: None.
        """
        if self.metaCC is None:
            self.metaCC = self.dlg.metadataConCopyright.toPlainText()
            self.metaCL = self.dlg.metadataConLicense.toPlainText()
            self.resCC = self.dlg.resourceConCopyright.toPlainText()
            self.resCL = self.dlg.resourceConLicense.toPlainText()
        self.dlg.metadataConCopyright.setText(
            self.mcopyright.replace('\\n', '\n'))
        self.dlg.metadataConLicense.setText(
            self.mlicense.replace('\\n', '\n'))
        self.dlg.resourceConCopyright.setText(
            self.rcopyright.replace('\\n', '\n'))
        self.dlg.resourceConLicense.setText(
            self.rlicense.replace('\\n', '\n'))

    def autoFillLegalUndo(self):
        """
        Undo Clicked on the Legal Tab.
        Undo the actions of Auto fill. If the original values have been set,
        update the resource/ metadata
        constraints accordingly.
        :return: None.
        """
        if self.metaCC is not None:
            self.dlg.metadataConCopyright.setText(self.metaCC)
            self.dlg.metadataConLicense.setText(self.metaCL)
            self.dlg.resourceConCopyright.setText(self.resCC)
            self.dlg.resourceConLicense.setText(self.resCL)

    def autoFill(self, i):
        """
        Auto Fill Clicked on the Contact Tab.
        Auto fill (resource(1) or metadata(2) clicked.
        Copy fields existing in other contact to current contact.
        :param i: Which auto fill button clicked.
        :return: None.
        """
        try:
            self.dlg.autoFillError.hide()
            resource, metadata = {}, {}
            if i == 2:
                fillName, fromName = resource, metadata
                fillVal, fromVal = '1', '2'
            else:
                fillName, fromName = metadata, resource
                fillVal, fromVal = '2', '1'
            for i in self.dlg.contact:
                if '1' in i.objectName():
                    resource[i.objectName()] = i.currentText()
                else:
                    metadata[i.objectName()] = i.currentText()
            for val in fillName:
                text = fillName[val]
                for i in self.dlg.contact:
                    if i.objectName() in fromName and i.objectName().split(
                            fromVal)[0] == val.split(fillVal)[0]:
                        if i.findText(text) == -1:
                            i.addItem(text)
                        i.setCurrentIndex(i.findText(text))
        except Exception as e:
            self.dlg.autoFillError.setText("Auto Fill Error: " + str(e))
            self.dlg.autoFillError.show()

    def textStyle(self, i):
        """
        Text style button clicked, bold(1), italic(2), link(3).
        Add **selected text** around selected text if bold clicked.
        Add *selected text* around selected text if italic clicked.
        Add [selected text](LINK HERE) around selected text if link clicked.
        :param i: which style button clicked.
        :return: None.
        """
        textStyle = '**'
        try:
            if i == 1:
                textStyle = "**"
            if i == 2:
                textStyle = "*"
            cursor = self.dlg.abs.textCursor()
            textSelected = cursor.selectedText()
            selectStart = cursor.selectionStart()
            selectEnd = cursor.selectionEnd()
            if len(textSelected) > 1:
                if i == 3:
                    tS = "[" + textSelected + "](LINK HERE)"
                else:
                    tS = textStyle + textSelected + textStyle
            else:
                if i == 3:
                    tS = "[TEXT HERE](LINK HERE)"
                else:
                    tS = textStyle + "TEXT HERE" + textStyle
            if selectStart != 0:
                start = self.dlg.abs.toPlainText()[:selectStart]
            else:
                start = ""
            if selectEnd != len(self.dlg.abs.toPlainText()) - 1:
                end = self.dlg.abs.toPlainText()[selectEnd:]
            else:
                end = ""
            text = start + tS + end
            self.dlg.abs.setText(text)
            if i == 3:
                textStyle = 'LINK HERE)'
            else:
                textStyle = 'TEXT HERE' + textStyle
            if self.dlg.abs.toPlainText().find(textStyle) != -1:
                newStart = self.dlg.abs.toPlainText().find(textStyle)
                newEnd = newStart + 9
                cursor.setPosition(newStart)
                cursor.setPosition(newEnd, QTextCursor.KeepAnchor)
                self.dlg.abs.setTextCursor(cursor)
            elif i != 3:
                if i == 1:
                    move = 2
                else:
                    move = 1
                cursor.setPosition(selectStart + move)
                cursor.setPosition(selectEnd + move, QTextCursor.KeepAnchor)
                self.dlg.abs.setTextCursor(cursor)
        except Exception as e:
            print ("Text Style Error: " + str(e))

    def run(self):
        """
        Run Dialog and Show.
        :return:
        """
        self.dlg.show()
