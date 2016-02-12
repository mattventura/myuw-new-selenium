#!/usr/bin/python

import datetime
from functools import total_ordering
from UserDict import IterableUserDict
from abc import ABCMeta, abstractmethod
import time

from .myuwFunctions import toTimeDelta, packElement, formatDiffs, findDiffs, \
    getCardName, uesc, isCardVisible, isVisibleFast, getCardName

from .testconfig import perf


def toDate(obj):
    '''Convert string, timedelta, or myuw date to datetime.date'''
    # Convert string to myuwDate
    # basestring catches both str and unicode
    if isinstance(obj, basestring):
        obj = myuwDate(obj)

    # Convert myuwDate, including one made above, to datetime.date
    # by grabbing its dateObj attribute. 
    if isinstance(obj, myuwDate):
        obj = obj.dateObj

    return obj

class MyuwDateTypeError(TypeError):
    '''Pre-packaged exception for when an invalid date format is 
    specified when constructing a myuwDate. '''
    def __init__(self, args):
        args = repr(args)
        message = 'Arguments to myuwDate must be "yyyy-mm-dd" or yyyy, mm, dd, got %s instead' %args
        super(self.__class__, self).__init__(message)

@total_ordering
class myuwDate(object):
    '''Wrapper around datetime.date that allows easy converion
    to and from "yyyy-mm-dd" format for myuw. '''
    
    def __init__(self, *args):
        '''Arguments are accepted in various forms:
        myuwDate(yyyy, mm, dd)
        myuwDate('yyyy-mm-dd')
        myuwDate(datetime.date instance)
        myuwDate(myuwDate instance)
        '''
        if len(args) == 1:
            arg = args[0]
            # If it's already a myuwDate object, make a new one with the same values
            if isinstance(arg, self.__class__):
                newDate = (arg.year, arg.month, arg.day)
                self.__init__(*newDate)

            # If it's a datetime.date, use it directly
            elif isinstance(arg, datetime.date):
                self.dateObj = arg

            # Interpret yyyy-mm-dd string
            elif isinstance(arg, basestring):
                try:
                    dateParts = [int(s) for s in arg.split('-')]
                except:
                    raise MyuwDateTypeError(*args)

                if len(dateParts) != 3:
                    raise MyuwDateTypeError(*args)

                self.dateObj = datetime.date(*dateParts)

            else:
                raise MyuwDateTypeError(*args)

        # Arguments specified as y, m, d
        elif len(args) == 3:
            self.dateObj = datetime.date(*args)

        # Raise exception on everything else and report erroneous arguments used
        else: 
            raise MyuwDateTypeError(*args)

        # Date sanity check
        if self.year < 1900:
            raise ValueError(
                'Got %s for year. Did you mean %s?' %(self.year, self.year + 2000)
            )

    @property
    def year(self):
        return self.dateObj.year

    @property
    def shortYear(self):
        '''Returns year - 2000'''
        return self.dateObj.year - 2000

    @property
    def month(self):
        return self.dateObj.month

    @property
    def day(self):
        return self.dateObj.day

    # String representation, suitable for use in override page
    def __str__(self):
        return '%s-%s-%s' %(self.year, self.month, self.day)

    def __repr__(self):
        return 'myuwDate(%s, %s, %s)' %(self.year, self.month, self.day)

    def __add__(self, other):
        '''Construct a new myuwDate by taking out own date, converting
        'other' to a timedelta, and then adding them together. 
        For example, foo = bar + 3 will result in foo being exactly three
        days after bar. '''
        try:
            other = toTimeDelta(other)

        except TypeError: 
            return NotImplemented

        newDateObj = self.dateObj + other
        return myuwDate(newDateObj)

    def __sub__(self, other):
        '''__add__ but goes back in time rather than forwards. '''
        return self.__add__(-1 * other)

    def __eq__(self, other):
        '''Try to convert other to a datetime.date, then compare 
        our dateObj to other. '''
        try:
            other = toDate(other)
        except:
            return NotImplemented

        return self.dateObj == other

    # Define gt and let @total_ordering take care of the rest
    def __gt__(self, other):
        '''Same logic as __eq__ but checks if our date occurs after other. '''
        try:
            other = toDate(other)
        except:
            return NotImplemented

        return self.dateObj > other

class myuwDateRange(object):
    '''Date range class, consisting of a start date and end date. 
    Start and end arguments may be specified in any format that the
    myuwDate constructor will accept. 

    Supports 'in' operation, and has the significantDates property which
    defaults to startDate - 1, startDate, endDate - 1, and endDate. 

    Ending date is inclusive, i.e. the endDate is the last day which 
    should be considered part of the date range. 
    A dateRange consisting of one day only should have the start and 
    end date be the same. 
    '''
    
    def __init__(self, startDate, endDate):
        '''startDate and endDate must either be a myuwDate, or a format
        which the myuwDate constructor understands. '''

        self.startDate = myuwDate(startDate)
        self.endDate = myuwDate(endDate)

        if self.startDate > self.endDate:
            raise Exception('Start date %s comes after end date %s'
                %(self.startDate, self.endDate))

    # Get dates that should be tested based on this date range
    @property
    def significantDates(self):
        return (
            self.startDate - 1, 
            self.startDate, 
            self.endDate, 
            self.endDate + 1,
        )

    # Lets us use 'date in dateRange' syntax to check if 
    # a date is part of this date range
    # This is INCLUSIVE of the end date
    # So for a card that should appear for only one day, you
    # would specify an identical start and end date
    def __contains__(self, element):
        element = myuwDate(element)
        return self.startDate <= element <= self.endDate

    def __repr__(self):
        return 'myuwDateRange(%s, %s)' %(self.startDate, self.endDate)

    def __eq__(self, other):
        '''Equality check. Returns True if start and end are equal. '''
        return (self.startDate == other.startDate) and \
            (self.endDate == other.endDate)

    def __gt__(self, other):
        '''Greater-than check. Start and end must both be greater. '''
        return (self.startDate > other.startDate) and \
            (self.endDate > other.endDate)

    def __lt__(self, other):
        '''Less-than check. Start and end must both be lesser. '''
        return (self.startDate < other.startDate) and \
            (self.endDate < other.endDate)

    # @total_ordering doesn't quite work for this
    def __ge__(self, other):
        return self == other or self > other

    def __le__(self, other):
        return self == other or self < other

    def __ne__(self, other):
        return not(self == other)

class nullDateRange(myuwDateRange):
    '''Dummy date range for when there are no dates whatsoever. 
    Has no significant dates, and __contains__ is always false. '''
    def __init__(self):
        pass

    def significantDates(self):
        return []

    def __contains__(self, element):
        return False

class cardPair(object):
    '''Holds an expected card and an actual card and allows
    them to be easily compared. '''
    def __init__(self, expected, actual):
        # Ensure that the cards have the same name, and then 
        # set this object's name to that. 
        aNames = actual.allNames
        eNames = expected.allNames
        if actual.name in eNames or expected.name in aNames:
            # Use the expected card's name since it will be more generic, 
            # if different to begin with. 
            self.name = expected.name
            self.otherName = actual.name
            self.nameErr = None
        else:
            self.nameErr = 'Name mismatch between %s and %s' %(actual.name, expected.name)
        self.actual = actual
        self.expected = expected

    def __repr__(self):
        return 'cardPair(%s, %s)' %(actual, expected)

    __str__ = __repr__

    def findDiffs(self):
        '''Find and report the differences between expected and actual card. '''

        actualError = isinstance(self.actual, errorCard)
        expectedError = isinstance(self.expected, errorCard)
        if self.nameErr:
            return self.nameErr
        if actualError == expectedError:
            return self.expected.findDiffs(self.actual)
        else:
            if actualError:
                return 'Actual card had unexpected error'
            else:
                return 'Expected error card, didn\'t get one'

class multiDate(IterableUserDict):
    '''Wrapper to allow us to make an event which recurs on each quarter. 
    Used extensively in myuwDates, see there for examples. 
    Supports multiDate +/- int operation, so you can do things like
    FinalsBegin + 1 to mean the day after finals begin. 

    Supports all the operations a normal dictionary does. 
    '''

    def __init__(self, qtrsDict):
        qtrsDict = qtrsDict.copy()
        # Iterate through and turn everything into a myuwDate
        for qtr, date in qtrsDict.items():
            if not isinstance(date, myuwDate):
                qtrsDict[qtr] = myuwDate(date)
        # IterableUserDict uses the 'data' property to 
        # hold the real dict. 
        self.data = qtrsDict

    def __add__(self, other):
        newQtrs = {}
        for qtr, date in self.items():
            newQtrs[qtr] = date + other
        return self.__class__(newQtrs)

    def __sub__(self, other):
        return self.__add__(-1 * other)

    def __repr__(self):
        return 'multiDate(%s)' %IterableUserDict.__repr__(self)

    __str__ = __repr__

# Visibility check classes

# Most of them need to be called with arguments, but others are 
# singletons thus need to be used directly

class visClass(object):
    '''New visClass, intended to replace old vis functions with an actual 
    class so that significantDates can be rolled into this. 
    This class is not meant to be used directly, you should subclass it. 
    Subclasses should override visCheck and the significantDates property. 
    Supports +/-/* operations for quick union/intersect/difference ops. 
    '''
    def __call__(self, date):
        return self.shouldAppear(date)

    def shouldAppear(self, date):
        return self.visCheck(date)

    @property
    def significantDates(self):
        return self.sigDates

    def __add__(self, other):
        return visUnion(self, other)

    def __mul__(self, other):
        return visIntersect(self, other)

    def __sub__(self, other):
        return visSub(self, other)

class visException(visClass):
    '''Dummy class to cause an exception whenever any of the vis 
    methods are used. Used by the base cardProxy class to make sure
    its _vis property gets overridden in a subclass. '''

    def makeExc(self):
        raise Exception('_vis must be overridden in a subclass of myuwCard')

    def shouldAppear(self, date):
        self.makeExc()

    @property
    def significantDates(self):
        self.makeExc()

class visNever(visClass):
    visCheck = lambda self, date: False
    sigDates = []

class visAlways(visClass):
    visCheck = lambda self, date: True
    sigDates = []

# Turn these into singletons
visNever = visNever()
visAlways = visAlways()
visException = visException()

def dateArgs(c):
    '''Given a callable, convert string args to myuwDate'''
    def inner(*args):
        newArgs = []
        for arg in args:
            if isinstance(arg, basestring):
                newArgs.append(myuwDate(arg))
            else:
                newArgs.append(arg)
        return c(*newArgs)
    return inner

class visRanges(visClass):
    def __init__(self, dateRanges):
        self.dateRanges = dateRanges[:]
        self.sigDates = []
        for dateRange in self.dateRanges:
            self.sigDates += dateRange.significantDates
            
    def visCheck(self, date):
        for dateRange in self.dateRanges:
            if date in dateRange:
                return True
        return False

class visCDM(visRanges):
    '''Visibility function for multiple date ranges. 
    visRanges must be specified as a list of either myuwDateRange instances, 
    or tuples of (startDate, endDate). '''
    def __init__(self, dates):
        dateRanges = processDateRanges(dates)
        super(self.__class__, self).__init__(dateRanges)


def visCD(start, end):
    '''Visibility function creator for a single date range,
    specified as a start and end date. '''
    return visCDM([(start, end)])

def visAuto(starts, ends, exclude = []):
    '''Given a starting and ending multiDate object, return
    an appropriate visibility function that returns True when 
    the date is between a start date and its corresponding end
    date in the same quarter. '''
    return visCDM(getMultiDateRange(starts, ends, exclude))

class visBefore(visClass):
    @dateArgs
    def __init__(self, end):
        self.endDate = end
        self.sigDates = [self.endDate - 1, self.endDate]

    def visCheck(self, date):
        return self.endDate > date

            
class visAfter(visClass):
    @dateArgs
    def __init__(self, after):
        self.afterDate = after
        self.sigDates = [self.afterDate, self.afterDate + 1]

    def visCheck(self, date):
        return self.afterDate < date

class visUnion(visClass):
    '''Visibility union. Returns True if at least one
    child vis returns True. '''
    def __init__(self, *children):
        self.children = children
        self.sigDates = []
        for child in children:
            self.sigDates += child.sigDates

    def visCheck(self, date):
        for child in self.children:
            if child(date):
                return True
        return False
            
class visIntersect(visUnion):
    '''Visibility intersection. Returns True only if there is
    no child vis which returns False. '''
    def visCheck(self, date):
        for child in self.children:
            if not(child(date)):
                return False
        return True

class visSub(visClass):
    '''Visibility difference class that will return true if the date is
    in visA but not visB. '''
    def __init__(visA, visB):
        self.visA = visA
        self.visB = visB
        self.sigDates = visA.sigDates + visB.sigDates

    def visCheck(self, date):
        return self.visA and not(self.visB)
    
def visQtr(include = [], exclude = []):
    '''Function to filter by quarter (qtr switch, not start of instruction). 
    Does not give significant dates on its own, so it should generally be 
    combined with some other vis function using visUnion/Intersect/Sub. 
    Can specify a partial quarter name (e.g. 'SU' instead of 'SU13'. 
    Also works with summer terms (SA/SB). '''

    if include and exclude:
        raise Exception('visFilterQtr needs an include or exclude list, not both')

    elif exclude:
        return visQtrEx(exclude)

    else:
        '''If both are left blank, just assume a null visibility function.'''
        return visQtrIn(include)

class visQtrIn(visClass):
    '''Class for restricting visibility to particular quarters. '''
    def __init__(self, include):
        self.qtrs = include

    def visCheck(self, date):
        # Workaround for circular dependencies
        from myuwDates import dateToQtr, dateToTerm
        qtr = dateToQtr(date)
        term = dateToTerm(date)
        for inc in self.qtrs:
            if (qtr.startswith(inc) or term.startswith(inc)):
                return True
        return False

class visQtrEx(visQtrIn):
    '''Class for restricting visibility to everything but the 
    specified quarters. '''
    def visCheck(self, date):
        return not(super(self.__class__, self).visCheck(date))


class cardProxy(object):
    '''Proxy for attaching additional show/hide logic to a card, for 
    example if a user does not get a particular card in a certain 
    quarter, we can special case it for that user without needing
    to create a subclass of that card. 

    This class is not meant to be used directly. You should subclass
    this and define the _vis property. 
    '''

    def __init__(self, card):
        self.card = card

    def __getattr__(self, attr):
        if attr == 'shouldAppear':
            return self.shouldAppear
        elif attr == 'significantDates':
            return self.significantDates
        elif attr == 'card':
            return self.card
        else:
            return self.card.__getattribute__(attr)

    # Cause an exception if _vis isn't overridden. This should never
    # happen normally. 
    _vis = visException
    # Leave sigDates undefined
    #significantDates = []

    def shouldAppear(self, date):
        '''Logic for whether the card should appear is:
        1. If our own visibility function says it should not appear, 
            return False. 
        2. If the card says has a shouldAppear function, return 
            whatever that returns. 
        3. Otherwise, return True
        '''
        if self._vis(date):

            if hasattr(self.card, 'shouldAppear'):
                return self.card.shouldAppear(date)
            else:
                return True

        else:
            return False

    @property
    def significantDates(self):
        '''Get a list of significant dates for this card, by combining
        those of the card (if it exists) and our _vis. '''
        cardDates = self._vis.significantDates[:]
        try:
            cardDates += self.card.significantDates
        except:
            pass
        return cardDates
        
class cardCustom(cardProxy):
    '''Quick way of creating a custom cardproxy using a specific
    visibility function.'''
    def __init__(self, card, vis):
        super(self.__class__, self).__init__(card)
        self._vis = vis

def processDateRanges(dates):
    '''Turns (start, end) pairs into myuwDateRange objects'''
    dateRanges = []
    for datePair in dates:
        if not(isinstance(datePair, myuwDateRange)):
            datePair = myuwDateRange(*datePair)
        dateRanges.append(datePair)
    return dateRanges

# Turns "smart" date ranges (e.g. QtrStart + 1 to FinalsBegin - 5)
# into a list of date ranges
def getMultiDateRange(starts, ends, exclude = []):
    '''Given two multiDate objects, turn them into a series of date
    ranges. For example, getMultiDateRange(FirstDayQtr, RedPd1) would
    give you a series of date ranges, each spanning from the first
    of the quarter to reg period 1 for its respective quarter. 
    
    Supports an optional exclude argument, which should contain a list
    of strings to use to filter out certain quarters, e.g.:
    exclude = ['SU', 'SP13'] would filter out dates in spring 2013 as
    well as any summer quarter. '''
    dateRanges = []
    for qtr, sd in starts.items():
        skip = False
        if exclude:
            for ex in exclude:
                if qtr.startswith(ex):
                    skip = True
        if qtr not in ends:
            skip = True
        if skip: 
            continue
        ed = ends[qtr]
        dateRange = myuwDateRange(sd, ed)
        dateRanges.append(dateRange)
    return dateRanges

def cardAlways(card):
    '''Card proxy to signify that the card should always appear. 
    Obsolete, since this is the behavior you would get if you just specified 
    the card directly. '''
    return cardCustom(card, visAlways)

def cardNever(card):
    '''Card proxy to signify that the card should never appear. 
    Not strictly necessary, since removing the card from expected data would 
    do the same. '''
    return cardCustom(card, visNever)

def cardCDM(card, dates):
    '''Card proxy generated from a list of date ranges. 
    See visCDM for allowable formats. '''
    return cardCustom(card, visCDM(dates))

def cardCD(card, dateRange):
    '''Card proxy for just a single date range. Date range can be specified
    as either a myuwDateRange instance, or a (start, end) tuple. '''
    # If argument is specified as a tuple, convert to myuwDate
    if isinstance(dateRange, tuple):
        dateRange = myuwDateRange(dateRange[0], dateRange[1])
    return cardCustom(card, visRanges([dateRange]))

# Lets you use multiDate (or even a plain old dict) for start and end
def cardAuto(card, startDates, endDates):
    '''Card proxy with automatically generated dates based on start
    and end dates specified as multiDate instances. 
    Example: cardCustom(HFSCard(), QtrStart + 2, LastDayInstr - 1)'''
    return cardCustom(card, visAuto(startDates, endDates))

def cardQtr(card, include = [], exclude = []):
    return cardCustom(card, visQtr(include, exclude))


class autoDiff(object):
    '''Mixin that provides a findDiffs method which uses the autoDiffs 
    property of the object. '''
    def findDiffs(self, other):
        # This is the findDiffs as defined in myuwFunctions
        return findDiffs(self, other)

# Generic card class
class myuwCard(autoDiff):
    '''Base class for every card. 

    Actual card classes should subclass this, and override:
    name (@isaCard will do this for you)
    altNames (if it has any)
    either visCheck if show/hide logic is only date dependent, 
        or shouldAppear if it is more complicated. 
    fromElement (must be a class method)
    __init__
    significantDates

    '''
    # Lets things that aren't actually cards (like cardProxies) be 
    # considered real subclasses of myuwCard. Easier than duck typing. 
    __metaclass__ = ABCMeta

    # Subclasses should define the class method fromElement, which should
    # return an instance of the class constructed by selenium element cardEl
    # on date 'date'. 
    @classmethod
    def fromElement(cls, date, cardEl):
        # Just return as basic an instance as possible by default
        return cls()

    # Subclasses can use autoDiffs if they wish to have their diffs done 
    # automatically. If they don't want this behavior, they should override
    # findDiffs. 
    autoDiffs = {}

    # findDiffs should do one of three things:
    # 1. Do nothing, if the card has nothing variable
    # 2. Use autoDiffs to do the checking
    # 3. Be overridden in a subclass

    def __eq__(self, other):
        return not(self.findDiffs(other))
    
    # The 'name' property is combined with altNames
    # to get a list of card IDs that this card class
    # should cover. 
    altNames = []

    # This method is used to retrive the list of acceptable
    # ids for a card when the class itself is being reference. 
    @classmethod
    def getAllNames(cls):
        return [cls.name] + cls.altNames[:]

    # As above but works only on instances
    # Can be overridden on an instance level if such behavior is desired
    @property
    def allNames(self):
        return [self.name] + self.altNames[:]

    # Method that should return a boolean based on whether the card should 
    # appear on the given date. By default, it uses self.visCheck after
    # unbinding it if applicable.  
    def shouldAppear(self, date):
        if hasattr(self, 'visCheck'):
            # If we got a bound version, we want it unbound
            try:
                vf = self.visCheck.__func__
            except:
                vf = self.visCheck
            return vf(date)
        else:
            return True

    # Significant dates
    @property
    def significantDates(self):
        return self.visCheck.significantDates

    visCheck = visAlways

class errorCard(myuwCard):

    @classmethod
    @packElement
    def fromElement(cls, date, cardEl):
        cardText = cardEl.text
        assert 'An error has occurred' in cardText
        cardName = cardEl.get_attribute('id')
        newObj = cls.__init__(cardName)
        return newObj

    def __init__(self, name):
        self.name = name
        self.__name__ = name + '_error'

    # This is checked elsewhere, so it shouldn't ever fail
    # here. 
    def findDiffs(self, other):
        if isinstance(other, errorCard):
            return ''
        else:
            return 'Error card vs non-error card'

# Make a cardproxy be considered a myuwCard subclass for the purposes of
# issubclass() and isinstance()
myuwCard.register(cardProxy)

class LandingWaitTimedOut(Exception):
    def __init__(self, els):
        cardNames = []
        for el in els:
            cardName = getCardName(el)
            cardNames.append(cardName)
        self.cardsNotLoaded = cardNames
        super(self.__class__, self).__init__(
            'Waited too long for landing page to finish loading. The following cards did\
            not load: %s' %(', '.join(cardNames))
        )

# Class for measuring how long certain things take
class perfCounter(object):
    def __init__(self, label = None):
        self.startTime = time.time()
        self.finished = False
        self.label = label

    def end(self):
        self.endTime = time.time()
        self.finished = True

    @property
    def elapsedTime(self):
        if self.finished:
            return self.endTime - self.startTime
        else:
            return time.time() - self.startTime

    @property
    def formatted(self):
        if self.label:
            return '%s took %s seconds' %(self.label, self.elapsedTime)
        else: 
            return str(self.elapsedTime)

    def endGetTime(self):
        self.end()
        return self.elapsedTime
    
    def endFmt(self):
        self.end()
        return self.formatted

class gradRequest(autoDiff):

    @uesc
    def __init__(self, name, statuses, visCheck = visAlways, title = None):
        self.name = name
        self.statuses = statuses
        self.visCheck = visCheck
        self.title = title
        if hasattr(self, 'statusFix'):
            self.statusFix()

    def shouldAppear(self, date):
        return self.visCheck(date)

    def __str__(self):
        return self.__class__.__name__ + ': ' + self.name

    def __repr__(self):
        return '<%s "%s": %s>' %(self.__class__.__name__, self.name, self.statuses)

    @classmethod
    def fromElement(cls, reqEl):
        reqName = reqEl.find_element_by_xpath('./h5').text
        try:
            title = reqEl.find_element_by_css_selector('div.degree-title').text
        except:
            title = None
        decisionEls = reqEl.find_elements_by_xpath('./ul/li')
        if decisionEls:
            pass
        else:
            # For ones with just a 'Status' decision, we can use the original element
            # to find the appropriate children. 
            decisionEls = [reqEl]
        decisions = {}
        for decEl in decisionEls:
            key = decEl.find_element_by_css_selector('span.card-badge-label').text
            value = decEl.find_element_by_css_selector('span.card-badge-value').text

            if key in cls.replacements:
                key = cls.replacements[key]
            if value in cls.replacements:
                value = cls.replacements[value]

            decisions[key] = value

        req = cls(reqName, decisions, title = title)
        return req

    replacements = {}

    autoDiffs = {
        'name': 'Request name',
        'statuses': 'Request statuses',
        'title': 'Request title',
    }

    def __eq__(self, other):
        result = self.findDiffs(other)
        return not(self.findDiffs(other))

    @property
    def significantDates(self):
        return self.visCheck.significantDates
        
        
class simpleStatus:
    '''Mixin for grad requests that only have a 'Status' property.''' 
    def statusFix(self):
        if isinstance(self.statuses, str):
            self.statuses = {'Status': self.statuses}

    def __repr__(self):
        className = self.__class__.__name__
        return '<%s "%s": %s>' %(className, self.name, self.statuses['Status'])
            

class petRequest(gradRequest):
    # TODO: make overrides for these for easier date behavior
    replacements = {
        'Graduate School Decision': 'grad',
        'Department Recommendation': 'dept'
    }

class leaveRequest(simpleStatus, gradRequest):
    pass

class degreeRequest(simpleStatus, gradRequest):
    pass

class link(autoDiff):
    '''Class for a link. Stores the link text, URL, and whether
    it should open in a new tab/window. '''
    @uesc
    def __init__(self, label, url, newTab = False):
        self.label = label
        self.url = url
        self.newTab = newTab

    @classmethod
    def fromElement(cls, e):
        label = e.text
        url = e.get_attribute('href')
        try:
            newTab = (e.get_attribute('target') == '_blank')
        except:
            newTab = False

        return cls(label, url, newTab)

    def __repr__(self):
        return 'link(%s, %s, %s)' %(self.label, self.url, self.newTab)

    autoDiffs = {
        'label': 'Link Label',
        'url': 'Link URL',
        'newTab': 'Link opens in new tab',
    }

    def __eq__(self, other):
        return (self.label == other.label and self.url == other.url \
            and self.newTab == other.newTab)

class thriveContent(autoDiff):
    '''Class for an individual thrive card. 
    A thrive card has a title, description, an optional Try This
    section, and one or more links. '''
    @uesc
    def __init__(self, title, desc = '', tryThis = '', links = []):
        self.title = title
        self.desc = desc
        self.tryThis = tryThis
        self.links = links

    autoDiffs = {
        'title': 'Thrive card title',
        # TODO: these can be re-enabled once we get the rest of 
        # the thrive mock data in
        #'desc': 'Thrive card first section',
        #'tryThis': 'Thrive card "Try This" section',
        #'links': 'Thrive card links'
    }

# Cards that didn't finish loading
class hungCardClass(myuwCard):
    pass

@uesc
def hungCard(name):
    return type('hungcard_%s' %name, (hungCardClass, ), {'name': name})()
