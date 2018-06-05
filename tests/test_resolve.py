
import unittest
import sys

sys.path.append('../scripts/')

#from resolve import RemoteResolver
import resolve

T = 'https://data.linz.govt.nz/layer/50772-nz-primary-parcels/metadata/iso/xml/'

class Test_1_init(unittest.TestCase):
        
    def setUp(self):  
        self.resolve = RemoteResolver()
        self.resolve.response.cacheLocation = '/tmp'
        self.resolve.PICKLESFX = '.test.history'
        
    def tearDown(self):
        del self.resolve    
        
    def test_10_resolve(self):
        response = urllib.urlopen(T)
        
class Test_2_remote(unittest.TestCase):
        
    def setUp(self):
        self.remote = Remote()
        self.remote.setschema() 
        self.resolve = RemoteResolver()
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
