#!/usr/bin/python


# Generic imports
from selenium.webdriver import Firefox
import unittest
import time
import sys

# myuw-specific imports
from myuwTesting.myuwClasses import myuwDate, errorCard, \
    LandingWaitTimedOut, perfCounter
from myuwTesting import myuwExpected
from myuwTesting.myuwCards import cardDict
from myuwTesting.myuwFunctions import isCardVisible, isVisibleFast, \
    getCardName, splitList, driverRetry
from myuwTesting.myuwHandler import mainMyuwHandler

from myuwTesting.myuwTests import mainMyuwTestCase, autoDateMyuwTestCase, \
    jsonMyuwTestCase

# This import is different depending on whether we're using this as a package
# or not. 
try:
    from .testconfig import *
    # We may need to write values here
    from . import testconfig
except:
    from testconfig import *
    import testconfig


class sampleMyuwTestCase(mainMyuwTestCase):
    '''Sample test case where you can specify what users/dates to test on. '''
    
    # Quick test with custom dates, mainly for testing the test itself
    testDates = {}
    #testDates['jinter'] = ('2013-02-09',)
    #testDates['javerage'] = ('2013-02-08',)
    testDates['javerage'] = ('2013-2-15', '2013-3-15', '2013-4-15')
    testDates['jinter'] = ('2013-02-15', '2013-01-09', '2013-05-12')
    testDates['seagrad'] = ('2013-1-15', )
    usersToTest = testDates.keys()


# Do nothing if loaded as a module rather than run as a script
if __name__ == '__main__':

    argv = sys.argv
    # --single option causes it to run individual test cases and report
    # them in json format rather than doing everything
    if len(argv) >= 3 and argv[1] == '--single':
        # Parse arguments
        pairs = argv[2:]
        testDates = {}
        for pair in pairs:
            user, date = pair.split(':')
            if user not in testDates:
                testDates[user] = []
            testDates[user].append(date)
        users = testDates.keys()
        # Disable parallelization
        testconfig.parallel = False

        class singleTestCase(jsonMyuwTestCase):
            '''Test class for --single mode'''
            testDates = testDates
            usersToTest = users

        # Run the test
        # This handles the output
        unittest.TextTestRunner().run(singleTestCase('_test_json_out'))
        
    elif len(argv) >= 2 and argv[1] == '--dump-dates':
        testUsers = getTestDates()
        for user, dates in testUsers.items():
            print 'Test dates for user %s:' %user
            print '    ' + ', '.join([str(date) for date in dates])
    elif len(argv) >= 2 and argv[1] == '--debug':

        # Scratch area where you can put whatever debug code
        d = Firefox()
        d.maximize_window()
        m = mainMyuwHandler(d, 'http://localhost:8081/')

        m.setUser('jbothell')
        m.setDate('2013-4-7')
        try:
            m.browseLanding()
        except Exception as e:
            print e
        el = d.find_element_by_id('SummerRegStatusCard1')
        print el.is_displayed()
        print repr(el.text)
        time.sleep(4)
        a = m.cards
        #
        #e = myuwExpected.getExpectedResults('javerage', '2013-06-10')
        #diff = myuwExpected.findDiffs(a, e)
        #h = a['GradStatusCard']
        #e = h.originalElement
    else:
        main = 'mainMyuwTestCase'
        sample = 'sampleMyuwTestCase'
        auto = 'autoDateMyuwTestCase'

        # This chooses what the default test case is
        unittest.main(defaultTest = auto)
