import os
import re
import sys
import urllib.request   as UR
import urllib.parse     as UP
import urllib.error     as UE
import getopt

from pprint import pprint
#from typing import List, Dict, Set
from lxml import etree
from lxml.etree import XMLParser, XML, ElementTree, _Element
from lxml.etree import XMLSyntaxError, XMLSchemaParseError
from io import StringIO

from bs4 import BeautifulSoup as BS
#from lxml.isoschematron import _schematron_root

from abc import ABCMeta, abstractmethod

#Shifting from urllib to urllib2 we lost urlretrieve with its caching features. 
#One solution was to implement a cache solution but no longer sure that its required

from cache import CacheHandler, CachedResponse
#from resolve import RemoteResolver
import resolve
from authenticate import Authentication


#Raw AS recipe is py2, modified as cache import above
#import importlib.util
#spec = importlib.util.spec_from_file_location('CacheHandler','../ActiveStateCode/recipes/Python/491261_Caching_throttling/recipe-491261.py')
#module = importlib.util.module_from_spec(spec)
#spec.loader.exec_module(module)
BORX = 'b'
ENC = 'utf-8'
CACHE = '.validator_cache'
USE_CACHE = False
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
       
SL = ['http://www.isotc211.org/2005/',  
      'http://schemas.opengis.net/iso/19139/20070417/',
      'http://standards.iso.org/ittf/PubliclyAvailableStandards/ISO_19139_Schemas/',
      'https://www.ngdc.noaa.gov/emma/xsd/schema/']
SLi = 0

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
        '''meta init'''
    def setmetadata(self,lid):
        self.md = self.metadata(lid)
        
    def validate(self,md=None):
        '''Wrap schema validation to throw MetadataParseException'''
        if not hasattr(self.sch,'validate'): 
            raise MetadataParseException('XML Schema invalid')
        if not self.sch.validate(md or self.md): 
            raise MetadataParseException('Unable to validate XML')
        #self.sch.assertValid(md or self.md)
        return True
    
    @staticmethod
    def _bcached(url,enc=ENC):
        '''Wrapper for cached url open with bs'''
        txt = SCHMD._request(url)
        bst = BS(txt,'lxml-xml')
        return bst
    
    @staticmethod
    def _xcached(url,enc=ENC):
        '''Wrapper for cached url open with lxml'''
        resp = SCHMD._request(url)
        txt = SCHMD._extracttxt(resp,enc)
        xml = SCHMD._parsetxt(txt,resp,enc)
        return xml
    
    @staticmethod
    def _parsetxt(txt,resp=None,enc=None,history=None):#{'cache':[],'fail':[]}):
        '''Parse provided text into XML doc'''
        if enc and resp and isinstance(resp,CachedResponse): 
            resolver = resolve.CacheResolver(resp,enc,history)
            parser = RemoteParser(enc)
            parser.resolvers.add(resolver)
            return etree.XML(txt, parser)
        return etree.XML(txt)
        
    @staticmethod
    def _extracttxt(resp,enc):
        '''Get the bytes text from the response if it hasn't already been done and if encoding is specified'''
        txt = resp.read()
        #test that an encoding value is supplied and that either the resp is http or the txt is not already bytes
        if enc and not isinstance(txt,bytes):#(hasattr(resp,'url') or 
            txt = txt.encode(enc)
        return txt
        #return SCHMD._hackisotc211(txt)
    
    @staticmethod
    def _request(url):
        '''Add cachehandler as additional opener and open'''
        if USE_CACHE:
            opener = UR.build_opener(CacheHandler(CACHE))
            UR.install_opener(opener)
        return UR.urlopen(url)
    
    @staticmethod
    def _hackisotc211(txt):
        '''The isotc211 sometimes goes offline but is still referred to throughout related schemas. 
        This hack replaces that reference in the supplied schema text'''
        return txt.replace(bytes(SL[0],'utf-8'),bytes(SL[SLi],'utf-8')) if SLi else txt
        
    def conditional(self, md=None):
        '''Bonus conditional extent checks'''
        dataset = False
        if md is not None: self.md = md
        for element in self.md.findall('gmd:hierarchyLevel/gmd:MD_ScopeCode',namespaces=NSX):
            if not element.get('codeListValue'):
                raise MetadataConditionalException('No Hierarchy Level Declared')
            elif element.get('codeListValue') == 'dataset':
                dataset = True
        
        if dataset:
            idin = self.md.find('gmd:identificationInfo',namespaces=NSX)
            for mddid in idin.iterfind('gmd:MD_DataIdentification',namespaces=NSX):
                if not isinstance(mddid.find('gmd:topicCategory/gmd:MD_TopicCategoryCode',namespaces=NSX),_Element):
                    raise MetadataConditionalException('No Topic Category Declared')
                if not isinstance(mddid.find('gmd:extent',namespaces=NSX),_Element):
                    raise MetadataConditionalException('No Extent Declared')
                else:
                    extent = mddid.find('gmd:extent/gmd:EX_Extent/gmd:geographicElement',namespaces=NSX)
                    if not isinstance(extent.find('gmd:EX_GeographicBoundingBox',namespaces=NSX),_Element) \
                    and not isinstance(extent.find('gmd:EX_GeographicDescription',namespaces=NSX),_Element):
                        raise MetadataConditionalException('No Geographic Bounding Box or Geographic Description Declared')
    
        if not isinstance(self.md.find('gmd:language/gco:CharacterString',namespaces=NSX),_Element):
           raise MetadataConditionalException('No language/CS defined')
       
        if not isinstance(self.md.find('gmd:characterSet/gmd:MD_CharacterSetCode',namespaces=NSX),_Element):
           raise MetadataConditionalException('No CharacterSetCode defined')
       
        mddid = self.md.find('gmd:identificationInfo/gmd:MD_DataIdentification',namespaces=NSX)
        if not isinstance(mddid.find('gmd:language/gco:CharacterString',namespaces=NSX),_Element):
           raise MetadataConditionalException('No ID Info language/CS defined')
       
        if not isinstance(mddid.find('gmd:characterSet/gmd:MD_CharacterSetCode',namespaces=NSX),_Element):
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
        sch_pr = UP.urlparse(SL[SLi])
        sch_path = os.path.abspath(os.path.join(os.path.dirname(__file__),cls.SP,sch_pr.netloc,sch_pr.path[1:],'gmd',sch_name))
        if not os.path.exists(sch_path):
            cls._copyschemas(sch_pr)
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
    
    @classmethod
    def _copyschemas(cls,pr):
        '''Pull an entire URL tree of schemas...'''
        os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__),cls.SP)))
        os.system('wget -r -np -R "index.html*" {}://{}{}'.format(pr.scheme,pr.netloc,pr.path))
            
class Remote(SCHMD):
    '''Remote parser grabbing remote content but employing caching'''
    def __init__(self):
        super(Remote,self).__init__()  
    
    @classmethod
    def schema(cls):
        '''Fetch and parse the ANZLIC metadata schema'''
        sch_name = '{url}gmd/metadataEntity.xsd'.format(url=SL[SLi])
        print (sch_name)
        sch_doc = cls._xcached(sch_name)
        try:
            sch = etree.XMLSchema(sch_doc)
            return sch
        except XMLSchemaParseError as xspe:
            print(xspe)
            raise
        
    @classmethod
    def metadata(cls,lid):
        '''Get the default metadata for each layer identified by layer id'''
        md_name = 'https://data.linz.govt.nz/layer/{lid}/metadata/iso/xml/'    

        try:
            md_handle = UR.urlopen(md_name.format(lid=lid[0]))
            md = etree.parse(md_handle)
            return md
        except XMLSyntaxError as xse:
            #Private layers are inaccessible
            if 'https://id.koordinates.com/login' in md_handle.url:
                raise InaccessibleMetadataException('Private layer {}.\n{}'.format(lid,xse))
            else:
                raise MetadataParseException('Metadata parse error {}.\n{}'.format(lid,xse))
        except UE.HTTPError as he:
            raise InaccessibleMetadataException('Metadata unavailable {}.\n{}'.format(lid,he))
        except Exception as e:
            #catch any other error and continue, may not be what is wanted
            raise ValidatorException('Processing error {}.\n{}'.format(lid,e))
        return None
        
    def getids(self, wxs = 'wfs', sorf = 'services', torl = 'layer'):
        '''Read the layer and table IDS from the getcapabilities for the WFS and WMS service types
        wxs: WFS or WMS (or both WxS TODO) 
        sorf: Services or Feeds (only one makes sense)
        torl: Layer or Table or both landt/tandl
        cap: capabilities url template
        ftx: feature type xpath fragment
        borx: parser selection, beautifulsoup or lxml
        '''
        cap, ftx, borx = self._geturlset(sorf, wxs)
        try:
            url = cap.format(key=KEY,wxs=wxs)
            bst = borx[0](url)
            #find all featuretypes
            ret = borx[1](bst, ftx)
        except UE.HTTPError as he:
            raise CapabilitiesAccessException('Failed to get {}/{} layer ids.\n{}'.format(wxs,sorf,he))
        except ValueError as ve:
            raise CapabilitiesParseException('Failed to read {}/{} layer ids.\n{}'.format(wxs,sorf,ve))
        #Catch if no features found
        try: ret
        except NameError: raise CapabilitiesParseException('No matching {} features found'.format(wxs))
            
        return ret if torl in ('tandl','landt') else ret[lort] 
    
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

    
    def _geturlset(self,sorf,wxs):
        '''Returns capabilities URL, xpath fragment to title/name and parser method
        wxs: Select xpath for wfs/wms layer types
        sorf: Select where to get layer IDs from; services or feeds. 
        (If selecting LDS Services, capabilities are limited to 250 results so will have to be paged)
        '''
        cap = {'services':'http://data.linz.govt.nz/services;key={key}/{wxs}?service={wxs}&request=GetCapabilities',
               'feeds':'http://data.linz.govt.nz/feeds/csw?service=CSW&version=2.0.2&request=GetRecords&constraintLanguage=CQL_TEXT&typeNames=csw:Record&resultType=results&ElementSetName=summary'}
        #wfs/wms feature paths      
        ftx = {'services':{'wfs':{'path':'FeatureType',
                       'name':'Name',
                       'title':'Title',
                       'lib':'b'},
                'wms':{'path':'Capability/Layer/Layer',
                       'name':'Name',
                       'title':'Title',
                       'lib':'x'}
               }[wxs],        
               'feeds':{'wfs':{'path':'//csw:SearchResults/csw:SummaryRecord',
                       'name':'./dc:identifier',
                       'title':'./dc:Title',
                       'lib':'b'},
                'wms':{'path':'//csw:SearchResults/csw:SummaryRecord',
                       'name':'./dc:identifier',
                       'title':'./dc:Title',
                       'lib':'x'}
               }[wxs]}
        borx = {'b':(self._bcached,self._bextract),'x':(self._xcached,self._xextract)}[ftx[src]['lib']]
        return cap[sorf],ftx[sorf],borx
    
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
    def metadata(cls,id=None,name=None): #-> _Element:
        '''Wrapper attempting local metadata load. 
        NB. Uses Filename or layer_id which determines fetch method'''
        if name:
            try: return Local.metadata(name)
            except Exception as lme:
                raise ValidatorException('Local MD failed. {}'.format(lme))
        if id:
            try: return Remote.metadata(id)
            except Exception as rme: 
                raise ValidatorException('Remote MD failed. {}'.format(rme))
            
        raise ValidatorException('No Layer Id or filename specified')
        
class RemoteParser(XMLParser):
    '''Simple custom parser wrapper overrodes init with encoding spec'''
    def __init__(self,enc): #-> None:
        super(RemoteParser,self).__init__(ns_clean=True,recover=True,encoding=enc)
       
    
def process(opts,args):
    '''Validate all layers'''
    
    global USE_CACHE
    
    id = None
    wxs = 'wfs'
    torl = 'layer'
    sorf = 'services'
    
    if 'cache' in args: 
        USE_CACHE = True
    else:
        USE_CACHE = False
        
    if 'local' in args:
        Validator = Local
    elif 'remote' in args:
        Validator = Remote
    else:
        Validator = Combined
        
    for o,v in opts:
        if o in ('-i','--id'): id = [(v,'user supplied'),]
        if o in ('-w','--wxs') and v in ('wfs','wms'): wxs = v
        if o in ('-t','--torl') and v in ('layer','table','tandl','landt'): torl = v
        if o in ('-s','--sorf') and v in ('services','feeds'): sorf = v
        
    #v1 = Remote()
    #v1.setschema()
    v3 = Validator()
    v3.setschema()
    
    wxsi = id or v3.getids(wxs=wxs,sorf=sorf,torl=torl)
    
    for lid in wxsi:
        try:
            v3.setmetadata(lid)
            v = v3.validate()
            c = v3.conditional()
            print(lid,v and c)
        except ValidatorException as ve:
            print (lid,ve,False)
    
def poa(oa):
    '''Options and Args reorganised for getopts'''
    o = [('{}:'.format(i[0]),'{}='.format(i[1:])) for i in oa[0].split(',')]
    a = [(i[0],i[1:]) for i in oa[1].split(',')]
    return (''.join([i[0] for i in o]+[i[0] for i in a]),[i[1] for i in o]+[i[1] for i in a])

def main():
    '''Main function gets args and parses the system ones'''
    
    oa = ['wwxs,iid,ttorl,ssorf','llocal,rremote,ccache,vversion,hhelp']
    try:
        opts, args = getopt.getopt(sys.argv[1:], *poa(oa))
    except getopt.error as msg:
        print (msg+". For help use --help")
        sys.exit(2)
        
    for opt, val in opts:
        if opt in ("-h", "--help"):
            print (__doc__)
            sys.exit(0)
        elif opt in ("-v", "--version"):
            print (__version__)
            sys.exit(0)
        
    process(opts,args)

if __name__ == "__main__":
    main()
