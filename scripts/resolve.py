'''
Name: resolve
Created: 11/03/2018
@author: jramsay

Notes.
Contains CacheResolver module that, given a CachedResponse, typically a schema document,  
will attempt to precache all linked sub schemas and provide these back to the lxml.etree parser 
when assigned as a resolver


Todo.
1.redirect _getXMLResponse to a logger instance (DisplayWrapper)
'''

import os
#import re
import urllib.request   as UR
import urllib.parse     as UP
import urllib.error     as UE
import pickle

# from validate import NSX, SCHMD, InaccessibleSchemaException
import validate

from pprint import pprint
# from typing import List, Dict, Set
from lxml import etree
from lxml.etree import Resolver, XMLParser, XML, ElementTree, _Element
from lxml.etree import XMLSyntaxError, XMLSchemaParseError
from io import StringIO
from functools import wraps, partial

from bs4 import BeautifulSoup as BS
# from lxml.isoschematron import _schematron_root

from abc import ABCMeta, abstractmethod

# Shifting from urllib to urllib2 we lost urlretrieve with its caching features.
# One solution was to implement a cache solution but no longer sure that its required

from cache import CacheHandler, CachedResponse

#http://schemas.opengis.net/gml/3.1.1/base/topology.xsd
SL = ['http://www.isotc211.org/2005/',  
      'http://schemas.opengis.net/iso/19139/20070417/',
      'http://standards.iso.org/ittf/PubliclyAvailableStandards/ISO_19139_Schemas/',
      'https://www.ngdc.noaa.gov/emma/xsd/schema/']
SLi = 1
    
DEPTH = 0

class NonCachedResponseException(Exception): pass

class DisplayWrapper(object):
    '''Simple wrapper function to display schema call stack'''
    @classmethod
    def show(cls,func=None):
        if func is None:
            return partial(cls.show)

        @wraps(func)
        def wrapper(*args, **kwargs):
            global DEPTH
            DEPTH += 1
            print('#{}# {} - {}'.format(DEPTH,'--'*DEPTH,args[1]))
            res = func(*args, **kwargs)
            DEPTH -= 1
            return res
        
        return wrapper
    
    

class CacheResolver(Resolver):
    '''Custom resolver to redirect resolution of cached resources back through the cache'''
    PICKLESFX = '.history'   # type: str
    BLANKHIST = {'cache':set([]),'fail':set([])}   # type: Dict[str,Set[str]]
    
    #def __init__(self,response,encoding='UTF-8',history=None): # -> None:
    def __init__(self,*args, **kwargs): # -> None
        self.response = self._testresp(kwargs.get('response') or args[0])
        self.encoding = kwargs.get('encoding') or args[1] or 'UTF-8'
        self.source = self.response.url
        self.history = kwargs.get('history') or args[2] or self._load_hist(self.source)
        #self.response = self._testresp(response)          
        #self.encoding = encoding      
        
        #self.history = history or self._load_hist(self.source)
        self.doc = XML(validate.SCHMD._extracttxt(self.response,self.encoding))
        if self.doc.tag.lower() == 'html':  
            raise validate.InaccessibleSchemaException('Invalid response, {} is HTML'.format(self.source))
        self.target = self.doc.attrib['targetNamespace'] if self.doc.attrib.has_key('targetNamespace') else SL[SLi]

        #precache imports
        self._precache()
        #if not history: # ensures saving only at end of resolve init
        self._save_hist()
    
    def _testresp(self,response):
        '''Test that the response is a cache type'''
        if isinstance(response,CachedResponse):
            return response
        raise NonCachedResponseException('Provided response object is not from a cached source')
     
    def _precache(self): # -> None:
        '''Precache imports and includes'''
        for incl in self.doc.findall('xs:include',namespaces=validate.NSX):
            for i,ns in enumerate([self.source,self.target]):
                if self._getimports(UR.urljoin(self._slash(ns),incl.attrib['schemaLocation']),'include-{}'.format(i)):
                    break
        for impt in self.doc.findall('xs:import',namespaces=validate.NSX):
            for i,ns in enumerate([self.source,self.target,impt.attrib['namespace']]):
                if self._getimports(UR.urljoin(self._slash(ns),impt.attrib['schemaLocation']),'import-{}'.format(i)):
                    break

    def _getimports(self,url,i): # -> None:
        '''import xsd using selectio of urls including targetNamespace, namespace and url of source'''
        #for i,url in enumerate(ul):
        #hasn't been fetched already or in failed list
        if url in self.history['cache']:
            pass
            #print ('URL {} fetched already'.format(url))
        elif url in self.history['fail']:
            pass
            #print ('Failing URL {} requested'.format(url))
        #if url not in [x for v in self.history.values() for x in v]:
        else:
            try:
                #print ('Precaching url {}. {}'.format(i,url))
                self._getXMLResponse(url)
                #break
                return True
            except validate.InaccessibleSchemaException as ise:
                print (ise)
            except XMLSyntaxError as xse:
                print ('Cannot parse url {}, {}'.format(i,url))
            except Exception as e:
                print ('Unexpected Exception {} with {}'.format(e,url))
            self.history = CacheResolver._merge(self.history,{'fail':set([url,])})
            CachedResponse.RemoveFromCache(self.response.cacheLocation,url)  
            return False
        return True
    
  
    def _load_hist(self,src=None): # -> Dict:
        '''Return fetch/fail history from file or touch/init a new picklefile if reqd'''
        hist = self.BLANKHIST
        if src and hasattr(self.response,'cacheLocation'):
            self.picklefile = '{}/{}{}'.format(self.response.cacheLocation,CachedResponse._hash(src),self.PICKLESFX)
            try: 
                with open(self.picklefile,'rb') as f:
                    hist = pickle.load(f)
                #return self._merge(self.history,pickle.load(open(self.picklefile,'rb')))
            except (EOFError, FileNotFoundError) as fnfe:
                #touch
                with open(self.picklefile, 'ab') as f:
                    pass
        return hist
           

    def _save_hist(self): # -> None:
        '''Save the fetched/failed url list into picklefile, merging with existing'''
        if hasattr(self,'picklefile'):
            hist = self._merge(self.history,self._load_hist())
            with open(self.picklefile,'wb') as f:
                pickle.dump(hist,f)
    
    @DisplayWrapper.show()
    def _getXMLResponse(self,url): # -> None:
        resp = validate.SCHMD._request(url)
        merge_hist = CacheResolver._merge(self.history,{'cache':set([url,])})
        resolver = CacheResolver(resp,self.encoding,merge_hist)
        self.history = CacheResolver._merge(self.history,resolver.history)
  
    @staticmethod        
    def _merge(a,b): # -> Dict:
        '''Unidirectional merge from a<-b'''
        c = a.copy()
        for k in c:
            if k in b: c[k].update(b[k])
        return c 
        #return {k:a[k].copy().update(b[k]) if k in b else a[k].copy() for k in a.keys()}

    @staticmethod
    def _slash(u): # -> str:
        return os.path.join(u,'') if u.rfind('/')>u.rfind('.') else u

    def _cached(self,frag): # -> str:
        for u in [h for h in self.history['cache'] if h not in self.history['fail']]:
            if frag.lstrip('.') in u: return u
        return None
        
    def resolve(self, system_url, public_id, context): # -> str:
        '''Override of resolver resolve method that fetches and reads cached pages using the result in a resolve_string call'''
        #pprint (self.history)
        rstr = None
        cached_url = self._cached(system_url)
        print (system_url,'->',cached_url)
        resp = validate.SCHMD._request(cached_url)
        txt = validate.SCHMD._extracttxt(resp,self.encoding)
        try:
            rstr = self.resolve_string(txt.decode(self.encoding),context) if txt else None
        except Exception as e:
            print ('resolve_string failed with {}, defaulting'.format(system_url))
        return rstr
        
        

def test1():
    '''Test function used here to check py27 vs py3 compatability'''
    
    opener = UR.build_opener(CacheHandler('.test_cache'))
    UR.install_opener(opener)
    resp = UR.urlopen('https://data.linz.govt.nz/layer/50772-nz-primary-parcels/metadata/iso/xml/')

    resolver = CacheResolver(resp,'utf-8',None)

def main():
    test1()
    
if __name__ == "__main__":
    main()
    

