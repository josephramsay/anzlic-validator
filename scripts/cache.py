import sys
import time
import re
import os
import urllib.request
import http.client
import unittest
import hashlib
import io
from email import policy,message
from typing import Dict

#based on activestate recipe 491261 from staffan@tomtebo.org

CACHE_HEADER = 'x-cache-local'
THROTTLE_HEADER = 'x-throttling'
THROTTLE_DELAY = 5
DEF_RESP_LEN = 100000

class ThrottlingProcessor(urllib.request.BaseHandler):
    """Prevents overloading the remote web server by delaying requests.

    Causes subsequent requests to the same web server to be delayed
    a specific amount of seconds. The first request to the server
    always gets made immediately"""
    
    __shared_state = {} # type: Dict[str, int]
    
    def __init__(self,throttleDelay=THROTTLE_DELAY):
        """The number of seconds to wait between subsequent requests"""
        # Using the Borg design pattern to achieve shared state
        # between object instances:
        self.__dict__ = self.__shared_state
        self.throttleDelay = throttleDelay
        if not hasattr(self,'lastRequestTime'):
            self.lastRequestTime = {}
        
    def default_open(self,request):
        currentTime = time.time()
        if ((request.host in self.lastRequestTime) and
            (time.time() - self.lastRequestTime[request.host] < self.throttleDelay)):
            self.throttleTime = (self.throttleDelay -
                                 (currentTime - self.lastRequestTime[request.host]))
            # print "ThrottlingProcessor: Sleeping for %s seconds" % self.throttleTime
            time.sleep(self.throttleTime)
        self.lastRequestTime[request.host] = currentTime

        return None

    def http_response(self,request,response):
        if hasattr(self,'throttleTime'):
            response.info().add_header(THROTTLE_HEADER, "%s seconds" % self.throttleTime)
            del(self.throttleTime)
        return response

class CacheHandler(urllib.request.BaseHandler):
    """Stores responses in a persistant on-disk cache.

    If a subsequent GET request is made for the same URL, the stored
    response is returned, saving time, resources and bandwith"""    
    def __init__(self,cacheLocation):
        """The location of the cache directory"""
        self.cacheLocation = CacheHandler._create(cacheLocation)
        
    @staticmethod
    def _getcachepath(cacheLocation):
        '''Get the cache location relative to this file'''
        return os.path.abspath(os.path.join(os.path.dirname(__file__),cacheLocation))
    
    @staticmethod
    def _create(cacheLocation):
        colocated = CacheHandler._getcachepath(cacheLocation)
        if not os.path.exists(colocated):
            os.mkdir(colocated)
        return colocated
            
    @staticmethod
    def _flush(cacheLocation):
        '''Empty cache contents and the cache directory itself'''
        colocated = CacheHandler._getcachepath(cacheLocation)
        if os.path.exists(colocated):
            for f in os.listdir(colocated):
                os.unlink('{}/{}'.format(colocated, f))
            os.rmdir(colocated)
            
    def default_open(self,request):
        '''Respond to the request by first checking if there is a cached response otherwise defer to http handler'''
        if ((request.get_method() == "GET") and 
            (CachedResponse.ExistsInCache(self.cacheLocation, request.get_full_url()))):
            # print "CacheHandler: Returning CACHED response for %s" % request.get_full_url()
            return CachedResponse(self.cacheLocation, request.get_full_url(), setCacheHeader=True)    
        else:
            return None # let the next handler try to handle the request
        
    def https_response(self, request, response):
        '''Call http_response from https_response'''
        return self.http_response(request, response)
        
    def http_response(self, request, response):
        '''Post process the response object by seeing if its from the cache or live
        if live, store a copy then pull that same copy (without the cache-header) to return, 
        if from cache, pull cached copy again (add a cache-header) and return
        '''
        if request.get_method() == "GET":
            if CACHE_HEADER not in response.info():
                CachedResponse.StoreInCache(self.cacheLocation, request.get_full_url(), response)
                return CachedResponse(self.cacheLocation, request.get_full_url(), setCacheHeader=False)
            else:
                return CachedResponse(self.cacheLocation, request.get_full_url(), setCacheHeader=True)
        else:
            return response
    
class CachedResponse(io.StringIO):
    """An urllib2.response-like object for cached responses.

    To determine wheter a response is cached or coming directly from
    the network, check the x-cache header rather than the object type."""
    
    @staticmethod
    def ExistsInCache(cacheLocation, url):
        '''Checks if the hashed URL exists in the cache'''
        hash = CachedResponse._hash(url)
        return all([os.path.exists('{}/{}.{}'.format(cacheLocation,hash,horb)) for horb in ('headers','body')])

    @staticmethod
    def StoreInCache(cacheLocation, url, response):
        '''Store the provided response object in the cache.'''
        resp_len = response.length if hasattr(response,'length') else DEF_RESP_LEN
        hash = CachedResponse._hash(url)
        #write head
        with open('{}/{}.headers'.format(cacheLocation,hash), "w") as f:
            f.write(str(response.info()))
        #write body
        with open('{}/{}.body'.format(cacheLocation,hash), "w") as f:
            f.write(response.read(resp_len).decode('utf-8'))
    
    @staticmethod
    def RemoveFromCache(cacheLocation, url):
        '''Delete hash in the cache'''
        hash = CachedResponse._hash(url)
        try:
            os.remove('{}/{}.headers'.format(cacheLocation,hash))
            os.remove('{}/{}.body'.format(cacheLocation,hash))
        except FileNotFoundError: pass

    
    def __init__(self, cacheLocation,url,setCacheHeader=True):
        self.cacheLocation = cacheLocation
        hash = self._hash(url)
        cache_body = open(self._path(hash, 'body'),'r').read()
        io.StringIO.__init__(self, cache_body)
        #super(CachedResponse,self).__init__(cache_body)
        self.url, self.code, self.msg = url, 200, 'OK'
        headerbuf = open(self._path(hash, 'headers'),'r').read().strip()
        if setCacheHeader:
            headerbuf += '\n{}: {}\r\n'.format(CACHE_HEADER,self._path(hash))
        self.headers = http.client.HTTPMessage(policy.default)
        for line in headerbuf.splitlines():
            self.headers.add_header(*line.split(':',1)) if line else None
           
    @staticmethod     
    def _hash(plain):
        '''Hashes URL to encode name in cache'''
        return hashlib.md5(bytes(plain,'utf-8')).hexdigest()

    def _path(self,hash,sfx=None):
        return '{}/{}{}'.format(self.cacheLocation,hash,'.'+sfx if sfx else '')
    
    def info(self):
        return self.headers
    def geturl(self):
        return self.url
    
    def read(self):
        '''Compatibility wrapper for httpresponse'''
        return self.getvalue()

        
