#!/usr/bin/python
'''
Python Script which checks every layer & table on LDS & Extracts Contact 
Information. From Contact and Point of Contact Fields.  

These fields extracted into a csv document along with the layer id.

In the case that any fields don't exist or are empty the text 'None' is put in 
place.
'''

import os
import sys
import urllib2
from urllib2 import HTTPError, ProxyHandler, URLError
from lxml import etree
import koordinates

# Set LDS API Key
API_KEY = ''
HOST = 'data.linz.govt.nz'

OUTPUT_CSV = open('allMetadata.csv', 'w')

ERROR_LOG = open('allMetadataCheck.log', 'w')

TEMP_FILE = 'allMetadataCheck_temp.xml'

LAYER_TYPE = type(koordinates.layers.Layer())


NSX = {'gmd' : 'http://www.isotc211.org/2005/gmd',
       'gco' : 'http://www.isotc211.org/2005/gco'}

FILEID = 'gmd:fileIdentifier/gco:CharacterString'
LANGUAGE = 'gmd:language/gco:CharacterString'
CHARSET = 'gmd:characterSet/gmd:MD_CharacterSetCode'

HIERARCHYLEVEL = 'gmd:hierarchyLevel/gmd:MD_ScopeCode'
HIERARCHYLEVELNAME = 'gmd:hierarchyLevelName/gco:CharacterString'

IDENT = 'gmd:identificationInfo/gmd:MD_DataIdentification'

CONTACTM = 'gmd:contact'
POINTOFCONTACT = IDENT + '/gmd:pointOfContact'

CONTACT = '/gmd:CI_ResponsibleParty'

INAME = CONTACT + '/gmd:individualName/gco:CharacterString'
ONAME = CONTACT + '/gmd:organisationName/gco:CharacterString'
PNAME = CONTACT + '/gmd:positionName/gco:CharacterString'
CONTACTINFO = CONTACT + '/gmd:contactInfo/gmd:CI_Contact'
PHONE = CONTACTINFO + '/gmd:phone/gmd:CI_Telephone'
VOICE = PHONE + '/gmd:voice/gco:CharacterString'
FACSIMILE = PHONE + '/gmd:facsimile/gco:CharacterString'
ADDRESS = CONTACTINFO + '/gmd:address/gmd:CI_Address'
DELIVERYPOINT = ADDRESS + '/gmd:deliveryPoint/gco:CharacterString'
CITY = ADDRESS + '/gmd:city/gco:CharacterString'
ADMINISTRATIVEAREA = ADDRESS + '/gmd:administrativeArea/gco:CharacterString'
POSTALCODE = ADDRESS + '/gmd:postalCode/gco:CharacterString'
COUNTRY = ADDRESS + '/gmd:country/gco:CharacterString'
EMAIL = ADDRESS + '/gmd:electronicMailAddress/gco:CharacterString'
ROLE = CONTACT + '/gmd:role/gmd:CI_RoleCode'

DATESTAMP = 'gmd:dateStamp/gco:Date'
METSTANDARDNAME = 'gmd:metadataStandardName/gco:CharacterString'
METSTANDARDVER = 'gmd:metadataStandardVersion/gco:CharacterString'
REFERENCESYSINFO = 'gmd:referenceSystemInfo/gmd:MD_ReferenceSystem/gmd:referenceSystemIdentifier/gmd:RS_Identifier/gmd:code/gco:CharacterString'

TITLE = IDENT + '/gmd:citation/gmd:CI_Citation/gmd:title/gco:CharacterString'
ALTTITLE = IDENT + '/gmd:citation/gmd:CI_Citation/gmd:alternateTitle/gco:CharacterString'
DATE = IDENT + '/gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date/gmd:date/gco:Date'
DATETYPE = IDENT + '/gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date/gmd:dateType/gmd:CI_DateTypeCode'
OTHERCITATION = IDENT + '/gmd:citation/gmd:CI_Citation/gmd:otherCitationDetails/gco:CharacterString'
ABSTRACT = IDENT + '/gmd:abstract/gco:CharacterString'
PURPOSE = IDENT + '/gmd:purpose/gco:CharacterString'
STATUS = IDENT + '/gmd:status/gmd:MD_ProgressCode'

MAINTENANCE = IDENT + '/gmd:resourceMaintenance/gmd:MD_MaintenanceInformation/gmd:maintenanceAndUpdateFrequency/gmd:MD_MaintenanceFrequencyCode'
MAINTENANCEUPDATE = IDENT + '/gmd:resourceMaintenance/gmd:MD_MaintenanceInformation/gmd:dateOfNextUpdate/gco:Date'

FORMATNAME = IDENT + '/gmd:resourceFormat/gmd:MD_Format/gmd:name/gco:CharacterString'
FROMATTYPE = IDENT + '/gmd:resourceFormat/gmd:MD_Format/gmd:version/gco:CharacterString'

KEYWORD = IDENT + '/gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:keyword/gco:CharacterString'
KEYWORDTYPE = IDENT + '/gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:type/gmd:MD_KeywordTypeCode'

RESOURCECONSTRAINT = IDENT + '/gmd:resourceConstraints'
SECURITYUL = RESOURCECONSTRAINT + '/gmd:MD_SecurityConstraints/gmd:useLimitation/gco:CharacterString'
SECURITYC = RESOURCECONSTRAINT + '/gmd:MD_SecurityConstraints/gmd:classification/gmd:MD_ClassificationCode'

LEGALUL = RESOURCECONSTRAINT + '/gmd:MD_LegalConstraints/gmd:useLimitation/gco:CharacterString'
LEGALA = RESOURCECONSTRAINT + '/gmd:MD_LegalConstraints/gmd:accessConstraints/gmd:MD_RestrictionCode'
LEGALUC = RESOURCECONSTRAINT + '/gmd:MD_LegalConstraints/gmd:useConstraints/gmd:MD_RestrictionCode'

SPATIALREP = IDENT + '/gmd:spatialRepresentationType/gmd:MD_SpatialRepresentationTypeCode'

SCALEDISTANCE = IDENT + '/gmd:spatialResolution/gmd:MD_Resolution/gmd:distance/gco:Distance'
SCALEEQUIVALENT = IDENT + '/gmd:spatialResolution/gmd:MD_Resolution/gmd:equivalentScale/gmd:MD_RepresentativeFraction/gmd:denominator/gco:Integer'

LANG2 = IDENT + '/gmd:language/gco:CharacterString'
CHARSET2 = IDENT + '/gmd:characterSet/gmd:MD_CharacterSetCode'

TOPICCATEGORY = IDENT + '/gmd:topicCategory/gmd:MD_TopicCategoryCode'

EXTENT = IDENT + '/gmd:extent/gmd:EX_Extent/gmd:geographicElement/'
BOUNDINGBOX = EXTENT + '/gmd:EX_GeographicBoundingBox'
DESCRIPTION = EXTENT + '/gmd:EX_GeographicDescription'
TEMPORAL = IDENT + '/gmd:extent/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent'
VERTICAL = IDENT + '/gmd:extent/gmd:EX_EXtent/gmd:verticalElement/gmd:EX_VerticalExtent'

DQ = 'gmd:dataQualityInfo/gmd:DQ_DataQuality'
SCOPELEVEL = DQ + '/gmd:scope/gmd:DQ_Scope/gmd:level/gmd:MD_ScopeCode'
SCOPELVELDESC = DQ + '/gmd:scope/gmd:DQ_Scope/gmd:levelDescription/gmd:MD_ScopeDescription/gmd:other/gco:CharacterString'
LINEAGE = DQ + '/gmd:lineage/gmd:LI_Lineage/gmd:statement/gco:CharacterString'
METACONSTRAINTS = 'gmd:metadataConstraints'
MSECURITYUL = METACONSTRAINTS + '/gmd:MD_SecurityConstraints/gmd:useLimitation/gco:CharacterString'
MSECURITYC = METACONSTRAINTS + '/gmd:MD_SecurityConstraints/gmd:classificaiton/gmd:MD_ClassificationCode'

MLEGALUL = METACONSTRAINTS + '/gmd:MD_LegalConstraints/gmd:useLimitation/gco:CharacterString'
MLEGALA = METACONSTRAINTS + '/gmd:MD_LegalConstraints/gmd:accessConstraints/gmd:MD_RestrictionCode'
MLEGALUC = METACONSTRAINTS + '/gmd:MD_LegalConstraints/gmd:useConstraints/gmd:MD_RestrictionCode'


DEFAULT = 'None \t'
layer_text = ""
layer_url = ""

# Set Default Encoding.
reload(sys)  
sys.setdefaultencoding('utf8')


def add_layer_text(layer_text, root, VALUE):
    if root.find(VALUE, namespaces=NSX) is not None:
	for val in root.findall(VALUE, namespaces=NSX):
	    if val.text is not None:
		layer_text += ((val.text + ' | ').replace('\n', ' ').replace('\t', ' '))
	    else:
		layer_text += ('empty |')
	layer_text += ('\t') 
    else:
	layer_text += DEFAULT
    return layer_text  


HEADING = 'LAYER ID\t FILE ID\t LANGUAGE\t CHARSET\t HIERARCHY LEVEL\t HIERARCHY LEVEL NAME\t   \
           INDIVIDUAL NAME 1\t ORGANISATION NAME 1\t POSTITION NAME 1\t VOICE 1\t FACSIMILE 1\t \
           DELIVERY POINT 1\t CITY 1\t ADMINISTRATIVE AREA 1\t POSTAL CODE 1\t COUNTRY 1\t \
           EMAIL 1\t ROLE 1\tINDIVIDUAL NAME 2\t ORGANISATION NAME 2\t POSTITION NAME 2\t \
           VOICE 2\t FACSIMILE 2\t DELIVERY POINT 2\t CITY 2\t ADMINISTRATIVE AREA 2\t \
           POSTAL CODE 2\t COUNTRY 2\t EMAIL 2\t ROLE 2\t DATESTAMP\t STANDARD NAME\t \
           STANDARD VERSION\t REFERENCE SYSTEM\t TITLE\t ALT TITLE\t DATE\t DATE TYPE\t \
           OTHER CITATION\t ABSTRACT\t PURPOSE\t STATUS\t MAINTENANCE\t UPDATE\t FORMAT NAME\t \
           Format TYPE\t KEYWORD\t KEYWORD TYPE\t SECURITY USE LIMITATION\t SECURITY \
           CLASSIFICATION\t RESOURCE USE LIMITATION\t RESOURCE ACCESS CONSTRAINT \t RESOURCE USE \
           CONSTRAINT\t SPATIAL REPRESENTATION\t SCALE DISTANCE\t SCALE EQUIVALENT\t \
           LANGUAGE\t CHARSET\t TOPIC CATEGORY\t EXTENT\t SCOPE LEVEL\t SCOPE LEVEL \
           DESCRIPTION\t LINEAGE\t METADATA SECURITY USE LIMITATION\t METADATA SECURITY \
           CLASSIFICATION\t METADATA USE LIMITATION\t METADATA ACCESS CONSTRAINT\t \
           METADATA USE CONSTRAINT\t URL\n'
           
OUTPUT_CSV.write(HEADING)
client = koordinates.Client(host=HOST, token=API_KEY)
TOTAL = len(client.catalog.list())
current = 0
for layer_item in client.catalog.list().filter(public='true'):
    current += 1
    if current % 5 == 0:
	print 'LAYER {}/{}'.format(current, TOTAL)
	OUTPUT_CSV.write(layer_text)
	OUTPUT_CSV.flush()
	layer_text = ""
	sys.stdout.flush()
    
    if type(layer_item) == LAYER_TYPE:
	try:
	    os.remove(TEMP_FILE)
	except OSError:
	    pass
	layer_id = layer_item.id
	layer_url = layer_item.url
	get_attempts = 0
	while get_attempts <=2:
	    get_attempts += 1
	    try:
		layer = client.layers.get(layer_item.id)
	    except koordinates.exceptions.ServerError as e:
		ERROR_LOG.write("Koordinates Server Error: {}\n".format(e))
	    if layer:
		break
	if not layer:
	    ERROR_LOG.write("Error: {}, THIS LAYER NOT PROCESSED\n".format(layer_id))
	    continue
	
	if layer.metadata is None:
	    ERROR_LOG.write("Error: {}, THIS LAYER NOT PROCESSED, NO METADATA\n".format(layer_id))
	    continue
	
	layer.metadata.get_xml(TEMP_FILE)
	tree = etree.parse(TEMP_FILE)
	root = tree.getroot()
	layer_text += (str(layer_id) + '\t')
	
	layer_text += add_layer_text(layer_text, root, FILEID)
	layer_text += add_layer_text(layer_text, root, LANGUAGE)
	layer_text += add_layer_text(layer_text, root, CHARSET)
	layer_text += add_layer_text(layer_text, root, HIERARCHYLEVEL)  
	layer_text += add_layer_text(layer_text, root, HIERARCHYLEVELNAME) 
    
	layer_text += add_layer_text(layer_text, root, CONTACTM + INAME) 
	layer_text += add_layer_text(layer_text, root, CONTACTM + ONAME) 
	layer_text += add_layer_text(layer_text, root, CONTACTM + PNAME)
	layer_text += add_layer_text(layer_text, root, CONTACTM + VOICE)    
	layer_text += add_layer_text(layer_text, root, CONTACTM + FACSIMILE)    
	layer_text += add_layer_text(layer_text, root, CONTACTM + DELIVERYPOINT)  
	layer_text += add_layer_text(layer_text, root, CONTACTM + CITY)        
	layer_text += add_layer_text(layer_text, root, CONTACTM + ADMINISTRATIVEAREA)
	layer_text += add_layer_text(layer_text, root, CONTACTM + POSTALCODE)        
	layer_text += add_layer_text(layer_text, root, CONTACTM + COUNTRY)   
	layer_text += add_layer_text(layer_text, root, CONTACTM + EMAIL)        
	layer_text += add_layer_text(layer_text, root, CONTACTM + ROLE)  

	layer_text += add_layer_text(layer_text, root, POINTOFCONTACT + INAME) 
	layer_text += add_layer_text(layer_text, root, POINTOFCONTACT + ONAME) 
	layer_text += add_layer_text(layer_text, root, POINTOFCONTACT + PNAME)
	layer_text += add_layer_text(layer_text, root, POINTOFCONTACT + VOICE)    
	layer_text += add_layer_text(layer_text, root, POINTOFCONTACT + FACSIMILE)    
	layer_text += add_layer_text(layer_text, root, POINTOFCONTACT + DELIVERYPOINT) 
	layer_text += add_layer_text(layer_text, root, POINTOFCONTACT + CITY)        
	layer_text += add_layer_text(layer_text, root, POINTOFCONTACT + ADMINISTRATIVEAREA)
	layer_text += add_layer_text(layer_text, root, POINTOFCONTACT + POSTALCODE)        
	layer_text += add_layer_text(layer_text, root, POINTOFCONTACT + COUNTRY)   
	layer_text += add_layer_text(layer_text, root, POINTOFCONTACT + EMAIL)        
	layer_text += add_layer_text(layer_text, root, POINTOFCONTACT + ROLE)         
    
	layer_text += add_layer_text(layer_text, root, DATESTAMP)
    
	layer_text += add_layer_text(layer_text, root, METSTANDARDNAME)
	layer_text += add_layer_text(layer_text, root, METSTANDARDVER)
	layer_text += add_layer_text(layer_text, root, REFERENCESYSINFO) 

	layer_text += add_layer_text(layer_text, root, TITLE)
	layer_text += add_layer_text(layer_text, root, ALTTITLE)
	layer_text += add_layer_text(layer_text, root, DATE)
	layer_text += add_layer_text(layer_text, root, DATETYPE)
	layer_text += add_layer_text(layer_text, root, OTHERCITATION)  
	layer_text += add_layer_text(layer_text, root, ABSTRACT)
	layer_text += add_layer_text(layer_text, root, PURPOSE)  
	layer_text += add_layer_text(layer_text, root, STATUS) 
	layer_text += add_layer_text(layer_text, root, MAINTENANCE)
	layer_text += add_layer_text(layer_text, root, MAINTENANCEUPDATE)
    
	layer_text += add_layer_text(layer_text, root, FORMATNAME)
	layer_text += add_layer_text(layer_text, root, FROMATTYPE)  
    
	layer_text += add_layer_text(layer_text, root, KEYWORD)
	layer_text += add_layer_text(layer_text, root, KEYWORDTYPE)
    
	layer_text += add_layer_text(layer_text, root, SECURITYUL)
	layer_text += add_layer_text(layer_text, root, SECURITYC)  
	layer_text += add_layer_text(layer_text, root, LEGALUL)
	layer_text += add_layer_text(layer_text, root, LEGALA)       
	layer_text += add_layer_text(layer_text, root, LEGALUC)
    
	layer_text += add_layer_text(layer_text, root, SPATIALREP) 
	layer_text += add_layer_text(layer_text, root, SCALEDISTANCE)       
	layer_text += add_layer_text(layer_text, root, SCALEEQUIVALENT)
    
	layer_text += add_layer_text(layer_text, root, LANG2)
	layer_text += add_layer_text(layer_text, root, CHARSET2)
	layer_text += add_layer_text(layer_text, root, TOPICCATEGORY)
    
	hasExtent = False
	if root.find(BOUNDINGBOX, namespaces=NSX) is not None:
	    hasExtent = True
	    layer_text += ('BOUNDING BOX | ')
	if root.find(DESCRIPTION, namespaces=NSX) is not None:
	    hasExtent = True
	    layer_text += ('DESCRIPTION | ')
	if root.find(TEMPORAL, namespaces=NSX) is not None:
	    hasExtent = True
	    layer_text += ('TEMPORAL | ')
	if root.find(VERTICAL, namespaces=NSX) is not None:
	    hasExtent = True
	    layer_text += ('VERTICAL | ') 
	if hasExtent:
	    layer_text += ('\t') 
	else:
	    layer_text += DEFAULT

	layer_text += add_layer_text(layer_text, root, SCOPELEVEL)
	layer_text += add_layer_text(layer_text, root, SCOPELVELDESC)
	layer_text += add_layer_text(layer_text, root, LINEAGE)
    
	layer_text += add_layer_text(layer_text, root, MSECURITYUL)
	layer_text += add_layer_text(layer_text, root, MSECURITYC)
	layer_text += add_layer_text(layer_text, root, MLEGALUL)
	layer_text += add_layer_text(layer_text, root, MLEGALA)
	layer_text += add_layer_text(layer_text, root, MLEGALUC)     

	layer_text += (layer_url + '\n')
    else:
	try:
	    ERROR_LOG.write('Error: {}, LAYER NOT PROCESSED, NOT LAYER/TABLE\n'.format(layer_item.id))
	except AttributeError as e:
	    ERROR_LOG.write('Error: LAYER NOT PROCESSED, NOT LAYER/TABLE AND {}\n'.format(e))   
	    
OUTPUT_CSV.write(layer_text)
OUTPUT_CSV.flush()
OUTPUT_CSV.close()



