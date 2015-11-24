#!/usr/bin/python


from selenium.webdriver import Firefox
from myuwClasses import myuwDate
import myuwExpected
from myuwCards import cardDict
import unittest
import time
from myuwFunctions import isCardVisible


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
            #print 'date is %s' %date
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
        if diff:
            errString  = 'On date %s:\n' %self.currentDate
            errString += diff
            self.diffs += errString

    def checkDiffs(self):
        actualCards = self.pageHandler.cards
        expectedCards = myuwExpected.getExpectedResults(self.currentUser, self.currentDate)
        self.logDiffs(myuwExpected.findDiffs(actualCards, expectedCards))


class sampleMyuwTestCase(mainMyuwTestCase):
    
    testusers = ['javerage']
    testDates = {'javerage': ('2013-02-15','2013-04-15', '2013-03-15', '2013-05-15')}


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
        cardEls = []
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

        for xpath in cardxpaths:
            cardEls += self.driver.find_elements_by_xpath(xpath)
        self._cards = {}
        for cardEl in cardEls:
            # If the card is not visible, then don't do anything with it
            if not(isCardVisible(cardEl)):
                continue
            # Cards are identified by their id
            cardId = cardEl.get_attribute('id')
            cardDataName = cardEl.get_attribute('data-name')
            cardName = cardId or cardDataName

            try:
                # Try to find class for the given card name
                cardClass = cardDict[cardName]
            except KeyError as e:
                # KeyError implies the card was not in the list card classes
                #raise Exception('Card %s not in list of known cards' %cardName)
                print 'WARNING: Card %s unknown. Please write at least a stub class for it. ' %cardName
            else:
                newCard = cardClass.fromElement(self.currentDate, cardEl)
                # For cards with multiple names, take the name from the class
                baseCardName = newCard.name
                self._cards[baseCardName] = newCard
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
# TODO
    def waitForLanding(self):
        # I don't know if selenium's implicit wait can wait until
        # an element is *not* found, so do it manually
        # TODO: make it use an actual time
        maxTime = 10
        startTime = time.time()
        endTime = startTime + maxTime
        while time.time() < endTime:
            try:
                time.sleep(.2)
                # Look for loading gears
                els = self.driver.find_elements_by_css_selector('i.fa-spin')
                # Filter these to only visible
                els = [el for el in els if el.is_displayed()]
            except:
                # Ignore exceptions arising from, for example, 
                # the browser being in a weird state. If it's a
                # real problem, something else will throw an exception
                # anyway. 
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
            raise Exception('Waited too long for landing page to finish loading.') 

        # If the loop ended due to there being no more loading gears, do this. 
        #print 'Page load finish took %s seconds' %(time.time() - startTime)

        # Sleep a little longer just in case we have a card that
        # hasn't quite finished but isn't displaying the loading 
        # gear either. 
        time.sleep(1)

            


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