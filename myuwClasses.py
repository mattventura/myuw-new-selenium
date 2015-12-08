#!/usr/bin/python

import datetime
from functools import total_ordering
from UserDict import IterableUserDict
from abc import ABCMeta
import time

from myuwFunctions import toTimeDelta, packElement, formatDiffs

# Convert string, timedelta, or myuw date to datetime.date
def toDate(obj):
    if isinstance(obj, str):
        obj = myuwDate(other)

    elif isinstance(obj, myuwDate):
        obj = obj.dateObj

    return obj


# Wrapper around datetime.date that allows easy converion
# to and from "yyyy-mm-dd" format for myuw. 
@total_ordering
class myuwDate(object):
    
    def __init__(self, *args):
        if len(args) == 1:
            arg = args[0]
            if isinstance(arg, self.__class__):
                newDate = (arg.year, arg.month, arg.day)
                return self.__init__(*newDate)

            elif isinstance(arg, datetime.date):
                self.dateObj = arg

            elif isinstance(arg, str):
                try:
                    # TODO: use standard time (un)formatting functions instead 
                    # of splitting it
                    dateParts = [int(s) for s in arg.split('-')]
                    self.dateObj = datetime.date(*dateParts)
                except:
                    raise self.MyuwDateTypeError()

            else:
                raise self.MyuwDateTypeError()

        # Arguments specified as y, m, d
        elif len(args) == 3:
            self.dateObj = datetime.date(*args)

        else: 
            raise self.MyuwDateTypeError()

    class MyuwDateTypeError(TypeError):
        def __init__(self):
            message = 'Arguments to mywDate must be "yyyy-mm-dd" or yyyy, mm, dd'
            super(self.__class__, self).__init__(message)

    @property
    def year(self):
        return self.dateObj.year

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

    # Add
    # Accepts either an int representing days or a timedelta
    def __add__(self, other):
        try:
            other = toTimeDelta(other)

        except TypeError: 
            return NotImplemented

        newDateObj = self.dateObj + other
        return myuwDate(newDateObj)


    # Subtraction
    def __sub__(self, other):
        return self.__add__(-1 * other)

    # Equality check
    def __eq__(self, other):
        try:
            other = toDate(other)
        except:
            return NotImplemented

        return self.dateObj == other

    def __gt__(self, other):
        try:
            other = toDate(other)
        except:
            return NotImplemented

        return self.dateObj > other
            
            

# Class for a date range
class myuwDateRange(object):
    
    # Takes a startDate and an endDate, which can be specified
    # in any format that the myuwDate constructor will accept. 
    
    def __init__(self, startDate, endDate):

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
            self.endDate - 1, 
            self.endDate
        )

    # Lets us use 'date in dateRange' syntax to check if 
    # a date is part of this date range
    # This is INCLUSIVE of the end date
    # So for a card that should appear for only one day, you
    # would specify an identical start and end date
    def __contains__(self, element):
        element = myuwDate(element)
        return self.startDate <= element <= self.endDate

# Dummy date range for when there are no dates whatsoever
class nullDateRange(myuwDateRange):
    def __init__(self):
        pass

    def significantDates(self):
        return ()

    def __contains__(self, element):
        return False



# Class to hold an actual and expected card to be compared. 
class cardPair(object):
    def __init__(self, actual, expected):
        # Ensure that the cards have the same name, and then 
        # set this object's name to that. 
        aNames = actual.allNames
        eNames = expected.allNames
        if actual.name in eNames or expected.name in aNames:
            # Use the expected card's name since it will be more generic, 
            # if different to begin with. 
            self.name = expected.name
            self.otherName = actual.name
        else:
            errStr = 'Name mismatch between %s and %s' %(actual.name, expected.name)
            raise AssertionError(errStr)
        self.actual = actual
        self.expected = expected

    def __repr__(self):
        return 'cardPair(%s, %s)' %(actual, expected)

    __str__ = __repr__

    # Find and report the differences between the two cards
    def findDiffs(self):

        actualError = isinstance(self.actual, errorCard)
        expectedError = isinstance(self.expected, errorCard)
        if actualError == expectedError:
            return self.actual.findDiffs(self.expected)
        else:
            if actualError:
                return 'Actual card had unexpected error'
            else:
                return 'Expected error card, didn\'t get one'

# Object to allow us to pack multiple dates into one friendly name
# and do operations on it,
# so that we can say something like 'ClassesStart + 1' and it will
# generate a list of dates that satisfy that. 
# Works like a plain old dictionary
class multiDate(IterableUserDict):
    
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

# Class to combine a card with a function to determine whether 
# or not it should show up for that user. 
# Allows the card itself to be unhinged from show/hide logic, 
# which may be different for different users. 
# Subclasses may populate the list of significant dates which 
# will be used by some test styles to automatically figure out 
# dates to test. 
class cardProxy(object):

    def __init__(self, card):
        self.card = card

    def __getattr__(self, attr):
        if attr == 'shouldAppear':
            return self.shouldAppear
        elif attr == 'card':
            return self.card
        else:
            return self.card.__getattribute__(attr)


    significantDates = []

    def shouldAppear(self, date):
        # If we say the card shouldn't appear, it shouldn't. 
        if hasattr(self, '_vis'):
            return self._vis(date)
        # If the card says it shouldn't appear, it shouldn't. 
        if hasattr(self.card, 'shouldAppear'):
            return self.card.shouldAppear(date)
        else:
            return True

    @property
    def significantDates(self):
        if hasattr(self.card, 'significantDates'):
            cardDates = self.card.significantDates
        else:
            cardDates = []
        cardDates = cardDates + self._significantDates
        return cardDates
        
        
    def _significantDates(self):
        return []
    

# Process date ranges
# Turns (start, end) pairs into myuwDateRange objects
def processDateRanges(dates):
    dateRanges = []
    for datePair in dates:
        if not(isinstance(datePair, myuwDateRange)):
            datePair = myuwDateRange(*datePair)
        dateRanges.append(datePair)
    return dateRanges

# Turns "smart" date ranges (e.g. QtrStart + 1 to FinalsBegin - 5)
# into a list of date ranges
def getMultiDateRange(starts, ends):
    dateRanges = []
    for qtr, sd in starts.items():
        if qtr not in ends:
            continue
        ed = ends[qtr]
        dateRange = myuwDateRange(sd, ed)
        dateRanges.append(dateRange)
    return dateRanges

# Visibility check functions

# visAlways and visNever should just be used as-is, whereas
# the others should be called with arguments. 
def visAlways(date):
    return True

def visNever(date):
    return False

def visCDM(dates):
    dateRanges = processDateRanges(dates)
        
    def visInner(date):
        for dateRange in dateRanges:
            if date in dateRange:
                return True
        return False
    return visInner

def visCD(start, end):
    return visCDM([(start, end)])

def visAuto(starts, ends):
    return visCDM(getMultiDateRange(starts, ends))
        
# Card that should always appear
class cardAlways(cardProxy):
    def _shouldAppear(self, date):
        return True

# Card that should never appear
class cardNever(cardProxy):
    def _shouldAppear(self, date):
        return False

# Card that appears conditionally based on date
# cardCDM takes a list of date ranges. 
# If you just want one, see cardCD below. 
class cardCDM(cardProxy):
    def __init__(self, card, dates):
        self._vis = visCDM(dates)
        self.card = card
        self.dateRanges = processDateRanges(dates)

    # Get dates that should be tested for this card. 
    # Currently, it is:
    # - Day before card is visible
    # - First day card is visible
    # - Day before card disappears
    # - First day the card is not visible
    @property
    def _significantDates(self):
        out = []
        for datePair in self.dateRanges:
            out.append(datePair.startDate - 1)
            out.append(datePair.startDate)
            out.append(datePair.endDate)
            out.append(datePair.endDate + 1)
        return out

# Like cardCDM, but just one single date range
# Helps avoid parenthesis overload when defining expected dates for cards
class cardCD(cardCDM):
    def __init__(self, card, dateRange):
        self.card = card
        self.dateRanges = [myuwDateRange(*dateRange)]
        self._vis = visCD(*dateRange)

# Lets you use multiDate (or even a plain old dict) for start and end
class cardAuto(cardCDM):
    def __init__(self, card, startDates, endDates):
        dateRanges = []
        for qtr, sd in startDates.items():
            # Make sure the quarter is defined in both dictionaries
            if qtr not in endDates:
                continue
            ed = endDates[qtr]
            dateRange = myuwDateRange(sd, ed)
            dateRanges.append(dateRange)

        super(self.__class__, self).__init__(card, dateRanges)


# Generic card class
class myuwCard(object):
    __metaclass__ = ABCMeta
    # Placeholder values to help identify cases where the 
    # required info was not given

    # Create a new object of the specified type from
    # a selenium element. 
    # For cards that have variable content, this behavior 
    # needs to be overridden in each card. 
    @classmethod
    def fromElement(cls, date, cardEl):
        return cls()

    autoDiffs = {}

    # findDiffs should do one of three things:
    # 1. Do nothing, if the card has nothing variable
    # 2. Use autoDiffs to do the checking
    # 3. Be overridden in a subclass
    def findDiffs(self, other):
        if self.autoDiffs:
            diffs = ''
            for prop, label in self.autoDiffs.items():
                valueSelf = getattr(self, prop)
                valueOther = getattr(other, prop)
                diffs += formatDiffs(label, valueSelf, valueOther)
            return diffs
        else: 
            return ''

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
    @property
    def allNames(self):
        return [self.name] + self.altNames[:]

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

class errorCard(myuwCard):

    @classmethod
    @packElement
    def fromElement(cls, date, cardEl):
        # TODO: verify it is an error
        cardName = cardEl.get_attribute('id')
        newObj = cls.__init__(cardName)
        return newObj

        #TODO


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
    def __init__(self):
        return super(self.__class__, self).__init__(
            'Waited too long for landing page to finish loading'
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
        
        

