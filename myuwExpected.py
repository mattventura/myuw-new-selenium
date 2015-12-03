#!/usr/bin/python

from myuwClasses import myuwDate, myuwDateRange, cardPair, \
cardAlways, cardNever, cardCDM, cardCD, cardAuto, errorCard
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
    cardAlways(CriticalInfoCard(True, True, False)),
    
    cardAlways(TuitionCard()),
    cardAlways(LibraryCard()),
    cardAlways(CourseCard()),
    cardAlways(GradStatusCard()),
    cardAlways(GradCommitteeCard()),
    cardAlways(SummerEFSCard(True, True)),
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
        GradeCard({
            'WI13': {
                'EMBA 503': None,
                'EMBA 533': None,
                'EMBA 590': None,
            },
            'SP13': {
                'PHYS 121': '4.0',
                'TRAIN 100': 'P',
                'TRAIN 101': 'HP',
            }
        }),
        LastDayInstr + 1,
        NextQtrClassesBegin - 1,
    ),
    cardAuto(
        FinalExamCard(),
        LastDayInstr + 1,
        BreakBegins - 1,
    ),
        
]

cardList['jinter'] = [
    HFSCard({'emp': '$1.00'}),
    ToRegisterCard(),
    TuitionCard(),
    LibraryCard(),
    cardAlways(errorCard('GradStatusCard')),
    cardAlways(errorCard('GradCommitteeCard')),
    cardAlways(PCEBanner()),
    cardAlways(app_notices()),
    cardAlways(app_acal()),
    cardAlways(SummerEFSCard(summerReg = False, considerEFS = True)), 
    VisualScheduleCard(),
    InternationalStuCard(),
    EmpFacStudentCard(True, True),
    
    cardAuto(
        RegStatusCard(), 
        RegCardShow,
        RegPd2 + 7
    ), 
    cardAuto(SummerRegStatusCard(),
        SummerRegShow,
        RegPd2 + 7
    ),
    cardAlways(CriticalInfoCard()),
]

# We want these to be dictionaries, 
# but no need to cause a bunch of 
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
                    s = 'Two expected cards with id %s on %s' %(name, date)
                    raise Exception(s)
                else:
                    userCardsVisible[name] = card
    return userCardsVisible

# Get significant dates to test for user. 
# Each card is allowed to report its own dates. 
# Done: implement start and end
def getSigDates(user, start = None, end = None): 
    # Expected cards for the given user
    userCards = cardList[user]
    # Convert start/end to myuwDate
    if start:
        start = myuwDate(start)
    if end:
        end = myuwDate(end)
    sigDates = []
    # Go through each card collection (set of each
    # different version a card might be in depending on 
    # date, as an alternative to natively supporting
    # that in the card). 
    for cardColl in userCards.values():
        # Go through each version of the card
        for card in cardColl:
            # Check each sigdate for each card and see if 
            # it falls within the desired range
            for sigDate in card.significantDates:
                # start and end are optional
                if start and sigDate < start:
                    continue
                elif end and sigDate > end:
                    continue
                elif sigDate not in sigDates:
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
        
        if pairDiff == None:
            raise TypeError('Diff for %s returned None\n' %name)
        elif not(isinstance(pairDiff, str)):
            print type(pairDiff)
            raise TypeError(
                'Diff for %s returned a non-string value "%s"\n' %(name, diffs)
            )
        elif pairDiff:
            diffs += 'Found differences in card %s:\n' %name
            diffs += pairDiff

    return diffs


