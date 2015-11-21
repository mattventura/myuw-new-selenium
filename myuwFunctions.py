#!/usr/bin/python


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

