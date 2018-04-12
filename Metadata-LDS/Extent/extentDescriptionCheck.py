#!/usr/bin/python
'''
Python Script which checks every layer & table on LDS & Extracts Extent Information
Checking If has bounding box, or geographic description, if has geographic 
description extracts text as some contain 'aus' rather than 'nz'

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

OUTPUT_CSV = open('extentDescriptionCheck.csv', 'w')

#RESOURCE = open('Resource-License.txt', 'w')
#METADATA = open('Metadata-License.txt', 'w')

#RUSECOPY = open('Resource-Use-Copyright.txt', 'w')
#RUSELI = open('Resource-Use-License.txt', 'w')
#MUSECOPY = open('Metatdata-Use-Copyright.txt', 'w')
#MUSELI = open('Metadata-Use-License.txt', 'w')

ERROR_LOG = open('extentDescriptionCheck.log', 'w')

TEMP_FILE = 'extentDescriptionCheck_temp.xml'

LAYER_TYPE = type(koordinates.layers.Layer())


NSX = {'gmd' : 'http://www.isotc211.org/2005/gmd',
       'gco' : 'http://www.isotc211.org/2005/gco'}


EXTENT = 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement'
DESCRIPTION = EXTENT + '/gmd:EX_GeographicDescription'
BOUNDING = EXTENT + '/gmd:EX_GeographicBoundingBox'
EXTENTCODE = DESCRIPTION + '/gmd:geographicIdentifier/gmd:MD_Identifier/gmd:code/gco:CharacterString'

DEFAULT = 'None \t'
layer_text = ""
layer_url = ""
layer_group = ""

# Set Default Encoding.
reload(sys)  
sys.setdefaultencoding('utf8')

HEADING = 'LAYER ID, EXTENT, URL, GROUP\n'
OUTPUT_CSV.write(HEADING)
client = koordinates.Client(host=HOST, token=API_KEY)
TOTAL = len(client.catalog.list())
current = 0
for layer_item in client.catalog.list():
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
	#l = client.layers.get(layer_item.id)
	#if l.group.name is not None:
	#    layer_group = l.group.name
	#else:
	#    layer_group = 'None'
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
	layer_text += (str(layer_id) + ', ')
	extentCode = root.find(EXTENTCODE, namespaces=NSX)
	extent = root.find(EXTENT, namespaces=NSX)
	bounding = root.find(BOUNDING, namespaces=NSX)
	
	if extentCode is not None:
	    if extentCode.text is not None:
		layer_text += (extentCode.text + ', ')
	    else:
		layer_text += ('Description None,')
	elif bounding is not None:
	    layer_text += ('Has Bounding, ')
	elif extent is not None:
	    layer_text += ('Has Other, ')
	else:
	    layer_text += ('None, ')
	layer_text += (layer_url + '\n')
	#OUTPUT_CSV.flush()
    else:
	try:
	    ERROR_LOG.write('Error: {}, LAYER NOT PROCESSED, NOT LAYER/TABLE\n'.format(layer_item.id))
	except AttributeError as e:
	    ERROR_LOG.write('Error: LAYER NOT PROCESSED, NOT LAYER/TABLE AND {}\n'.format(e))    
OUTPUT_CSV.write(layer_text + '\n')
OUTPUT_CSV.flush()
OUTPUT_CSV.close()

