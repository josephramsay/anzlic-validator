"""
Run from QGIS python console/editor.

From selected layers in QGIS Legend Extracts details from.
Which could be used to input/ check against values in anzlic-validator.
Also could be added to a 'load from layer' option.

-All
    * Abstract
    * Attribution
    * CRS
        * Description
        * Ellipsoid Acronym
        * Geographic CRS Auth ID
        * Map Units
        * Proj4
        * WKT
            * GEOGCS
                * DATUM
                    * SPHEROID
                        * AUTHORITY
                    * TOWGS84
                    * AUTHORITY
                * PRIMEM
                    * AUTHORITY
                * UNIT
                    * AUTHORITY
                * AUTHORITY            
        * AuthID.
    * Extent
    * Keyword List
    * Metadata URL
    * Name
    * Public Source
    * Original Name
    * Short Name
    * Source
    * Title
    * Type
        * Raster, Vector

-Raster Layers
    * Band Count
        * Band Name
        * Band Offset
        * Band Scale
        * Band Color
        * Band Data Type
    * Provider Type
    * Storage Type
    * Raster Type
        * Grey/ Undefined, Palette, Multiband, Color Layer.
    * Raster Units Per Pixel X
    * Raster Units Per Pixel Y

-Vector Layers
    * Feature Count
    * Geometry Type
        * Point, Line, Polygon, Unknown, None.
    * Provider Type
    * Storage Type

@author: Ashleigh Ross
"""

from qgis.core import *
from collections import OrderedDict
import re

try:
    selectedLayers = iface.legendInterface().selectedLayers()
    
    if not selectedLayers:
        print ('Select A Layer')
    
    vector = ('featureCount', 'geometryType',
              'providerType', 'storageType')
    raster = ('bandCount', 'providerType', 'storageType',
              'rasterType', 'rasterUnitsPerPixelX', 'rasterUnitsPerPixelY')
    anyval = ('abstract', 'attribution', 'crs', 'extent', 'keywordList',
              'metadataUrl', 'name', 'publicSource', 'originalName',
              'shortName', 'source', 'title', 'type')
    
    geometryType = ['Point', 'Line', 'Polygon', 'Unknown Geometry',
                    'No Geometry']
    types = ['Vector', 'Raster']
    rasterType = ['Grey or Undefined', 'Palette', 'Multiband', 'Color Layer']
    mapUnits = ['Meters', 'Feet', 'Degrees', 'NauticalMiles', 'Kilometers', 
                'Yards', 'Miles', 'Unknown Unit', 'Decimal Degrees', 
                'Degrees Minutes Seconds', 'Degrees Decimal Minutes']
                
    dataType = ['Unknown Data Type', 'Byte', 'UInt16', 'Int16', 'UInt32',
                'Int32', 'Float32', 'Float64', 'CInt16', 'CInt32', 'CFloat32',
                'CFloat64', 'ARGB32', 'ARGB32_Premultiplied']
    
    for layer in selectedLayers:
        output = OrderedDict()
        if layer.type() == QgsMapLayer.VectorLayer:
            output['Vector'] = layer.name()
    
            for item in vector:
                if hasattr(layer, item) and getattr(layer, item)() != '':
                    ids = re.sub(r"(\w)([A-Z])", r"\1 \2", item).title()
                    i = getattr(layer, item)()
                    if item == 'geometryType':
                        i = geometryType[i]
                    output[ids] = i
        elif layer.type() == QgsMapLayer.RasterLayer:
            output['Raster'] = layer.name()
    
            for item in raster:
                if hasattr(layer, item) and getattr(layer, item)() != '':
                    ids = re.sub(r"(\w)([A-Z])", r"\1 \2", item).title()
                    i = getattr(layer, item)()
                    if item == 'rasterType':
                        i = rasterType[i]
                    output[ids] = i

            band = OrderedDict()
            if layer.bandCount() != 0:
                output['Band'] = band
    
            for i in range(1, layer.bandCount()+1):
                dp = layer.dataProvider()
                band['Band Name'] = layer.bandName(i)
                band['Band Offset'] = dp.bandOffset(i)
                band['Band Scale'] = dp.bandScale(i)
                band['Colour'] = dp.colorInterpretationName(i)
                band['Data Type'] = dataType[dp.dataType(i)]
        else:
            print ('Not Vector/Raster Layer')
        
        if layer.type() == QgsMapLayer.VectorLayer or \
                layer.type() == QgsMapLayer.RasterLayer:
            for item in anyval:
                if hasattr(layer, item) and getattr(layer, item)() != '':
                    ids = re.sub(r"(\w)([A-Z])", r"\1 \2", item).title()
                    i = getattr(layer, item)()
                    
                    if item == 'crs':
                        crs = OrderedDict()
                        output['Crs types'] = crs
                        crs['Description'] = i.description()
                        crs['Ellipsoid Acronym'] = i.ellipsoidAcronym()
                        crs['Geographic CRS Auth ID'] = i.geographicCRSAuthId()
                        crs['Map Units'] = i.mapUnits()
                        crs['Proj4'] = i.toProj4()
                        crs['WKT'] = i.toWkt()
                        i = str(i.authid())
                    elif item == 'extent':
                        i = str(i.toString())
                    elif item == 'type':
                        i = types[i]
                    output[ids] = i
        
        for key in output:
            if key == 'Crs types' or key == 'Band':
                print key + ':'
                for i in output[key]:
                    print '\t{} -> {}'.format(i, output[key][i])
            else:
                print '{} -> {}'.format(key, output[key])
        print '\n------------------------------------------------------------\n'

except NameError as ne:
    print "{}...\nRun via QGIS Python Console.".format(ne)
