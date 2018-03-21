from lxml import etree
from abc import ABCMeta, abstractmethod
import os
import re
import urllib2
from lxml.isoschematron import _schematron_root
from urllib2 import HTTPError, ProxyHandler, URLError
from authenticate import Authentication
from lxml.etree import XMLSyntaxError

key = Authentication.apikey('~/.apikey3')

NSX = {'xlink'   : 'http://www.w3.org/1999/xlink',
       'xsi'     : 'http://www.w3.org/2001/XMLSchema-instance',  
       'dc'      : 'http://purl.org/dc/elements/1.1/',
       'g'       : 'http://data.linz.govt.nz/ns/g', 
       'r'       : 'http://data.linz.govt.nz/ns/r', 
       'ows'     : 'http://www.opengis.net/ows/1.1', 
       'csw'     : 'http://www.opengis.net/cat/csw/2.0.2',
       'wms'     : 'http://www.opengis.net/wms',
       'ogc'     : 'http://www.opengis.net/ogc',
       'gco'     : 'http://www.isotc211.org/2005/gco',
       'gmd'     : 'http://www.isotc211.org/2005/gmd',
       'gmx'     : 'http://www.isotc211.org/2005/gmx',
       'gsr'     : 'http://www.isotc211.org/2005/gsr',
       'gss'     : 'http://www.isotc211.org/2005/gss',
       'gts'     : 'http://www.isotc211.org/2005/gts',
       'f'       : 'http://www.w3.org/2005/Atom',
       'null'    : '',
       'wfs'     : 'http://www.opengis.net/wfs/2.0',
       'gml'     : 'http://www.opengis.net/gml/3.2',
       'v'       : 'http://wfs.data.linz.govt.nz',
       'lnz'     : 'http://data.linz.govt.nz'}

class SCHMD(object):
    
    __metaclass__ = ABCMeta
    
    _sch = None
    _md = None
    
    @property
    def sch(self): return self._sch
    @sch.setter
    def sch(self,value): self._sch = value    
    
    @property
    def md(self): return self._md
    @md.setter
    def md(self,value): self._md = value
    
    sch = None
    md = None
    
    def __init__(self):
        self.schema()
        #self.metadata()
        
    @abstractmethod
    def schema(self):
        '''schema init'''    
        
    @abstractmethod
    def metadata(self):
        '''schema init'''
        
class Local(SCHMD):
    
    SP = '../../ANZLIC-XML/standards.iso.org/iso/19110/gfc/1.1/'
    TP = '../tests/data/'
    
    def __init__(self):
        super(Local,self).__init__()
    
    def schema(self):
        sch_name = 'featureCatalogue.xsd'#metadataEntity?
        sch_path = os.path.abspath(os.path.join(os.path.dirname(__file__),self.SP,sch_name))
        
        sch_doc = etree.parse(sch_path)
        self.sch = etree.XMLSchema(sch_doc)
        
    def metadata(self):
        md_name = 'nz-primary-parcels.iso.xml'    
        md_path = os.path.abspath(os.path.join(os.path.dirname(__file__),self.TP,md_name))
        self.md = etree.parse(md_path)

class Remote(SCHMD):
    GC = 'get caps url'
    
    def __init__(self):
        super(Remote,self).__init__()  
    
    def schema(self):
        sch_name = 'http://www.isotc211.org/2005/gmd/metadataEntity.xsd'
        sch_handle = urllib2.urlopen(sch_name)
        
        sch_doc = etree.parse(sch_handle)
        self.sch = etree.XMLSchema(sch_doc)    
        
    def metadata(self,lid):
        md_name = 'https://data.linz.govt.nz/layer/{lid}/metadata/iso/xml/'    

        try:
            md_handle = urllib2.urlopen(md_name.format(lid=lid[0]))
            self.md = etree.parse(md_handle)
            return True
        except XMLSyntaxError as xse:
            if 'https://id.koordinates.com/login' in md_handle.url:
                print ('ERROR cannot find metadata for document {}.\n{}'.format(lid,xse))
            else:
                print ('ERROR parsing metadata document {}.\n{}'.format(lid,xse))
        except HTTPError as he:
            print ('ERROR layer unavailable {}.\n{}'.format(lid,he))
        except Exception as e:
            print ('ERROR processing {}.\n{}'.format(lid,e))
        return False

    def getids(self,wxs):
        npath = "./wfs:Name"
        tpath = "./wfs:Title"
        cap = 'http://data.linz.govt.nz/services;key={key}/{wxs}?service={wxs}&request=GetCapabilities'
        ftx = {'wfs':'//wfs:FeatureType','wms':'/Capability/Layer/Layer'}[wxs]

        ret = {'layer':(),'table':()}
        content = None
        try:
            content = urllib2.urlopen(cap.format(key=key,wxs=wxs))
            tree = etree.parse(content)
            #find all featuretypes
            for ft in tree.findall(ftx,namespaces=NSX):
                #regex out id and table/layer type
                match = re.search('(layer|table)-(\d+)',ft.find(npath, namespaces=NSX).text)
                lort = match.group(1)
                name = int(match.group(2))
                title = ft.find(tpath, namespaces=NSX).text
                ret[lort] += ((name,title),)
        except HTTPError as he:
            if cls._HTTPErrorHandler(he, 'WxS',url):
                retry = True
            raise
            
        #just return layer for now
        return ret['layer']

def testvals():      
    return [(i,'succeed') for i in ('50772','50845','50789')] \
        + [(i,'fail') for i in ('50813','51362','51920')] \
        + [(i,'error') for i in ('52552',)]
        
def main():
    
    #v1 = Local()
    #print(v1.sch.validate(v1.md))]

    v2 = Remote()
    #wfsi = v2.getids('wfs')
    for lid in testvals():
    #for lid in wfsi:
        if v2.metadata(lid):
            print(lid,v2.sch.validate(v2.md))
        else:
            print(lid,False)
    
if __name__ == "__main__":
    main()
