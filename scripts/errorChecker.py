'''
Error Checker

Checks for errors where LINZ required fields, are empty, don't exist or don't
contain the required fields determined by those in the config file.

The Config file allows the search values to be:
    - Checked if a value exists. (True/False)
      (POSITIONNAME: True)
    - Checked if a particular value exists.
      (CITY: "Wellington")
    - Checked if a value in a range of values exists.
      (INDIVIDUALNAME: ["omit", "Omit"])
    - Checked only if a value is correct, if there is a
      value in the first place. By adding the keyword(s):
        NONE - any metadata that doesn't contain the xml search
               path will be ignored.
        EMPTY - any metadata that does contain the xml search path,
                but there is no text will be ignored.
      (EXTENTDESCRIPTION: ["nzl", "NZ_MAINLAND_AND_CHATHAMS", "NONE"])

    - Resource and Metadata use constraint codes will be checked that all
      values in the range defined in the config exist.

* Address - (Contact & PointOfContact)
    * INDIVIDUALNAME
    * ORGANISATIONNAME
    * POSITIONNAME
    * DELIVERYADDRESS
    * VOICE
    * POSTALCODE
    * CITY
    * COUNTRY
    * ROLE1 (Metadata Contact Role)
    * ROLE2 (Resource Point of Contact Role)
    * EMAIL
    * VOICEMAIL
    
* Hierarchy Level
    * HIERARCHYLEVEL
    * HIERARCHYLEVELNAME
    * SCOPE
    * SCOPELEVELDESC

* Resource and Metadata Copyright & Licensing information
    * Resource & Metadata Security Constraint Classification
        * SECURITYCLASSRES
        * SECURITYCLASSMET
    * Resource & Metadata Use Constraint Restriction Code
        * RESTRICCODERES
        * RESTRICCODEMET
    * Resource & Metadata Use Constraint Text
        * RESOURCECON
        * METADATACON

* Extent
    * EXTENTBOUNDINGBOX
    * EXTENTDESCRIPTION
    * EXTENTTEMPORAL
    * EXTENTVERTICAL

* Reference System (Checks against reference system on LDS Api)
    * REFERENCESYS1 (Check that the reference system is not none)
    * REFERENCESYS2 (Check that the reference system matches correctly)

* Status (Completed, onGoing ... )
    * STATUS
    
* Lineage
    * LINEAGE

* Linkage
    * LINKAGE

* Spatial Representation
    * SPATIALREPRESENTATION

* File Identifier
    * FID

* Maintenance
    * MAINTENANCE

* Keyword
    * KEYWORD
    
* Date Format
    * DATEFORMAT (Checks date formats in required)
      YYYY or YYYY-MM or YYYY-MM-DD

* Empty Format
    * EMPTYFORMAT (Checks the whole xml document for any empty xml tags,
      where text should be)
'''

import os
import requests
import json
import yaml
import sys

from validate import InaccessibleMetadataException, MetadataParseException, \
     Remote, KEY, Local
class ErrorCheckerException(Exception): pass
class MetadataErrorException(ErrorCheckerException): pass
class MetadataIncorrectException(MetadataErrorException): pass
class MetadataEmptyException(MetadataErrorException): pass
class MetadataNoneException(MetadataErrorException): pass
class InaccessibleFileException(ErrorCheckerException): pass
class InaccessibleLayerException(ErrorCheckerException): pass
class InvalidConfigException(ErrorCheckerException): pass


FILE = r'{}/config.yaml'.format(os.path.abspath(os.path.join(__file__, '../..')))
print ()

NSX = {'xlink'                  : 'http://www.w3.org/1999/xlink',
       'xs'                     : 'http://www.w3.org/2001/XMLSchema',
       'xsi'                    : 'http://www.w3.org/2001/XMLSchema-instance',
       'dc'                     : 'http://purl.org/dc/elements/1.1/',
       'g'                      : 'http://data.linz.govt.nz/ns/g',
       'r'                      : 'http://data.linz.govt.nz/ns/r',
       'ows'                    : 'http://www.opengis.net/ows/1.1',
       'csw'                    : 'http://www.opengis.net/cat/csw/2.0.2',
       'wms'                    : 'http://www.opengis.net/wms',
       'ogc'                    : 'http://www.opengis.net/ogc',
       'gco'                    : 'http://www.isotc211.org/2005/gco',
       'gmd'                    : 'http://www.isotc211.org/2005/gmd',
       'gmx'                    : 'http://www.isotc211.org/2005/gmx',
       'gsr'                    : 'http://www.isotc211.org/2005/gsr',
       'gss'                    : 'http://www.isotc211.org/2005/gss',
       'gts'                    : 'http://www.isotc211.org/2005/gts',
       'f'                      : 'http://www.w3.org/2005/Atom',
       'null'                   : '',
       'wfs'                    : 'http://www.opengis.net/wfs/2.0',
       'gml'                    : 'http://www.opengis.net/gml/3.2',
       'v'                      : 'http://wfs.data.linz.govt.nz',
       'lnz'                    : 'http://data.linz.govt.nz',
       'data.linz.govt.nz'      : 'http://data.linz.govt.nz',
       'fes'                    : 'http://www.opengis.net/fes/2.0'}

# Set XML Paths
# Base Data Identification
IDENT = 'gmd:identificationInfo/gmd:MD_DataIdentification'

# Base Contact Information
CONTACT = '/gmd:CI_ResponsibleParty'
CONTACTINFO = CONTACT + '/gmd:contactInfo/gmd:CI_Contact'
PHONE = CONTACTINFO + '/gmd:phone/gmd:CI_Telephone'
ADDRESS = CONTACTINFO + '/gmd:address/gmd:CI_Address'

# Contact Information
INDIVIDUALNAME = CONTACT + '/gmd:individualName/gco:CharacterString'
ORGANISATIONNAME = CONTACT + '/gmd:organisationName/gco:CharacterString'
POSITIONNAME = CONTACT + '/gmd:positionName/gco:CharacterString'
VOICE = PHONE + '/gmd:voice/gco:CharacterString'
FACSIMILE = PHONE + '/gmd:facsimile/gco:CharacterString'
DELIVERYADDRESS = ADDRESS + '/gmd:deliveryPoint/gco:CharacterString'
CITY = ADDRESS + '/gmd:city/gco:CharacterString'
POSTALCODE = ADDRESS + '/gmd:postalCode/gco:CharacterString'
COUNTRY = ADDRESS + '/gmd:country/gco:CharacterString'
EMAIL = ADDRESS + '/gmd:electronicMailAddress/gco:CharacterString'
ROLE = CONTACT + '/gmd:role/gmd:CI_RoleCode'

# Hierarchy & Scope Level
DQ = 'gmd:dataQualityInfo/gmd:DQ_DataQuality'
HIERARCHYLEVEL = 'gmd:hierarchyLevel/gmd:MD_ScopeCode'
HIERARCHYLEVELNAME = 'gmd:hierarchyLevelName/gco:CharacterString'
SCOPELEVEL = DQ + '/gmd:scope/gmd:DQ_Scope/gmd:level/gmd:MD_ScopeCode'
SCOPELEVELDESC = DQ + '/gmd:scope/gmd:DQ_Scope/gmd:levelDescription/gmd:MD_' + \
                 'ScopeDescription/gmd:other/gco:CharacterString'

TITLE = IDENT + '/gmd:citation/gmd:CI_Citation/gmd:title/gco:CharacterString'
ABSTRACT = IDENT + '/gmd:abstract/gco:CharacterString'
PURPOSE = IDENT + '/gmd:purpose/gco:CharacterString'

# Date
DATE = IDENT + '/gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date/gmd:date' + \
       '/gco:Date'

# Status
STATUS = IDENT + '/gmd:status/gmd:MD_ProgressCode'

# Base Resource & Metadata Constraint
RESOURCECONSTRAINT = IDENT + '/gmd:resourceConstraints'
METACONSTRAINTS = 'gmd:metadataConstraints'

# Resource & Metadata Constraints
SECURITYCLASSRES = RESOURCECONSTRAINT + '/gmd:MD_SecurityConstraints/gmd:cl' + \
                   'assification/gmd:MD_ClassificationCode'
RESOURCECON = RESOURCECONSTRAINT + '/gmd:MD_LegalConstraints/gmd:useLimitat' + \
              'ion/gco:CharacterString'
RESTRICCODERES = RESOURCECONSTRAINT + '/gmd:MD_LegalConstraints/gmd:useCons' + \
                 'traints/gmd:MD_RestrictionCode'

SECURITYCLASSMET = METACONSTRAINTS + '/gmd:MD_SecurityConstraints/gmd:class' + \
                   'ification/gmd:MD_ClassificationCode'
METADATACON = METACONSTRAINTS + '/gmd:MD_LegalConstraints/gmd:useLimitation' + \
              '/gco:CharacterString'
RESTRICCODEMET = METACONSTRAINTS + '/gmd:MD_LegalConstraints/gmd:useConstra' + \
                 'ints/gmd:MD_RestrictionCode'

# Lineage
LINEAGE = DQ + '/gmd:lineage/gmd:LI_Lineage/gmd:statement/gco:CharacterString'

# Linkage
LINKAGE = 'gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd' + \
          ':MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource/gmd:' + \
          'linkage/gmd:URL'

# Extent
EXTENT = IDENT + '/gmd:extent/gmd:EX_Extent'
EXTENTBOUNDINGBOX = EXTENT + '/gmd:geographicElement/gmd:EX_GeographicBound' + \
                    'ingBox/gmd:westBoundLongitude/gco:Decimal'
EXTENTDESCRIPTION = EXTENT + '/gmd:geographicElement/gmd:EX_GeographicDescr' + \
                    'iption/gmd:geographicIdentifier/gmd:MD_Identifier/gmd:' + \
                    'code/gco:CharacterString'
EXTENTTEMPORAL = EXTENT + '/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:e' + \
                 'xtent/gml:TimeInstant/gml:timePosition'
EXTENTVERTICAL = EXTENT + '/gmd:verticalElement/gmd:EX_VerticalExtent/gmd:m' + \
                 'inimumValue/gco:Real'

# Spatial Representation
SPATIALREPRESENTATION = IDENT + '/gmd:spatialRepresentationType/gmd:MD_Spat' + \
                        'ialRepresentationTypeCode'

# Reference System
REFERENCESYS = 'gmd:referenceSystemInfo/gmd:MD_ReferenceSystem/gmd:referenc' + \
               'eSystemIdentifier/gmd:RS_Identifier/gmd:code/gco:CharacterString'

# FID
FID = 'gmd:fileIdentifier/gco:CharacterString'

# Maintenance
MAINTENANCE = IDENT + '/gmd:resourceMaintenance/gmd:MD_MaintenanceInformati' + \
              'on/gmd:maintenanceAndUpdateFrequency/gmd:MD_MaintenanceFrequ' + \
              'encyCode'

# Keyword
KEYWORD = IDENT + '/gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:keyword/gco' + \
          ':CharacterString'

ADDRESSVALUES = ('INDIVIDUALNAME', 'ORGANISATIONNAME', 'POSITIONNAME', 'VOICE',\
                 'FACSIMILE', 'DELIVERYADDRESS', 'CITY', 'POSTALCODE', 'EMAIL',\
                 'COUNTRY', 'ROLE1', 'ROLE2')

EXTENTVALUES = ('EXTENTDESC', 'EXTENTBOUNDINGBOX', 'EXTENTDESCRIPTION',        \
                'EXTENTTEMPORAL', 'EXTENTVERTICAL')

RESOURCEMETAVALUES = ('SECURITYCLASSRES','SECURITYCLASSMET', 'RESTRICCODEMET', \
                      'RESOURCECON', 'METADATACON', 'RESTRICCODERES')

HIERARCHYVALUES = ('HIERARCHYLEVEL', 'HIERARCHYLEVELNAME', 'SCOPELEVEL',       \
                   'SCOPELEVELDESC')

REFSYSVALUES = ('REFERENCESYS1', 'REFERENCESYS2')

OTHERNONE = ('LINKAGE', 'FID', 'SPATIALREPRESENTATION', 'LINEAGE', 'STATUS', \
             'MAINTENANCE', 'KEYWORD', 'TITLE', 'ABSTRACT', 'PURPOSE')

class ConfigReader():

    def __init__(self, file = None):
        if not file:
            file = FILE

        if not os.path.exists(file):
            raise InvalidConfigException('Can not find config file')

        with open(file, 'r') as f:
            config = yaml.load(f)

        self.checkValues = []
        for val in config:
            self.checkValues += [(val, config[val])]
        
        self.av, self.ev, self.rv, self.hv, \
                 self.rsv, self.ov, self.form = (), (), (), (), (), (), ()

        for val in self.checkValues:
            if val[0] in ADDRESSVALUES and val[1]:
                self.av += ([val[0], val[1]],)

            elif val[0] in EXTENTVALUES and val[1]:
                self.ev += ([val[0], val[1]],)

            elif val[0] in RESOURCEMETAVALUES and val[1]:
                self.rv += ([val[0], val[1]],)

            elif val[0] in HIERARCHYVALUES and val[1]:
                self.hv += ([val[0], val[1]],)

            elif val[0] in REFSYSVALUES and val[1]:
                self.rsv += ([val[0], val[1]],)

            elif val[0] in OTHERNONE and val[1]:
                self.ov += ([val[0], val[1]],)

            elif (val[0] == 'DATEFORMAT' and val[1]) \
                 or (val[0] == 'EMPTYFORMAT' and val[1]):
                self.form += (val[0],)

            elif val[1]:
                raise InvalidConfigException('Invalid Config Option: {}'.format(val[0]))

def allChecks(meta, xmlPath, name, searchVal, iterCheck=False, allChecks=False):
    '''
    Perform all checks for a given criteria,
        meta: metadata etree
        xmlPath: xml path to check inside the meta document
        searchVal: Search Value(s) to check that the text at end of xml path is,
                   or none, if set to 'True'.
        iterationsCheck: Set to true if is an address, check there isn't
                         multiple pointOfContact.
        allChecks: set to true if everything in the searchval must exist in the
                   meta document.
    '''
    noneAllowed, emptyAllowed = False, False
    iterations = 0
    allChecksVal = []

    # Check if AllChecks is True, everything in search val must exist.
    if allChecks:
        for i in searchVal:
            allChecksVal += [i]
            
    # Check if 'NONE' or 'EMPTY' were included in the search val, set to ignore
    # corresponding errors.
    if searchVal != True:
        if 'NONE' in searchVal:
            noneAllowed = True
        if 'EMPTY' in searchVal:
            emptyAllowed = True
    else:
        searchVal = False
    if meta.find(xmlPath, namespaces=NSX) is not None:
        for val in meta.findall(xmlPath, namespaces=NSX):
            if iterCheck:
                iterations += 1
            if val.text is None and not emptyAllowed:
                    raise MetadataEmptyException('Empty {}'.format(name))
            if searchVal and val.text is not None:
                if str(val.text) not in searchVal:
                        raise MetadataIncorrectException(
                            'Invalid/Incorrect {} "{}"\n Valid Field(s): "{}"'.format(name, val.text, searchVal))
                elif allChecks:
                    allChecksVal.remove(val.text)
    elif not noneAllowed:
        if searchVal:
            raise MetadataNoneException('No {}\n Valid Field(s): {}'.format(name, searchVal))
        else:
            raise MetadataNoneException('No {}'.format(name))
    if iterCheck and iterations == 2:
        raise MetadataIncorrectException('Multiple pointOfContact fields')
    if allChecks and len(allChecksVal) != 0:
        raise MetadataIncorrectException(\
            'Missing {} in {}'.format(allChecksVal, name))

def checkAddress(meta, address):
    '''
    Check pointOfContact and contact address fields.
    '''
    contact = 'gmd:contact'
    pointOfContact = IDENT + '/gmd:pointOfContact'
    
    if 'ROLE' in address[0]:
        if '1' in address[0]:
            allChecks(meta, contact + ROLE, address[0], address[1])
        else:
            allChecks(meta, pointOfContact + ROLE,address[0], address[1])
    else:
        allChecks(meta, contact + globals().get(address[0]),address[0], address[1])
        allChecks(meta, pointOfContact + globals().get(address[0]),\
                  address[0], address[1], iterCheck=True)


def checkDateFormat(meta):
    '''
    Check date format is:
      - YYYY
      - YYYY-MM
      - YYYY-MM-DD

    '''
    if meta.find(DATE, namespaces=NSX) is not None:
        for val in meta.findall(DATE, namespaces=NSX):
            if val.text is not None:
                if (len(val.text) != 4 and
                    len(val.text) != 7 and len(val.text) != 10):
                    raise MetadataIncorrectException('Invalid Date Format')
                elif (len(val.text) == 4 and str(val.text).find('-') != -1):
                    raise MetadataIncorrectException('Invalid Date Format')
                elif (len(val.text) == 7 and str(val.text).count('-') != 1):
                    raise MetadataIncorrectException('Invalid Date Format')
                elif (len(val.text) == 10 and str(val.text).count('-') != 2):
                    raise MetadataIncorrectException('Invalid Date Format')
            else:
                raise MetadataEmptyException('Empty Date')
    else:
        raise MetadataNoneException('No Date')


def checkReferenceSystem(meta, lid, noneCheck=False):
    '''
    Extract data.crs value from api, in the format 'EPSG:{CRS}' From this the
    value can be checked against reference system in metadata.

    Can only be used for layers.
    '''
    
    headers = {'Content-Type': 'application/json',
               'Authorization': 'key {}'.format(KEY)}
    
    url = 'https://data.linz.govt.nz/services/api/v1/layers/{lid}/'.format(
        lid=lid)

    try:
        response = requests.get(url, headers=headers)
        crsAct = (json.loads(response.text)['data']['crs'][5:])
        val = meta.find(REFERENCESYS, namespaces = NSX)
        if val is not None and val.text is not None:
            if str(val.text) != str(crsAct):
                raise MetadataIncorrectException(
                    'Invalid/Incorrect Reference System Format,\n should be:'+ \
                    '" {}", got: "{}"'.format(crsAct, val.text))
        
        elif noneCheck:            
            raise MetadataNoneException(
            'No Reference System, should be: {}'.format(crsAct))

    except MetadataNoneException as mne:
        raise MetadataNoneException(mne)
    except MetadataIncorrectException as mie:
        raise MetadataIncorrectException(mie)
    except Exception as e:
        raise InaccessibleLayerException('HTTP {0} calling [{1}]'.format(
            response.status_code, url), e)


def emptyTagCheck(meta):
    '''
    Iterate through metadata check if is an element that should contain text,
    if doesn't raise empty exception.
    '''
    for val in meta.iter():
        if 'gco' in val.tag:
            if val.text is None:
                error = (val.getparent().tag[val.getparent().tag.rfind('}')+1:])
                raise MetadataEmptyException('Empty {}'.format(error))
            
            
def runChecks(meta, lid=None, con=None):
    '''
    Run all checks based on those set/returned from the config file.
    - Address Checks
    - Extent Checks
    - Restriction Checks
    - Hierarchy Checks
    - Reference System Checks
    - All Other Valid Checks
    - Format Checks
    '''

    config = ConfigReader(con)

    for address in config.av:
        checkAddress(meta, address)

    for extent in config.ev:
        allChecks(meta, globals().get(extent[0]),extent[0], extent[1])
                
    for restrict in config.rv:
        if 'RESTRICCODE' in restrict[0]:
             allChecks(meta, globals().get(restrict[0]),\
                       restrict[0], restrict[1], allChecks=True)
        else:
            allChecks(meta, globals().get(restrict[0]),restrict[0], restrict[1])
                    
    for hier in config.hv:
         allChecks(meta, globals().get(hier[0]),hier[0], hier[1])
    if lid != None:
        for refsys in config.rsv:
            if '1' in refsys[0] and '2' in refsys[0]:
                checkReferenceSystem(meta, lid[0], True)
            elif '1' in refsys[0]:
                allChecks(meta, REFERENCESYS,refsys[0], refsys[1])
            elif '2' in refsys[0]:
                checkReferenceSystem(meta, lid[0])
    else:
        for refsys in config.rsv:
            if '1' in refsys[0]:
                allChecks(meta, REFERENCESYS,refsys[0], refsys[1])
                
    for otherVal in config.ov:
         allChecks(meta, globals().get(otherVal[0]),otherVal[0], otherVal[1])
                
    for formatVal in config.form:
        if 'DATEFORMAT' in formatVal[0]:
            checkDateFormat(meta)
        elif 'EMPTYFORMAT' in formatVal[0]:
            emptyTagCheck(meta)

def main():
     
    vdtr = Remote()
    #layers = ('51777','50201','50972','50202','50203','51083','50665','50648',
    #                '52233', '52344', '51362','51920','50772', '50789',
    #                '53451', '53519','50845','51306','50846','51368','51389',)
    
    #layers = vdtr.getids('wfs')
    #for lay in layers:
    #    try:
    #        meta = vdtr.metadata(lay)
    #        runChecks(meta, lay)
    #        print (lay, True)
    #    except MetadataErrorException as mee:
    #        print (lay, mee, False)
    #    except Exception as e:
    #        print (lay, e, False)
    vdtr = Local()
    layer = '/home/aross/outputXML.xml'
    meta = vdtr.metadata(layer)
    runChecks(meta)
    


if __name__ == '__main__':
    main()
