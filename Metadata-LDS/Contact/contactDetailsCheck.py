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

OUTPUT_CSV = open('contactDetailsCheck.csv', 'w')

#RESOURCE = open('Resource-License.txt', 'w')
#METADATA = open('Metadata-License.txt', 'w')

#RUSECOPY = open('Resource-Use-Copyright.txt', 'w')
#RUSELI = open('Resource-Use-License.txt', 'w')
#MUSECOPY = open('Metatdata-Use-Copyright.txt', 'w')
#MUSELI = open('Metadata-Use-License.txt', 'w')

ERROR_LOG = open('contactDetailsCheck.log', 'w')

TEMP_FILE = 'contactDetailsCheck_temp.xml'

LAYER_TYPE = type(koordinates.layers.Layer())


NSX = {'gmd' : 'http://www.isotc211.org/2005/gmd',
       'gco' : 'http://www.isotc211.org/2005/gco'}


CONTACT = 'gmd:contact/gmd:CI_ResponsibleParty/'
INAME = 'gmd:individualName/gco:CharacterString'
ONAME = 'gmd:organisationName/gco:CharacterString'
PNAME = 'gmd:positionName/gco:CharacterString'
CONTACT_INFO = 'gmd:contactInfo/gmd:CI_Contact/'
PHONE = CONTACT_INFO + 'gmd:phone/gmd:CI_Telephone/gmd:voice/gco:CharacterString'
ADDRESS = CONTACT_INFO + 'gmd:address/gmd:CI_Address/'
DELPOINT = ADDRESS + 'gmd:deliveryPoint/gco:CharacterString'
CITY = ADDRESS + 'gmd:city/gco:CharacterString'
PCODE = ADDRESS + 'gmd:postalCode/gco:CharacterString'
COUNTRY = ADDRESS + 'gmd:country/gco:CharacterString'
EMAIL = ADDRESS + 'gmd:electronicMailAddress/gco:CharacterString'
ROLE = 'gmd:role/gmd:CI_RoleCode'

POCONTACT = 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:pointOfContact/gmd:CI_ResponsibleParty/'


DEFAULT = 'None \t'
layer_text = ""

# Set Default Encoding.
reload(sys)  
sys.setdefaultencoding('utf8')

#HEADING = 'LAYER ID\t RESOURCE ACCESS COPYRIGHT\t RESOURCE ACCESS LICENSE\t RESOURCE USE COPYRIGHT\t RESOURCE USE LICENSE\t METADATA ACCESS COPYRIGHT\t METADATA ACCESS LICENSE\t METADATA USE COPYRIGHT\t METADATA USE LICENSE\t\n'
HEADING = 'LAYER ID\t INDIVIDUAL NAME\t ORGANISATION NAME\t POSITION NAME\t PHONE\t DELIVERY POINT\t CITY\t POSTAL CODE\t COUNTRY\t EMAIL\t ROLE\n'
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
	i = 0 
	while i < 2:
	    i += 1
	    if i == 1:
		IN = CONTACT + INAME
		ON = CONTACT + ONAME
		PN = CONTACT + PNAME
		PH = CONTACT + PHONE
		DE = CONTACT + DELPOINT
		CI = CONTACT + CITY
		PC = CONTACT + PCODE
		CO = CONTACT + COUNTRY
		EM = CONTACT + EMAIL
		RO = CONTACT + ROLE
	    else:
		IN = POCONTACT + INAME
		ON = POCONTACT + ONAME
		PN = POCONTACT + PNAME
		PH = POCONTACT + PHONE
		DE = POCONTACT + DELPOINT
		CI = POCONTACT + CITY
		PC = POCONTACT + PCODE
		CO = POCONTACT + COUNTRY
		EM = POCONTACT + EMAIL
		RO = POCONTACT + ROLE
		
	    layer_text += (str(layer_id) + '\t')
	    if root.find(IN, namespaces=NSX) is not None and root.find(IN, namespaces=NSX).text is not None:
		layer_text += (root.find(IN, namespaces=NSX).text + '\t')
	    else:
		layer_text += DEFAULT
	    
	    if root.find(ON, namespaces=NSX) is not None and root.find(ON, namespaces=NSX).text is not None:
		layer_text += (root.find(ON, namespaces=NSX).text + '\t')
	    else:
		layer_text += DEFAULT
	    
	    if root.find(PN, namespaces=NSX) is not None and root.find(PN, namespaces=NSX).text is not None:
		layer_text += (root.find(PN, namespaces=NSX).text + '\t')
	    else:
		layer_text += DEFAULT
		
	    if root.find(PH, namespaces=NSX) is not None and root.find(PH, namespaces=NSX).text is not None:
		layer_text += (root.find(PH, namespaces=NSX).text + '\t')
	    else:
		layer_text += DEFAULT
		
	    if root.find(DE, namespaces=NSX) is not None and root.find(DE, namespaces=NSX).text is not None:
		layer_text += (root.find(DE, namespaces=NSX).text + '\t')
	    else:
		layer_text += DEFAULT
		
	    if root.find(CI, namespaces=NSX) is not None and root.find(CI, namespaces=NSX).text is not None:
		layer_text += (root.find(CI, namespaces=NSX).text + '\t')
	    else:
		layer_text += DEFAULT
		
	    if root.find(PC, namespaces=NSX) is not None and root.find(PC, namespaces=NSX).text is not None:
		layer_text += (root.find(PC, namespaces=NSX).text + '\t')
	    else:
		layer_text += DEFAULT
		
	    if root.find(CO, namespaces=NSX) is not None and root.find(CO, namespaces=NSX).text is not None:
		layer_text += (root.find(CO, namespaces=NSX).text + '\t')
	    else:
		layer_text += DEFAULT
		
	    if root.find(EM, namespaces=NSX) is not None and root.find(EM, namespaces=NSX).text is not None:
		layer_text += (root.find(EM, namespaces=NSX).text + '\t')
	    else:
		layer_text += DEFAULT    
		
	    if root.find(RO, namespaces=NSX) is not None and root.find(RO, namespaces=NSX).text is not None:
		layer_text += (root.find(RO, namespaces=NSX).text + '\t')
	    else:
		layer_text += DEFAULT    
	    #print layer_text
	    layer_text += '\n'
	#OUTPUT_CSV.flush()
    else:
	try:
	    ERROR_LOG.write('Error: {}, LAYER NOT PROCESSED, NOT LAYER/TABLE\n'.format(layer_item.id))
	except AttributeError as e:
	    ERROR_LOG.write('Error: LAYER NOT PROCESSED, NOT LAYER/TABLE AND {}\n'.format(e))    
OUTPUT_CSV.write(layer_text + '\n')
OUTPUT_CSV.flush()
OUTPUT_CSV.close()

