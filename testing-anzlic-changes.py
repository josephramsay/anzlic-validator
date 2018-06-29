"""
Testing Mapping between current 19115 to 19115-3

Testing Validation of converted 19115-3, to schema,
(Currently gets 'No matching global declaration available for the validation
root.' error.)
(Shouldn't validate as doesn't have codelist values added as well as changes to
time & voice.
"""

from lxml import etree, isoschematron
import re
import sys
import urllib2

sys.path.append('/home/aross/.qgis2/python/plugins/anzlic-validator')

# Set Namespaces
# NSX = {'xlink': 'http://www.w3.org/1999/xlink',
#        'gco': 'http://www.isotc211.org/2005/gco',
#        'gmd': 'http://www.isotc211.org/2005/gmd',
#        'gts': 'http://www.isotc211.org/2005/gts',
#        'gml': 'http://www.opengis.net/gml'}

NSX = {'xsi':   'http://www.w3.org/2001/XMLSchema-instance',
       'cat':   'http://standards/iso.org/19115/-3/cat/1.0',
       'cit':   'http://standards/iso.org/19115/-3/cit/1.0',
       'gcx':   'http://standards/iso.org/19115/-3/gcx/1.0',
       'gex':   'http://standards/iso.org/19115/-3/gex/1.0',
       'lan':   'http://standards/iso.org/19115/-3/lan/1.0',
       'srv':   'http://standards/iso.org/19115/-3/srv/1.0',
       'mas':   'http://standards/iso.org/19115/-3/mas/1.0',
       'mcc':   'http://standards/iso.org/19115/-3/mcc/1.0',
       'mco':   'http://standards/iso.org/19115/-3/mco/1.0',
       'mda':   'http://standards/iso.org/19115/-3/mda/1.0',
       'mdb':   'http://standards/iso.org/19115/-3/mdb/1.0',
       'mds':   'http://standards/iso.org/19115/-3/mds/1.0',
       'mdt':   'http://standards/iso.org/19115/-3/mdt/1.0',
       'mex':   'http://standards/iso.org/19115/-3/mex/1.0',
       'mmi':   'http://standards/iso.org/19115/-3/mmi/1.0',
       'mpc':   'http://standards/iso.org/19115/-3/mpc/1.0',
       'mrc':   'http://standards/iso.org/19115/-3/mrc/1.0',
       'mrd':   'http://standards/iso.org/19115/-3/mrd/1.0',
       'mri':   'http://standards/iso.org/19115/-3/mri/1.0',
       'mrl':   'http://standards/iso.org/19115/-3/mrl/1.0',
       'mrs':   'http://standards/iso.org/19115/-3/mrs/1.0',
       'msr':   'http://standards/iso.org/19115/-3/msr/1.0',
       # 'mdq':   'http://standards/iso.org/19157/-2/mdq/1.0',
       'mac':   'http://standards/iso.org/19115/-3/mac/1.0',
       'gco':   'http://standards/iso.org/19115/-3/gco/1.0',
       'gml':   'http://www.opengis.net/gml/3.2',
       'xlink': 'http://www.w3.org/1999/xlink'}

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
ACCESSCONST = '/gmd:MD_LegalConstraints/gmd:accessConstraints/gmd:MD_' + \
              'RestrictionCode'
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
RESOURCEACCESS = ID + '/gmd:resourceConstraints' + ACCESSCONST

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
METAACCESS = MD + '/gmd:metadataConstraints' + ACCESSCONST

paths = (FID, LAN, CHSET, HLEVEL, HLEVELNAME, INAME, ONAME, PNAME, VOICE, FACS,
         DELIVERYPOINT, CITY, POSTALCODE, COUNTRY, EMAIL, ROLE, DSTAMP, MSN,
         MSV, RS, TITLE, ALTTITLE, CITDATE, CITDATETYPE, ABSTRACT, PURPOSE,
         STATUS, POCINAME, POCONAME, POCPNAME, POCVOICE, POCFACS,
         POCDELIVERYPOINT, POCCITY, POCCOUNTRY, POCPOSTALCODE, POCEMAIL,
         POCROLE, RMAINTCODE, RMAINTDATE, RFORMATN, RFORMATV, KEYWORDS,
         KEYWORDSTYPE, CLASSIFCODE, RESOURCELIMIT, RESOURCEUSE, SPATIALREP,
         SCALE, RESOLUTION, IDENTLAN, IDENTCS, TOPIC, EXTENTDES, EXTENTBBW,
         EXTENTBBE, EXTENTBBN, EXTENTBBS, TSINGLE, TBEGIN, TEND, LINKAGE, SCOPE,
         SCOPEDESC, LINEAGE, MCLASSIFCODE, METALIMIT, METAUSE, METAACCESS,
         RESOURCEACCESS)
# ------------------------------------------------------------------------------
MD = 'mdb:MD_Metadata'
CONTACT = MD + '/mdb:contact/cit:CI_Responsibility'
CONTACTPARTY = CONTACT + '/cit:party/cit:CI_Organisation'
ADDRESS = CONTACTPARTY + '/cit:contactInfo/cit:CI_Contact/cit:address/cit:' + \
          'CI_Address'
IDENT = MD + '/mdb:identificationInfo/mri:MD_DataIdentification'
CITATION = IDENT + '/mri:citation/cit:CI_Citation'
PCONTACT = IDENT + '/mri:pointOfContact/cit:CI_Responsibility'
PCONTACTPARTY = PCONTACT + '/cit:party/cit:CI_Organisation'
PADDRESS = PCONTACTPARTY + '/cit:contactInfo/cit:CI_Contact/cit:address/' + \
           'cit:CI_Address'

FID3 = MD + '/mdb:metadataIdentifier/mcc:MD_Identifier/mcc:code/gco:' + \
       'CharacterString'
LAN3 = MD + '/mdb:defaultLocale/lan:PT_Locale/lan:language/lan:LanguageCode'
CHSET3 = MD + '/mdb:defaultLocale/lan:PT_Locale/lan:characterEncoding/lan:' + \
         'MD_CharacterSetCode'
HLEVEL3 = MD + '/mdb:metadataScope/mdb:MD_MetadataScope/mdb:resourceScope/' + \
          'mcc:MD_ScopeCode'
HLEVELNAME3 = MD + '/mdb:metadataScope/mdb:MD_MetadataScope/mdb:name/gco:' + \
              'CharacterString'

INAME3 = CONTACTPARTY + '/cit:individual/cit:CI_Individual/cit:name/gco:' + \
         'CharacterString'
ONAME3 = CONTACTPARTY + '/cit:name/gco:CharacterString'
PNAME3 = CONTACTPARTY + '/cit:individual/cit:CI_Individual/cit:positionName' + \
    '/gco:CharacterString'
VOICE3 = CONTACTPARTY + '/cit:contactInfo/cit:CI_Contact/cit:phone/cit:CI_' + \
         'Telephone/cit:number/gco:CharacterString'
VOICETYPE3 = CONTACTPARTY + '/cit:contactInfo/cit:CI_Contact/cit:phone/cit' + \
    ':CI_Telephone/cit:numberType/cit:CI_TelephoneTypeCode'
DELIVERYPOINT3 = ADDRESS + '/cit:deliveryPoint/gco:CharacterString'
CITY3 = ADDRESS + '/cit:city/gco:CharacterString'
POSTALCODE3 = ADDRESS + '/cit:postalCode/gco:CharacterString'
COUNTRY3 = ADDRESS + '/cit:country/gco:CharacterString'
EMAIL3 = ADDRESS + '/cit:electronicMailAddress/gco:CharacterString'
ROLE3 = CONTACT + '/cit:role/cit:CI_RoleCode'

DSTAMP3 = MD + '/mdb:dateInfo/cit:CI_Date/cit:date/gco:DateTime'

MSN3 = MD + '/mdb:metadataStandard/cit:CI_Citation/cit:title/gco:Character' + \
       'String'
MSV3 = MD + '/mdb:metadataStandard/cit:CI_Citation/cit:edition/gco:' + \
       'CharacterString'

RS3 = MD + '/mdb:referenceSystemInfo/mrs:MD_ReferenceSystemIdentifier/mcc:' + \
      'MD_Identifier/mcc:code/gco:CharacterString'

TITLE3 = CITATION + '/cit:title/gco:CharacterString'
ALTTITLE3 = CITATION + '/cit:alternateTitle/gco:CharacterString'
CITDATE3 = CITATION + '/cit:date/cit:CI_Date/cit:date/gco:DateTime'
CITDATETYPE3 = CITATION + '/cit:date/cit:CI_Date/cit:dateType/cit:CI_Date' + \
               'TypeCode'
ABSTRACT3 = IDENT + '/mri:abstract/gco:CharacterString'
PURPOSE3 = IDENT + '/mri:purpose/gco:CharacterString'
STATUS3 = IDENT + '/mri:status/mri:MD_ProgressCode'

POCINAME3 = PCONTACTPARTY + '/cit:individual/cit:CI_Individual/cit:name/' + \
            'gco:CharacterString'
POCONAME3 = PCONTACTPARTY + '/cit:name/gco:CharacterString'
POCPNAME3 = PCONTACTPARTY + '/cit:individual/cit:CI_Individual/cit:position' + \
            'Name/gco:CharacterString'
POCVOICE3 = PCONTACTPARTY + '/cit:contactInfo/cit:CI_Contact/cit:phone/cit:' + \
            'CI_Telephone/cit:number/gco:CharacterString'
POCVOICETYPE3 = PCONTACTPARTY + '/cit:contactInfo/cit:CI_Contact/cit:phone/' + \
                'cit:CI_Telephone/cit:numberType/cit:CI_TelephoneTypeCode'
POCDELIVERYPOINT3 = PADDRESS + '/cit:deliveryPoint/gco:CharacterString'
POCCITY3 = PADDRESS + '/cit:city/gco:CharacterString'
POCPOSTALCODE3 = PADDRESS + '/cit:postalCode/gco:CharacterString'
POCCOUNTRY3 = PADDRESS + '/cit:country/gco:CharacterString'
POCEMAIL3 = PADDRESS + '/cit:electronicMailAddress/gco:CharacterString'
POCROLE3 = PCONTACT + '/cit:role/cit:CI_RoleCode'

RMAINTCODE3 = IDENT + '/mri:resourceMaintenance/mmi:MD_Maintenance' + \
              'Information/mmi:maintenanceAndUpdateFrequency/mmi:MD_' + \
              'MaintenanceFrequencyCode'
RMAINTDATE3 = IDENT + '/mri:resourceMaintenance/mmi:MD_Maintenance' + \
              'Information/mmi:maintenanceDate/cit:CI_Date/cit:date/' + \
              'gco:DateTime'
RMAINTDATETYPE3 = IDENT + '/mri:resourceMaintenance/mmi:MD_Maintenance' + \
                  'Information/mmi:maintenanceDate/cit:CI_Date/cit:dateType' + \
                  '/cit:CI_DateTypeCode'
RFORMATN3 = IDENT + '/mri:resourceFormat/mrd:MD_Format/mrd:format' + \
            'SpecificationCitation/cit:CI_Citation/cit:title/gco:' + \
            'CharacterString'
RFORMATV3 = IDENT + '/mri:resourceFormat/mrd:MD_Format/mrd:format' + \
            'SpecificationCitation/cit:CI_Citation/cit:edition/gco:' + \
            'CharacterString'
KEYWORDS3 = IDENT + '/mri:descriptiveKeywords/mri:MD_Keywords/mri:' + \
            'keyword/gco:CharacterString'
KEYWORDSTYPE3 = IDENT + '/mri:descriptiveKeywords/mri:MD_Keywords/mir:' + \
                'type/mri:MD_KeywordTypeCode'
CLASSIFCODE3 = IDENT + '/mri:resourceConstraints/mco:MD_SecurityConstraints' + \
    '/mco:classification/mco:MD_ClassificationCode'
RESOURCELIMIT3 = IDENT + '/mri:resourceConstraints/mco:MD_LegalConstraints' + \
    '/mco:useLimitation/gco:CharacterString'
RESOURCEUSE3 = IDENT + '/mri:resourceConstraints/mco:MD_LegalConstraints/' + \
               'mco:useConstraints/mco:MD_RestrictionCode'
RESOURCEACCESS3 = IDENT + '/mri:resourceConstraints/mco:MD_LegalConstraints' + \
    '/mco:accessConstraints/mco:MD_RestrictionCode'
SPATIALREP3 = IDENT + '/mri:spatialRepresentationType/mri:MD_Spatial' + \
              'RepresenationTypeCode'
SCALE3 = IDENT + '/mri:spatiaLResolution/mri:MD_Resolution/mri:equivalent' + \
         'Scale/mri:MD_RepresentativeFraction/mri:denominator/gco:Integer'
RESOLUTION3 = IDENT + '/mri:spatialResolution/mri:MD_Resolution/mri:' + \
              'distance/gco:Distance'
IDENTLAN3 = IDENT + '/mri:defaultLocale/lan:PT_Locale/lan:language/lan:' + \
            'LanguageCode'
IDENTCS3 = IDENT + '/mri:defaultLocale/lan:PT_Locale/lan:characterEncoding/' + \
           'lan:MD_CharacterSetCode'

TOPIC3 = IDENT + '/mri:topicCategory'

EXTENTDES3 = IDENT + '/mri:extent/gex:EX_Extent/gex:geographicElement/' + \
             'gex:EX_GeographicDescription/gex:geographicIdentifier/mcc:MD_' + \
             'Identifier/mcc:code/gco:CharacterString'
EXTENTBBW3 = IDENT + '/mri:extent/gex:EX_Extent/gex:geographicElement/' + \
             'gex:EX_GeographicBoundingBox/gex:westBoundLongitude/gco:Decimal'
EXTENTBBE3 = IDENT + '/mri:extent/gex:EX_Extent/gex:geographicElement/' + \
             'gex:EX_GeographicBoundingBox/gex:eastBoundLongitude/gco:Decimal'
EXTENTBBN3 = IDENT + '/mri:extent/gex:EX_Extent/gex:geographicElement/' + \
             'gex:EX_GeographicBoundingBox/gex:northBoundLatitude/gco:Decimal'
EXTENTBBS3 = IDENT + '/mri:extent/gex:EX_Extent/gex:geographicElement/' + \
             'gex:EX_GeographicBoundingBox/gex:southBoundLatitude/gco:Decimal'
TSINGLE3 = ''

TBEGIN3 = IDENT + '/mri:extent/gex:EX_Extent/gex:temporalElement/' + \
          'gex:EX_TemporalExtent/gex:extent/gml:TimePeriod/gml:begin/' + \
          'gml:TimeInstant/gml:timePosition'
TEND3 = IDENT + '/mri:extent/gex:EX_Extent/gex:temporalElement/gex:EX_' + \
        'TemporalExtent/gex:extent/gml:TimePeriod/gml:end/gml:TimeInstant/' + \
        'gml:timePosition'
LINKAGE3 = MD + '/mdb:distributionInfo/mrd:MD_Distribution/mrd:transfer' + \
           'Options/mrd:MD_DigitalTransferOptions/mrd:onLine/cit:CI_Online' + \
           'Resource/cit:linkage/gco:CharacterString'
SCOPE3 = MD + '/mdb:dataQualityInfo/mdq:DQ_DataQuality/mdq:scope/mcc:MD_' + \
         'Scope/mcc:level/mcc:MD_ScopeCode'
SCOPEDESC3 = MD + '/mdb:dataQualityInfo/mdq:DQ_DataQuality/mdq:scope/mcc:' + \
             'MD_Scope/mcc:levelDescription/mcc:MD_ScopeDescription/mcc:' + \
             'other/gco:CharacterString'
LINEAGE3 = MD + '/mdb:resourceLineage/mrl:LI_Lineage/mrl:statement/gco:' + \
           'CharacterString'
MCLASSIFCODE3 = MD + '/mdb:metadataConstraints/mco:MD_SecurityConstraints' + \
    '/mco:classification/mco:MD_ClassificationCode'
METALIMIT3 = MD + '/mdb:metadataConstraints/mco:MD_LegalConstraints/mco:' + \
             'useLimitation/gco:CharacterString'
METAUSE3 = MD + '/mdb:metadataConstraints/mco:MD_LegalConstraints/mco:use' + \
           'Constraints/mco:MD_RestrictionCode'
METAACCESSCONST3 = MD + '/mdb:metadataConstraints/mco:MD_LegalConstraints' + \
    '/mco:accessConstraints/mco:MD_RestrictionCode'
newpaths = {FID:                FID3,  # Also Need to add TSINGLE
            LAN:                LAN3,
            CHSET:              CHSET3,
            HLEVEL:             HLEVEL3,
            HLEVELNAME:         HLEVELNAME3,
            INAME:              INAME3,
            ONAME:              ONAME3,
            PNAME:              PNAME3,
            VOICE:              VOICE3,  # Needs Voice Type Added
            FACS:               VOICE3,  # Needs Voice Type Added
            DELIVERYPOINT:      DELIVERYPOINT3,
            CITY:               CITY3,
            POSTALCODE:         POSTALCODE3,
            COUNTRY:            COUNTRY3,
            EMAIL:              EMAIL3,
            ROLE:               ROLE3,
            MSN:                MSN3,
            MSV:                MSV3,
            RS:                 RS3,
            TITLE:              TITLE3,
            ALTTITLE:           ALTTITLE3,
            CITDATE:            CITDATE3,  # Changes to include time
            CITDATETYPE:        CITDATETYPE3,
            ABSTRACT:           ABSTRACT3,
            PURPOSE:            PURPOSE3,
            STATUS:             STATUS3,
            POCINAME:           POCINAME3,
            POCONAME:           POCONAME3,
            POCPNAME:           POCPNAME3,
            POCDELIVERYPOINT:   POCDELIVERYPOINT3,
            POCCITY:            POCCITY3,
            POCPOSTALCODE:      POCPOSTALCODE3,
            POCCOUNTRY:         POCCOUNTRY3,
            POCEMAIL:           POCEMAIL3,
            POCROLE:            POCROLE3,
            POCVOICE:           POCVOICE3,  # Needs Voice Type Added
            POCFACS:            POCVOICE3,  # Needs Voice Type Added
            RMAINTCODE:         RMAINTCODE3,
            RMAINTDATE:         RMAINTDATE3,
            RFORMATN:           RFORMATN3,
            RFORMATV:           RFORMATV3,
            KEYWORDS:           KEYWORDS3,
            KEYWORDSTYPE:       KEYWORDSTYPE3,
            CLASSIFCODE:        CLASSIFCODE3,
            RESOURCELIMIT:      RESOURCELIMIT3,
            RESOURCEUSE:        RESOURCEUSE3,
            SPATIALREP:         SPATIALREP3,
            RESOLUTION:         RESOLUTION3,  # Also Has Units
            IDENTLAN:           IDENTLAN3,
            IDENTCS:            IDENTCS3,
            TOPIC:              TOPIC3,
            SCALE:              SCALE3,
            EXTENTDES:          EXTENTDES3,
            EXTENTBBW:          EXTENTBBW3,
            EXTENTBBE:          EXTENTBBE3,
            EXTENTBBN:          EXTENTBBN3,
            EXTENTBBS:          EXTENTBBS3,
            TBEGIN:             TBEGIN3,
            TEND:               TEND3,
            LINKAGE:            LINKAGE3,
            # SCOPE:              SCOPE3,
            # SCOPEDESC:          SCOPEDESC3,
            LINEAGE:            LINEAGE3,
            MCLASSIFCODE:       MCLASSIFCODE3,
            METALIMIT:          METALIMIT3,
            METAUSE:            METAUSE3,
            METAACCESS:         METAACCESSCONST3,
            RESOURCEACCESS:     RESOURCEACCESS3,
            DSTAMP:             DSTAMP3}  # Changes to include time

orderedNew = (FID3, LAN3, CHSET3, HLEVEL3, HLEVELNAME3, ROLE3, ONAME3, VOICE3,
              DELIVERYPOINT3, CITY3, POSTALCODE3, COUNTRY3, EMAIL3, INAME3,
              PNAME3, DSTAMP3, MSN3, MSV3, RS3, TITLE3, ALTTITLE3,
              CITDATE3, CITDATETYPE3, ABSTRACT3, PURPOSE3, STATUS3, POCROLE3,
              POCONAME3, POCVOICE3, POCDELIVERYPOINT3, POCCITY3, POCPOSTALCODE3,
              POCCOUNTRY3, POCEMAIL3, POCINAME3, POCPNAME3, SPATIALREP3,
              RESOLUTION3, SCALE3, TOPIC3, EXTENTBBW3, EXTENTBBE3, EXTENTBBS3,
              EXTENTBBN3, EXTENTDES3, TBEGIN3, TEND3, RMAINTCODE3, RMAINTDATE3,
              RFORMATN3, RFORMATV3, KEYWORDS3, KEYWORDSTYPE3, RESOURCELIMIT3,
              RESOURCEUSE3, RESOURCEACCESS3, CLASSIFCODE3, IDENTLAN3, IDENTCS3,
              LINKAGE3, SCOPE3, SCOPEDESC3, LINEAGE3, METAUSE3, METALIMIT3,
              METAACCESSCONST3, MCLASSIFCODE3)

print 'Mapping: '
for i in newpaths:
    print '{} -> {}'.format(i, newpaths[i])

print

xmlFile = '/home/aross/Downloads/XML Files/bay-of-plenty-025m-rural-aerial' + \
          '-photos-2011-2012.iso.xml'
meta = etree.parse(xmlFile)
output = {}

for i in meta.iter():
    if i.text is not None and i.text != '':
        if re.sub('\[+.+?\]', '', meta.getpath(i)) in paths:
            if re.sub('\[+.+?\]', '', meta.getpath(i)) in newpaths:
                npath = (newpaths[re.sub('\[+.+?\]', '', meta.getpath(i))])
                if npath in output:
                    output[npath] = output[npath] + (i.text.encode('utf-8'),)
                else:
                    output[npath] = (i.text.encode('utf-8'),)
                # print (npath)
            else:
                print ('{} not in newpaths.\nHas {}'.format(
                    re.sub('\[+.+?\]', '', meta.getpath(i)),
                    i.text.encode('utf-8')))
        elif i.text:
            print ('{} not in paths.\nHas {}'.format(
                re.sub('\[+.+?\]', '', meta.getpath(i)),
                i.text.encode('utf-8')))

md = etree.Element('{http://standards/iso.org/19115/-3/mdb/1.0}MD_Metadata',
                   nsmap=NSX)
tree = etree.ElementTree(md)

for i in orderedNew:
    if i in output:
        tup, times = False, 1
        if type(output[i]) == tuple:
            times = len(output[i])
            tup = True

        for it in range(times):
            if tup:
                text = output[i][times-1]
            else:
                text = output[i]
            base, insert, found = '', '', None
                        
            for val in i[16:].split('/'):
                if md.find(base + val, namespaces=NSX) is not None:
                    found = base + val
                base += (val + '/')
    
            if base.rfind('/') == len(base)-1:
                base = base[:len(base)-1]

            if not found:
                insert = base
                f = tree.getroot()
            else:
                insert = base.split(found)[1][1:]
                f = tree.find(found, namespaces=NSX)

            if insert.rfind('/') == len(insert)-1:
                insert = insert[:len(insert)-1]
            if insert and insert != '':
                for k in insert.split('/'):
                    j = (k.split(':'))
                    element = etree.SubElement(f, etree.QName(NSX[j[0]], j[1]))
                    f = element
                f.text = text.decode('utf-8')
                

out = etree.tostring(md, pretty_print=True)
print out
with open('temp.xml', 'wb') as f:
    f.write(out)

sch = urllib2.urlopen('http://standards.iso.org/iso/19115/-3/mdb/1.0/mdb.xsd')
# sch = open('/home/aross/Downloads/19115/-3/mdb/1.0/mdb.xsd')
# print sch
# with open('/home/aross/Downloads/19115/-3/mdb/1.0/mdb.xsd') as f:
#    sch = f.read()
sch_doc = etree.parse(sch)

# print sch_doc
schema = etree.XMLSchema(sch_doc)
# schema = isoschematron.Schematron(sch_doc)

print schema.validate(md)
print schema.error_log
print schema.error_log.last_error
meta = urllib2.urlopen('http://standards.iso.org/iso/19115/-3/mdb/1.0/' +
                       'AppendixD.1MinimalExample.xml')
meta = etree.parse(meta)
print schema.validate(meta)
