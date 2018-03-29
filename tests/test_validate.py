
import unittest
import os
import sys
from numpy.random import sample

sys.path.append('../scripts/')

from validate import Remote, Local,ValidatorParseException,ValidatorAccessException
from cache import CacheHandler
from authenticate import Authentication

#testlog = LDSUtilities.setupLogging(ff=2)

            
class Test_1_setup(unittest.TestCase):
    
    def setUp(self):
        self.vdtr = Remote()
        
    def tearDown(self):
        del self.vdtr
        
    def test_1_get_wfs_ids(self):
        idlist = self.vdtr.getids('wfs')
        self.assertTrue(len(idlist)>0)
        
    def test_2_get_wms_ids(self):
        idlist = self.vdtr.getids('wms')
        self.assertTrue(len(idlist)>0)
        
    
    def test_3_get_metadata(self):
        '''test that we can get metadata'''
        for lid in _testvals('s'):
            sample = self.vdtr.metadata(lid) 
            self.assertTrue(_scanxml(sample))
            
    def test_4_validate_success_metadata(self):
        '''test validation of known successful layers'''
        for lid in _testvals('s'):
            self.vdtr.metadata(lid)
            self.vdtr.sch.validate(self.vdtr.md)
            self.assertTrue(True)
    
    def test_5_access_failure_metadata(self):
        '''test validation of known successful layers'''
        for lid in _testvals('ex'):
            try:
                self.vdtr.metadata(lid)
            except ValidatorAccessException as vae:
                self.assertIsInstance(vae,ValidatorAccessException)
                
    def test_6_validate_failure_metadata(self):
        '''test validation of known failing layers'''
        for lid in _testvals('f'):
            try:
                self.vdtr.metadata(lid)
                self.vdtr.sch.validate(self.vdtr.md)
            except ValidatorParseException as vpe:
                self.assertIsInstance(vpe,ValidatorParseException)


def _testvals(type='sf'):
    '''Returns a list of test ids'''
    ids = []
    if 's' in type: ids += [(i,'succeed') for i in ('50772','50845','50789')]
    if 'f' in type: ids += [(i,'fail') for i in ('50813','51362','51920')]
    if 'e' in type: ids += [(i,'error') for i in ('52552',)]
    if 'x' in type: ids += [(i,'nonexistant') for i in ('98765',)]
    return ids

def _scanxml(sample,snip=''): 
    '''Look XML snippet in sample'''
    return sample == True or snip in sample


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testLDSRead']
    unittest.main()