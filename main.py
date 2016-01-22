#!/usr/bin/python


# Generic imports
from selenium.webdriver import Firefox
import unittest
import time
import sys
import os
import json
import subprocess

# myuw-specific imports
from myuwClasses import myuwDate, errorCard, LandingWaitTimedOut, perfCounter
import myuwExpected
from myuwCards import cardDict
from myuwFunctions import isCardVisible, isVisibleFast, getCardName, splitList, \
    driverRetry

# Some settings
# Enable this to do some performance profiling
perf = False
debug = False
# Run each user in parallel
parallel = True
# Split up tests for each user into separate parallel processes
parallelDateSplit = 4
# Number of concurrent tests running at any given time will be at most
# the number of users to test times parallelDateSplit

# Delay between starting processes for parallel mode
parallelDelay = 4

# For auto date tests, restrict dates to this range
defaultStartDate = '2013-1-1'
#startDate = '2013-6-1'
defaultEndDate = '2013-12-17'
#endDate = '2013-7-25'

def getTestDates(start = defaultStartDate, end = defaultEndDate):
    userList = myuwExpected.cardList.keys()
    tcDict = {}
    for user in userList:
        sd = myuwExpected.getSigDates(user, start, end)
        tcDict[user] = sd
    return tcDict
    

class mainMyuwTestCase(unittest.TestCase):
    '''Main myuw test case. Others should subclass this and override testDates
    and usersToTest. '''
    driverFunc = Firefox
    baseUrl = 'http://localhost:8081'
    # This won't do anything, just there as a default in case
    usersToTest = ['javerage', 'jinter']

    # These should be set to the values that myuw will default to
    # with no override. 
    defaultUser = 'javerage'
    defaultDate = myuwDate(2013, 04, 15)
    testDates = {}

    def setUp(self):
        if not(parallel):
            self.driverSetup()
        self.diffs = {}
        self.errors = []

    def driverSetup(self):
        self.driver = driverRetry(self.driverFunc)
        self.driver.maximize_window()
        self.pageHandler = mainMyuwHandler(self.driver, self.baseUrl,
            self.defaultDate, self.defaultUser)
        # Not sure if these are necessary
        self.currentUser = self.defaultUser
        self.currentDate = self.defaultDate


    def tearDown(self):
        if not(parallel):
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
        # Parallel test currently just spawns 1 process for each user to test
        if parallel:
            # List for holding diffs
            # These will each be a string of json
            diffList = []
            # List for holding each Popen object
            processes = []
            for user, dates in self.testDates.items():
                # If there are no dates to test, skip this user
                if not(dates):
                    continue
                dateLists = splitList(dates, parallelDateSplit)
                # splitList() correctly handles the situation where we have
                # more splits than actual dates, so we don't have to handle the
                # blank list case here
                for dates in dateLists:
                    # Turn dates from myuwDate objects to strings
                    datesStr = [str(date) for date in dates]
                    # Use this file's name as the script to run
                    mainFile = __file__
                    # Run it
                    process = subprocess.Popen(
                        ['python', mainFile, '--single', user] + datesStr,
                        stdout = subprocess.PIPE,
                        stderr = subprocess.PIPE,
                        # Reduce priority of child process (doesn't work on Windows)
                        preexec_fn = lambda: os.nice(15),
                    )
                    processes.append(process)

                    # Stagger processes to even out load and reduce
                    # bottlenecking. 
                    time.sleep(parallelDelay)

            finished = False
            # Wait for every process to finish
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

    # TODO
    def _test_json_out(self):
        '''Run tests, but report results in json.'''
        # TODO
        self.runAllUsers()
        diffs = self.getJsonDiffs()
        if diffs:
            print diffs

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
            # TODO: make browseLanding throw a specific exception when it times
            # out so it can be differentiated from an actual failure. 
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
        
    def getJsonDiffs(self):
        '''Dump raw diff dictionary as json. Return None if there are no diffs. '''
        diffDict = self.diffs
        if diffDict:
            return json.dumps(diffDict)
        else:
            return None
                
                
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

class autoDateMyuwTestCase(mainMyuwTestCase):
    '''Test case which automatically finds test users and dates. '''

    startDate = defaultStartDate
    endDate = defaultEndDate

    @property
    def testDates(self):
        return getTestDates(self.startDate, self.endDate)

class mainMyuwHandler(object):
    '''Page object model handler for myuw. '''
    
    # Go to override page and set override username
    def changeUser(self, username):
        '''Set override username. You probably want setUser instead. '''
        self.browseToPage(self.userUrl)
        time.sleep(.5)
        userBox = self.driver.find_element_by_xpath('//input[@name="override_as"]')
        userBox.send_keys(username)
        userBox.submit()
        time.sleep(1)
        self.currentUser = username

    # Go to override page and set override date
    def changeDate(self, dateStr):
        '''Set override date. You probably want setDate instead. '''
        self.browseToPage(self.dateUrl)
        time.sleep(.5)
        dateBox = self.driver.find_element_by_xpath('//input[@name="date"]')
        dateBox.clear()
        dateBox.send_keys(dateStr)
        dateBox.submit()
        time.sleep(1)
        self.currentDate = myuwDate(dateStr)

    # Set user if it is different from the current user
    def setUser(self, username):
        '''Set override username only if that isn't already our username. '''
        if username != self.currentUser:
            self.changeUser(username)

    # Set date if it is different from the current date
    def setDate(self, newDate):
        '''Set override date only if that isn't already our date. '''
        newDate = myuwDate(newDate)
        if self.currentDate != newDate:
            self.changeDate(str(newDate))

    # Go to landing page
    def browseLanding(self):
        '''Browse back to the landing page. '''
        self.browseToPage(self.landingUrl)
        self.waitForLanding()

    def browseToPage(self, url):
        '''Browse to a specific URL, and indicate that cards will need
        to be re-parsed. '''
        self.cardsValid = False
        self.driver.get(url)

    # Constructor
    # Minimally needs a driver and a base url
    # (adds the trailing / if not given)
    # Can also take a user and date to override assumed
    # javerage/2013-04-15
    def __init__(self, driver, baseUrl, date = myuwDate('2013-04-15'), user = 'javerage',
        userUrl = None, dateUrl = None):
        '''Constructor for mainMyuwHandler. 
        baseUrl: root URL for the site. 
        date, user: these indicate what the server will default to before we override. 
        userUrl: override the user override page. Defaults to baseUrl + 'users/'. 
        dateUrl: Same for date page. Defaults to baseUrl + 'admin/dates'. 
        '''

        self.cardsValid = False
        if baseUrl[-1] != '/':
            baseUrl += '/'
        self.baseUrl = baseUrl
        self.landingUrl = baseUrl
        self.userUrl = userUrl or baseUrl + 'users/'
        self.dateUrl = dateUrl or baseUrl + 'admin/dates'
        self.driver = driver
        self.currentUser = user
        self.currentDate = date

    def _parsePage(self):
        '''Internal function for parsing cards. '''
        # If requested, set up timing
        if perf: 
            allParseTimer = perfCounter('Parsing all cards')
        cardEls = []
        # Various search strings to use for finding cards
        cardxpaths = (
            # Notices
            '//div[@id="notice_banner_location"]/div',
            # Calendar on mobile
            '//div[@id="calendar_banner_location_mobile"]/div',
            # Calendar on desktop
            '//div[@id="calendar_banner_location_desktop"]/div', 
            # PCE message
            '//div[@id="pce_banner_location"]/div',
            # Left column on desktop layout, only column on mobile
            '//div[@id="landing_content_cards"]/div',
            # Right column on desktop layout
            '//div[@id="landing_accounts_cards"]/div',
        )

        # Using each search string above, find cards
        for xpath in cardxpaths:
            cardEls += self.driver.find_elements_by_xpath(xpath)

        # Iterate over each card element
        self._cards = {}
        for cardEl in cardEls:
            if perf: 
                cardTimer = perfCounter('Parsing card')
            # Get name of card using whatever's available
            cardName = getCardName(cardEl)
            # If the card is not visible, then don't do anything with it
            if isCardVisible(cardEl):
                # Cards are identified by their id

                cardIsError = 'An error has occurred' in cardEl.text
                    
                # If the card errors out, use myuwClasses.errorCard and provide
                # the name. This allows us to give an error card as the expected
                # result. 
                if cardIsError:
                    newCard = errorCard(cardName)
                    self._cards[cardName] = newCard

                else:
                    try:
                        # Try to find class for the given card name
                        cardClass = cardDict[cardName]
                    except KeyError as e:
                        # KeyError implies the card was not in the list card classes
                        # This doesn't fail the test as it might just be a new card. 
                        print 'WARNING: Card %s unknown. Please write at least a stub class for it. ' %cardName
                    else:
                        newCard = cardClass.fromElement(self.currentDate, cardEl)
                        # For cards with multiple names, take the name from the class
                        if newCard is None:
                            raise Exception('Tried to make %s from element, but it returned none' %cardClass)
                        baseCardName = newCard.name
                        self._cards[baseCardName] = newCard
            else:
                # Card is hidden
                if perf:
                    cardTimer.label = 'Parsing hidden card'
                continue

            if perf:
                parseTime = cardTimer.endFmt()
                print parseTime
            #    raise e


        # Mark the card list as being fresh
        self.cardsValid = True
        if perf:
            allParseTime = allParseTimer.endFmt()
            print allParseTime

        # Do other stuff too, like directory info, email link

    @property
    def cards(self):
        '''Get cards. Only parses if they haven't already been parsed. '''
        if not(self.cardsValid):
            self._parsePage()
        return self._cards

    def waitForLanding(self):
        '''Wait for landing to finish loading. If this times out, it will raise
        a LandingWaitTimedOut exception, which accepts a list of elements that did
        not finish loading. The presence of the loading gear is used to determine
        that an element has not finished loading. Waits 1 second after the last 
        loading gear has disappeared. 
        '''
        # I don't know if selenium's implicit wait can wait until
        # an element is *not* found, so do it manually
        maxTime = 10
        loadTimer = perfCounter('Page load')
        els = []
        while loadTimer.elapsedTime < maxTime:
            try:
                time.sleep(.2)
                # Look for loading gears
                els = self.driver.find_elements_by_css_selector('i.fa-spin')
                # Filter these to only visible
                els = filter(isVisibleFast, els)
                #els = [el for el in els if el.is_displayed()]
            except:
                # Ignore exceptions from the browser being in some weird
                # state while loading. If there's a legitimate exception, 
                # it will be caught elsewhere. 
                pass
            else:
                # If there were gears, wait some more. 
                if els:
                    pass
                # If there were no loading gears found, consider
                # the page to have finished loading. 
                else:
                    break
        else:
            # If the loop ends due to running out of time, throw 
            # this exception. 
            els = filter(isVisibleFast, els)
            newEls = []
            for el in els:
                cardName = None
                while cardName is None:
                    el = el.find_element_by_xpath('..')
                    cardName = getCardName(el)
                else:
                    newEls.append(el)
            raise LandingWaitTimedOut(newEls)

        # If the loop ended due to there being no more loading gears, 
        # it will hit this code instead. 

        loadTimer.end()
        if perf:
            print loadTimer.formatted

        # Sleep a little longer just in case we have a card that
        # hasn't quite finished but isn't displaying the loading 
        # gear either. 
        time.sleep(1)

            

# debug option will just load the page rather than actually running any tests
if debug:
    d = Firefox()
    d.maximize_window()
    m = mainMyuwHandler(d, 'http://localhost:8081/')

    m.setUser('jinter')
    m.setDate('2013-05-29')
    m.browseLanding()
    time.sleep(4)
    a = m.cards
    #
    #e = myuwExpected.getExpectedResults('javerage', '2013-06-10')
    #diff = myuwExpected.findDiffs(a, e)
    h = a['GradStatusCard']
    #e = h.originalElement

else:

    # Do nothing if loaded as a module rather than run as a script
    if __name__ == '__main__':

        argv = sys.argv
        # --single option causes it to run individual test cases and report
        # them in json format rather than doing everything
        if len(argv) >= 4 and argv[1] == '--single':
            # Parse arguments
            user = argv[2]
            dates = argv[3:]
            # Disable parallelization
            parallel = False

            class singleTestCase(mainMyuwTestCase):
                '''Test class for --single mode'''
                testDates = {user: dates}
                usersToTest = [user]

            # Run the test
            # This handles the output
            unittest.TextTestRunner().run(singleTestCase('_test_json_out'))
            
        elif len(argv) >= 2 and argv[1] == '--dump-dates':
            testUsers = getTestDates()
            for user, dates in testUsers.items():
                print 'Test dates for user %s:' %user
                print '    ' + ', '.join([str(date) for date in dates])

        else:
            #del mainMyuwTestCase
            #del sampleMyuwTestCase
            #del autoDateMyuwTestCase
            main = 'mainMyuwTestCase'
            sample = 'sampleMyuwTestCase'
            auto = 'autoDateMyuwTestCase'

            # This chooses what the default test case is
            unittest.main(defaultTest = auto)
