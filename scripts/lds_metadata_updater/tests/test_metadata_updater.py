
#!/usr/bin/python3

import unittest
import sys
import os
import shutil
import types
import logging
import argparse

sys.path.append('../')  
from metadata_updater import metadata_updater
from metadata_updater import log

# These tests make no API calls but rely on data in the
# /test/data dir

class TestMetadataUpdaterHasText(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestMetadataUpdaterHasText, self).__init__(*args, **kwargs)
        #could move the below to setup
        self.file = os.path.join(os.getcwd(), 'data/TEST_metadata_file.iso.xml')

    def test_file_has_text_true(self):
        """
        Test 'file_has_text' method finds text in file
        and returns True
        """
        
        search_text = 'Wellington'
        ignore_case = True
        result = metadata_updater.file_has_text(search_text, ignore_case, self.file)
        self.assertTrue(result)

    def test_file_has_text_false(self):
        """
        Test 'file_has_text' method returns False
        when search text not present in file
        """

        search_text = 'Gore'
        ignore_case = True
        result = metadata_updater.file_has_text(search_text, ignore_case, self.file)
        self.assertFalse(result)

    def test_file_has_text_false_case(self):
        """
        Test 'file_has_text' method returns False
        when case does not match
        """
        
        search_text = 'wellington'
        ignore_case = False
        result = metadata_updater.file_has_text(search_text, ignore_case, self.file)
        self.assertFalse(result)

class TestMetadataUpdaterRemoveIllChars(unittest.TestCase):

    def test_remove_illegal_chars_neg_remove_none(self):
        """
        Test 'remove_illegal_chars' does
        not modified text when not necessary
        """
        
        title = 'this is a test'
        result = metadata_updater.remove_illegal_chars(title)
        self.assertEqual(result, 'this is a test')
 
    def test_remove_illegal_chars_remove_all(self):
        """
        Test 'remove_illegal_chars' removes
        all illegal MS Windows OS chars
        """
        
        title = 't<h,i>s :is" /a\ t|e?s*t'
        result = metadata_updater.remove_illegal_chars(title)
        self.assertEqual(result, 'this is a test')

class TestMetadataUpdaterConfig(unittest.TestCase):

    def test_read_config(self):
        """
        Ensure all required properties are present in 
        config template
        """

        config_file = os.path.join(os.sep, os.getcwd(), '../metadata_updater/config_template.yaml')
        config = metadata_updater.ConfigReader(config_file)

        #self.assertEqual(config.api_key, '<ADMIN API KEY>') not tested in travis
        self.assertEqual(config.domain, '<Data Service Domain>')
        self.assertEqual(config.text_mapping, {1: {'search': 'the terrace', 
                                                      'replace': 'The Road', 
                                                      'ignore_case': True}, 
                                               2: {'search': 'Land Info New Zealand', 
                                                   'replace': 'Land Information Aoteroa',
                                                   'ignore_case': True}})
        self.assertEqual(config.destination_dir, '<Directory>')
        self.assertEqual(config.layers, '<Layers to Process>')
        self.assertEqual(config.test_dry_run, True)
        self.assertEqual(config.test_overwrite,True)

    def test_config_get_cwd(self):
        self.assertRaises(FileNotFoundError, metadata_updater.ConfigReader, None)


class TestMetadataUpdaterUpdFile(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestMetadataUpdaterUpdFile, self).__init__(*args, **kwargs)
        self.file =  os.path.join(os.getcwd(), 'data/TEST_metadata_file.iso.xml')

    def setUp(self):
        """
        Create backup of test metadata file. This
        will allow the original file to be reinstated
        after manipulation tests 
        """
        
        shutil.copyfile(self.file, self.file+'._bak')
    def tearDown(self):
        """
        Remove edited file and reinstate original via backup
        """
        os.remove(self.file)
        os.rename(self.file+'._bak', self.file)

    def test_update_metadata_edit(self):
        """
        1. Test the string "Kelp" is present in the metadata file
        2. Remove the string "Kelp"
        3. Ensure the string has been removed
        """

        # Ensure the word "Kelp" is present
        result = metadata_updater.file_has_text('kelp', True, self.file)
        self.assertTrue(result)
        # Remove the word "Kelp"
        mapping = {'replace': '', 'ignore_case': True, 'search': 'Kelp'}
        metadata_updater.update_metadata(self.file, mapping)
        # Ensure the word "Kelp" is not present
        result = metadata_updater.file_has_text('kelp', True, self.file)
        self.assertFalse(result)

    def test_update_metadata_edit_case_sens(self):
        """
        Test Case IGNORECASE
        1. Test the capitalised version of the string "Kelp" is present
        2. Test the all lower case version of the string "Kelp" is present
        3. Remove the string "Kelp" (capitalised version)
        4. Test the string "Kelp" (capitalised version) is not present
        5. Test the string "kelp" (all lower case version) is present
        """

        # Ensure the word "Kelp" is present
        result = metadata_updater.file_has_text('kelp', False, self.file)
        self.assertTrue(result)
        result = metadata_updater.file_has_text('Kelp', False, self.file)
        self.assertTrue(result)
        # Remove the word "Kelp" (capitalised)
        mapping = {'replace': '', 'ignore_case': False, 'search': 'Kelp'}
        metadata_updater.update_metadata(self.file, mapping)
        # Ensure the word "Kelp" is not present
        result = metadata_updater.file_has_text('kelp', False, self.file)
        self.assertTrue(result)
        result = metadata_updater.file_has_text('Kelp', False, self.file)
        self.assertFalse(result)

class TestMetadataUpdaterBakFile(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestMetadataUpdaterBakFile, self).__init__(*args, **kwargs)
        self.file = os.path.join(os.getcwd(), 'data/TEST_metadata_file.iso.xml')

    def tearDown(self):
        """
        At test completion, remove backup file
        """

        os.remove(self.file+'._bak')

    def test_create_backup(self):
        """
        Test the creation of the metadata backup file
        """
        metadata_updater.create_backup(self.file, True)
        self.assertTrue(os.path.isfile(self.file+'._bak'))

class TestMetadataUpdaterSelectiveLayers(unittest.TestCase):
    
    def test_iterate_selective_type(self):
        """
        Test method 'iterate_selective' return an 
        generator object
        """

        gen = metadata_updater.iterate_selective([123, 456, 789])
        self.assertIsInstance(gen, types.GeneratorType)

    def test_iterate_selective_values(self):
        """
        Test the iterate_selective generator 
        returns all expected values
        """

        gen = metadata_updater.iterate_selective([123, 456, 789])
        self.assertEqual(list(gen), [123, 456, 789])

class TestMetadataLog(unittest.TestCase):
    """
    Log Tests
    """
    
    def test_log(self):
        """
        test a logging instance is returned 
        """

        logger = log.conf_logging('root')
        self.assertIsInstance(logger, logging.Logger)

if __name__ == '__main__':
    unittest.main()
