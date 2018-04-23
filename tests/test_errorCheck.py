import unittest
import os
import sys

sys.path.append('../scripts/')

from validate import Remote, Local, InaccessibleMetadataException
import errorChecker
from errorChecker import runAllChecks, search, MetadataIncorrectException, \
     MetadataEmptyException, MetadataNoneException, MetadataErrorException, \
     InaccessibleFileException, runBasicChecks

from typing import List, Tuple

class Test_1_setup(unittest.TestCase):

    def setUp(self):
        self.vdtr = Remote()

    def tearDown(self):
        del self.vdtr

    def test_1_getMetadata(self):
        ''' test that can get metadata '''
        for lid in _testvals('c'):
            meta = self.vdtr.metadata(lid)
            self.assertTrue(_scanxml(meta))

    def test_2_correctAllMetadata(self):
        ''' test error check on correct layers '''
        for lid in _testvals('c'):
            try:
                meta = self.vdtr.metadata(lid)
                runAllChecks(meta, lid)
            except Exception as e:
                self.assertFalse(True, 'Expected To Pass, Got: {}'.format(e))
                continue
        

    def test_3_correctBasicMetadata(self):
        ''' test error check on selected base checks '''
        for lid in _testvals('bc'):
            try:
                meta = self.vdtr.metadata(lid)
                runBasicChecks(meta)
            except Exception as e:
                self.assertFalse(True, 'Expected To Pass, Got: {}'.format(e))
                continue

    def test_3_incorrectMetadata(self):
        ''' test error check on incorrect/invalid layers '''
        for lid in _testvals('i'):
            try:
                meta = self.vdtr.metadata(lid)
                runAllChecks(meta, lid)
            except MetadataIncorrectException as mie:
                self.assertIsInstance(mie, MetadataIncorrectException)
                continue
            self.assertFalse(True, 'Expected MetadataIncorrectException')

    def test_4_emptyMetadata(self):
        ''' test error check on layers with empty tags '''
        for lid in _testvals('e'):
            try:
                meta = self.vdtr.metadata(lid)
                runAllChecks(meta, lid)
            except MetadataEmptyException as mee:
                self.assertIsInstance(mee, MetadataEmptyException)
                continue
            self.assertFalse(True, 'Expected MetadataEmptyException')

    def test_5_noneMetadata(self):
        ''' test error check on layers with missing fields '''
        for lid in _testvals('n'):
            try:
                meta = self.vdtr.metadata(lid)
                runAllChecks(meta, lid)
            except MetadataNoneException as mne:
                self.assertIsInstance(mne, MetadataNoneException)
                continue
            self.assertFalse(True, 'Expected MetadataNoneException')

    def test_6_errorMetadata(self):
        ''' test all in error '''
        for lid in _testvals('ipn'):
            try:
                meta = self.vdtr.metadata(lid)
                runAllChecks(meta, lid)
            except MetadataErrorException as mee:
                self.assertIsInstance(mee, MetadataErrorException)
                continue
            self.asserFalse(True, 'Expected MetadataErrorException')

    def test_7_fileSearchError(self):
        ''' test file search raises error if cannot find keyword '''
        try:
            search(errorChecker.FILE, 'TEST: ')
            self.assertFalse(True, 'Expected InaccessibleFileException')
        except InaccessibleFileException as ife:
            self.assertIsInstance(ife, InaccessibleFileException)
            


    def test_8_fileSearchCorrect(self):
        ''' test file search can find text based on keyword '''
        try:
            word = search(errorChecker.FILE, 'ORGANISATIONNAME: ')
        except Exception as e:
            self.assertFalse(True, e)
            
        self.assertTrue(word)

        
def _testvals(type: str = 'sf') -> List[Tuple]:
    '''Returns a list of test ids'''
    ids = [] # type: List[Tuple]
    if 'b' in type: ids += [(i, 'baseCorrect') for i in ('53455', '50201', '50972', '50202', '50203', )]
    if 'c' in type: ids += [(i, 'correct') for i in ('50813', '50053', '50526', '50643',)]
    if 'i' in type: ids += [(i, 'incorrect') for i in ('51871', '51769', '51870', '52344', '51362', '50845', '53455',)]
    if 'p' in type: ids += [(i, 'empty') for i in ('51920','50772', '50789', '53451', '53519',)]
    if 'n' in type: ids += [(i, 'none') for i in ('51306', '51368','51389',)]
    
    return ids

def _scanxml(sample, snip: str = '') -> bool: 
    '''Look for XML snippet in sample'''
    if sample is not None:
        return True
    else:
        return snip in sample

if __name__ == "__main__":
    unittest.main()
