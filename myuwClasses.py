#!/usr/bin/python

import datetime
from functools import total_ordering

# Functions
# Convert int to timedelta, if necessary
def toTimeDelta(obj):
    if type(obj) == int:
        obj = datetime.timedelta(obj)
        
    if type(obj) == datetime.timedelta:
        return obj

    else:
        raise TypeError('toTimeDelta requires either an int or datetime.timedelta as its argument')

# Convert string, timedelta, or myuw date to datetime.date
def toDate(obj):
    if type(obj) == str:
        obj = myuwDate(other)

    if type(obj) == myuwDate:
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
            if type(arg) == self.__class__:
                # Might be dangerous if arg.dateObj is modified later
                self.dateObj = arg.dateObj
            elif type(arg) == datetime.date:
                self.dateObj = arg
            elif type(arg) == str:
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
    if type(date) == myuwDate:
        return date
    elif type(date) == str:
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
            if type(arg) == myuwDateRange:
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


# Exception for telling the user that they didn't parse the cards
# before trying to read them. 
# Not yet used/TODO
class CardsNotParsed(Exception):
    def __init__(self, message):
        super(CardsNotParsed, self).__init__('You must parse cards before reading them')

# Class to hold an actual and expected card to be compared. 
class cardPair(object):
    def __init__(self, actual, expected):
        # Ensure that the cards have the same name, and then 
        # set this object's name to that. 
        if actual.name == expected.name:
            self.name = actual.name
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
