'''
Error Checker

Checks for errors where LINZ required fields, are empty, don't exist or don't
contain the required fields determined by those in the associated file.

* Address - (Contact & PointOfContact)
    * Individual Name
    * Organisation Name
    * Position Name
    * Delivery Address
    * Voice
    * Postal Code
    * City
    * Country
    * Role
    * Email
    * Voicemail (Not currently included as most have 'None')
    
* Hierarchy Level ( As 4 currently have fields other than dataset)
    * Hierachy Level
    * Hierachy Level Description
    * Scope 
    * Scope Description

* Date Format
    * Checking format:
        * YYYY
        * YYYY-MM
        * YYYY-MM-DD
        
* Status (Completed, onGoing ... ) (As 7 currently have None)

* Resource and Metadata Copyright & Licensing information
    * Resource Security Constraint Classification
    * Resource & Metadata Use Constraint Restriction Code
    * Resource & Metadata Use Constraint Text
    
* Lineage (As currently 42 currently have None or Empty)

* Linkage

* Extent
    * Bounding Box
    * Description (
    * Temporal Extent
    * Vertical Extent

* Spatial Representation (As 39 currently have None)

* Reference System (Checks against reference system on LDS Api)
  (Doesn't check if None, or empty as there are a large number (~1500)
  of layers that don't have reference system defined in metadata,
  even though are listed on LDS Api)

'''
import sys
import os
import requests
import json
import inspect
import urllib.request
from urllib.error import HTTPError, URLError
from io import StringIO
from lxml import etree
from lxml.etree import XMLSyntaxError
from authenticate import Authentication
import datetime
from validate import InaccessibleMetadataException, MetadataParseException, \
     Remote, KEY

class ErrorCheckerException(Exception): pass
class MetadataErrorException(ErrorCheckerException): pass
class MetadataIncorrectException(MetadataErrorException): pass
class MetadataEmptyException(MetadataErrorException): pass
class MetadataNoneException(MetadataErrorException): pass
class InaccessibleFileException(ErrorCheckerException): pass
class InaccessibleLayerException(ErrorCheckerException): pass

FILE = r'../scripts/acceptedValues.txt'

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
INAME = CONTACT + '/gmd:individualName/gco:CharacterString'
ONAME = CONTACT + '/gmd:organisationName/gco:CharacterString'
PNAME = CONTACT + '/gmd:positionName/gco:CharacterString'
VOICE = PHONE + '/gmd:voice/gco:CharacterString'
FACSIMILE = PHONE + '/gmd:facsimile/gco:CharacterString'
DELIVERYPOINT = ADDRESS + '/gmd:deliveryPoint/gco:CharacterString'
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
SCOPELEVELDESC = DQ + '/gmd:scope/gmd:DQ_Scope/gmd:levelDescription/' + \
                 'gmd:MD_ScopeDescription/gmd:other/gco:CharacterString'

# Date
DATE = IDENT + '/gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date/' + \
       'gmd:date/gco:Date'

# Status
STATUS = IDENT + '/gmd:status/gmd:MD_ProgressCode'

# Base Resource & Metadata Constraint
RESOURCECONSTRAINT = IDENT + '/gmd:resourceConstraints'
METACONSTRAINTS = 'gmd:metadataConstraints'

# Resource & Metadata Constraints
SECURITYC = RESOURCECONSTRAINT + '/gmd:MD_SecurityConstraints/' + \
            'gmd:classification/gmd:MD_ClassificationCode'
LEGALUL = RESOURCECONSTRAINT + '/gmd:MD_LegalConstraints/gmd:useLimitation/' + \
          'gco:CharacterString'
LEGALUC = RESOURCECONSTRAINT + '/gmd:MD_LegalConstraints/gmd:useConstraints/' + \
          'gmd:MD_RestrictionCode'
MLEGALUL = METACONSTRAINTS + '/gmd:MD_LegalConstraints/gmd:useLimitation/' + \
           'gco:CharacterString'
MLEGALUC = METACONSTRAINTS + '/gmd:MD_LegalConstraints/gmd:useConstraints/' + \
           'gmd:MD_RestrictionCode'

# Lineage
LINEAGE = DQ + '/gmd:lineage/gmd:LI_Lineage/gmd:statement/gco:CharacterString'

# Linkage
LINKAGE = 'gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/' + \
          'gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource/' + \
          'gmd:linkage/gmd:URL'

# Extent
EXTENT = IDENT + '/gmd:extent/gmd:EX_Extent'
BOUNDINGBOX = EXTENT + '/gmd:geographicElement/gmd:EX_GeographicBoundingBox/'+ \
              'gmd:westBoundLongitude/gco:Decimal'
DESCRIPTION = EXTENT + '/gmd:geographicElement/gmd:EX_GeographicDescription/'+ \
              'gmd:geographicIdentifier/gmd:MD_Identifier/gmd:code/' + \
              'gco:CharacterString'
TEMPORAL = EXTENT + '/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/' + \
           'gml:TimeInstant/gml:timePosition'
VERTICAL = EXTENT + '/gmd:verticalElement/gmd:EX_VerticalExtent/' + \
           'gmd:minimumValue/gco:Real'

# Spatial Representation
SPATIALREP = IDENT + '/gmd:spatialRepresentationType/' + \
             'gmd:MD_SpatialRepresentationTypeCode'

# Reference System
REFERENCESYSINFO = 'gmd:referenceSystemInfo/gmd:MD_ReferenceSystem/gmd:referenceSystemIdentifier/gmd:RS_Identifier/gmd:code/gco:CharacterString'

def search(file, word):
    '''
    Search and return value(s) associated to each search element, from file.
    '''
    value = ()
    with open(file) as f:
        for line in f:
            if word in line and line[0] != '#':
                value = value + (line[len(word):len(line)-1], )
    if not value:
        raise InaccessibleFileException(
            "{} doesn't exist in {}.".format(word, file))

    return value


def singleChecks(mta, name, searchname, printOut=True, iterationsCheck=False):
    '''
    Perform base check operation, checking:
      - Not Empty (Contains XML Path, but no text)
      - Not None (Doesn't contain XML Path)
      - Not Invalid/ Incorrect against search name (if given)

      - If is a Contact Field (given iterationsCheck True), check that there isn't a
      - double up of pointOfContact fields inside the data identification path.
    '''
    iterations = 0
    error = name[name[:name.rfind('/')].rfind('/')+1:name.rfind('/')]
    correct = True
    if mta.find(name, namespaces=NSX) is not None:
        for val in mta.findall(name, namespaces=NSX):
            if iterationsCheck:
                iterations += 1
            if val.text is None:
                if printOut:
                    raise MetadataEmptyException('Empty {}'.format(error))
                correct = False
            if searchname:
                if val.text != searchname:
                    if printOut:
                        raise MetadataIncorrectException(
                            'Invalid/Incorrect {} "{}"'.format(error, val.text))
                    correct = False
    else:
        raise MetadataNoneException('No {}'.format(error))
        correct = False
    if iterationsCheck and iterations == 2:
        raise MetadataIncorrectException('Multiple pointOfContact fields')
        correct = False
        
    return correct


def allChecks(mta, name, searchname=None, iterationsCheck=False):
    '''
    If search name given, perform singleCheck on every name found in the search
    file, to check if correct, as well as not empty or not none.

    Else if no search name given, perform singleCheck just checking if not empty
    and not none.
    '''
    if searchname:
        test = search(FILE, searchname)
        correct = False
        if len(test) > 1:
            multi = True
        else:
            multi = False
        for val in test:
            if (singleChecks(mta, name, val, not multi, iterationsCheck)):
                correct = True
    else:
        return singleChecks(mta, name, False, True, iterationsCheck)
    
    return correct
    

def checkAddress(mta):
    '''
    Check pointOfContact and contact address fields.
    '''
    contact = 'gmd:contact'
    pointOfContact = IDENT + '/gmd:pointOfContact'
    correct = True

    for i in range(2):
        if i == 0:
            con = contact
            role = 'ROLE1: '
        else:
            con = pointOfContact
            role = 'ROLE2: '
            
        if not allChecks(mta, con + INAME, 'INDIVIDUALNAME: '):
            correct = False            
        if not allChecks(
            mta, con + ONAME, 'ORGANISATIONNAME: ', iterationsCheck=True):
            correct = False
        if not allChecks(mta, con + PNAME):
            correct = False
        if not allChecks(mta, con + VOICE, 'VOICE: '):
            correct = False
        #if not allChecks(mta, con + FACSIMILE):
        #    correct = False
        if not allChecks(mta, con + DELIVERYPOINT, 'DELIVERYADDRESS: '):
            correct = False
        if not allChecks(mta, con + CITY, 'CITY: '):
            correct = False
        if not allChecks(mta, con + POSTALCODE, 'POSTALCODE: '):
            correct = False
        if not allChecks(mta, con + EMAIL, 'EMAIL: '):
            correct = False
        if not allChecks(mta, con + COUNTRY, 'COUNTRY: '):
            correct = False
        if not allChecks(mta, con+ROLE, role):
            correct = False

    return correct


def checkHierarchyLevel(mta):
    '''
    Check Hierarchy/ Scope Fields.
    '''
    correct = True
    if not allChecks(mta, HIERARCHYLEVEL, 'HIERARCHYLEVEL: '):
        correct = False
    if not allChecks(mta, HIERARCHYLEVELNAME, 'HIERARCHYLEVELNAME: '):
        correct = False
    if not allChecks(mta, SCOPELEVEL, 'SCOPELEVEL: '):
        correct = False
    if not allChecks(mta, SCOPELEVELDESC, 'SCOPELEVELDESC: '):
        correct = False

    return correct


def checkDateFormat(mta):
    '''
    Check date format is:
      - YYYY
      - YYYY-MM
      - YYYY-MM-DD

    '''
    correct = True
    if mta.find(DATE, namespaces=NSX) is not None:
        for val in mta.findall(DATE, namespaces=NSX):
            if val.text is not None:
                if (len(val.text) != 4 and
                    len(val.text) != 7 and len(val.text) != 10):
                    correct = False
                elif (len(val.text) == 4 and str(val.text).find('-') != -1):
                    correct = False
                elif (len(val.text) == 7 and str(val.text).count('-') != 1):
                    correct = False
                elif (len(val.text) == 10 and str(val.text).count('-') != 2):
                    correct = False
                if not correct:
                    raise MetadataIncorrectException('Invalid Date Format')
            else:
                raise MetadataEmptyException('Empty Date')
                correct = False
    else:
        raise MetadataNoneException('No Date')
        correct = False

    return correct


def checkStatus(mta):
    '''
    Check Status field not none or empty.
    '''
    return allChecks(mta, STATUS)


def checkResourceMeta(mta):
    '''
    Check Resource and Metadata Constraints,
      - Contain both 'license' and 'copyright' use constraints
      - 'license' and 'copyright' constraints contain text
      - Resource security constraint is 'unclassified'. (Metadata security constraint,
        not checked as none currently have metadata security constraint)

      - Haven't got any checks on access constraints as it seems only a few layers
        have them.
    '''
    correct = True

    # Check Resource Security Classification
    if not allChecks(mta, SECURITYC, 'SECURITYCLASS: '):
        correct = False

    for i in range(2):
        if i == 0:
            typ, code1, code2 = 'Resource', LEGALUC, LEGALUL
        else:
            typ, code1, code2 = 'Metadata', MLEGALUC, MLEGALUL

        copyright, license = 0, 0

        # Check Resource/Metadata Constraint Classification
        if mta.find(code1, namespaces=NSX) is not None:
            for val in mta.findall(code1, namespaces=NSX):
                if val.text is None:
                    raise MetadataEmptyException(
                        'Empty {} Constraint'.format(typ))
                    correct = False
                elif (val.text != 'copyright' and val.text != 'license'):
                    raise MetadataIncorrectException(
                        'Invalid/Incorrect {} Constraint'.format(typ))
                    correct = False
                elif (val.text == 'copyright'):
                    copyright += 1
                elif (val.text == 'license'):
                    license += 1
            if copyright != 1 or license != 1:
                raise MetadataIncorrectException(
                    'Missing Copyright/ License Fields')
                correct = False
        else:
            raise MetadataNoneException('No {} Constraint'.format(typ))
            correct = False

        # Check Resource/Metadata Constraint Text
        if not allChecks(mta, code2):
            correct = False

    return correct


def checkLineage(mta):
    '''
    Check Lineage field, not none or empty.
    '''
    return allChecks(mta, LINEAGE)


def checkLinkage(mta):
    '''
    Check Linkage field, not none or empty. (Added on when put on LDS?)
    '''
    return allChecks(mta, LINKAGE)


def checkExtent(mta):
    '''
    Check Extents.
      - Check an extent exists.
      - Check that bounding box exists (should be automatically added when put on LDS)
      - If contains geographic description, check that contains valid NZ description.
      - If contains geographic description, temporal or vertical element check that
      - they are not empty or none.
    '''
    extentExists = False
    descriptionExists = False
    temporalExists = False
    verticalExists = False
    boundingExists = False

    correct = True

    # Check which fields (if any exist)
    for element in mta.iter():
        if 'extent' in element.tag:
            extentExists = True
        if 'GeographicBoundingBox' in element.tag:
            boundingExists = True
        if 'GeographicDescription' in element.tag:
            descriptionExists = True
        if 'temporalElement' in element.tag:
            temporalExists = True
        if 'verticalElement' in element.tag:
            verticalExists = True

    if not extentExists:
        raise MetadataNoneException('No Extent')
        correct = False
    else:
        if not boundingExists:
            raise MetadataNoneException('No Bounding Box Extent')
            correct = False
        else:
            if not allChecks(mta, BOUNDINGBOX):
                correct = False
        if descriptionExists:
            if not allChecks(mta, DESCRIPTION, 'EXTENTDESC: '):
                correct = False
        if temporalExists:
            if not allChecks(mta, TEMPORAL):
                correct = False
        if verticalExists:
            if not allChecks(mta, VERTICAL):
                correct = False

    return correct


def checkSpatialRep(mta):
    '''
    Check Spatial Representation field, not none or empty.
    '''
    return allChecks(mta, SPATIALREP)


def checkReferenceSystem(mta, lid):
    '''
    Extract data.crs value from api, in the format 'EPSG:{CRS}' From this the value can be checked
    against reference system in metadata.

    Can only be used for layers.
    '''
    
    headers = {'Content-Type': 'application/json',
               'Authorization': 'key {}'.format(KEY)}
    
    url = 'https://data.linz.govt.nz/services/api/v1/layers/{lid}/'.format(
        lid=lid)

    try:
        response = requests.get(url, headers=headers)
        crsAct = (json.loads(response.text)['data']['crs'][5:])
        val = mta.find(REFERENCESYSINFO, namespaces = NSX)
        if val is not None and val.text is not None:
            if str(val.text) != str(crsAct):
                raise MetadataIncorrectException(
                    'Invalid/Incorrect Reference System Format,\n should be:'+ \
                    '" {}", got: "{}"'.format(crsAct, val.text))

        # Skip this as around 1500 layers don't have reference system associated
        # in metadata, although can get reference system from 'crsAct'.
        
        #else:            
            #raise MetadataNoneException(
            #'No Reference System, should be: {}'.format(crsAct))

    except MetadataNoneException as mne:
        raise MetadataNoneException(mne)
    except MetadataIncorrectException as mie:
        raise MetadataIncorrectException(mie)
    except Exception as e:
        raise InaccessibleLayerException('HTTP {0} calling [{1}]'.format(
            response.status_code, url), e)


def runAllChecks(mta, lid):
    '''
    Run all available checks.
    '''
    current = sys.modules[__name__]
    methods = [i for i in dict(inspect.getmembers(current)) if i[:5]=='check']
    methods.sort()
    for i in methods:
        if i == 'checkReferenceSystem':
            getattr(current, i)(mta, lid[0])
        else:
            getattr(current, i)(mta)


def runBasicChecks(mta):
    '''
    Run only Address, Date Format, Extent and Resource/Metadata Copyright checks
    '''
    checkAddress(mta)
    checkDateFormat(mta)
    checkExtent(mta)
    checkResourceMeta(mta)

def main():
    vdtr = Remote()
    #layers = ('50201','50972','50202','50203','51083','50665','50648','52233'
    #                '52344', '51362','51920','50772', '50789', '53451',
    #                '53519','50845','51306','50846','51368','51389',)
    layers = vdtr.getids('wfs')
    for lay in layers:
        try:
            meta = vdtr.metadata(lay)
            #checkReferenceSystem(meta, lay)
            runAllChecks(meta,lay)
            #runBasicChecks(meta)
            print (lay, True)
        except MetadataErrorException as mee:
            print (lay, mee, False)
        except Exception as e:
            print (lay, e, False)

if __name__ == '__main__':
    main()
