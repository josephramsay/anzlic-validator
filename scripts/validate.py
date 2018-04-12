import os
import re
import urllib.request

from urllib.request import ProxyHandler
from urllib.error import HTTPError, URLError
from lxml import etree
from lxml.etree import XMLSyntaxError

from bs4 import BeautifulSoup as BS
#from lxml.isoschematron import _schematron_root

from abc import ABCMeta, abstractmethod

#Shifting from urllib to urllib2 we lost urlretrieve with its caching features. 
#One solution was to implement a cache solution but no longer sure that its required

from cache import CacheHandler
from authenticate import Authentication

#Raw AS recipe is py2, modified as cache import above
#import importlib.util
#spec = importlib.util.spec_from_file_location('CacheHandler','../ActiveStateCode/recipes/Python/491261_Caching_throttling/recipe-491261.py')
#module = importlib.util.module_from_spec(spec)
#spec.loader.exec_module(module)
BORX = 'b'
ENC = 'utf-8'
CACHE = '.validator_cache'
KEY = Authentication.apikey('~/.apikey3')
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

       #xmlns="http://www.opengis.net/wfs/2.0"
       
SL1 = 'http://www.isotc211.org/2005/'  
SL2 = 'http://schemas.opengis.net/iso/19139/20070417/'
SL3 = 'http://standards.iso.org/ittf/PubliclyAvailableStandards/ISO_19139_Schemas/'
SL = SL3

class ValidatorException(Exception): pass
class ValidatorAccessException(ValidatorException): pass
class ValidatorParseException(ValidatorException): pass
class ValidatorResponseException(ValidatorException): pass
class InaccessibleSchemaException(ValidatorAccessException): pass
class InaccessibleMetadataException(ValidatorAccessException): pass
class MetadataParseException(ValidatorParseException): pass
class MetadataConditionalException(ValidatorParseException): pass
class CapabilitiesAccessException(ValidatorAccessException): pass
class CapabilitiesParseException(ValidatorAccessException): pass

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
        #self.schema()
        #self.metadata()
        pass
        
    @abstractmethod
    def schema(self):
        '''schema init'''
    def setschema(self):
        self.sch = self.schema()
        
    @abstractmethod
    def metadata(self):
        '''schema init'''
    def setmetadata(self,lid):
        self.md = self.metadata(lid)
        
    def validate(self,md=None):
        '''Wrap schema validation to throw MetadataParseException'''
        if not hasattr(self.sch,'validate'): 
            raise MetadataParseException('XML Schema invalid')
        if not self.sch.validate(md or self.md): 
            raise MetadataParseException('Unable to validate XML')
        return True
    
    @staticmethod
    def _bcached(url,enc=ENC):
        '''Wrapper for cached url open with bs'''
        txt = SCHMD._request(url, enc)
        return BS(txt,'lxml-xml')    
    
    @staticmethod
    def _xcached(url,enc=ENC):
        '''Wrapper for cached url open with lxml'''
        txt = SCHMD._request(url, enc)
        if enc: return etree.XML(txt, etree.XMLParser(ns_clean=True,recover=True,encoding=enc))
        return etree.XML(txt)
    
    @staticmethod
    def _request(url,enc):
        opener = urllib.request.build_opener(CacheHandler(CACHE))
        resp = opener.open(url)
        return SCHMD._hackisotc211(resp.getvalue().encode(enc) if enc else resp.getvalue())
    
    @staticmethod
    def _hackisotc211(txt):
        '''The isotc211 domain has expired but is still referred to throughout related schemas. This hack replaces that reference'''
        return txt.replace(bytes(SL1,'utf-8'),bytes(SL,'utf-8'))
        #return txt.replace(SL1,SL)
        
    def conditional(self):
        '''Bonus conditional extent checks'''
        dataset = False
            
        for element in self.md.findall('hierarchyLevel',namespaces=NSX):
            if not element.get('codeListValue'):
                raise MetadataConditionalException('No Hierarchy Level Declared')
            elif element.get('codeListValue') == 'dataset':
                dataset = True
        
        if dataset:
            idin = self.md.find('identificationInfo',namespaces=NSX)
            for mddid in idin.iter('MD_DataIdentification',namespaces=NSX):
                if not mddid.find('topicCategory/MD_TopicCategoryCode',namespaces=NSX):
                    raise MetadataConditionalException('No Topic Category Declared')
                if not mddid.find('extent',namespaces=NSX):
                    raise MetadataConditionalException('No Extent Declared')
                else:
                    extent = mddid.find('extent/EX_Extent/geographicElement',namespaces=NSX)
                    if not extent.find('EX_GeographicBoundingBox',namespaces=NSX) \
                    and not extent.find('EX_GeographicDescription',namespaces=NSX):
                        raise MetadataConditionalException('No Geographic Bounding Box or Geographic Description Declared')
    
        if not self.md.find('language/CharacterString',namespaces=NSX):
           raise MetadataConditionalException('No language/CS defined')
       
        if not self.md.find('characterSet/MD_CharacterSetCode',namespaces=NSX):
           raise MetadataConditionalException('No CharacterSetCode defined')
       
        mddid = self.md.find('identificationInfo/MD_DataIdentification',namespaces=NSX)
        if not mddid.find('language/CharacterString',namespaces=NSX):
           raise MetadataConditionalException('No ID Info language/CS defined')
       
        if not mddid.find('characterSet/MD_CharacterSetCode',namespaces=NSX):
           raise MetadataConditionalException('No ID Info CharacterSetCode defined')
        
        return True
        

class Local(SCHMD):
    '''Parser setup using local data store, user configured'''
    #SP = '../../ANZLIC-XML/standards.iso.org/iso/19110/gfc/1.1/'
    SP = '../data/schema/'
    TP = '../data/metadata'
    
    def __init__(self):
        super(Local,self).__init__()
        
    @classmethod
    def schema(cls):
        sch_name = 'metadataEntity.xsd'
        sch_path = os.path.abspath(os.path.join(os.path.dirname(__file__),cls.SP,'gmd',sch_name))
        #sch_doc = ''
        #with open(sch_path,'rb') as h:
        #    sch_doc = etree.XML(SCHMD._hackisotc211(h.read()))
        sch_doc = etree.parse(sch_path)
        sch = etree.XMLSchema(sch_doc)
        return sch
        
    @classmethod
    def metadata(cls,md_name):
        md_sample = 'nz-primary-parcels.iso.xml'    
        md_path = os.path.abspath(os.path.join(os.path.dirname(__file__),cls.TP,md_name or md_sample))
        md = etree.parse(md_path)
        return md

class Remote(SCHMD):
    '''Remote parser grabbing remote content but employing caching'''
    def __init__(self):
        super(Remote,self).__init__()  
    
    @classmethod
    def schema(cls):
        '''Fetch and parse the ANZLIC metadata schema'''
        sch_name = '{url}/gmd/metadataEntity.xsd'.format(url=SL)
        sch_doc = cls._xcached(sch_name)
        sch = etree.XMLSchema(sch_doc)
        return sch 
        
    @classmethod
    def metadata(cls,lid):
        '''Get the default metadata for each layer identified by layer id'''
        md_name = 'https://data.linz.govt.nz/layer/{lid}/metadata/iso/xml/'    

        try:
            md_handle = urllib.request.urlopen(md_name.format(lid=lid[0]))
            md = etree.parse(md_handle)
            return md
        except XMLSyntaxError as xse:
            #Private layers are inaccessible
            if 'https://id.koordinates.com/login' in md_handle.url:
                raise InaccessibleMetadataException('Private layer {}.\n{}'.format(lid,xse))
            else:
                raise MetadataParseException('Metadata parse error {}.\n{}'.format(lid,xse))
        except HTTPError as he:
            raise InaccessibleMetadataException('Metadata unavailable {}.\n{}'.format(lid,he))
        except Exception as e:
            #catch any other error and continue, may not be what is wanted
            raise ValidatorException('Processing error {}.\n{}'.format(lid,e))
        return None
        
    def getids(self,wxs,sorf = 0):
        '''Read the layer and table IDS from the getcapabilities for the WFS and WMS service types
        cap: capabilities url template
        ftx: feature type xpath fragment
        borx: parser selection, baeutifulsoup or lxml
        '''
        cap, ftx, borx = self._geturlset(sorf, wxs)
        try:
            url = cap.format(key=KEY,wxs=wxs)
            bst = borx[0](url)
            #find all featuretypes
            ret = borx[1](bst, ftx)
        except HTTPError as he:
            raise CapabilitiesAccessException('Failed to get {}/{} layer ids.\n{}'.format(wxs,sorf,he))
        except ValueError as ve:
            raise CapabilitiesParseException('Failed to read {}/{} layer ids.\n{}'.format(wxs,sorf,ve))
        #Catch if no features found
        try: ret
        except NameError: raise CapabilitiesParseException('No matching {} features found'.format(wxs))
            
        return ret['layer']
    
    def _bextract(self,bst,ftx):
        '''regex out id and table/layer type using bsoup'''
        ret = {'layer':(),'table':()}
        for ft in bst.find_all(ftx['path']):
            match = re.search('(layer|table)-(\d+)',ft.find(ftx['name']).text)
            ret[match.group(1)] += ((int(match.group(2)),ft.find(ftx['title']).text),)
        return ret
    
    def _xextract(self,xft,ftx):
        '''regex out id and table/layer type using lxml'''
        ret = {'layer':(),'table':()}
        for ft in xft.findall(ftx['path'],namespaces=NSX):
            match = re.search('(layer|table)-(\d+)',ft.find(ftx['name'], namespaces=NSX).text)
            ret[match.group(1)] += ((int(match.group(2)),ft.find(ftx['title'], namespaces=NSX).text),)
        return ret

        
    
    def _geturlset(self,src,wxs):
        '''Returns capabilities URL, xpath fragment to title/name and parser method
        wxs: Select xpath for wfs/wms layer types
        src: Select where to get layer IDs from; services(0) or feeds(1). 
        (If selecting LDS Services, capabilities are limited to 250 results so will have to be paged)
        '''
        cap = ('http://data.linz.govt.nz/services;key={key}/{wxs}?service={wxs}&request=GetCapabilities',
               'http://data.linz.govt.nz/feeds/csw?service=CSW&version=2.0.2&request=GetRecords&constraintLanguage=CQL_TEXT&typeNames=csw:Record&resultType=results&ElementSetName=summary')
        #wfs/wms feature paths      
        ftx = ({'wfs':{'path':'FeatureType',
                       'name':'Name',
                       'title':'Title',
                       'lib':'b'},
                'wms':{'path':'Capability/Layer/Layer',
                       'name':'Name',
                       'title':'Title',
                       'lib':'x'}
               }[wxs],        
               {'wfs':{'path':'//csw:SearchResults/csw:SummaryRecord',
                       'name':'./dc:identifier',
                       'title':'./dc:Title',
                       'lib':'b'},
                'wms':{'path':'//csw:SearchResults/csw:SummaryRecord',
                       'name':'./dc:identifier',
                       'title':'./dc:Title',
                       'lib':'x'}
               }[wxs])
        borx = {'b':(self._bcached,self._bextract),'x':(self._xcached,self._xextract)}[ftx[src]['lib']]
        return cap[src],ftx[src],borx
    
class Combined(Remote):
    '''Subclass of the Remote connector but subclassing schema/metadata to attempt local file load first'''
    
    def __init__(self):
        super(Combined,self).__init__()
        
    @classmethod
    def schema(cls):
        try: return Local.schema()
        except Exception as lse:
            msg1 = 'Local SCH failed. {}'.format(lse)
            try: return Remote.schema()
            except Exception as rse: 
                msg2 = 'Remote SCH failed. {}'.format(rse)
                raise ValidatorException('{}\n{}'.format(msg1,msg2))
        
    @classmethod
    def metadata(cls,md_name): 
        try: return Local.metadata(md_name)
        except Exception as lme:
            msg1 = 'Local MD failed. {}'.format(lme)
            try: return Remote.metadata(md_name)
            except Exception as rme: 
                msg2 = 'Remote MD failed. {}'.format(rme)
                raise ValidatorException('\n{}\n{}'.format(msg1,msg2))
        
def main():
    
    v3 = Combined()
    v3.setschema()
    wfsi = v3.getids('wms')
    
    for lid in wfsi:
        try:
            v3.setmetadata(lid)
            v3.validate()
            v3.conditional()
            print(lid,True)
        except ValidatorAccessException as vae:
            print (lid,vae,False)
        except ValidatorParseException as vpe:
            print (lid,vpe,False)

#def main():
#    v2 = Remote()
#    wfsi = v2.getids('wms')
    
if __name__ == "__main__":
    main()
