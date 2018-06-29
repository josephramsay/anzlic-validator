#!/usr/bin/python
"""
Simple Python script to extract Dublin Core records from the LDS, and check
for double ups where there shouldn't be ie.(Identifier), and for where fields 
don't exist.

@author: Ashleigh Ross

Dublin Core --> ANZLIC Mapping
------------------------------
description --> identificationInfo - abstract 
language --> language
creator --> contact - organisationName [Errors in ANZLIC]
title --> identificationInfo - title
source --> dataQualityInfo - lineage [None occur in ANZLIC]
coverage - identificationInfo - extent - boundingBox [None occur in ANZLIC], or
[Description]
date --> identificationInfo - date
identifier --> distributionInfo - url [None occur in ANZLIC], or [Double fields
occur]
type --> identificationInfo - spatialRepresentation [None occur in ANZLIC]
subject --> identificationInfo - topicCategory
"""

import koordinates
import lxml
import urllib2
from lxml import etree
from StringIO import StringIO
import sys

# Set LDS API Key
API_KEY = ''
HOST = 'data.linz.govt.nz'

SCH_URL = 'http://www.openarchives.org/OAI/2.0/oai_dc.xsd'
LAYER_URL = 'https://data.linz.govt.nz/layer/{}/metadata/dc/xml'

SCH_DOC = etree.parse(SCH_URL)
SCH = etree.XMLSchema(SCH_DOC)

LAYER_TYPE = type(koordinates.layers.Layer())
CLIENT = koordinates.Client(host=HOST, token=API_KEY)

TOTNUM = len(CLIENT.catalog.list().filter(public='true'))

print 'Found {} Layers'.format(TOTNUM)

dict1 = {'description': 0, 'language': 0, 'creator': 0, 'title': 0,
         'dc': 0, 'source': 0, 'coverage': 0, 'date': 0, 'identifier': 0,
         'type': 0, 'subject': 0}
count = 0

nvali = 0
vali = 0
nonlay = 0

for layer in CLIENT.catalog.list().filter(public='true'):
    count += 1            
    if type(layer) == LAYER_TYPE:
        metafile = urllib2.urlopen(LAYER_URL.format(layer.id))
        metadata = metafile.read()
        metafile.close()
        meta = etree.parse(StringIO(metadata))
        
        if not SCH.validate(meta):
            sys.stderr.write('Layer {}: Not Valid!\n'.format(layer.id))
            nvali += 1
        else:
            vali += 1
            values = ()
            for el in meta.iter():
                value = str(el.tag[el.tag.rfind('}')+1:])

                if value in values:
                    # Ignoring 'subject' and 'date' values which can occur
                    # multiple times.
                    if value != 'subject' and value != 'date':
                        sys.stderr.write(
                            'Double Field: {} in Layer {}\n'.format(
                                value, layer.id))
                else:
                    values = values + (value,)
                    
                    if value in dict1:
                        dict1[value] += 1

                    else:
                        sys.stderr.write(
                            'Adding Field: {} at Layer: {}\n'.format(
                                value, layer.id))
                        dict1[value] = 1 

            for i in dict1:
                if i not in values:
                    sys.stderr.write('Field: {}, not in layer {}\n'.format(
                        i, layer.id))

        sys.stdout.flush()
        sys.stderr.flush()
        
    else:
        nonlay += 1
        if type(layer) == dict:
            sys.stderr.write(
                'Layer: {} Not Checked not Layer/Table Type\n'.format(
                    layer['id']))
        else:
            sys.stderr.write(
                'Layer: {} Not Checked not Layer/Table Type\n'.format(layer.id))
        

print 'Valid: {}, Not Valid: {}, Not Tested: {}.'.format(vali, nvali, nonlay)
