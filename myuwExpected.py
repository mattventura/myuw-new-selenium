#!/usr/bin/python

from myuwClasses import myuwDate, myuwDateRange, cardPair, \
cardAlways, cardNever, cardCDM, cardCD, cardAuto
from myuwCards import *
from myuwDates import *


# Assemble actual lists of users and their expected cards
# These are given as lists then turned into the required dictionary
# format later. 
# You can specify multiple conditional cards with disjoint date ranges as a 
# way of specifying different sets of data for different time periods, but
# ideally this should be put in the card itself. 
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
    cardCD(
        EventsCard(),
        ('2013-03-19', '2013-04-30')
    ),
    cardAlways(ToRegisterCard()),
    cardAuto(
        VisualScheduleCard(),
        FirstDayQtr,
        LastDayInstr
    ),
    cardAlways(app_notices()),
    cardAlways(PCEBanner()),
    cardAlways(app_acal()),
#    cardAlways(notice_banner_location()),
#    cardAlways(calendar_banner_location_mobile()),
#    cardAlways(landing_content_cards()),

    #cardCD(VisualScheduleCard(), ('2013-01-07', '2013-03-15')),
    #cardCD(TextbookCard(), ('2013-01-07', '2013-01-13')),
    #cardCD(GradeCard(), ('2013-03-16', '2013-03-26')),
    cardCD(
        FutureQuarterCard({
            'Spring 2013': {
                'credits' : 15,
                'sections': 6,
            },
        }),
        # Bugged?
        #(RegPd1['WI13'], LastDayQtr['WI13'])
        (FirstDayQtr['WI13'], LastDayQtr['WI13'])
    ),
    cardCD(
        FutureQuarterCard({
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
        (FirstDayQtr['SP13'], LastDayQtr['SP13'])
    ),
    cardAuto(
        TextbookCard(),
        FirstDayQtr, 
        ClassesBegin + 7
    ),
    cardAuto(
        GradeCard(),
        LastDayInstr + 1,
        NextQtrClassesBegin - 1,
    ),
    cardAuto(
        FinalExamCard(),
        LastDayInstr + 1,
        BreakBegins - 1,
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
# Also pack conditionals into a list
def cardListToDict(cl):
    cd = {}
    for card in cl:
        name = card.name
        if name in cd:
            cd[name].append(card)
        else:
            cd[name] = [card]
    return cd

for name, cl in cardList.items():
    cardList[name] = cardListToDict(cl)

# Function to get expected results for a date and user
def getExpectedResults(user, date):
    userCards = cardList[user]
    userCardsVisible = {}
    # Go over the collection of possible card states, figure out which to display
    for name, cardColl in userCards.items():
        for card in cardColl:
            if card.shouldAppear(date):
                if name in userCardsVisible:
                    s = 'Two expected cards with name %s on %s' %(name, date)
                    raise Exception(s)
                else:
                    userCardsVisible[name] = card
    return userCardsVisible

# Get significant dates to test for user. 
# Each card is allowed to report its own dates. 
# TODO: implement start and end
def getSigDates(user, start = None, end = None): 
    userCards = cardList[user]
    if start:
        start = myuwDate(start)
    if end:
        end = myuwDate(end)
    sigDates = []
    for cardColl in userCards.values():
        for card in cardColl:
            for sigDate in card.significantDates:
                if sigDate < start or sigDate > end:
                    continue
                if sigDate not in sigDates:
                    sigDates.append(sigDate)
    outList = sigDates
    outList.sort()
    return outList

# Given two dictionaries of cards, find the differences between them. 
# This includes missing/unexpected cards as well as differences in card content. 
def findDiffs(actual, expected):

    # Cards in common. 
    # These will need to be compared to each other individually to find 
    # differences between actual and expected data
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


