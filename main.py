#!/usr/bin/python


# Generic imports
from selenium.webdriver import Firefox
import unittest
import time
import sys

# myuw-specific imports
from myuwtesting.classes import myuwDate, errorCard, \
    LandingWaitTimedOut, perfCounter
from myuwtesting import expected
from myuwtesting.cards import cardDict
from myuwtesting.functions import isCardVisible, isVisibleFast, \
    getCardName, splitList, driverRetry
from myuwtesting.handler import mainMyuwHandler

from myuwtesting.tests import mainMyuwTestCase, autoDateMyuwTestCase, \
    jsonMyuwTestCase

from myuwtesting.tests import getTestDates

# This import is different depending on whether we're using this as a package
# or not.
try:
    from . import testconfig
except:
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
    if len(argv) >= 2:

        if argv[1] == '--help':
            # TODO
            print 'Placeholder help text'

        if argv[1] == '--single':
            # Parse arguments

            # No test user/dates specified
            if len(argv) == 2:
                print 'Please specify one or more test user:date pairs. '
                print 'Example: main.py --single javerage:2013-2-5'

            else:

                try:
                    pairs = argv[2:]
                    testDates = {}
                    for pair in pairs:
                        user, date = pair.split(':')
                        if user not in testDates:
                            testDates[user] = []
                        testDates[user].append(date)
                    users = testDates.keys()

                except:
                    
                    print 'Syntax error in --single arguments'
                    print 'Bad argument was "%s"' %pair

                else:

                    # Make test case with our specific dates and users
                    class singleTestCase(jsonMyuwTestCase):
                        '''Test class for --single mode'''
                        testDates = testDates
                        usersToTest = users

                    # Run the test with json output
                    unittest.TextTestRunner().run(singleTestCase('_test_json_out'))


        elif argv[1] == '--dump-dates':
            testUsers = getTestDates()
            for user, dates in testUsers.items():
                print 'Test dates for user %s:' % user
                print '    ' + ', '.join([str(date) for date in dates])


        elif argv[1] == '--debug':

            # Scratch area where you can put whatever debug code
            # Best used with python's -i option so you can poke around. 
            d = Firefox()
            d.maximize_window()
            m = mainMyuwHandler(d, testconfig.testUrl)

            m.setUser('seagrad')
            m.setDate('2013-3-27')
            try:
                m.browseLanding()
            except Exception as e:
                print e
            #el = d.find_element_by_id('SummerRegStatusCard1')
            #print el.is_displayed()
            #print repr(el.text)
            #time.sleep(4)
            a = m.cards
            #
            #e = myuwExpected.getExpectedResults('javerage', '2013-06-10')
            #diff = myuwExpected.findDiffs(a, e)
            #h = a['GradStatusCard']
            #e = h.originalElement

        elif len(argv) == 3 and argv[1] == '--user':

            user = argv[2]

            # Make test class for a specific user
            class userTest(autoDateMyuwTestCase):
                usersToTest = [user]

            unittest.TextTestRunner().run(userTest('test_runtests'))

    else:
        # Run default test case
        unittest.main(defaultTest = 'autoDateMyuwTestCase')
