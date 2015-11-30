#!/usr/bin/python

from myuwClasses import myuwDate
from myuwDates import FirstDayQtr, LastDayQtr

# Function that attempts to determine if a card is visible
def isCardVisible(cardEl):
    #print 'Checking is_displayed'
    if not cardEl.is_displayed():
        return False
    #print 'Checking innerHTML'
    #if not cardEl.get_attribute('innerHTML'):
    #    return False
    #print 'Checking .text'
    if not cardEl.text:
        return False
    return True

# Try to convert 
def dateToQtr(date):
    date = myuwDate(date)
    for qtr, start in FirstDayQtr.items():
        try:
            end = LastDayQtr[qtr]
            if start <= date <= end:
                return qtr
        except: 
            continue
    raise Exception("Couldn't find quarter for date %s" %date)
