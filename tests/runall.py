'''
v.0.0.9

anzlic-validator

Copyright 2011 Crown copyright (c)
Land Information New Zealand and the New Zealand Government.
All rights reserved

This program is released under the terms of the new BSD license. See the 
LICENSE file for more information.

Test Suite runner

Created on 24/07/2012

@author: jramsay
'''
import unittest

from test_validate import Test_1_setup as T21
from test_cache import Test_1_setup as T11
from test_cache import Test_2_canned as T12


class FullSuite(unittest.TestSuite):

    def __init__(self):
        pass
    
    def _suite(self):
        '''Finer control of which tests to run'''
        suite = unittest.TestSuite()

        suite.addTest(T1('test_1_flushcache'))
        suite.addTest(T1('test_2_loadexternal'))
        suite.addTest(T1('test_3_loadcache'))        
        
        suite.addTest(T2('test_1_flushcache'))
        suite.addTest(T2('test_2_loadexternal'))
        suite.addTest(T2('test_3_loadcache'))
        
        return suite
    
    def suite(self):
        suites = ()
        suites += unittest.makeSuite(T11)
        suites += unittest.makeSuite(T12)
        suites += unittest.makeSuite(T21)
   
        return unittest.TestSuite(suites)

    
def main():
    
    if True:
        suite = FullSuite().suite()  
    else:
        suite  = unittest.TestSuite()
    
    runner = unittest.TextTestRunner()
    runner.run(suite)
    
if __name__ == "__main__":
    main()

    