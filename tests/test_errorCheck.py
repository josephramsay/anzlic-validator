import unittest
import os
import sys

script_path = os.path.abspath(os.path.join(os.path.dirname(__file__),'../scripts'))
sys.path.append(script_path)


from validate import Combined, InaccessibleMetadataException
from errorChecker import runChecks, MetadataIncorrectException, \
     MetadataEmptyException, MetadataNoneException, MetadataErrorException, \
     InaccessibleFileException, InvalidConfigException

class Test_1_setup(unittest.TestCase):

    def setUp(self):
        self.vdtr = Combined()

    def tearDown(self):
        del self.vdtr

    def test_1_getMetadata(self):
        ''' test that can get metadata '''
        for lid in _testvals('c'):
            meta = self.vdtr.metadata(lid)
            self.assertTrue(_scanxml(meta))

    def test_2_correctAllMetadata(self):
        ''' test error check on correct layers '''
        try:
            print (os.getcwd())
            metafile =  r'{}/testAllCorrect.xml'.format(os.getcwd())
            con = r'{}/testConfigAll.yaml'.format(os.getcwd())
            meta = self.vdtr.metadata(name=metafile)
            runChecks(meta, con=con)
        except Exception as e:
            self.assertFalse(True)

    def test_3_incorrectMetadata(self):
        ''' test error check on incorrect/invalid layers '''
        for lid in _testvals('i'):
            try:
                meta = self.vdtr.metadata(lid)
                runChecks(meta, lid)
            except MetadataIncorrectException as mie:
                self.assertIsInstance(mie, MetadataIncorrectException)
                continue
            self.assertFalse(True, 'Expected MetadataIncorrectException')

    def test_4_emptyMetadata(self):
        ''' test error check on layers with empty tags '''
        for lid in _testvals('e'):
            try:
                meta = self.vdtr.metadata(lid)
                runChecks(meta, lid)
            except MetadataEmptyException as mee:
                self.assertIsInstance(mee, MetadataEmptyException)
                continue
            self.assertFalse(True, 'Expected MetadataEmptyException')
            
    def test_5_noneMetadata(self):
        ''' test error check on layers with missing fields '''
        for lid in _testvals('n'):
            try:
                meta = self.vdtr.metadata(lid)
                runChecks(meta, lid)
            except MetadataNoneException as mne:
                self.assertIsInstance(mne, MetadataNoneException)
                continue
            self.assertFalse(True, 'Expected MetadataNoneException')
                             
    def test_6_errorMetadata(self):
        ''' test all in error '''
        for lid in _testvals('ipn'):
            try:
                meta = self.vdtr.metadata(lid)
                runChecks(meta, lid)
            except MetadataErrorException as mee:
                self.assertIsInstance(mee, MetadataErrorException)
                continue
            self.asserFalse(True, 'Expected MetadataErrorException')

    def test_7_allOptionsConfig(self):
        ''' test config with all options at least True
            All 'correct' should show as None, as none have facsimile for metadata contact. '''
        for lid in _testvals('c'):
            try:
                meta = self.vdtr.metadata(lid)
                file = r'{}/testConfigAll.yaml'.format(os.getcwd())
                runChecks(meta, lid=lid, con=file)
            except MetadataNoneException as mne:
                self.assertIsInstance(mne, MetadataNoneException)
                continue
            self.assertFalse(True, 'Expected MetadataNoneException')

    def test_8_invalidConfig(self):
        '''test config with invalid config option '''
        for lid in _testvals('c'):
            try:
                meta = self.vdtr.metadata(lid)
                file = r'{}/testConfigInvalid.yaml'.format(os.getcwd())
                runChecks(meta, lid=lid, con=file)
            except InvalidConfigException as ie:
                self.assertIsInstance(ie, InvalidConfigException)
                continue
            self.assertFalse(True, 'Expected InvalidConfigException')

        
def _testvals(type='sf'):
    '''Returns a list of test ids'''
    ids = [] # type: List[Tuple]
    if 'c' in type: ids += [(i, 'correct') for i in ('52233','52141', '52154', '52166', '52167')]
    if 'i' in type: ids += [(i, 'incorrect') for i in ('51389', '51368','51306','50526', '50053')]
    if 'p' in type: ids += [(i, 'empty') for i in ('51920','50772', '50789', '53451', '53519',)]
    if 'n' in type: ids += [(i, 'none') for i in ('50842',)]
    
    return ids

def _scanxml(sample, snip=''):
    '''Look for XML snippet in sample'''
    if sample is not None:
        return True
    else:
        return snip in sample

if __name__ == "__main__":
    unittest.main()
