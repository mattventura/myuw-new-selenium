#!/usr/bin/python

import datetime

# Function that attempts to determine if a card is visible
def isCardVisible(cardEl):
    if not cardEl.is_displayed():
        return False
    #print 'Checking innerHTML'
    #if not cardEl.get_attribute('innerHTML'):
    #    return False
    #print 'Checking .text'
    if not cardEl.text:
        return False
    return True

# Like above but checks less stuff
def isVisibleFast(el):
    return el.is_displayed()

# Functions
# Convert int to timedelta, if necessary
def toTimeDelta(obj):
    if isinstance(obj, int):
        obj = datetime.timedelta(obj)
        
    if isinstance(obj, datetime.timedelta):
        return obj

    else:
        raise TypeError('toTimeDelta requires either an int or datetime.timedelta as its argument')

# Pack the element argument of a fromElement method into the 
# resultant object for debugging purposes. 
def packElement(func):
    def inner(cls, date, e):
        newCardInstance = func(cls, date, e)
        newCardInstance.originalElement = e
        return newCardInstance
    return inner
    
def formatDiffs(label, a, b):
    if a == b:
        return ''
    else:
        outStr = 'Different %s (%s vs %s)\n' %(label, a, b)
        return outStr
