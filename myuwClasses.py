#!/usr/bin/python

import datetime
from functools import total_ordering
from UserDict import IterableUserDict

# Functions
# Convert int to timedelta, if necessary
def toTimeDelta(obj):
    if isinstance(obj, int):
        obj = datetime.timedelta(obj)
        
    if isinstance(obj, datetime.timedelta):
        return obj

    else:
        raise TypeError('toTimeDelta requires either an int or datetime.timedelta as its argument')

# Convert string, timedelta, or myuw date to datetime.date
def toDate(obj):
    if isinstance(obj, str):
        obj = myuwDate(other)

    if isinstance(obj, myuwDate):
        obj = obj.dateObj

    return obj

# Object for a date, takes either a string or y,m,d as individual arguments
@total_ordering
class myuwDate(object):
    
    def __init__(self, *args):
        # Arguments specified as a string of the form yyyy-mm-dd
        # TODO: use standard time (un)formatting functions instead of splitting it
        if len(args) == 1:
            arg = args[0]
            if isinstance(arg, self.__class__):
                # Might be dangerous if arg.dateObj is modified later
                self.dateObj = arg.dateObj
            elif isinstance(arg, datetime.date):
                self.dateObj = arg
            elif isinstance(arg, str):
                try:
                    dateParts = [int(s) for s in arg.split('-')]
                    self.dateObj = datetime.date(*dateParts)
                except:
                    raise TypeError('myuwDate accepts either "yyyy-mm-dd" or yyyy, mm, dd as its arguments')

            else:
                raise TypeError('myuwDate accepts either "yyyy-mm-dd" or yyyy, mm, dd as its arguments')

        # Arguments specified as y, m, d
        elif len(args) == 3:
            self.dateObj = datetime.date(*args)

        else: 
            raise TypeError('myuwDate accepts either "yyyy-mm-dd" or yyyy, mm, dd as its arguments')


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

        except: 
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
            
            


# Convert a date to myuwDate if necessary
def processDate(date):
    if isinstance(date, myuwDate):
        return date
    elif isinstance(date, str):
        return myuwDate(date)
    else:
        raise Exception('Argument must either be a myuwDate or a string')

# Class for a date range
class myuwDateRange(object):
    
    # Takes arguments in any of the following forms:
    # myuwDate, myuwDate
    # (myuwDate, myuwDate)
    # 'yyyy-mm-dd', 'yyyy-mm-dd'
    # ('yyyy-mm-dd', 'yyyy-mm-dd')
    def __init__(self, *args):
        # Arguments specified as a tuple
        # Just unpack them
        if len(args) == 1:
            arg = args[0]
            if isinstance(arg, myuwDateRange):
                self.startDate = arg.startDate
                self.endDate = arg.endDate
            else:
                self.__init__(*arg)

        elif len(args) == 2:
            dateA = args[0]
            dateB = args[1]
            dateA = processDate(dateA)
            dateB = processDate(dateB)
            self.startDate = dateA
            self.endDate = dateB

        else: 
            raise TypeError('myuwDateRange requires one or two arguments')

    # Get dates that should be tested based on this date range
    @property
    def significantDates(self):
        return (self.startDate - 1, self.startDate, self.endDate - 1, self.endDate)

    # Lets us use 'date in dateRange' syntax to check if a date is part of this date range
    # This is INCLUSIVE of the end date
    def __contains__(self, element):
        element = processDate(element)
        return self.startDate <= element <= self.endDate



# Class to hold an actual and expected card to be compared. 
class cardPair(object):
    def __init__(self, actual, expected):
        # Ensure that the cards have the same name, and then 
        # set this object's name to that. 
        if actual.name in expected.allNames or expected.name in actual.allNames:
            self.name = expected.name
            self.otherName = actual.name
        else:
            raise AssertionError('Actual card and expected card have different names')
        self.actual = actual
        self.expected = expected

    def __repr__(self):
        return 'cardPair(%s, %s)' %(actual, expected)

    __str__ = __repr__

    # Find and report the differences between the two cards
    def findDiffs(self):
        return self.actual.findDiffs(self.expected)

# Object to allow us to pack multiple dates into one friendly name
# and do operations on it,
# so that we can say something like 'ClassesStart + 1' and it will
# generate a list of dates that satisfy that. 
class multiDate(IterableUserDict):
    
    def __init__(self, qtrsDict):
        qtrsDict = qtrsDict.copy()
        for qtr, date in qtrsDict.items():
            if not isinstance(date, myuwDate):
                qtrsDict[qtr] = myuwDate(date)
        self.data = qtrsDict
        #super(type(self), self).__init__(qtrsDict)

    def __add__(self, other):
        newQtrs = {}
        for qtr, date in self.items():
            newQtrs[qtr] = date + other
        return self.__class__(newQtrs)

    def __sub__(self, other):
        return self.__add__(-1 * other)

# Class to combine a card with a function to determine whether or not it should
# show up for that user. 
# Allows the card itself to be unhinged from show/hide logic, which may be different
# for different users. 
# Subclasses may populate the list of significant dates which will be used by some
# test styles to automatically figure out dates to test. 
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


# Card that should always appear
class cardAlways(cardProxy):
    def shouldAppear(self, date):
        return True

# Card that should never appear
class cardNever(cardProxy):
    def shouldAppear(self, date):
        return False

# Card that appears conditionally based on date
# cardCDM takes a list of date ranges. 
# If you just want one, see cardCD below. 
class cardCDM(cardProxy):
    def __init__(self, card, dates):
        self.card = card
        self.dateRanges = []
        for datePair in dates:
            r = myuwDateRange(*datePair)
            # Append tuple of processed dates to our date range list:
            self.dateRanges.append(r)

    # Test if the card should appear on a particular date
    def shouldAppear(self, date):
        for dateRange in self.dateRanges:
            if date in dateRange:
                if hasattr(self.card, 'shouldAppear'):
                    return self.card.shouldAppear()
                else:
                    return True
        return False

    # Get dates that should be tested for this card. 
    # Currently, it is:
    # - Day before card is visible
    # - First day card is visible
    # - Day before card disappears
    # - First day the card is not visible
    @property
    def significantDates(self):
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
        self.dateRanges = [myuwDateRange(dateRange)]

# Lets you use multiDate (or even a plain old dict) for start and end
class cardAuto(cardCDM):
    # qtrSpan lets you specify that the range should span to the next quarter
    # Not done yet, so for now just specify the card twice, once from the start to 
    # end of qtr, then start of next qtr to true end. 
    # Or define the actual event dates that way. 
    def __init__(self, card, startDates, endDates, offset = 0):
        self.card = card
        self.dateRanges = []
        for qtr, sd in startDates.items():
            # Make sure the quarter is defined in both dictionaries
            if qtr not in endDates:
                continue
            ed = endDates[qtr]
            dateRange = myuwDateRange(sd, ed)
            self.dateRanges.append(dateRange)

