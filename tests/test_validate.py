
import unittest
import os
import sys

sys.path.append('../scripts/')

from validate import Remote, Local,Combined,ValidatorParseException,ValidatorAccessException,NSX
from cache import CacheHandler
from authenticate import Authentication

from typing import List, Tuple

class Test_1_init(unittest.TestCase):
        
    def setUp(self):
        self.local = Local()
        self.remote = Remote()
        
    def tearDown(self):
        del self.local
        del self.remote
        
    def test_10_setlocalschema(self):
        '''Test that we can set a local schema'''
        m = 'Failed to setschema on local'
        try: 
            self.local.setschema()
        except Exception as e:  
            m += ' '+str(e)
        self.assertNotEqual(self.local.sch,None,m)
        
    def test_20_setalllocalschema(self):
        pass
        
    def test_30_setremoteschema(self):
        '''Test that we can set a remote schema'''
        m = 'Failed to setschema on remote'
        try:
            self.remote.setschema()    
        except Exception as e:  
            m += ' '+str(e)
        self.assertNotEqual(self.remote.sch,None,m)
        
    def test_40_setremotewithlocalschema(self):
        '''Test that we can set a local schema on a remote instance'''
        m = 'Failed remote.sch = Local.sch()'
        try:
            self.remote.sch = Local.schema()  
        except Exception as e:  
            m += ' '+str(e)
        self.assertNotEqual(self.remote.sch,None,m)    
    
    def test_50_setlocalwithremoteschema(self):
        '''Test that we can set a remote schema on a local instance'''
        m = 'Failed local.sch = Remote.sch()'
        try:
            self.local.sch = Remote.schema()    
        except Exception as e:  
            m += ' '+str(e)
        self.assertNotEqual(self.local.sch,None,m)

            
class Test_2_setuplocal(unittest.TestCase):
    
    def setUp(self):
        self.local = Local()
        self.local.setschema()
        
    def tearDown(self):
        del self.local
        
    def test_10_get_metadata(self):
        '''Test that we can get local metadata'''
        for mdn in _testnames():
            sample = self.local.metadata(mdn[0]) 
            self.assertTrue(_scanxml(sample,'gmd:MD_Metadata'))
           
class Test_3_setupremote(unittest.TestCase):
    
    def setUp(self):
        self.remote = Remote()
        self.remote.setschema()
        
    def tearDown(self):
        del self.remote
        
    def test_10_get_wfs_ids(self):
        idlist = self.remote.getids('wfs')
        self.assertTrue(len(idlist)>0)
        
    def test_20_get_wms_ids(self):
        idlist = self.remote.getids('wms')
        self.assertTrue(len(idlist)>0)
        
    def test_30_get_metadata(self):
        '''test that we can get metadata'''
        for lid in _testvals('s'):
            sample = self.remote.metadata(lid) 
            self.assertTrue(_scanxml(sample))
            
    def test_40_validate_success_metadata(self):
        '''test validation of known successful layers'''
        self.remote.setschema()
        for lid in _testvals('s'):
            self.remote.setmetadata(lid)
            self.remote.validate()
            self.assertTrue(True)
    
    def test_50_access_failure_metadata(self):
        '''test validation of known successful layers'''
        self.remote.setschema()
        for lid in _testvals('ex'):
            try:
                self.remote.setmetadata(lid)
            except ValidatorAccessException as vae:
                self.assertIsInstance(vae,ValidatorAccessException)
                continue
            self.assertFalse(True, 'Expected ValidatorAccessException')    
            
    def test_60_access_failure_metadata_ARTEST(self):
        '''test validation of known successful layers'''
        self.remote.setschema()
        for lid in _testvals('ex'):
            assertRaises(ValidatorAccessException,self.remote.setmetadata,lid)
   
                
    def test_70_validate_failure_metadata(self):
        '''test validation of known failing layers'''
        self.remote.setschema()
        for lid in _testvals('f'):
            try:
                self.remote.setmetadata(lid)
                self.remote.validate()
            except ValidatorParseException as vpe:
                self.assertIsInstance(vpe,ValidatorParseException)
                continue
            self.assertFalse(True, 'Expected ValidatorParseException')

class Test_4_setupcombined(unittest.TestCase):
    
    def setUp(self):
        self.combined = Combined()
        self.combined.setschema()
        
    def tearDown(self):
        del self.combined
        
    def test_10_get_wfs_ids(self):
        idlist = self.combined.getids('wfs')
        self.assertTrue(len(idlist)>0)
        
    def test_20_get_wms_ids(self):
        idlist = self.combined.getids('wms')
        self.assertTrue(len(idlist)>0)
        
    
    def test_30_get_metadata(self):
        '''test that we can get metadata'''
        for lid in _testvals('s'):
            sample = self.combined.metadata(lid) 
            self.assertTrue(_scanxml(sample))
        
        
def _testvals(type: str = 'sf') -> List[Tuple]:
    '''Returns a list of test ids'''
    ids = [] # type: List[Tuple]
    if 's' in type: ids += [(i,'succeed') for i in ('50772','50845','50789')]
    if 'f' in type: ids += [(i,'fail') for i in ('50813','51362','51920')]
    if 'e' in type: ids += [(i,'error') for i in ('52552',)]
    if 'x' in type: ids += [(i,'nonexistant') for i in ('98765','12345',)]
    return ids

def _testnames(type: str = '') -> List[Tuple]:
    return [('nz-primary-parcels.iso.xml','succeed'),]

def _scanxml(sample, snip: str = '') -> bool: 
    '''Look for XML snippet in sample'''
    return sample == True or sample.getroot().find(snip,namespaces=NSX)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testLDSRead']
    unittest.main()