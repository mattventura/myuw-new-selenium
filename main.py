#!/usr/bin/python


from selenium.webdriver import Firefox
from myuwClasses import myuwDate
import myuwExpected
from myuwCards import cardDict
import unittest
import time
from myuwFunctions import isCardVisible

# TODO
def waitForLanding():
    # I don't know if selenium's implicit wait can wait until
    # an element is *not* found, so do it manually
    # TODO: make it use an actual time
    maxTime = 15
    startTime = time.time()
    endTime = startTime + maxTime
    while time.time < endTime:


        time.sleep(6)
    # i.fa-spin

class mainMyuwTestCase(unittest.TestCase):
    
    driverFunc = Firefox
    baseUrl = 'http://localhost:8081'
    usersToTest = ['javerage']
    defaultUser = 'javerage'
    defaultDate = myuwDate(2013, 04, 15)
    testDates = {}
    diffs = ''

    def setUp(self):
        self.driver = self.driverFunc()
        self.driver.maximize_window()
        self.pageHandler = mainMyuwHandler(self.driver, self.baseUrl, 
            self.defaultDate, self.defaultUser)
        # Not sure if these are necessary
        self.currentUser = self.defaultUser
        self.currentDate = self.defaultDate


    def tearDown(self):
        self.driver.close()

    # Run tests and report discrepancies between expected and actual results
    def test_runtests(self):
        self.runAllUsers()
        if self.diffs:
            errString  = 'Found differences between actual and expected data:\n'
            errString += self.diffs
            self.fail(errString)

    # RunTests is where code specific to a test style should go
    def runAllUsers(self):
        for user in self.usersToTest:
            self.runTestsForUser(user)

    # Run tests for a user
    def runTestsForUser(self, user):
        dates = self.testDates[user]
        self.setUser(user)
        for date in dates:
            print 'date is %s' %date
            self.setDate(date)
            self.browseLanding()
            self.checkDiffs()

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
    def logDiffs(self, diff):
        errString  = 'On date %s:\n' %self.currentDate
        errString += diff
        self.diffs += errString

    def checkDiffs(self):
        actualCards = self.pageHandler.cards
        expectedCards = myuwExpected.getExpectedResults(self.currentUser, self.currentDate)
        self.logDiffs(myuwExpected.findDiffs(actualCards, expectedCards))


class sampleMyuwTestCase(mainMyuwTestCase):
    
    testusers = ['javerage']
    testDates = {'javerage': ('2013-02-15',)}


class autoDateMyuwTestCase(mainMyuwTestCase):

    @property
    def testDates(self):
        userList = myuwExpected.cardList.keys()
        tcDict = {}
        for user in userList:
            tcDict[user] = myuwExpected.getSignificantDates(user)
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
        waitForLanding()

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
        # Main column cards
        cardsA = self.driver.find_elements_by_xpath('//div[@id="landing_content_cards"]/div')
        # Secondary desktop column cards
        cardsB = self.driver.find_elements_by_xpath('//div[@id="landing_accounts_cards"]/div')
        # All cards
        cardElements = cardsA + cardsB
        # Assemble a dictionary from this list of cards
        self._cards = {}
        for cardEl in cardElements:
            # If the card is not visible, then don't do anything with it
            if not(isCardVisible(cardEl)):
                continue
            # Cards are identified by their id
            cardName = cardEl.get_attribute('id')
            try:
                # Try to find class for the given card name
                cardClass = cardDict[cardName]
            except KeyError as e:
                # KeyError implies the card was not in the list card classes
                #raise Exception('Card %s not in list of known cards' %cardName)
                print 'WARNING: Card %s unknown. Please write at least a stub class for it. ' %cardName
            else:
                newCard = cardClass.fromElement(self.currentDate, cardEl)
                self._cards[cardName] = newCard
            #    raise e

        # Mark the card list as being fresh
        self.cardsValid = True

        # Do other stuff too, like directory info, email link

    @property
    def cards(self):
        if not(self.cardsValid):
            self._parsePage()
        return self._cards

    #TODO: allow you to just do 'pageHandler.cards' and parse if necessary

    
'''
d = Firefox()
d.maximize_window()
m = mainMyuwHandler(d, 'http://localhost:8081/')
    
m.browseLanding()
time.sleep(4)
a = m.cards
e = myuwExpected.getExpectedResults('javerage', '2013-04-15')
diff = myuwExpected.findDiffs(a, e)
h = a['FutureQuarterCardA']
e = h.originalElement
'''


if __name__ == '__main__':
    del mainMyuwTestCase
    del sampleMyuwTestCase
    #del autoDateMyuwTestCase
    unittest.main()
