#!/usr/bin/python

import datetime

# Function that attempts to determine if a card is visible
def isCardVisible(cardEl):
    if not cardEl.is_displayed():
        return False
    #if not cardEl.get_attribute('innerHTML'):
    #    return False
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
        #diffs = str(diffs)
        return diffs
    else: 
        raise Exception('Used findDiffs on %s without autoDiffs attribute' %self)

def rangesToSigDates(dateRanges):
    out = []
    for r in dateRanges:
        out += r.significantDates
    return out

# Get card name from an element
# Useful for when you can't make a proper card out of the 
# element, but still need a useful identifier, e.g. 
# the loading spinner. 
def getCardName(cardEl):
    cardId = cardEl.get_attribute('id')
    cardDataName = cardEl.get_attribute('data-name')
    cardName = cardId or cardDataName
    return cardName
