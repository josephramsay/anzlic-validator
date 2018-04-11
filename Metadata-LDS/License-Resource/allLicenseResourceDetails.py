#!/usr/bin/python
'''
Python Script which checks every layer & table on LDS & Extracts Resource Use 
(Copyright & License), Resource Access (Copyright & License), Metadata Use 
(Copyright & License) & Metadata Access (Copyright & License). 

These fields extracted into a csv document along with the layer id.

In the case that any fields don't exist or are empty the text 'None' is put in 
place.
'''
# Set LDS API Key
API_KEY = ''


import os
import sys
import urllib2
from urllib2 import HTTPError, ProxyHandler, URLError
from lxml import etree
import koordinates

HOST = 'data.linz.govt.nz'

OUTPUT_CSV = open('allLicenseResource.csv', 'w')

ERROR_LOG = open('licensecopyrightCheck.log', 'w')

TEMP_FILE = 'licensecopyrightCheck_temp.xml'

LAYER_TYPE = type(koordinates.layers.Layer())


NSX = {'gmd' : 'http://www.isotc211.org/2005/gmd',
       'gco' : 'http://www.isotc211.org/2005/gco'}

DATAID = 'gmd:identificationInfo/gmd:MD_DataIdentification'
LCSTRING = 'gmd:MD_LegalConstraints/gmd:useLimitation/gco:CharacterString'
ACCESSCON = 'gmd:MD_LegalConstraints/gmd:accessConstraints/gmd:MD_RestrictionCode'
USECON = 'gmd:MD_LegalConstraints/gmd:useConstraints/gmd:MD_RestrictionCode'
MCON = 'metadataConstraints'
RCON = 'resourceConstraints'
TAG = DATAID + '/gmd:resourceConstraints/gmd:MD_SecurityConstraints/gmd:classification/gmd:MD_ClassificationCode'
TAG_TEXT = DATAID + 'gmd:resourceConstraints/gmd:MD_SecurityConstraints/gmd:useLimitation/gco:CharacterString'
DEFAULT = 'None \t'

# Set Default Encoding.
reload(sys)  
sys.setdefaultencoding('utf8')

HEADING = 'LAYER ID\t RESOURCE ACCESS \tTYPE\t RESOURCE ACCESS \tTYPE\t RESOURCE USE \tTYPE\t RESOURCE USE \tTYPE\t METADATA ACCESS \tTYPE\t METADATA ACCESS \tTYPE\t METADATA USE \tTYPE\t METADATA USE \tTYPE\n'
OUTPUT_CSV.write(HEADING)
client = koordinates.Client(host=HOST, token=API_KEY)
TOTAL = len(client.catalog.list())
current = 0
for layer_item in client.catalog.list().filter(public='true'):
    current += 1
    if current % 10 == 0:
	print 'LAYER {}/{}'.format(current, TOTAL)
    sys.stdout.flush()
    
    if type(layer_item) == LAYER_TYPE:
	try:
	    os.remove(TEMP_FILE)
	except OSError:
	    pass
	layer_id = layer_item.id
	get_attempts = 0
	while get_attempts <=3:
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
	
	layer_text = (str(layer_id) + '\t')
	if layer.metadata is None:
	    ERROR_LOG.write("Error: {}, THIS LAYER NOT PROCESSED, NO METADATA\n".format(layer_id))
	    continue
	
	layer.metadata.get_xml(TEMP_FILE)
	tree = etree.parse(TEMP_FILE)
	root = tree.getroot()
	i = 0
	if root.find(DATAID, namespaces=NSX) is not None:
	    for element in root.find(DATAID, namespaces=NSX):
		if RCON in element.tag:
		    el = element.find(LCSTRING, namespaces=NSX)
		    if el is not None:
			access_constraint = element.find(ACCESSCON, namespaces=NSX)
			use_constraint = element.find(USECON, namespaces=NSX)
			if access_constraint is not None:
			    i += 1
			    layer_text += ((element.find(LCSTRING, namespaces=NSX).text).replace('\n', ' ').replace('\t', ' '))
			    i += 1
			    layer_text += ('\t' + access_constraint.text + '\t')
			elif use_constraint is not None:
			    i += 1
			    while i < 5:
				layer_text += DEFAULT
				i += 1
			    layer_text += ((element.find(LCSTRING, namespaces=NSX).text).replace('\n', ' ').replace('\t', ' '))
			    i += 1
			    layer_text += ('\t' + use_constraint.text + '\t')
	    
	    for element in root:
		if MCON in element.tag:
		    el = element.find(LCSTRING, namespaces=NSX)
		    if el is not None:
			access_constraint = element.find(ACCESSCON, namespaces=NSX)
			use_constraint = element.find(USECON, namespaces=NSX)
			if access_constraint is not None:
			    i += 1
			    while i < 9:
				layer_text += DEFAULT
				i += 1
			    layer_text += ((element.find(LCSTRING, namespaces=NSX).text).replace('\n', ' ').replace('\t', ' '))
			    i += 1
			    layer_text += ('\t' + access_constraint.text + '\t')
			elif use_constraint is not None:
			    i += 1
			    while i < 13:
				layer_text += DEFAULT
				i += 1
			    layer_text += ((element.find(LCSTRING, namespaces=NSX).text).replace('\n', ' ').replace('\t', ' '))
			    i += 1
			    layer_text += ('\t' + use_constraint.text + '\t')
			
	    while i < 16:
		layer_text += DEFAULT
		i += 1
	    if root.find(TAG, namespaces=NSX) is not None:
		t = root.find(TAG, namespaces=NSX)
		if t.text is not None:
		    layer_text += (t.text + '\t')
	    if root.find(TAG_TEXT, namespaces=NSX) is not None:
		t2 = root.find(TAG_TEXT, namespaces=NSX)
		if t2.text is not None:
		    layer_text += (t2.text + '\t')
		
		
	    layer_text = layer_text.replace('\n', '')
	    OUTPUT_CSV.write(layer_text + '\n')
	    OUTPUT_CSV.flush()
	    ERROR_LOG.flush()
    else:
	try:
	    ERROR_LOG.write('Error: {}, LAYER NOT PROCESSED, NOT LAYER/TABLE\n'.format(layer_item.id))
	except AttributeError as e:
	    ERROR_LOG.write('Error: LAYER NOT PROCESSED, NOT LAYER/TABLE AND {}\n'.format(e))    
	    
OUTPUT_CSV.close()
ERROR_LOG.close()

