#!/usr/bin/python

import unittest
import time
import os
import json
import subprocess
from selenium.webdriver import Firefox

from .myuwClasses import myuwDate, perfCounter, LandingWaitTimedOut
from .myuwFunctions import splitList, driverRetry
from . import myuwExpected
from .testconfig import parallel, perf, defaultStartDate, defaultEndDate
from . import testconfig
from myuwTesting.myuwHandler import mainMyuwHandler

def getTestDates(start = defaultStartDate, end = defaultEndDate):
    '''Get test dates based off expected cards and known dates. '''
    userList = myuwExpected.cardList.keys()
    tcDict = {}
    for user in userList:
        sd = myuwExpected.getSigDates(user, start, end, True)
        tcDict[user] = sd
    return tcDict

class mainMyuwTestCase(unittest.TestCase):
    '''Main myuw test case. Others should subclass this and override testDates
    and usersToTest. '''
    driverFunc = Firefox
    baseUrl = 'http://localhost:8081'
    # By default, don't test anything. Real test cases should subclass
    # this class and define these two variables. 
    # usersToTest: List of usernames in string format
    usersToTest = []
    # testDates: Dictionary of usernames as strings -> list or tuple of 
    # dates as strings. 
    testDates = {}

    # These should be set to the values that myuw will default to
    # with no override. 
    defaultUser = 'javerage'
    defaultDate = myuwDate(2013, 04, 15)

    def setUp(self):
        self.parallel = self.checkPara()
        if not(self.parallel):
            self.driverSetup()
        self.diffs = {}
        self.errors = []

    def checkPara(self):
        return testconfig.parallel

    def driverSetup(self):
        self.driver = driverRetry(self.driverFunc)
        self.driver.maximize_window()
        self.pageHandler = mainMyuwHandler(self.driver, self.baseUrl,
            self.defaultDate, self.defaultUser)

        self.currentUser = self.defaultUser
        self.currentDate = self.defaultDate


    def tearDown(self):
        if not(self.parallel):
            self.driverTeardown()

    def driverTeardown(self):
        self.driver.close()

    # Run tests and report discrepancies between expected and actual results
    def test_runtests(self):
        '''Run all tests as defined in testDates and usersToTest.
        Will parallelize on a per-user basis if the parallel option
        is set. usersToTest should be a list of usernames to test with,
        while testDates should be a dictionary mapping usernames to a list
        of dates which they should be tested on. '''
        # Parallel test spawns 'parallelDateSplit' number of processes per user
        # to test. 
        if self.parallel:
            # List for holding diffs. These will each be a string of json.
            diffList = []
            # List for holding each Popen instance.
            processes = []
            # User-date pairs
            udpairs = []
            for user, dates in self.testDates.items():
                if not(dates):
                    continue
                for date in dates:
                    pair = '%s:%s' %(user, date)
                    udpairs.append(pair)

            datesplits = splitList(udpairs, testconfig.parallelNum)

            for datepairs in datesplits:
                mainFile = 'main.py'

                process = subprocess.Popen(
                    ['python', mainFile, '--single'] + datepairs,
                    stdout = subprocess.PIPE,
                    stderr = subprocess.PIPE,
                    # Reduce priority of child process (doesn't work on Windows)
                    preexec_fn = lambda: os.nice(15),
                )
                processes.append(process)

                # Stagger processes to even out load and reduce bottlenecks
                time.sleep(testconfig.parallelDelay)

            # Wait for every process to finish
            finished = False
            while not(finished):
                time.sleep(2)

                # Set finished to True, but if any process is not finished
                # then set it back to false
                finished = True
                for proc in processes:
                    # Returns None if process is not finished, otherwise
                    # gives the exit code 
                    if proc.poll() is None:
                        finished = False

                # Grab output from each process
                # The unittest stuff as well as any errors will go to stderr,
                # while the actual output will
                # go to stdout which we read from here
                for proc in processes:
                    try:
                        (stdout, stderr) = proc.communicate()
                        if stderr:
                            errs = ''
                            errLines = stderr.split('\n')
                            # Filter out anything that isn't an error
                            # There has to be a better way to do this, but right now
                            # it's more important to make sure errors will be seen
                            # if they exist. 
                            for line in errLines:
                                if len(line) == 0:
                                    continue
                                if line == 'E':
                                    continue
                                if line[0] in ('.', 'F'): 
                                    continue
                                if line[0:4] == '----':
                                    continue
                                if line[0:3] in ('Ran', 'Run'):
                                    continue
                                if line[0:6] == 'FAILED':
                                    continue
                                if line[0:2] == 'OK':
                                    continue
                                #print 'Line: <start>%s<end>' %line
                                errs += line + '\n'

                            # If there is something left, report it
                            if errs:
                                #print 'Got errors:\n%s' %stderr
                                self.errors.append(errs)

                        if stdout:
                            diffList.append(stdout)

                    # If the process's output has already hit EOF, then don't worry
                    # about it. This just means we already got the data from that
                    # particular process. 
                    except ValueError:
                        pass

            diffDicts = []
            # For each json diff, convert it to a real dictionary
            for diffJson in diffList:
                diffDict = json.loads(diffJson)
                diffDicts.append(diffDict)

            # Combine dictionaries into one, like what we would get from the 
            # non-parallelized version
            fullDiffs = self.mergeDiffs(diffDicts)
            # Format them like how they would normally be formatted
            diffStr = self.formatDiffsFull(fullDiffs)
            if self.errors:
                errStr = 'Got errors from children: \n'
                for err in self.errors:
                    errStr += err
            else:
                errStr = ''
            # If there are differences, fail the test
            if diffStr or errStr:
                allStr = diffStr + '\n' + errStr
                self.fail(allStr)


        # Old, non-parallel test
        else:
            self.runAllUsers()
            diffs = self.getFormattedDiffs()
            if diffs:
                errString  = 'Found differences between actual and expected data:\n'
                errString += diffs
                self.fail(errString)

    @staticmethod
    def mergeDiffs(diffDicts):
        '''Merge multiple dicts of differences together. '''
        out = {}
        for dic in diffDicts:

            sortedUsers = sorted(dic.items())
            for user, dateDict in sortedUsers:
                if user not in out:
                    out[user] = {}

                sortedDates = sorted(dateDict.items())
                for date, diffs in sortedDates:
                    out[user][date] = diffs

        return out

    # RunTests is where code specific to a test style should go
    def runAllUsers(self):
        '''Run tests for all users in usersToTest'''
        for user in self.usersToTest:
            self.runTestsForUser(user)

    # Run tests for a user
    def runTestsForUser(self, user):
        '''Run tests for a specific user'''
        dates = self.testDates[user]
        self.setUser(user)
        for date in dates:
            self.setDate(date)
            try:
                self.browseLanding()
            except LandingWaitTimedOut as e:
                cardsNotLoaded = ', '.join(e.cardsNotLoaded)
                self.logDiffCurrent(
                    'Some cards did not finish loading: %s\n' %cardsNotLoaded
                )

                
            self.checkDiffs()

    def browseLanding(self):
        '''Browse the landing page'''
        self.pageHandler.browseLanding()

    # Change user if necessary
    def setUser(self, user):
        '''Set the username. Since this uses setUser, it will do
        nothing if we already have the right username. '''
        self.currentUser = user
        self.pageHandler.setUser(user)

    # Change date if necessary
    def setDate(self, date):
        '''Set the date. Since this uses setDate, it will do
        nothing if the date is already correct. '''
        self.currentDate = date
        self.pageHandler.setDate(date)

    # Report differences
    def logDiffs(self, user, date, diffs):
        '''Given a username, date, and string of differences, put these
        differences in the appropriate location in the diffs dictionary,
        with each line being considered a different diff. '''
        if diffs:
            # Might get more than one at a time, separated
            # by linefeeds. 
            for diff in diffs.split('\n'):
                # Ignore empty lines
                if diff:
                    # Make sure user exists in diffs dictionary, else create
                    if user not in self.diffs:
                        self.diffs[user] = {}
                    userDiffs = self.diffs[user]
                    # Make sure date exists in user's dictionary
                    if date not in userDiffs:
                        userDiffs[date] = []
                    dateDiffs = userDiffs[date]

                    # Add diff
                    dateDiffs.append(diff)

    def getFormattedDiffs(self):
        '''Returns formatted version of the diff dictionary. '''
        return self.formatDiffsFull(self.diffs)

    @staticmethod 
    def formatDiffsFull(diffs, indentChar = '  '):
        '''Given a diff dictionary, format them with indentChar used to 
        indicate nesting. '''
        diffStr = ''
        # Use myuwDate to sort the dates, since a string won't necessarily
        # do that (e.g. "2013-12-20" < "2013-6-20")
        dateSortKey = lambda date: myuwDate(date)
        for user, dates in sorted(diffs.items()):
            diffStr += 'Failures for user %s:\n' %user

            for date in sorted(dates.keys(), key = dateSortKey):
                diffs = dates[date]
                diffStr += indentChar + 'On date %s:\n' %date

                for diff in diffs:
                    diffStr += indentChar * 2 + '%s\n' %diff
        return diffStr
        
                
    # Log diff for the current user and date
    def logDiffCurrent(self, diff):
        '''Given a diff, get the current user and date, and use logDiffs
        to report it. '''
        self.logDiffs(self.currentUser, self.currentDate, diff)
        

    # Check diffs and log any that were found
    def checkDiffs(self):
        '''Check diffs for the page as it currently stands. '''
        actualCards = self.pageHandler.cards
        expectedCards = myuwExpected.getExpectedResults(self.currentUser, self.currentDate)
        if perf:
            diffTimer = perfCounter('Diff checking')
        diffs = myuwExpected.findDiffs(expectedCards, actualCards)
        if perf:
            diffTime = diffTimer.endFmt()
            print diffTime
        self.logDiffCurrent(diffs)

class jsonMyuwTestCase(mainMyuwTestCase):
    def getJsonDiffs(self):
        '''Dump raw diff dictionary as json. Return None if there are no diffs. '''
        diffDict = self.diffs
        if diffDict:
            return json.dumps(diffDict)
        else:
            return None

    def _test_json_out(self):
        '''Run tests, but report results in json.'''
        self.runAllUsers()
        diffs = self.getJsonDiffs()
        if diffs:
            print diffs

    def checkPara(self):
        return False

class autoDateMyuwTestCase(mainMyuwTestCase):
    '''Test case which automatically finds test users and dates. '''

    startDate = defaultStartDate
    endDate = defaultEndDate

    @property
    def testDates(self):
        return getTestDates(self.startDate, self.endDate)


