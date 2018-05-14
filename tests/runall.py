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

from test_cache     import Test_1_setup         as T11
from test_cache     import Test_2_canned        as T12
from test_validate  import Test_1_init          as T21
from test_validate  import Test_2_setuplocal    as T22
from test_validate  import Test_3_setupremote   as T23
from test_validate  import Test_4_setupcombined as T24
#from test_resolve   import Test_1_init          as T31


class FullSuite(unittest.TestSuite):

    def __init__(self):
        pass
    
    
    def suite(self):
        suites = ()
        suites += unittest.makeSuite(T11)
        suites += unittest.makeSuite(T12)
        
        suites += unittest.makeSuite(T21)
        suites += unittest.makeSuite(T22)
        suites += unittest.makeSuite(T23)
        suites += unittest.makeSuite(T24)
        
        #suites += unittest.makeSuite(T31)
   
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

    