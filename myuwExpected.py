#!/usr/bin/python

from myuwClasses import myuwDate, myuwDateRange, cardPair
from myuwCards import *
from UserDict import IterableUserDict

# Function to get expected results for a date and user
def getExpectedResults(user, date):
    userCards = cardList[user]
    userCardsVisible = {}
    for name, card in userCards.items():
        if card.shouldAppear(date):
            userCardsVisible[name] = card
    return userCardsVisible

# Get significant dates to test for user. 
# Each card is allowed to report its own dates. 
# TODO: implement start and end
def getSignificantDates(user, start = None, end = None): 
    userCards = cardList[user]
    sigDates = []
    for card in userCards.values():
        sigDates.extend(card.significantDates)
    outList = list(set(sigDates))
    outList.sort()
    return outList

# Given two dictionaries of cards, find the differences between them. 
# This includes missing/unexpected cards as well as differences in card content. 
def findDiffs(actual, expected):

    # Cards in common. 
    # These will need to be compared to each other. 
    common = {}

    # Figure out what we have in common
    for cardName in actual:
        if cardName in expected:
            actualCard = actual[cardName]
            expectedCard = expected[cardName]
            # Assemble a cardPair object for these two cards. 
            common[cardName] = cardPair(actualCard, expectedCard)

    # For the cards in common, remove them from the dictionaries of 
    # the actual and expected lists (after copying them) to form 
    # the list of cards exclusive to each group. 
    onlyInActual = actual.copy()
    onlyInExpected = expected.copy()
    for cardName in common:
        onlyInActual.pop(cardName)
        onlyInExpected.pop(cardName)
    
    # Calculate actual differences
    diffs = ''
    # Report cards which were found but not expected
    if onlyInActual:
        fmtdList = ', '.join(onlyInActual.keys())
        diffs += 'Found the following unexpected cards: %s\n' %fmtdList
    # Report cards which were expected but not found
    if onlyInExpected:
        fmtdList = ', '.join(onlyInExpected.keys())
        diffs += 'Didn\'t find the following expected cards: %s\n' %fmtdList
    # Report differences between actual and expected data on the cards
    for name, pair in common.items():
        pairDiff = pair.findDiffs()
        if pairDiff:
            diffs += 'Found differences in card %s:\n' %name
            diffs += pairDiff

    return diffs

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




# Object to allow us to pack multiple dates into one friendly name
# and do operations on it,
# so that we can say something like 'ClassesStart + 1' and it will
# generate a list of dates that satisfy that. 
class multiDate(IterableUserDict):
    
    def __init__(self, qtrsDict):
        qtrsDict = qtrsDict.copy()
        for qtr, date in qtrsDict.items():
            if type(date) != myuwDate:
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


QuarterStart = multiDate({
    'WI13': '2013-01-07',
    'SP13': '2013-04-01',
})

RegPd1 = multiDate({
    'WI13': '2013-02-15',
    'SP13': '2013-04-15',
})

LastDayQtr = multiDate({
    'WI13': '2013-03-27', 
    'SP13': '2013-06-19',
})

FinalsBegin = multiDate({
    'WI13': '2013-03-18',
    'SP13': '2013-06-10',
})

BreakBegins = multiDate({
    'WI13': '2013-03-23',
    'SP13': '2013-06-10',
})


    
# Assemble actual lists of users and their expected cards
# These are given as lists then turned into the required dictionary
# format later. 
cardList = {}
cardList['javerage'] = [
    cardAlways(HFSCard({'stu': '$1.23', 'emp': '$1.00', 'din': '$5.10'})),
    #cardAlways(EmpFacStudentCard(True, False)),
    cardAlways(CriticalInfoCard()),
    
    cardAlways(TuitionCard()),
    cardAlways(LibraryCard()),
###    cardAlways(AcademicCard()),
    cardAlways(CourseCard()),
    cardAlways(GradStatusCard()),
    cardAlways(GradCommitteeCard()),
    cardAlways(SummerEFSCard()),
    cardAlways(EventsCard()),
    cardAlways(ToRegisterCard()),
#    cardAlways(notice_banner_location()),
#    cardAlways(calendar_banner_location_mobile()),
#    cardAlways(landing_content_cards()),

    #cardCD(VisualScheduleCard(), ('2013-01-07', '2013-03-15')),
    #cardCD(TextbookCard(), ('2013-01-07', '2013-01-13')),
    #cardCD(GradeCard(), ('2013-03-16', '2013-03-26')),
    cardAuto(FinalExamCard(), FinalsBegin, BreakBegins - 1),
    cardCD(
        FutureQuarterCardA({
            'Summer 2013 A-Term': {
                'credits' : 2,
                'sections': 2,
            },
            'Summer 2013 B-Term': {
                'credits' : 2,
                'sections': 2,
            },
            'Autumn 2013': {
                'credits' : 5,
                'sections': 1,
            },
        }),
        # Fake dates for testing XXX
        (RegPd1['WI13'], LastDayQtr['WI13'])
    ),
    # This card has "seen"-dependent logic, so it never actually appears at the 
    # bottom for our tests. 
    #card(FutureQuarterCard1, ('2013-03-12', '2013-03-27')),
#    cardN(FutureQuarterCard1()),

#    cardN(RegStatusCard()), 
#    cardN(SummerRegStatusCardA()),
#    cardN(SummerRegStatusCard1()),
#    cardN(EventsCard()),
]

# We want these to be dictionaries, but no need to cause a bunch of 
# extra typing when listing them. 
def cardListToDict(cl):
    cd = {}
    for card in cl:
        name = card.name
        cd[name] = card
    return cd

for name, cl in cardList.items():
    cardList[name] = cardListToDict(cl)

