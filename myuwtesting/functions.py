#!/usr/bin/python

import datetime
from selenium.common.exceptions import WebDriverException


def uesc(func):
    '''Escape unicode from all arguments. '''

    def inner(*args, **kwargs):

        newArgs = []
        for arg in args:
            if isinstance(arg, unicode):
                arg = arg.encode('unicode-escape')
            newArgs.append(arg)

        for k,v in kwargs.items():
            if isinstance(v, unicode):
                kwargs[k] = v.encode('unicode-escape')

        return func(*newArgs, **kwargs)

    return inner


def isCardVisible(cardEl):
    '''Attempt to determine if a card is visible using numerous indicators.'''
    if not(cardEl.is_displayed()):
        return False
    #if not cardEl.get_attribute('innerHTML'):
    #    return False
    text = cardEl.text
    if not(cardEl.text):
        return False

    return True


def isVisibleFast(el):
    '''Attempt to determine if a card is visible using just is_displayed().'''
    return el.is_displayed()


def toTimeDelta(obj):
    '''Convert an int to a datetime.timedelta. If the input is already
    a timedelta, just return it. '''
    if isinstance(obj, int):
        return datetime.timedelta(obj)

    if isinstance(obj, datetime.timedelta):
        return obj

    else:
        raise TypeError('toTimeDelta requires either an int or '
            'datetime.timedelta as its argument')


def packElement(func):
    '''Decorator to set the 'originalElement' property of a card
    to the web element used to construct it. Useful for debugging.
    '''
    def inner(cls, date, e):
        newCardInstance = func(cls, date, e)
        newCardInstance.originalElement = e
        return newCardInstance
    return inner


@uesc
def formatDiffs(label, a, b):
    '''Format diffs.
    If a and b are equal, return an empty string.
    If not, then use 'label' to form a description of the differences.
    Escapes unicode such as to not cause problems.
    '''
    if a == b:
        return ''
    # TODO
    #elif isinstance(a, list) and isinstance(b, list):
    #    return formatListDiffs(label, a, b)
    else:
        return 'Different %s (%s vs %s)\n' %(label, a, b)

# Not finished TODO
"""
def formatListDiffs(label, a, b):
    '''Find differences between two lists'''

    if len(a) != len(b):
        outStr = 'Different lengths of %s (%s vs %s)\n' %(label, len(a), len(b))
        return outStr

    sortedA = list(a)
    sortedB = list(b)
    sortedA.sort()
    sortedB.sort()

    if sortedA == sortedB:
        outStr = 'Different order of %s (%s vs %s)\n' %(label, a, b)
        return outStr

    outStr = 'Different lists %s
    """


def findDiffs(self, other):
    if hasattr(self, 'autoDiffs'):
        diffs = ''
        for prop, label in self.autoDiffs.items():
            valueSelf = getattr(self, prop)
            valueOther = getattr(other, prop)
            # If the values themselves have diff methods, use those
            # instead of a simple comparison
            diffSelf = hasattr(valueSelf, 'findDiffs')
            diffOther = hasattr(valueOther, 'findDiffs')
            if diffSelf and diffOther:
                diffs += valueSelf.findDiffs(valueOther)
            else:
                diffs += formatDiffs(label, valueSelf, valueOther)
        return diffs
    else:
        raise Exception(
            'Used findDiffs on %s without autoDiffs attribute' %self
        )

def rangesToSigDates(dateRanges):
    '''Given a list of date ranges, find all the significant dates.
    Does not handle removing dupes. '''
    return sum([r.significantDates for r in dateRanges], [])

def getCardName(cardEl):
    '''Try to guess card name from an element. Useful for when you can't
    make a proper card out of the element, but still need some sort of
    identifier, e.g. a card that hasn't finished loading.'''
    cardId = cardEl.get_attribute('id')
    cardDataName = cardEl.get_attribute('data-name')
    cardName = cardId or cardDataName
    return cardName


def splitList(l, n):
    '''Split a list into n smaller lists, with a minimum of one item per
    chunk.'''
    out = []
    for i in range(n):
        length = len(l)
        start = length * i / n
        end = length * (i + 1) / n
        chunk = l[start:end]
        # Ignore blank chunks, happens when len(l) < n
        if chunk:
            out.append(chunk)
    return out


def driverRetry(driverFunc, numTries = 3):
    '''Function to automatically retry (at most numTries times) opening the
    browser when you get the "Can't load the profile" error. This error
    occasionally happens randomly, but if it happens more than a few times
    in a row it's likely an actual blocker. Most likely, you updated the
    browser to a version that the WebDriver isn't equipped to handle, so
    either "pip install --upgrade selenium" or roll back the browser. '''

    try:
        return driverFunc()
    except WebDriverException as ex:
        if numTries > 1:
            return driverRetry(driverFunc, numTries - 1)
        else:
            raise ex


def filterListVis(inList, date):
    '''Filter a list down to elements whose shouldAppear method returns true
    on that date. '''
    return [item for item in inList if item.shouldAppear(date)]
