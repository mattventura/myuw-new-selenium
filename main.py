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
from myuwFunctions import isCardVisible, isVisibleFast, getCardName

# Some settings
# Enable this to do some performance profiling
perf = False
debug = False
parallel = 3

class mainMyuwTestCase(unittest.TestCase):
    
    driverFunc = Firefox
    baseUrl = 'http://localhost:8081'
    usersToTest = ['javerage', 'jinter']
    defaultUser = 'javerage'
    defaultDate = myuwDate(2013, 04, 15)
    testDates = {}

    def setUp(self):
        self.driver = self.driverFunc()
        self.driver.maximize_window()
        self.pageHandler = mainMyuwHandler(self.driver, self.baseUrl, 
            self.defaultDate, self.defaultUser)
        # Not sure if these are necessary
        self.currentUser = self.defaultUser
        self.currentDate = self.defaultDate
        self.diffs = {}


    def tearDown(self):
        self.driver.close()

    # Run tests and report discrepancies between expected and actual results
    def test_runtests(self):
        # Parallel test currently just spawns 1 process for each user to test
        if parallel:
            # List for holding diffs
            # These will each be a string of json
            diffList = []
            # List for holding each Popen object
            processes = []
            for user, dates in self.testDates.items():
                
                # Turn dates from myuwDate objects to strings
                datesStr = [str(date) for date in dates]
                # Use this file's name as the script to run
                mainFile = __file__
                # Run it
                process = subprocess.Popen(
                    ['python', mainFile, '--single', user] + datesStr, 
                    stdout = subprocess.PIPE, 
                    stderr = subprocess.PIPE
                )
                processes.append(process)

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
                            # There has to be a better way to do this
                            for line in errLines:
                                if len(line) == 0:
                                    continue
                                if line[0] in ('.', 'E', 'F'): 
                                    continue
                                if line[0:4] == '----':
                                    continue
                                if line[0:3] == 'Ran':
                                    continue
                                if line[0:6] == 'FAILED':
                                    continue
                                if line[0:2] == 'OK':
                                    continue
                                print 'Line: <start>%s<end>' %line
                                errs += line + '\n'

                            # If there is something left, report it
                            if errs:
                                print 'Got errors:\n%s' %stderr

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
            # If there are differences, fail the test
            if diffStr:
                self.fail(diffStr)



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
        out = {}
        for dic in diffDicts:
            
            for user, dateDict in dic.items():
                if user not in out:
                    out[user] = {}

                for date, diffs in dateDict.items():
                    out[user][date] = diffs

        return out


    # TODO
    def _test_json_out(self):
        # TODO
        self.runAllUsers()
        diffs = self.getJsonDiffs()
        if diffs:
            print diffs

    # RunTests is where code specific to a test style should go
    def runAllUsers(self):
        for user in self.usersToTest:
            self.runTestsForUser(user)

    # Run tests for a user
    def runTestsForUser(self, user):
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

    # Browse landing
    def browseLanding(self):
        self.pageHandler.browseLanding()

    # Change user if necessary
    def setUser(self, user):
        self.currentUser = user
        self.pageHandler.setUser(user)

    # Change date if necessary
    def setDate(self, date):
        self.currentDate = date
        self.pageHandler.setDate(date)

    # Report differences
    def logDiffs(self, user, date, diffs):
        if diffs:
            # Might get more than one at a time, separated
            # by linefeeds. 
            for diff in diffs.split('\n'):
                if diff:
                    # Make sure user exists in diffs dictionary
                    if user not in self.diffs:
                        self.diffs[user] = {}
                    userDiffs = self.diffs[user]
                    # Make sure date exists in user's dictionary
                    if date not in userDiffs:
                        userDiffs[date] = []
                    dateDiffs = userDiffs[date]

                    # Add diff
                    dateDiffs.append(diff)


    # Returns formatted version of the diff dictionary
    def getFormattedDiffs(self):
        return self.formatDiffsFull(self.diffs)


    @staticmethod 
    def formatDiffsFull(diffs, indentChar = '  '):
        diffStr = ''
        for user, dates in diffs.items():
            diffStr += 'Failures for user %s:\n' %user
            for date, diffs in dates.items():
                diffStr += indentChar + 'On date %s:\n' %date

                for diff in diffs:
                    diffStr += indentChar * 2 + '%s\n' %diff
        return diffStr
        

    def getJsonDiffs(self):
        diffDict = self.diffs
        if diffDict:
            return json.dumps(diffDict)
        else:
            return None
                
                
    # Log diff for the current user and date
    def logDiffCurrent(self, diff):
        self.logDiffs(self.currentUser, self.currentDate, diff)
        

    # Check diffs and log any that were found
    def checkDiffs(self):
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
    
    # Quick test with custom dates, mainly for testing the test itself
    testDates = {}
    #testDates['jinter'] = ('2013-02-09',)
    #testDates['javerage'] = ('2013-02-08',)
    testDates['javerage'] = ('2013-2-15', '2013-3-15', '2013-4-15')
    testDates['jinter'] = ('2013-02-15', '2013-01-09', '2013-05-12')
    usersToTest = testDates.keys()


class autoDateMyuwTestCase(mainMyuwTestCase):

    @property
    def testDates(self):
        userList = myuwExpected.cardList.keys()
        tcDict = {}
        for user in userList:
            sd = myuwExpected.getSigDates(user, '2013-1-1', '2013-06-18')
            tcDict[user] = sd
        return tcDict

class mainMyuwHandler(object):
    
    # Go to override page and set override username
    def changeUser(self, username):
        self.browseToPage(self.userUrl)
        time.sleep(.5)
        userBox = self.driver.find_element_by_xpath('//input[@name="override_as"]')
        userBox.send_keys(username)
        userBox.submit()
        time.sleep(1)
        self.currentUser = username

    # Go to override page and set override date
    def changeDate(self, dateStr):
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
        if username != self.currentUser:
            self.changeUser(username)

    # Set date if it is different from the current date
    def setDate(self, newDate):
        newDate = myuwDate(newDate)
        if self.currentDate != newDate:
            self.changeDate(str(newDate))

    # Go to landing page
    def browseLanding(self):
        self.browseToPage(self.landingUrl)
        self.waitForLanding()

    # Browse to a particular page, relative
    # to the root of the site
    # i.e. browseToPage('foo') -> my.uw.edu/foo
    def browseToPage(self, url):
        self.cardsValid = False
        self.driver.get(url)

    # Constructor
    # Minimally needs a driver and a base url
    # (adds the trailing / if not given)
    # Can also take a user and date to override assumed
    # javerage/2013-04-15
    def __init__(self, driver, baseUrl, date = myuwDate('2013-04-15'), user = 'javerage',
        userUrl = None, dateUrl = None):

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
            # Main landing content
            '//div[@id="landing_content_cards"]/div',
            # Right column
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
        if not(self.cardsValid):
            self._parsePage()
        return self._cards

    def waitForLanding(self):
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

            

if debug:
    d = Firefox()
    d.maximize_window()
    m = mainMyuwHandler(d, 'http://localhost:8081/')

    m.setDate('2013-02-15')
    m.browseLanding()
    time.sleep(4)
    a = m.cards
    #
    #e = myuwExpected.getExpectedResults('javerage', '2013-06-10')
    #diff = myuwExpected.findDiffs(a, e)
    h = a['GradStatusCard']
    #e = h.originalElement

else:

    if __name__ == '__main__':

        argv = sys.argv
        if len(argv) >= 4 and argv[1] == '--single':
            user = argv[2]
            dates = argv[3:]

            class singleTestCase(mainMyuwTestCase):
                
                testDates = {user: dates}
                usersToTest = [user]

                
            unittest.TextTestRunner().run(singleTestCase('_test_json_out'))
            

        else:

            #del mainMyuwTestCase
            #del sampleMyuwTestCase
            #del autoDateMyuwTestCase
            main = 'mainMyuwTestCase'
            sample = 'sampleMyuwTestCase'
            auto = autoDateMyuwTestCase


            unittest.main(defaultTest = sample)

