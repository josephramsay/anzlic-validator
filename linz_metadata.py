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
from qgis.core import QgsRectangle, QgsCoordinateReferenceSystem
from PyQt4.QtCore import QSettings, QCoreApplication, QDate, QTime, Qt
from PyQt4.QtGui import QIcon, QAction, QFileDialog, QItemSelectionModel, \
     QTextCursor, QFont, QTableWidgetItem, QComboBox, QPalette, QColor
# Initialize Qt resources from file resources.py
import scripts.resources
# Import the code for the dialog
from linz_metadata_dialog import LINZ_MetadataDialog
from scripts.codeList import codeList
import os.path
from lxml import etree
import re
import os
import uuid
from shutil import copyfile
import yaml

import sys
sys.path.append('../')

from scripts.validate import Local, ValidatorException
from scripts.errorChecker import runChecks

# Set Namespaces
NSX = {'xlink'  : 'http://www.w3.org/1999/xlink',
       'gco'    : 'http://www.isotc211.org/2005/gco',
       'gmd'    : 'http://www.isotc211.org/2005/gmd',
       'gts'    : 'http://www.isotc211.org/2005/gts',
       'gml'    : 'http://www.opengis.net/gml/3.2'}

# Set Metadata Tags
MD = '/gmd:MD_Metadata'
CONTACT = MD + '/gmd:contact/gmd:CI_ResponsibleParty'
CINFO = CONTACT + '/gmd:contactInfo/gmd:CI_Contact'
PHONE = CINFO + '/gmd:phone/gmd:CI_Telephone'
ADDRESS = CINFO + '/gmd:address/gmd:CI_Address'
IDENT = MD + '/gmd:identificationInfo/gmd:MD_DataIdentification'
CITATION = IDENT + '/gmd:citation/gmd:CI_Citation'
POC = IDENT + '/gmd:pointOfContact/gmd:CI_ResponsibleParty'
POCINFO = POC + '/gmd:contactInfo/gmd:CI_Contact'
POCPHONE = POCINFO + '/gmd:phone/gmd:CI_Telephone'
POCADDRESS = POCINFO + '/gmd:address/gmd:CI_Address'
SECURITYCODE = '/gmd:MD_SecurityConstraints/gmd:classification/gmd:MD_' +      \
               'ClassificationCode'
USELIMIT = '/gmd:MD_LegalConstraints/gmd:useLimitation/gco:CharacterString'
USECONST = '/gmd:MD_LegalConstraints/gmd:useConstraints/gmd:MD_RestrictionCode'
DQ = MD + '/gmd:dataQualityInfo/gmd:DQ_DataQuality'
SC = DQ + '/gmd:scope/gmd:DQ_Scope'
EXTENT = IDENT + '/gmd:extent/gmd:EX_Extent'
EXTENTBB = EXTENT + '/gmd:geographicElement/gmd:EX_GeographicBoundingBox'

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
RS = MD + '/gmd:referenceSystemInfo/gmd:MD_ReferenceSystem/gmd:' +             \
     'referenceSystemIdentifier/gmd:RS_Identifier/gmd:code' + CS

TITLE = CITATION + '/gmd:title' + CS
ALTTITLE = CITATION + '/gmd:alternateTitle' + CS
CITDATE = CITATION + '/gmd:date/gmd:CI_Date/gmd:date' + DT
CITDATETYPE = CITATION + '/gmd:date/gmd:CI_Date/gmd:dateType' + CIDTC
ABSTRACT = IDENT + '/gmd:abstract' + CS
PURPOSE = IDENT + '/gmd:purpose' + CS
STATUS = IDENT + '/gmd:status' + MDPC

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

RMAINTCODE = IDENT+'/gmd:resourceMaintenance/gmd:MD_MaintenanceInformation/' + \
             'gmd:maintenanceAndUpdateFrequency' + MDMFC
RMAINTDATE = IDENT+'/gmd:resourceMaintenance/gmd:MD_MaintenanceInformation/' + \
             'gmd:dateOfNextUpdate' + DT
RFORMATN = IDENT + '/gmd:resourceFormat/gmd:MD_Format/gmd:name' + CS
RFORMATV = IDENT + '/gmd:resourceFormat/gmd:MD_Format/gmd:version' + CS

KEYWORDS = IDENT + '/gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:keyword' + CS
KEYWORDSTYPE = IDENT+'/gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:type' + MDKTC
CLASSIFCODE = IDENT + '/gmd:resourceConstraints' + SECURITYCODE
RESOURCELIMIT = IDENT + '/gmd:resourceConstraints' + USELIMIT
RESOURCEUSE = IDENT + '/gmd:resourceConstraints' + USECONST

SPATIALREP = IDENT + '/gmd:spatialRepresentationType/gmd:MD_Spatial' +         \
             'RepresentationTypeCode'
SCALE = IDENT+'/gmd:spatialResolution/gmd:MD_Resolution/gmd:equivalentScale' + \
        '/gmd:MD_RepresentativeFraction/gmd:denominator/gco:Integer'

RESOLUTION = IDENT+'/gmd:spatialResolution/gmd:MD_Resolution/gmd:distance/'  + \
             'gco:Distance'

IDENTLAN = IDENT + '/gmd:language' + CS
IDENTCS = IDENT + '/gmd:characterSet' + MDCSC

TOPIC = IDENT + '/gmd:topicCategory/gmd:MD_TopicCategoryCode'

EXTENTDES = EXTENT + '/gmd:geographicElement/gmd:EX_GeographicDescription/' +  \
            'gmd:geographicIdentifier/gmd:MD_Identifier/gmd:code' + CS

EXTENTBBW = EXTENTBB + '/gmd:westBoundLongitude' + DE
EXTENTBBE = EXTENTBB + '/gmd:eastBoundLongitude' + DE
EXTENTBBN = EXTENTBB + '/gmd:northBoundLatitude' + DE
EXTENTBBS = EXTENTBB + '/gmd:southBoundLatitude' + DE

TEMPORALSINGLE = EXTENT + '/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:'  + \
                 'extent/gml:TimeInstant/gml:timePosition'
TEMPORALBEGIN = EXTENT + '/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:'   + \
                'extent/gml:TimePeriod/gml:beginPosition'
TEMPORALEND = EXTENT + '/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:'     + \
              'extent/gml:TimePeriod/gml:endPosition'


LINKAGE = MD+'/gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions' + \
          '/gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource/' + \
          'gmd:linkage/gmd:URL'

SCOPE = SC + '/gmd:level' + MDSC
SCOPEDESC = SC + '/gmd:levelDescription/gmd:MD_ScopeDescription/gmd:other' + CS
LINEAGE = DQ + '/gmd:lineage/gmd:LI_Lineage/gmd:statement' + CS

MCLASSIFCODE = MD + '/gmd:metadataConstraints' + SECURITYCODE
METALIMIT = MD + '/gmd:metadataConstraints' + USELIMIT
METAUSE = MD + '/gmd:metadataConstraints' + USECONST

# FIELDS, all metadata fields
FIELDS = (FID, LAN, CHSET, HLEVEL, HLEVELNAME, INAME, ONAME, PNAME, VOICE, FACS,
          DELIVERYPOINT, CITY, POSTALCODE, COUNTRY, EMAIL, ROLE, DSTAMP,MSN,MSV,
          RS, TITLE, ALTTITLE, CITDATE, CITDATETYPE, ABSTRACT, PURPOSE, STATUS,
          POCINAME, POCONAME, POCPNAME, POCVOICE, POCFACS, POCDELIVERYPOINT,
          POCCITY, POCPOSTALCODE, POCCOUNTRY, POCEMAIL, POCROLE, RMAINTCODE,
          RMAINTDATE, RFORMATN, RFORMATV, KEYWORDS, KEYWORDSTYPE, CLASSIFCODE,
          RESOURCELIMIT, RESOURCEUSE, SPATIALREP, SCALE, RESOLUTION, IDENTLAN,
          IDENTCS, TOPIC, EXTENTDES, EXTENTBBW, EXTENTBBE, EXTENTBBN, EXTENTBBS,
          TEMPORALSINGLE, TEMPORALBEGIN, TEMPORALEND, LINKAGE, SCOPE, SCOPEDESC,
          LINEAGE, MCLASSIFCODE, METALIMIT, METAUSE)

# SETFIELDS, all metadata fields set in LINZ METADATA PLUGIN
SETFIELDS= (HLEVEL, HLEVELNAME, INAME, ONAME, PNAME, VOICE, FACS, DELIVERYPOINT,
            CITY, POSTALCODE, COUNTRY, EMAIL, ROLE, RS, TITLE, ALTTITLE,
            CITDATE, CITDATETYPE, ABSTRACT, PURPOSE, STATUS, POCINAME, POCONAME,
            POCPNAME, POCVOICE, POCFACS, POCDELIVERYPOINT, POCCITY,
            POCPOSTALCODE, POCCOUNTRY, POCEMAIL, POCROLE, RMAINTCODE,RMAINTDATE,
            KEYWORDS, KEYWORDSTYPE, CLASSIFCODE, RESOURCELIMIT, RESOURCEUSE,
            SPATIALREP, SCALE, RESOLUTION, TOPIC, EXTENTDES, TEMPORALSINGLE,
            TEMPORALBEGIN, TEMPORALEND, SCOPE, SCOPEDESC, LINEAGE, MCLASSIFCODE,
            METALIMIT, METAUSE)

TEMPLATEFID = 'C6BCE1F1-AFA7-42DB-B9CF-29C59333A173'

TEMPFILE = 'outputXML.xml'

class LINZ_Metadata:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.
        :param iface: An interface instance that will be passed to this class
            which provides the hook to manipulate the QGIS application at run
            time.
        :type iface: QgisInterface
        """
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'LINZ_Metadata_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        self.actions = []
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
        self.dlg = LINZ_MetadataDialog()
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
            self.iface.addPluginToMenu(
                self.menu,
                action)
        self.actions.append(action)
        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
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
        self.tF={POCPNAME           : self.dlg.pName1,
                 PNAME              : self.dlg.pName2,
                 POCFACS            : self.dlg.fas1,
                 FACS               : self.dlg.fas2,
                 TITLE              : self.dlg.title,
                 ALTTITLE           : self.dlg.atitle,
                 ABSTRACT           : self.dlg.abs,
                 PURPOSE            : self.dlg.purpose,
                 LINEAGE            : self.dlg.lineage}

        # Set Combo Fields
        self.cF={ROLE         : [self.dlg.role2, codeList('CI_RoleCode')],
                 POCROLE      : [self.dlg.role1, codeList('CI_RoleCode')],
                 HLEVEL       : [self.dlg.hlName, codeList('MD_ScopeCode')],
                 STATUS       : [self.dlg.status, codeList('MD_ProgressCode')],
                 RMAINTCODE   : [self.dlg.maintenance,
                                 codeList('MD_MaintenanceFrequencyCode')],
                 SPATIALREP   : [self.dlg.spatialrep,
                                 codeList('MD_SpatialRepresentationTypeCode')],
                 CLASSIFCODE  : [self.dlg.resSecClass,
                                 codeList('MD_ClassificationCode')],
                 MCLASSIFCODE : [self.dlg.metSecClass,
                                 codeList('MD_ClassificationCode')],
                 EXTENTDES    : [self.dlg.geoDescCombo,
                                 ('nzl', 'NZ_MAINLAND_AND_CHATHAMS')]}

        # COULD ADD FACS/ POCFACS
        self.cFS={VOICE       : self.dlg.voice2,
                  ONAME       : self.dlg.oName2,
                  INAME       : self.dlg.iName2,
                  POCVOICE    : self.dlg.voice1,
                  POCONAME    : self.dlg.oName1,
                  POCINAME    : self.dlg.iName1,
                  POCDELIVERYPOINT  : self.dlg.dadd1,
                  DELIVERYPOINT     : self.dlg.dadd2,
                  POCCITY           : self.dlg.city1,
                  CITY              : self.dlg.city2,
                  POCEMAIL          : self.dlg.email1,
                  EMAIL             : self.dlg.email2,
                  POCPOSTALCODE     : self.dlg.postCode1,
                  POSTALCODE        : self.dlg.postCode2,
                  POCCOUNTRY        : self.dlg.country1,
                  COUNTRY           : self.dlg.country2}
        
        # Set Resolution Code -> Units
        self.resolutionCode={
            'm'         :   'metre',
            'km'        :   'kilometre',
            'deg'       :   'degree',
            'ft'        :   'foot',
            'fath'      :   'fathom',
            'mile'      :   'mile',
            'nm'        :   'nautical mile',
            'yd'        :   'yard',
            'rad'       :   'radian',
            'u'         :   'unknown'}

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

        self.dlg.temporalCheck.stateChanged.connect(self.toggleTemporal)
        self.dlg.startTimeCheck.stateChanged.connect(self.toggleStartTime)
        self.dlg.endDateCheck.stateChanged.connect(self.toggleEndDate)
        self.dlg.endTimeCheck.stateChanged.connect(self.toggleEndTime)

        self.dlg.resourceCreateCheck.stateChanged.connect(self.toggleCreateDate)
        self.dlg.resourcePublishCheck.stateChanged.connect(self.togglePublishDate)
        self.dlg.resourceUpdateCheck.stateChanged.connect(self.toggleUpdateDate)

        # Create Metadata Clicked
        self.dlg.createMetadata.clicked.connect(self.done)
        # Validate/ Error Check Clicked 
        self.dlg.validateErrorCheck.clicked.connect(self.check)

        self.dlg.autofillResource.clicked.connect(lambda: self.autoFill(1))
        self.dlg.autofillMetadata.clicked.connect(lambda: self.autoFill(2))

        self.dlg.boldText.clicked.connect(lambda: self.textStyle(1))
        self.dlg.italicText.clicked.connect(lambda: self.textStyle(2))
        self.dlg.linkText.clicked.connect(lambda: self.textStyle(3))

        self.dlg.fixError.clicked.connect(self.fixError)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(u'&LINZ Metadata'), action)
            self.iface.removeToolBarIcon(action)
        del self.toolbar

    def loadMetadata(self, button):
        ''' load metadata template or existing metadata file
            into associated fields.'''
        try:
            self.resolutionUnits = None
            lice, copy, metlice, metcopy, meta, res = None,None,None,None,None,None
            crsList = {'NZGD2000/New Zealand Transverse Mercator 2000'  : 2193,
                       'WGS 84'                                         : 4326}
            topicCategoryValues = codeList('MD_TopicCategoryCode')
            self.MDTEXT = {}
            if button == 1:
                if self.dlg.templateFile.toPlainText() == '' or \
                   self.dlg.outputFile.toPlainText() == '':
                    raise Exception("Metadata Load Error, No File Selected")
                self.dlg.changeTemplate(self.dlg.templateFile.toPlainText())
                self.dlg.OUTPUTFILE = self.dlg.outputFile.toPlainText()
            elif button == 2:
                if self.dlg.metadataFile.toPlainText() == '':
                    raise Exception("Metadata Load Error, No File Selected")
                self.dlg.changeTemplate(self.dlg.metadataFile.toPlainText())
                self.dlg.OUTPUTFILE = self.dlg.metadataFile.toPlainText()
            try:
                md = etree.parse(os.path.abspath(os.path.join(os.path.dirname(__file__),self.dlg.TEMPLATEPATH)))
            except Exception as e:
                raise Exception("Metadata Load Error: {}".format(e))
            file = r'{}/config.yaml'.format(os.path.abspath(os.path.join(__file__, '../')))
            if not os.path.exists(file):
                raise Exception("Cannot Find Config File {}".format(file))
            with open(file, 'r') as f:
                config = yaml.load(f)
            if 'Metadata' not in md.getroot().tag:
                raise Exception('Metadata Load Error, not ISO Metadata')
            
            self.dlg.reset_form()
            self.dlg.referenceSys.setCrs(QgsCoordinateReferenceSystem())
            # Read through metadata file and set path, text in MDTEXT
            for m in md.iter():
                if m.text:
                    key = re.sub('\[+.+?\]', '', md.getpath(m))
                    if key in self.MDTEXT:
                        if type(self.MDTEXT[key]) == tuple:
                            self.MDTEXT[key] = self.MDTEXT[key] + (m.text,)
                        else: self.MDTEXT[key] = (self.MDTEXT[key], m.text)
                    else:
                        self.MDTEXT[key] = m.text

            # Add Topic Category Selection Values to UI List.
            for val in topicCategoryValues:
                self.dlg.topicCategory.addItem(val.strip())
            self.dlg.topicCategory.sortItems()

            configDict = {VOICE     : 'VOICE1',
                          POCVOICE  : 'VOICE2',
                          ONAME     : 'ORGANISATIONNAME1',
                          POCONAME  : 'ORGANISATIONNAME2',
                          INAME     : 'INDIVIDUALNAME1',
                          POCINAME  : 'INDIVIDUALNAME2',
                          DELIVERYPOINT     : 'DELIVERYADDRESS1',
                          POCDELIVERYPOINT  : 'DELIVERYADDRESS2',
                          CITY              : 'CITY1',
                          POCCITY           : 'CITY2',
                          POSTALCODE        : 'POSTALCODE1',
                          POCPOSTALCODE     : 'POSTALCODE2',
                          COUNTRY           : 'COUNTRY1',
                          POCCOUNTRY        : 'COUNTRY2',
                          EMAIL             : 'EMAIL1',
                          POCEMAIL          : 'EMAIL2'}
            
            for i in FIELDS:
                if i in self.cFS:
                    if i in configDict:
                        self.cFS[i].addItem('')
                        if type(config[configDict[i]]) == list:
                            self.cFS[i].addItems(config[configDict[i]])
                            for v in range(self.cFS[i].count()):
                                if self.cFS[i].itemText(v) == 'NONE' or self.cFS[i].itemText(v) == 'EMPTY':
                                    self.cFS[i].removeItem(v)
                        elif type(config[configDict[i]]) == str:
                            self.cFS[i].addItem(config[configDict[i]])
                        else:
                            print ("TRUE/ FALSE VALUE {}, needs set enabled/text entered".format(configDict[i]))


            # Add Combo Box Selection Values to UI Combo Fields.
            for i in FIELDS:
                if i in self.cF:
                    self.cF[i][0].addItem('')
                    self.cF[i][0].addItems(self.cF[i][1])

            # Update UI Fields based on fields found in Metadata
            for i in FIELDS:
                if i in self.MDTEXT:
                    # Update Scale Fields
                    if i == SCALE:
                        self.dlg.scale.setChecked(True)
                        self.dlg.scaleRadioButton.setChecked(True)
                        if ':' in self.MDTEXT[i]:
                            self.MDTEXT[i] = self.MDTEXT[i].split(':')[1]
                        self.dlg.scaleWidget.setScaleString("1:" + self.MDTEXT[i])

                    elif i == TEMPORALSINGLE or \
                         i == TEMPORALBEGIN  or \
                         i == TEMPORALEND:
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
                        if M is None: M = 1
                        if d is None: d = 1
                        date = QDate(int(y), int(M), int(d))
                        if i == TEMPORALSINGLE or i == TEMPORALBEGIN:
                            self.dlg.startDate.setDate(date)
                        else:
                            self.dlg.endDateCheck.setChecked(True)
                            self.dlg.endDate.setDate(date)
                        if time is not None:
                            if m is None: m = 1
                            if s is None: s = 0
                            time = QTime(int(h), int(m), int(s))
                            if i == TEMPORALSINGLE or i == TEMPORALBEGIN:
                                self.dlg.startTimeCheck.setChecked(True)
                                self.dlg.startTime.setTime(time)
                            if i == TEMPORALEND:
                                self.dlg.endTimeCheck.setChecked(True)
                                self.dlg.endTime.setTime(time)

                    elif i == KEYWORDS:
                        if type(self.MDTEXT[i]) == tuple:
                            selection = ()
                            for val in self.MDTEXT[i]:
                                val = val.replace('-', ' ')
                                if 'non specific' in val:
                                    val = val.replace('non specific', 'non-specific')
                                if val[1].isupper():
                                    found = self.dlg.keywordList.findItems(
                                        val, Qt.MatchExactly)
                                    if len(found) > 0:
                                        self.dlg.keywordList.setCurrentRow(
                                            self.dlg.keywordList.row(found[0]),
                                            QItemSelectionModel.Select)
                                    else:
                                        print ("WARNING: Invalid Keyword Ignored "+\
                                               "{}".format(val))
                        else:
                            if self.MDTEXT[i][1].isupper():
                                found = self.dlg.keywordList.findItems(
                                    val, Qt.MatchExactly)
                                if len(found) > 0:
                                    self.dlg.keywordList.setCurrentRow(
                                        self.dlg.keywordList.row(found[0]),
                                        QItemSelectionModel.Select)
                                else:
                                    print ("WARNING: Invalid Keyword Ignored "   + \
                                           "{}".format(val))

                    # Update Resolution Fields
                    elif i == RESOLUTION:
                        ms = md.find(RESOLUTION[16:], namespaces=NSX).attrib['uom']
                        self.dlg.scale.setChecked(True)
                        self.dlg.resolutionRadioButton.setChecked(True)
                        self.dlg.resolutionText.setText(self.MDTEXT[i])
                        self.dlg.resolutionUnits.setCurrentIndex(
                            self.dlg.resolutionUnits.findText(
                                self.resolutionCode[ms]))

                    elif i == CITDATE:
                        dates = {'creation'   : (self.dlg.resourceCreate,
                                                 self.dlg.resourceCreateCheck),
                                 'publication': (self.dlg.resourcePublish,
                                                 self.dlg.resourcePublishCheck),
                                 'revision'   : (self.dlg.resourceUpdate,
                                                 self.dlg.resourceUpdateCheck)}
                        if type(self.MDTEXT[i]) == tuple:
                            for num, el in enumerate(self.MDTEXT[i]):
                                dt = el.split('-')
                                if len(dt) == 1: dt = (dt[0], 1, 1)
                                elif len(dt) == 2: dt = (dt[0], dt[1], 1)
                                dates[self.MDTEXT[CITDATETYPE][num]][0].setEnabled(
                                    True)
                                dates[self.MDTEXT[CITDATETYPE][num]][0].setDate(
                                    QDate(int(dt[0]), int(dt[1]), int(dt[2])))
                                dates[self.MDTEXT[CITDATETYPE][num]][1].setChecked(
                                    True)
                        else:
                            dt = self.MDTEXT[i].split('-')
                            if len(dt) == 1: dt = (dt[0], 1, 1)
                            elif len(dt) == 2: dt = (dt[0], dt[1], 1)
                            dates[self.MDTEXT[CITDATETYPE]][0].setEnabled(True)
                            dates[self.MDTEXT[CITDATETYPE]][0].setDate(
                                QDate(int(dt[0]), int(dt[1]), int(dt[2])))
                            dates[self.MDTEXT[CITDATETYPE]][1].setChecked(True)

                    # Update Reference System Fields
                    elif i == RS:
                        if self.MDTEXT[i].isdigit():
                            crs = QgsCoordinateReferenceSystem(int(self.MDTEXT[i]))
                            self.dlg.referenceSys.setCrs(crs)
                        elif 'urn:ogc:def:crs:EPSG::' in self.MDTEXT[i]:
                            crs = QgsCoordinateReferenceSystem(
                                int(self.MDTEXT[i].split(
                                    'urn:ogc:def:crs:EPSG::')[1]))
                            self.dlg.referenceSys.setCrs(crs)
                        elif 'EPSG::' in self.MDTEXT[i]:
                            crs = QgsCoordinateReferenceSystem(
                                int(self.MDTEXT[i].split('EPSG::')[1]))
                            self.dlg.referenceSys.setCrs(crs)
                        else:
                            if self.MDTEXT[i] in crsList:
                                crs = QgsCoordinateReferenceSystem(
                                    crsList[self.MDTEXT[i]])
                                self.dlg.referenceSys.setCrs(crs)
                            
                            else:
                                print ("WARNING unknown CRS", self.MDTEXT[i])
                        

                    elif i in RMAINTDATE:
                        if self.MDTEXT[i] != '':
                            dt, val, d = ['year', 'month', 'day'], 0, ()
                            while val < len(self.MDTEXT[i].split('-')):
                                dt[val] = (dt[val], self.MDTEXT[i].split('-')[val])
                                val += 1
                            for val in dt:
                                if type(val) == tuple: d += (int(val[1]),)
                                else: d += (01,)
                            self.dlg.date.setDate(QDate(d[0], d[1], d[2]))
                            self.dlg.dONUCheck.setChecked(True)
                            self.dlg.date.setEnabled(True)

                    # Update All Other Text Fields
                    elif i in self.tF:
                        # Select Only First Value If Multiple
                        # - Should only be one if correct.
                        if type(self.MDTEXT[i]) == tuple:
                            print ("WARNING found {} for {}, only using {}".
                                   format(self.MDTEXT[i], i, self.MDTEXT[i][0]))
                            self.tF[i].setText(self.MDTEXT[i][0])
                        else:
                            self.tF[i].setText(self.MDTEXT[i])
                            
                    elif i in self.cFS:
                        if type(self.MDTEXT[i]) == tuple:
                            print ("WARNING FOUND {} for {}, only using {}".
                                   format(self.MDTEXT[i], i, self.MDTEXT[i][0]))
                            val = self.MDTEXT[i][0]
                        else:
                            val = self.MDTEXT[i]
                        found = False
                        for l in range(self.cFS[i].count()):
                            if self.cFS[i].itemText(l) == val:
                                found = True
                                self.cFS[i].setCurrentIndex(l)
                        if not found:
                            self.cFS[i].setCurrentIndex(0)

                    # Update All Other Combo Fields
                    elif i in self.cF:
                        if type(self.MDTEXT[i]) == tuple:
                            # Select Only First Value If Multiple
                            # - Should only be one if correct.
                            print ("WARNING found {} for {}, only using {}".
                                   format(self.MDTEXT[i], i, self.MDTEXT[i][0]))
                            self.cF[i][0].setCurrentIndex(
                                self.cF[i][0].findText(self.MDTEXT[i][0]))
                        else:
                            self.cF[i][0].setCurrentIndex(
                                self.cF[i][0].findText(self.MDTEXT[i]))

                    # Else if is Topic Category or Resource or Bounding Box Value(s)
                    else:
                        if type(self.MDTEXT[i]) == tuple:
                            if i == TOPIC:
                                for item in self.MDTEXT[i]:
                                    found = self.dlg.topicCategory.findItems(
                                        item.strip(), Qt.MatchExactly)
                                    if len(found) > 0:
                                        self.dlg.topicCategory.setCurrentRow(
                                            self.dlg.topicCategory.row(found[0]),
                                            QItemSelectionModel.Select)
                            elif i == RESOURCELIMIT: res = self.MDTEXT[i]
                            elif i == RESOURCEUSE:
                                for k, val in enumerate(self.MDTEXT[i]):
                                    if val == 'copyright': copy = k
                                    elif val == 'license': lice = k
                            elif i == METALIMIT: meta = self.MDTEXT[i]
                            elif i == METAUSE:
                                for k, val in enumerate(self.MDTEXT[i]):
                                    if val == 'copyright': metcopy = k
                                    elif val == 'license': metlice = k
                        else:
                            if i == TOPIC:
                                item = self.MDTEXT[i]
                                found = self.dlg.topicCategory.findItems(
                                    item.strip(), Qt.MatchExactly)
                                if len(found) > 0:
                                    self.dlg.topicCategory.setCurrentRow(
                                        self.dlg.topicCategory.row(found[0]),
                                        QItemSelectionModel.Select)
                            elif i == RESOURCELIMIT: res = (self.MDTEXT[i],)
                            elif i == RESOURCEUSE:
                                if self.MDTEXT[i] == 'copyright': copy = 0
                                elif self.MDTEXT[i] == 'license': lice = 0
                            elif i == METALIMIT: meta = (self.MDTEXT[i],)
                            elif i == METAUSE:
                                if self.MDTEXT[i] == 'copyright': metcopy = 0
                                elif self.MDTEXT[i] == 'license': metlice = 0
                            elif i == EXTENTBBE:
                                self.dlg.eastExtent.setText(self.MDTEXT[EXTENTBBE])
                            elif i == EXTENTBBW:
                                self.dlg.westExtent.setText(self.MDTEXT[EXTENTBBW])
                            elif i == EXTENTBBS:
                                self.dlg.southExtent.setText(self.MDTEXT[EXTENTBBS])
                            elif i == EXTENTBBN:
                                self.dlg.northExtent.setText(self.MDTEXT[EXTENTBBN])

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
        fname = self.dlg.TEMPLATEPATH[self.dlg.TEMPLATEPATH.rfind('/')+1:]
        self.dlg.setWindowTitle("LINZ ANZLIC METADATA - " + fname)
        self.dlg.setCurrentIndex(1)
        for i in range(self.dlg.count()): self.dlg.setTabEnabled(i, True)

    def formatSummary(self, tree):
        ''' Write fields to the formatted summary tab.
            tree: updated xml tree.
        '''
        general= (FID, LAN, CHSET, HLEVEL, DSTAMP, MSN, MSV, RFORMATN, RFORMATV)
        metadataAddress= (INAME, ONAME, PNAME, VOICE, FACS, DELIVERYPOINT, CITY,
                          POSTALCODE, COUNTRY, EMAIL, ROLE)
        resourceAddress= (POCINAME, POCONAME, POCPNAME, POCVOICE, POCFACS,
                          POCDELIVERYPOINT, POCCITY, POCPOSTALCODE, POCCOUNTRY,
                          POCEMAIL, POCROLE)
        resourceFields = (TITLE, ALTTITLE, ABSTRACT, PURPOSE, CITDATE,
                          CITDATETYPE, LINEAGE, LINKAGE, KEYWORDS, TOPIC)
        systemInfo = (RS, STATUS, RMAINTCODE, RMAINTDATE, SPATIALREP, SCALE,
                      RESOLUTION, EXTENTDES, EXTENTBBW, EXTENTBBE, EXTENTBBN,
                      EXTENTBBS, TEMPORALSINGLE, TEMPORALBEGIN, TEMPORALEND)
        rconstraints = (CLASSIFCODE, RESOURCELIMIT, RESOURCEUSE)
        mconstraints = (MCLASSIFCODE, METALIMIT, METAUSE)
        gen, mA, rA, rF, sI, rcon, mcon = (), (), (), (), (), (), ()
        j, k, values = 0, 0, 0

        # Iterate through tree getting text and text 'title'
        for el in tree.iter():
            if el.text is not None:
                t1 = el.getparent().tag[el.getparent().tag.rfind('}')+1:]
                t2 = el.text
                if re.sub('\[+.+?\]', '', tree.getpath(el)) in general:
                    gen += ([re.sub('([A-Z])', r' \1', t1).title(), t2],)
                elif re.sub('\[+.+?\]', '',tree.getpath(el)) in metadataAddress:
                    mA += ([re.sub('([A-Z])', r' \1', t1).title(), t2],)
                elif re.sub('\[+.+?\]', '',tree.getpath(el)) in resourceAddress:
                    rA += ([re.sub('([A-Z])', r' \1', t1).title(), t2],)
                elif re.sub('\[+.+?\]', '', tree.getpath(el)) in resourceFields:
                    rF += ([re.sub('([A-Z])', r' \1', t1).title(), t2],)
                elif re.sub('\[+.+?\]', '', tree.getpath(el)) in systemInfo:
                    sI += ([re.sub('([A-Z])', r' \1', t1).title(), t2],)
                elif re.sub('\[+.+?\]', '', tree.getpath(el)) in rconstraints:
                    rcon += ([re.sub('([A-Z])', r' \1', t1).title(), t2],)
                elif re.sub('\[+.+?\]', '', tree.getpath(el)) in mconstraints:
                    mcon += ([re.sub('([A-Z])', r' \1', t1).title(), t2],)

        # Set default values for formatted table
        vals = ('General', gen, 'Metadata Address', mA, 'Resource Address', rA,
                'Resource Fields', rF, 'System Info', sI, 'Resource Constraints',
                rcon, 'Metadata Constraints', mcon)
        for i in vals:
            if type(i) == str: j += 1
            else: j += len(i)
        for i in vals:
            for w in i:
                if w[0] == 'Date Type':
                    j -= 1
                elif w[0] == 'West Bound Longitude':
                    j += 1
                elif w[0] == 'Use Constraints':
                    j -= 1
        self.dlg.metadataTable.setColumnCount(2)
        self.dlg.metadataTable.setRowCount(j)
        self.dlg.metadataTable.setColumnWidth(0, 210)
        self.dlg.metadataTable.setWordWrap(True)
        font = QFont('Noto Sans', 14, weight=QFont.Bold, italic=True)
        boundingBox = ('East Bound Longitude', 'West Bound Longitude',
                       'South Bound Latitude', 'North Bound Latitude')
        # Update formatted table to include text and text 'title' values.
        while values < len(vals):
            if type(vals[values]) == str:
                self.dlg.metadataTable.setItem(
                    k, 0, QTableWidgetItem(vals[values]))
                self.dlg.metadataTable.item(k, 0).setFont(font)
                k += 1
            else:
                for num, i in enumerate(vals[values]):
                    add, item0, item1 = False, i[0], i[1]
                    if i[0] == 'Date':
                        add = True
                        item0 += ' - ' + vals[values][num+1][1].title()
                    elif i[0] == 'Code' and i[1].isdigit():
                        add, item0 = True, 'Reference System'
                        item1 += ' - '+self.dlg.referenceSys.crs().description()
                    elif i[0] == 'Code':
                        add, item0 = True, 'Extent Description'
                    elif i[0] in boundingBox:
                        add, item0 = True, '      ' + i[0] 
                        if i[0] == 'West Bound Longitude':
                            self.dlg.metadataTable.setItem(
                                k, 0, QTableWidgetItem('Extent Bounding Box'))
                            k += 1
                    elif i[0] == 'Classification':
                        add, item0 = True, 'Security Classification'
                    elif i[0] == 'Use Limitation':
                        add = True
                        item0 += ' - ' + vals[values][num+1][1].title()
                    elif i[0] != 'Date Type' and i[0] != 'Use Constraints':
                        add = True
                    if add:
                        self.dlg.metadataTable.setItem(
                            k, 1, QTableWidgetItem(item1))
                        self.dlg.metadataTable.setItem(
                            k, 0, QTableWidgetItem(item0))
                        k += 1
            values += 1
        self.dlg.metadataTable.resizeRowsToContents()

    def write(self, i, tree, text, many=None, constraint=None):
        ''' write text value to the xml tree, tree.
            i: xml path to the text to be inserted
            tree: tree for text to be inserted
            text: text to be inserted into tree
            many: xml path to be inserted if many fields allowed and full path
                  already exists
            constraint: constraint 'license' or 'copyright'
        '''
        base = ''
        found = None
        codeUrl = 'http://standards.iso.org/ittf/PubliclyAvailableStandards' + \
                  '/ISO_19139_Schemas/resources/Codelist/gmxCodelists.xml#'
        
        if text[0] == '[' and text[len(text)-1] == ']':
            # Is a template field, so don't add.
            return tree

        # Find tag that exists in the tree already. (Found)
        for val in i[17:].split('/'):
            if tree.find(base + val, namespaces=NSX) is not None:
                found = base+val
            base += (val+'/')

        # If none of the tag can be found in the tree, insert from the
        # root, else insert from the point found.
        if found is None:
            found = base[:len(base)-1]
            insert = found
            f = tree.getroot()
        else:
            insert = (i[17:].split(found)[1][1:])
            f = tree.find(found, namespaces=NSX)
            
        if insert == "" and many is not None or                          \
           many is not None and 'extent' in i and 'Bounding' not in i or \
           many is not None and 'extent' in i and 'west' in i:
            if many == tree.getroot():
                insert = found
                f = tree.getroot()
            else:
                insert = base.split(many)[1].lstrip('/').rstrip('/')
                f = tree.find(many, namespaces=NSX)

        # Add elements to be inserted to the xml tree one by one.
        # If is a use Limitation add restriction and use constraints, else if
        # is not a 'gco' field add codelist values.
        for k in insert.split('/'):
            j = (k.split(':'))
            element= etree.SubElement(f, etree.QName(NSX[str(j[0])], str(j[1])))
            f = element
            if constraint is not None and j[1] == 'useLimitation':
                sib = etree.Element(etree.QName(NSX['gmd'], 'useConstraints'))
                code = etree.SubElement(
                    sib, etree.QName(NSX['gmd'], 'MD_RestrictionCode'))
                code.attrib['codeList'] = codeUrl + 'MD_RestrictionCode'
                code.attrib['codeListValue'] = constraint
                code.text = constraint
                f.addnext(sib)
        if 'gco' not in f.tag and 'URL' not in f.tag and 'Position' not in f.tag and 'Topic' not in f.tag:
            f.attrib['codeList'] = codeUrl + f.tag[f.tag.rfind('}')+1:]
            f.attrib['codeListValue'] = text
        f.text = text
        return tree

    def writeXML(self):
        ''' Iterate through fields and set them in xml tree from UI fields.
        '''
        try:
            md = etree.Element('{http://www.isotc211.org/2005/gmd}MD_Metadata',
                               nsmap=NSX)
            tree = etree.ElementTree(md)

            for i in FIELDS:
                if i == FID and self.dlg.outputFile.toPlainText() != '':
                    tree = self.write(i, tree, str(uuid.uuid4()))
                elif i == DSTAMP and self.dlg.outputFile.toPlainText() != '':
                    date = QDate.currentDate().toString('yyyy-MM-dd')
                    tree = self.write(i, tree, date,'gmd:identificationInfo/gmd' + \
                                      ':MD_DataIdentification')
                elif i == SCALE                 and \
                   self.dlg.scale.isChecked() and \
                   self.dlg.scaleRadioButton.isChecked():
                    tree = self.write(
                        i,tree,self.dlg.scaleWidget.scaleString().replace(',', '').split('1:')[1])

                # Update Resolution Fields
                elif i == RESOLUTION            and \
                     self.dlg.scale.isChecked() and \
                     self.dlg.resolutionRadioButton.isChecked():
                    tree=self.write(i, tree, self.dlg.resolutionText.toPlainText())
                    for i in self.resolutionCode:
                        if self.resolutionCode[i] == \
                           self.dlg.resolutionUnits.currentText():
                            res = tree.find(RESOLUTION[16:], namespaces=NSX)
                            res.attrib['uom'] = i

                # Update Reference System Field
                elif i == RS and self.dlg.referenceSys.crs().authid() !=  "":
                    tree = self.write(
                        i, tree, self.dlg.referenceSys.crs().authid().split(':')[1])

                # Update Text Fields
                elif i in self.tF and self.tF[i].toPlainText() != '':
                    tree = self.write(i, tree, self.tF[i].toPlainText())

                elif i in self.cFS and self.cFS[i].currentText() != '':
                    tree = self.write(i, tree, self.cFS[i].currentText())

                # Update Combo Fields
                elif i in self.cF and self.cF[i][0].currentText() != '':
                    if 'extent' in i:
                        tree = self.write(i, tree, self.cF[i][0].currentText(), 'gmd:identificationInfo/gmd:MD_DataIdentification')
                        auth = etree.Element(etree.QName(NSX['gmd'], 'authority'))
                        ci = etree.SubElement(auth, etree.QName(NSX['gmd'], 'CI_Citation'))
                        ti = etree.SubElement(ci, etree.QName(NSX['gmd'], 'Title'))
                        cs = etree.SubElement(ti, etree.QName(NSX['gco'], 'CharacterString'))
                        cs.text = 'ANZLIC Geographic Extent Name Register'
                        dt = etree.SubElement(ci, etree.QName(NSX['gmd'], 'date'))
                        cidt = etree.SubElement(dt, etree.QName(NSX['gmd'], 'CI_Date'))
                        dt2 = etree.SubElement(cidt, etree.QName(NSX['gmd'], 'date'))
                        Dt = etree.SubElement(dt2, etree.QName(NSX['gco'], 'Date'))
                        Dt.text = '2006-10-10'
                        dttp = etree.SubElement(cidt, etree.QName(NSX['gmd'], 'dateType'))
                        cidttp = etree.SubElement(dttp, etree.QName(NSX['gmd'], 'CI_DateTypeCode'))
                        cidttp.text = 'publication'
                        cidttp.attrib['codeList'] = 'http://standards.iso.org/ittf/PubliclyAvailableStandards/ISO_19139_Schemas/resources/Codelist/gmxCodelists.xml#CI_DateTypeCode'
                        cidttp.attrib['codeListValue'] = 'publication'
                        ed = etree.SubElement(ci, etree.QName(NSX['gmd'], 'edition'))
                        cs = etree.SubElement(ed, etree.QName(NSX['gco'], 'CharacterString'))
                        cs.text = 'Version 2'
                        edDt = etree.SubElement(ci, etree.QName(NSX['gmd'], 'editionDate'))
                        Dt = etree.SubElement(edDt, etree.QName(NSX['gco'], 'Date'))
                        Dt.text = '2001-02'
                        ide = etree.SubElement(ci, etree.QName(NSX['gmd'], 'identifier'))
                        mdId = etree.SubElement(ide, etree.QName(NSX['gmd'], 'MD_Identifer'))
                        cde = etree.SubElement(mdId, etree.QName(NSX['gmd'], 'code'))
                        cs = etree.SubElement(cde, etree.QName(NSX['gco'], 'CharacterString'))
                        cs.text = 'http://asdd.ga.gov.au/asdd/profileinfo/anzlic-allgens.xml#new_zealand'
                        cRP = etree.SubElement(ci, etree.QName(NSX['gmd'], 'citedResponsibleParty'))
                        org = etree.SubElement(cRP, etree.QName(NSX['gmd'], 'organisationName'))
                        cs = etree.SubElement(org, etree.QName(NSX['gco'], 'CharacterString'))
                        cs.text = 'ANZLIC the Spatial Information Council'
                        rle = etree.SubElement(cRP, etree.QName(NSX['gmd'], 'role'))
                        cirlc = etree.SubElement(rle, etree.QName(NSX['gmd'], 'CI_RoleCode'))
                        cirlc.text = 'custodian'
                        cirlc.attrib['codeList'] = 'http://standards.iso.org/ittf/PubliclyAvailableStandards/ISO_19139_Schemas/resources/Codelist/gmxCodelists.xml#CI_RoleCode'
                        cirlc.attrib['codeListValue'] = 'custodian'
                        mdid = tree.find(i[17:], namespaces=NSX)
                        mdid.getparent().addprevious(auth)
                    else:
                        tree = self.write(i, tree, self.cF[i][0].currentText())

                # Update Hierarchy Level Name, based on Hierarchy Level
                elif i == HLEVELNAME and self.cF[HLEVEL][0].currentText() != '':
                    tree = self.write(i, tree, self.cF[HLEVEL][0].currentText())

                # Update Scope based on Hierarchy Level
                elif i == SCOPE and self.cF[HLEVEL][0].currentText() != '':
                    tree = self.write(i, tree, self.cF[HLEVEL][0].currentText())

                # Update Scope Description based on Hierarchy Level
                elif i == SCOPEDESC and self.cF[HLEVEL][0].currentText() != '':
                    tree = self.write(i, tree, self.cF[HLEVEL][0].currentText())

                # Update Topic Category(s)
                elif i == TOPIC:
                    for j in self.dlg.topicCategory.selectedItems():
                        tree = self.write(
                            i, tree, j.text(),
                            'gmd:identificationInfo/gmd:MD_DataIdentification')

                elif i == RMAINTDATE:
                    if self.dlg.date.isEnabled() == True:
                        date = self.dlg.date.date().toString('yyyy-MM')
                        tree = self.write(i, tree, date)

                # Update Resource Constraints
                elif i == RESOURCELIMIT:
                    if self.dlg.resourceConLicense.toPlainText() != '':
                        tree = self.write(i, tree,
                                          self.dlg.resourceConLicense.toPlainText(),
                                          'gmd:identificationInfo/gmd:MD_' + \
                                          'DataIdentification/gmd:resourceConstraints',constraint='license')
                    if self.dlg.resourceConCopyright.toPlainText() != '':
                        tree=self.write(i, tree,
                                        self.dlg.resourceConCopyright.toPlainText(),
                                        'gmd:identificationInfo/gmd:MD_' + \
                                        'DataIdentification/gmd:resourceConstraints',constraint='copyright')

                # Update Metadata Constraints
                elif i == METALIMIT:
                    if self.dlg.metadataConLicense.toPlainText() != '':
                        tree = self.write(i, tree,
                                          self.dlg.metadataConLicense.toPlainText(),
                                          'gmd:metadataConstraints', constraint='license')
                    if self.dlg.metadataConCopyright.toPlainText() != '':
                        tree=self.write(i, tree,
                                        self.dlg.metadataConCopyright.toPlainText(),
                                        'gmd:metadataConstraints', constraint='copyright')

                elif i == TEMPORALSINGLE or i == TEMPORALBEGIN:
                    if i == TEMPORALSINGLE and not \
                       self.dlg.endDateCheck.isChecked() or \
                       i == TEMPORALBEGIN and self.dlg.endDateCheck.isChecked():
                        if self.dlg.temporalCheck.isChecked():
                            date = self.dlg.startDate.date().toString('yyyy-MM-dd')
                            if self.dlg.startTimeCheck.isChecked():
                                date += 'T' + self.dlg.startTime.time().toString(
                                    'hh:mm:ss')
                            tree = self.write(i, tree, date, 'gmd:identification'+ \
                                              'Info/gmd:MD_DataIdentification')
                elif i == TEMPORALEND:
                    if self.dlg.temporalCheck.isChecked() and \
                       self.dlg.endDateCheck.isChecked():
                        date = self.dlg.endDate.date().toString('yyyy-MM-dd')
                        if self.dlg.endTimeCheck.isChecked():
                            date += 'T' + self.dlg.endTime.time().toString(
                                'hh:mm:ss')
                        tree = self.write(i, tree, date, 'gmd:identificationInfo/'+\
                                          'gmd:MD_DataIdentification/gmd:extent/' +\
                                          'gmd:EX_Extent/gmd:temporalElement/gmd' +\
                                          ':EX_TemporalExtent/gmd:extent/gml:'    +\
                                          'TimePeriod')

                elif i == KEYWORDS or i == KEYWORDSTYPE:
                    if i == KEYWORDS:
                        keywordUrl = 'http://standards.iso.org/ittf/Publicly'    + \
                                     'AvailableStandards/ISO_19139_Schemas/'     + \
                                     'resources/Codelist/gmxCodelists.xml#MD'    + \
                                     '_KeywordTypeCode'
                        tree = self.write(i, tree, 'New Zealand', 'gmd:'         + \
                                          'identificationInfo/gmd:MD_Data'       + \
                                          'Identification/gmd:descriptiveKeywords'+\
                                          '/gmd:MD_Keywords')
                        
                        kt = etree.Element(etree.QName(NSX['gmd'], 'type'))
                        ktc= etree.SubElement(kt, etree.QName(NSX['gmd'],
                                                              'MD_KeywordTypeCode'))
                        ktc.attrib['codeList'] = keywordUrl
                        ktc.attrib['codeListValue'] = 'theme'
                        h = tree.find(i[17:], namespaces=NSX)
                        h.getparent().addnext(kt)
                        
                        tName = etree.Element(etree.QName(NSX['gmd'], 'thesaurusName'))
                        ciCit = etree.SubElement(tName, etree.QName(NSX['gmd'], 'CI_Citation'))
                        ti = etree.SubElement(ciCit, etree.QName(NSX['gmd'], 'title'))
                        cs = etree.SubElement(ti, etree.QName(NSX['gco'], 'CharacterString'))
                        cs.text = 'ANZLIC Jurisdictions'
                        dte = etree.SubElement(ciCit, etree.QName(NSX['gmd'], 'date'))
                        cidte = etree.SubElement(dte, etree.QName(NSX['gmd'], 'CI_Date'))
                        dte2 = etree.SubElement(cidte, etree.QName(NSX['gmd'], 'date'))
                        Dte = etree.SubElement(dte2, etree.QName(NSX['gco'], 'Date'))
                        Dte.text = '2008-10-29'
                        dtetp = etree.SubElement(cidte, etree.QName(NSX['gmd'], 'dateType'))
                        cidtetyp = etree.SubElement(dtetp, etree.QName(NSX['gmd'], 'CI_DateTypeCode'))
                        cidtetyp.text = 'revision'
                        cidtetyp.attrib['codeList'] = 'http://standards.iso.org/ittf/PubliclyAvailableStandards/ISO_19139_Schemas/resources/Codelist/gmxCodelists.xml#CI_DateTypeCode'
                        cidtetyp.attrib['codeListValue'] = 'revision'
                        ed = etree.SubElement(ciCit, etree.QName(NSX['gmd'], 'edition'))
                        cs = etree.SubElement(ed, etree.QName(NSX['gco'], 'CharacterString'))
                        cs.text = 'Version 2.1'
                        edDte = etree.SubElement(ciCit, etree.QName(NSX['gmd'], 'editionDate'))
                        dt = etree.SubElement(edDte, etree.QName(NSX['gco'], 'Date'))
                        dt.text = '2008-10-29'
                        iden = etree.SubElement(ciCit, etree.QName(NSX['gmd'], 'identifier'))
                        mdId = etree.SubElement(iden, etree.QName(NSX['gmd'], 'MD_Identifier'))
                        cde = etree.SubElement(mdId, etree.QName(NSX['gmd'], 'code'))
                        cs = etree.SubElement(cde, etree.QName(NSX['gco'], 'CharacterString'))
                        cs.text = 'http://asdd.ga.gov.au/asdd/profileinfo/anzlic-jurisdic.xml#anzlic-jurisdic'
                        cRP = etree.SubElement(ciCit, etree.QName(NSX['gmd'], 'citedResponsibleParty'))
                        ciCRP = etree.SubElement(cRP, etree.QName(NSX['gmd'], 'CI_ResponsibleParty'))
                        org = etree.SubElement(ciCRP, etree.QName(NSX['gmd'], 'organisationName'))
                        cs = etree.SubElement(org, etree.QName(NSX['gco'], 'CharacterString'))
                        cs.text = 'ANZLIC the Spatial Information Council'
                        rle = etree.SubElement(ciCRP, etree.QName(NSX['gmd'], 'role'))
                        cirlcd = etree.SubElement(rle, etree.QName(NSX['gmd'] ,'CI_RoleCode'))
                        cirlcd.text = 'custodian'
                        cirlcd.attrib['codeList'] = 'http://standards.iso.org/ittf/PubliclyAvailableStandards/ISO_19139_Schemas/resources/Codelist/gmxCodelists.xml#CI_RoleCode'
                        cirlcd.attrib['codeListValue'] = 'custodian'
                        
                        kt.addnext(tName)

                        found = False
                        for j in self.dlg.keywordList.selectedItems():
                            found = True
                            tree = self.write(i, tree, j.text().replace(' ', '-'),
                                              'gmd:identificationInfo/gmd:MD_Data'+\
                                              'Identification/gmd:descriptive'   + \
                                              'Keywords/gmd:MD_Keywords')
                        if found:
                            kt = etree.Element(etree.QName(NSX['gmd'], 'type'))
                            ktc = etree.SubElement(kt, etree.QName(
                                NSX['gmd'], 'MD_KeywordTypeCode'))
                            ktc.attrib['codeList'] = keywordUrl
                            ktc.attrib['codeListValue'] = 'theme'
                            tree.findall(i[17:], namespaces=NSX)[
                                len(tree.findall(
                                    i[17:],
                                    namespaces=NSX))-1].getparent().addnext(kt)

                elif i == CITDATE or i == CITDATETYPE:
                    if i == CITDATE:
                        dateUrl = 'http://standards.iso.org/ittf/Publicly' + \
                                  'AvailableStandards/ISO_19139_Schemas/'  + \
                                  'resources/Codelist/gmxCodelists.xml#CI' + \
                                  '_DateTypeCode'
                        
                        codeListVal = {self.dlg.resourceCreateCheck  :
                                       ('creation', self.dlg.resourceCreate),
                                       self.dlg.resourceUpdateCheck  :
                                       ('revision', self.dlg.resourceUpdate),
                                       self.dlg.resourcePublishCheck :
                                       ('publication', self.dlg.resourcePublish)}

                        for val in (self.dlg.resourceCreateCheck,
                                    self.dlg.resourcePublishCheck,
                                    self.dlg.resourceUpdateCheck):
                            if val.isChecked():
                                date = codeListVal[val][1].date().toString(
                                    'yyyy-MM-dd')
                                tree = self.write(i, tree, date,
                                                  'gmd:identificationInfo/gmd:' + \
                                                  'MD_DataIdentification/gmd:'  + \
                                                  'citation/gmd:CI_Citation')
                                citD = etree.Element(etree.QName(NSX['gmd'],
                                                                 'dateType'))
                                citDCode = etree.SubElement(citD,
                                                            etree.QName(
                                                                NSX['gmd'],
                                                                'CI_DateTypeCode'))
                                citDCode.attrib['codeList'] = dateUrl
                                citDCode.attrib['codeListValue']=codeListVal[val][0]
                                citDCode.text = codeListVal[val][0]
                                tree.findall(i[17:], namespaces=NSX)[
                                    len(tree.findall(
                                        i[17:],
                                        namespaces=NSX))-1].getparent().addnext(citD)

                elif i in self.MDTEXT       and \
                     'Constraint' not in i  and \
                     i != RS                and \
                     i != HLEVELNAME        and \
                     i != SCOPE             and \
                     i != SCOPEDESC:
                    # Update Any other fields that are not empty.
                    if type(self.MDTEXT[i]) != tuple and \
                       self.MDTEXT[i] != '' and \
                       i not in SETFIELDS:
                        if 'extent' in i:
                            tree = self.write(i, tree, self.MDTEXT[i],
                                              'gmd:identificationInfo/gmd:MD' + \
                                              '_DataIdentification')
                        else:
                            tree = self.write(i, tree, self.MDTEXT[i])

            # Create New Metadata File
            md_text = etree.tostring(md, pretty_print=True,
                                     xml_declaration=True, encoding='utf-8')
            with open(TEMPFILE, 'w') as f:
                f.write(md_text)

            # Create XML Summary
            self.dlg.summary.setText(md_text.decode("utf-8"))

            # Create Formatted Summary
            self.formatSummary(tree)

        except Exception as e:
            raise Exception("Write Error: " + str(e))
            
        

    def done(self):
        ''' create metadata clicked '''
        # Clear validation and update output file.
        self.dlg.validationLog.clear()
        try:
            copyfile(TEMPFILE, self.dlg.OUTPUTFILE)
            os.remove(TEMPFILE)
        except Exception as e:
            self.dlg.validationLog.setText("XML Creation Error: " + str(e))
            return
        if self.dlg.OUTPUTFILE == self.dlg.TEMPLATEPATH:
            self.dlg.validationLog.setText('Metadata "{}" Edited'.
                                           format(self.dlg.OUTPUTFILE))
        else:
            self.dlg.validationLog.setText('Metadata "{}" Created'.
                                           format(self.dlg.OUTPUTFILE))
        self.dlg.createMetadata.setEnabled(False)        

    def toggleDate(self, state):
        ''' date of next update check box state changed '''
        if state > 0: self.dlg.date.setEnabled(True)
        else: self.dlg.date.setEnabled(False)

    def toggleState(self, state):
        ''' scale check box state changed. '''
        if state > 0:
            self.dlg.scaleFrame.setEnabled(True)
        else:
            self.dlg.scaleFrame.setEnabled(False)

    def toggleRadio(self, checked):
        ''' scale/ resolution radio buttons state changed '''
        if checked:
            self.dlg.scaleWidget.setEnabled(True)
            self.dlg.resolutionText.setEnabled(False)
            self.dlg.resolutionUnits.setEnabled(False)
        else:
            self.dlg.scaleWidget.setEnabled(False)
            self.dlg.resolutionText.setEnabled(True)
            self.dlg.resolutionUnits.setEnabled(True)

    def toggleTemporal(self, state):
        ''' temporal check box state changed. '''
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

    def toggleStartTime(self, state):
        ''' start time check box state changed.'''
        if state > 0:
            self.dlg.startTime.setEnabled(True)
        else:
            self.dlg.startTime.setEnabled(False)

    def toggleEndTime(self, state):
        ''' end time check box state changed '''
        if state > 0:
            self.dlg.endTime.setEnabled(True)
        else:
            self.dlg.endTime.setEnabled(False)

    def toggleEndDate(self, state):
        ''' end date check box state changed '''
        if state > 0:
            self.dlg.endDate.setEnabled(True)
            self.dlg.endTimeCheck.setEnabled(True)
        else:
            self.dlg.endDate.setEnabled(False)
            self.dlg.endTimeCheck.setEnabled(False)
            self.dlg.endTimeCheck.setChecked(False)

    def toggleCreateDate(self, state):
        if state > 0:
            self.dlg.resourceCreate.setEnabled(True)
        else:
            self.dlg.resourceCreate.setEnabled(False)
            
    def togglePublishDate(self, state):
        if state > 0:
            self.dlg.resourcePublish.setEnabled(True)
        else:
            self.dlg.resourcePublish.setEnabled(False)
            
    def toggleUpdateDate(self, state):
        if state > 0:
            self.dlg.resourceUpdate.setEnabled(True)
        else:
            self.dlg.resourceUpdate.setEnabled(False)

    def check(self):
        ''' validate / error check clicked '''
        # Clear validation log, and update xml, before performing checks on
        contact = ('INDIVIDUALNAME', 'ORGANISATIONNAME', 'POSITIONNAME', 'VOICE',
                   'FACSIMILE', 'DELIVERYADDRESS', 'CITY', 'COUNTRY', 'POSTALCODE',
                   'EMAIL', 'ROLE')
        basic = ('HIERARCHYLEVEL', 'TITLE', 'ABSTRACT', 'PURPOSE')
        security= ('SECURITYCLASSRES', 'SECURITYCLASSMET', 'RESTRICCODERES',
                   'RESTRICCODEMET')
        extent = ('EXTENTDESCRIPTION', 'EXTENTBOUNDINGBOX', 'EXTENTTEMPORAL',
                  'EXTENTVERTICAL')
        ident = ('REFERENCESYS1', 'STATUS', 'LINEAGE', 'SPATIALREPRESENTATION',
                 'MAINTENANCE')
        other = ('KEYWORD',)

        tabDict = {'INDIVIDUALNAME'     : (self.dlg.iName1, self.dlg.iName2),
                   'ORGANISATIONNAME'   : (self.dlg.oName1, self.dlg.oName2),
                   'POSITIONNAME'       : (self.dlg.pName1, self.dlg.pName2) ,
                   'VOICE'              : (self.dlg.voice1, self.dlg.voice2),
                   'FACSIMILE'          : (self.dlg.fas1, self.dlg.fas2),
                   'DELIVERYADDRESS'    : (self.dlg.dadd1, self.dlg.dadd2),
                   'CITY'               : (self.dlg.city1, self.dlg.city2),
                   'COUNTRY'            : (self.dlg.country1, self.dlg.country2),
                   'POSTALCODE'         : (self.dlg.postCode1, self.dlg.postCode2),
                   'EMAIL'              : (self.dlg.email1, self.dlg.email2),
                   'ROLE'               : (self.dlg.role1, self.dlg.role2),
                   'HIERARCHYLEVEL'     : self.dlg.hlName,
                   'TITLE'              : self.dlg.title,
                   'ABSTRACT'           : self.dlg.abs,
                   'PURPOSE'            : self.dlg.purpose,
                   'SECURITYCLASSRES'   : self.dlg.resSecClass,
                   'SECURITYCLASSMET'   : self.dlg.metSecClass,
                   'RESTRICCODERES'    : (self.dlg.resourceConCopyright, self.dlg.resourceConLicense),
                   'RESTRICCODEMET'    : (self.dlg.metadataConCopyright, self.dlg.metadataConLicense),
                   'EXTENTDESCRIPTION'  : self.dlg.geoDescCombo,
                   'EXTENTBOUNDINGBOX'  : self.dlg.geoBBFrame,
                   'EXTENTTEMPORAL'     : self.dlg.temporalFrame,
                   'REFERENCESYS1'      : self.dlg.referenceSys,
                   'STATUS'             : self.dlg.status,
                   'LINEAGE'            : self.dlg.lineage,
                   'SPATIALREPRESENTATION' : self.dlg.spatialrep,
                   'MAINTENANCE'        : self.dlg.maintenance,
                   'KEYWORD'            : self.dlg.keywordList}
        
        self.dlg.validationLog.clear()
        try:
            self.writeXML()
        except Exception as e:
            self.dlg.validationLog.setText(str(e))
            return
        file, vdtr = r'{}/{}'.format(os.getcwd(), TEMPFILE), Local()
        meta = vdtr.metadata(file)
        if self.dlg.check != 0:
            self.use.setPalette(self.palette)
        try:
            runChecks(meta)
            self.dlg.fixError.hide()
            self.dlg.validationLog.setText('Error Checks Complete')
            # TODO: Add validation checks here.
            #vdtr.setschema()
            #vdtr.validate(meta)
            #vdtr.conditional(meta)
            #self.dlg.validationLog.setText('Error Checks Complete\nValidation Checks Complete')
            self.checks = True
            self.dlg.createMetadata.setEnabled(True)
        except Exception as e:
            if isinstance(e, ValidatorException):
                print (str(e))
            else:
                self.dlg.check += 1
                self.widget = self.dlg.widget(7)        
                valFound = None
                self.dlg.fixError.show()
                self.dlg.validationLog.setText('Checker Error: {}'.format(e))
                font = QFont('Noto Sans', 14, weight=QFont.Bold, italic=True)
                for val in contact:
                    if val in str(e):
                        self.widget = self.dlg.widget(2)
                        valFound = val
                        break
                for val in basic:
                    if val in str(e):
                        self.widget = self.dlg.widget(1)
                        valFound = val
                        break
                for val in security:
                    if val in str(e):
                        self.widget = self.dlg.widget(6)
                        valFound = val
                        break
                for val in extent:
                    if val in str(e):
                        self.widget = self.dlg.widget(5)
                        valFound = val
                        break
                for val in ident:
                    if val in str(e):
                        self.widget = self.dlg.widget(3)
                        valFound = val
                        break
                for val in other:
                    if val in str(e):
                        self.widget = self.dlg.widget(4)
                        valFound = val
                        break
                if type(tabDict[valFound]) == tuple:
                    if 'copyright' in str(e):
                        self.use = tabDict[valFound][0]
                    elif 'license' in str(e):
                        self.use = tabDict[valFound][1]
                    elif valFound + '2' in str(e):
                        self.use = tabDict[valFound][0]
                    else:
                        self.use = tabDict[valFound][1]
                else:
                    self.use = tabDict[valFound]
                self.palette = self.use.palette()
                palette = QPalette(self.palette)
                palette.setColor(QPalette.Window, QColor(Qt.red))
                palette.setColor(QPalette.Base, QColor(Qt.red))
                self.use.setPalette(palette)
                self.checks = False
                self.dlg.createMetadata.setEnabled(False)

    def fixError(self):
        self.dlg.fixError.hide()
        self.dlg.setCurrentWidget(self.widget)

    def setFile(self, i):
        ''' select file clicked '''
        try:
            self.dlg.loadError.hide()
            qfd, filename = QFileDialog(), ()
            self.dlg.metadataFile.clear()
            qfd.setFileMode(QFileDialog.AnyFile)
            if i == 1:
                qfd.setFilter("XML Template file (*.xml)")
            elif i == 2:
                qfd.setFilter("XML Output file (*.xml)")
            else:
                qfd.setFilter("XML Metadata file (*.xml)")
            if qfd.exec_():
                self.dlg.reset_form()
                filename = qfd.selectedFiles()
                if filename:
                    if i == 1:
                        self.dlg.changeTemplate(filename[0])
                        self.dlg.templateFile.setText(self.dlg.TEMPLATEPATH)
                        self.dlg.outputFile.setText(self.dlg.TEMPLATEPATH)
                    elif i == 2:
                        self.dlg.OUTPUTFILE = filename[0]
                        self.dlg.outputFile.setText(self.dlg.OUTPUTFILE)
                    else:
                        self.dlg.OUTPUTFILE = filename[0]
                        self.dlg.changeTemplate(filename[0])
                        self.dlg.metadataFile.setText(self.dlg.OUTPUTFILE)
        except Exception as e:
            self.dlg.loadError.setText("File Selection Error: " + str(e))
            self.dlg.loadError.show()

    def updateFileText(self):
        ''' default template clicked '''
        self.dlg.changeTemplate(self.dlg.DEFAULTTEMP)
        self.dlg.templateFile.setText(self.dlg.TEMPLATEPATH)

    def autoFill(self, i):
        ''' auto fill (resource(1) or metadata(2)) clicked.
            copy fields existing in other contact to current contact.
        '''
        try:
            self.dlg.autoFillError.hide()
            resource, metadata = {}, {}
            if i == 2:
                fillName, fromName, fillVal, fromVal = resource, metadata, '1', '2'
            else:
                fillName, fromName, fillVal, fromVal = metadata, resource, '2', '1'
            for i in self.dlg.contact:
                if '1' in i.objectName():
                    if type(i) == QComboBox:
                        resource[i.objectName()] = i.currentText()
                    else:
                        resource[i.objectName()] = i.toPlainText()
                else:
                    if type(i) == QComboBox:
                        metadata[i.objectName()] = i.currentText()
                    else:
                        metadata[i.objectName()] = i.toPlainText()
            for val in fillName:
                text = fillName[val]
                for i in self.dlg.contact:
                    if i.objectName() in fromName and \
                       i.objectName().split(fromVal)[0] == val.split(fillVal)[0]:
                        if type(i) == QComboBox:
                            i.setCurrentIndex(i.findText(text))
                        else:
                            i.setText(text)

        except Exception as e:
            self.dlg.autoFillError.setText("Auto Fill Error: " + str(e))
            self.dlg.autoFillError.show()

    def textStyle(self, i):
        ''' text style button clicked (bold (1), italic (2), link (3))
            Add **selected text** around selected text if bold clicked
            Add *selected text* around selected text if italic clicked
            Add [selected text](LINK HERE) around selected text if link clicked.
        '''
        try:
            if i == 1: textStyle = "**"
            if i == 2: textStyle = "*"
            cursor = self.dlg.abs.textCursor()
            textSelected = cursor.selectedText()
            selectStart, selectEnd = cursor.selectionStart(), cursor.selectionEnd()
            if len(textSelected) > 1:
                if i == 3: tS = "[" + textSelected + "](LINK HERE)"
                else: tS = textStyle + textSelected + textStyle
            else:
                if i == 3: tS = "[TEXT HERE](LINK HERE)"
                else: tS = textStyle + "TEXT HERE" + textStyle
            if selectStart != 0:
                start = self.dlg.abs.toPlainText()[:selectStart]
            else: start = ""
            if selectEnd != len(self.dlg.abs.toPlainText())-1:
                end = self.dlg.abs.toPlainText()[selectEnd:]
            else: end = ""
            text = start+tS+end
            self.dlg.abs.setText(text)
            if i ==3: textStyle = 'LINK HERE)'
            else: textStyle = 'TEXT HERE' + textStyle
            if self.dlg.abs.toPlainText().find(textStyle) != -1:
                newStart = self.dlg.abs.toPlainText().find(textStyle)
                newEnd = newStart + 9
                cursor.setPosition(newStart)
                cursor.setPosition(newEnd, QTextCursor.KeepAnchor)
                self.dlg.abs.setTextCursor(cursor)
            elif i != 3:
                if i == 1: move = 2
                else: move = 1
                cursor.setPosition(selectStart+move)
                cursor.setPosition(selectEnd+move, QTextCursor.KeepAnchor)
                self.dlg.abs.setTextCursor(cursor)
        except Exception as e:
            print ("Text Style Error: " + str(e))

    def run(self):
        self.dlg.show()
