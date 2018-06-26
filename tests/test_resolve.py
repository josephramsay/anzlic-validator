
import unittest
import sys
import os
import urllib

script_dir = os.path.abspath(os.path.join(os.path.dirname(__file__),'../scripts/'))
sys.path.append(script_dir)

#from resolve import RemoteResolver
import resolve
import validate

T = 'https://data.linz.govt.nz/layer/50772-nz-primary-parcels/metadata/iso/xml/'
E = 'UTF-8'

class Test_1_init(unittest.TestCase):
        
    def setUp(self):  
        pass
#         resp = urllib.request.urlopen(T)
#         self.resolve = resolve.CacheResolver(resp,E,None)
#         self.resolve.response.cacheLocation = '/tmp'
#         self.resolve.PICKLESFX = '.test.history'
        
    def tearDown(self):
        pass
#        del self.resolve    
        
    def test_10_resolve(self):
        resp = validate.SCHMD._request(T)
        #txt = validate.SCHMD._extracttxt(resp,E)
        #xml = validate.SCHMD._parsetxt(txt,resp,E)
        rso = resolve.CacheResolver(resp,E,None)
        rso.response.cacheLocation = '/tmp'
        rso.PICKLESFX = '.test.history'

        
    def test_20_noncache(self):
        '''Test that an HTTP resp raises a non-cached error'''
        resp = urllib.request.urlopen(T)
        with self.assertRaises(resolve.NonCachedResponseException) as ncre:
            rso = resolve.CacheResolver(resp,E,None)
        self.assertEqual('Provided response object is not from a cached source', str(ncre.exception), 'Not expecting CachedResponse object')
        
class Test_2_remote(unittest.TestCase):
        
    def setUp(self):
        self.remote = validate.Remote()
        self.remote.setschema() 
        self.resolve = resolve.CacheResolver()
        self.resolve.response.cacheLocation = '/tmp'
        self.resolve.PICKLESFX = '.test.history'
        
    def tearDown(self):
        del self.resolve    
        
    def test_10_resolve(self):
        opener = urllib.request.build_opener(CacheHandler(TEST_CACHE))
        resp = opener.open(TEST_URL)
        
SXML = '''
<?xml version="1.0" encoding="utf-8"?>
<note>
  <to>str1234</to>
  <from>str1234</from>
  <heading>str1234</heading>
  <body>str1234</body>
</note>
'''
SXSD = '''
<?xml version="1.0"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:element name="note">
      <xs:complexType>
        <xs:sequence>
          <xs:element name="to" type="xs:string"/>
          <xs:element name="from" type="xs:string"/>
          <xs:element name="heading" type="xs:string"/>
          <xs:element name="body" type="xs:string"/>
        </xs:sequence>
      </xs:complexType>
    </xs:element>
</xs:schema> 
'''


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testLDSRead']
    unittest.main()
