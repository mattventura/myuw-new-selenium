#!/usr/bin/python

import time

from .cards import cardFromElement
from .functions import getCardName, isCardVisible, isVisibleFast
from .testconfig import perf
from .classes import myuwDate, hungCard
from .exceptions import LandingWaitTimedOut
from .perf import perfCounter


class mainMyuwHandler(object):
    '''Page object model handler for myuw. '''

    # Go to override page and set override username
    def _changeUser(self, username):
        '''Set override username. You probably want setUser instead. '''
        self.browseToPage(self.userUrl)
        # XXX
        time.sleep(.2)
        userBox = self.driver.find_element_by_xpath(
            '//input[@name="override_as"]')
        userBox.send_keys(username)
        userBox.submit()
        # XXX
        time.sleep(.2)
        self.currentUser = username

    # Go to override page and set override date
    def _changeDate(self, dateStr):
        '''Set override date. You probably want setDate instead. '''
        self.browseToPage(self.dateUrl)
        time.sleep(.2)
        dateBox = self.driver.find_element_by_xpath('//input[@name="date"]')
        dateBox.clear()
        dateBox.send_keys(dateStr)
        dateBox.submit()
        time.sleep(.2)
        self.currentDate = myuwDate(dateStr)

    # Set user if it is different from the current user
    def setUser(self, username):
        '''Set override username only if that isn't already our username. '''
        if username != self.currentUser:
            self._changeUser(username)

    # Set date if it is different from the current date
    def setDate(self, newDate):
        '''Set override date only if that isn't already our date. '''
        newDate = myuwDate(newDate)
        if self.currentDate != newDate:
            self._changeDate(newDate.getDateOverride())

        try:
            timeOverride = newDate.getTimeOverride()
            self._changeTime(timeOverride)
        except AttributeError:
            pass

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
    def __init__(self, driver, baseUrl, date=myuwDate('2013-04-15'),
                 user='javerage', userUrl=None, dateUrl=None):
        '''
        Constructor for mainMyuwHandler.
        baseUrl: root URL for the site.
        date, user: these indicate what the server will default to before we
        override.
        userUrl: user override page. Defaults to baseUrl + 'users/'.
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
        '''
        if perf:
            allParseTimer = perfCounter('Parsing all cards')
        '''
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
            # Email link
            '//div[@id="app_header"]//div[@id="uwemail"]'
        )

        self.driver.find_elements_by_css_selector('i.fa-spin')

        # Cards that didn't finish loading
        failedCards = []
        spinners = self.driver.find_elements_by_css_selector('i.fa-spin')

        spinners = filter(isVisibleFast, spinners)
        for el in spinners:
            cardName = None
            while cardName is None:
                el = el.find_element_by_xpath('..')
                cardName = getCardName(el)
            else:
                failedCards.append(el)

        # Using each search string above, find cards
        for xpath in cardxpaths:
            cardEls += self.driver.find_elements_by_xpath(xpath)

        # Iterate over each card element
        self._cards = {}
        st = time.time()
        for cardEl in cardEls:
            result = cardFromElement(cardEl, self.currentDate)
            self._cards.update(result)

        failedCards = filter(isVisibleFast, failedCards)
        for cardEl in failedCards:
            cardName = getCardName(cardEl)
            self._cards[cardName] = hungCard(cardName)

        # Mark the card list as being fresh
        self.cardsValid = True
        '''
        if perf:
            allParseTime = allParseTimer.endFmt()
            print allParseTime
        '''

    @property
    def cards(self):
        '''Get cards. Only parses if they haven't already been parsed. '''
        if not(self.cardsValid):
            self._parsePage()
        return self._cards

    def waitForLanding(self):
        '''
        Wait for landing to finish loading. If this times out, it will raise
        a LandingWaitTimedOut exception, which accepts a list of elements that
        did not finish loading. The presence of the loading gear is used to
        determine that an element has not finished loading. Waits 1 second
        after the last loading gear has disappeared.
        '''
        # I don't know if selenium's implicit wait can wait until
        # an element is *not* found, so do it manually
        maxTime = 10
        loadTimer = perfCounter('Page load')
        els = []
        while loadTimer.elapsedTime < maxTime:
            try:
                # Look for loading gears
                els = self.driver.find_elements_by_css_selector('i.fa-spin')
                # Filter these to only visible
                els = filter(isVisibleFast, els)
            except:
                # Ignore exceptions from the browser being in some weird state
                # while loading. If there's a legitimate issue, it will be
                # caught elsewhere.
                pass
            else:
                # If there were gears, wait some more.
                if els:
                    pass
                # If not, then the page finished loading
                else:
                    break
            time.sleep(.8)

        else:
            # If the loop ends due to running out of time, throw our
            # custom exception.
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
        '''
        if perf:
            print loadTimer.formatted
        '''

        # Sleep a little longer just in case we have a card that
        # hasn't quite finished but isn't displaying the loading
        # gear either.
        time.sleep(.5)
