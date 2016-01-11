#!/usr/bin/python

from myuwClasses import myuwDate, myuwDateRange, cardPair, \
cardAlways, cardNever, cardCDM, cardCD, cardAuto, errorCard, \
cardProxy
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
    HFSCard({'stu': '$1.23', 'emp': '$1.00', 'din': '$5.10'}),
    CriticalInfoCard(True, True, False),
    TuitionCard(),
    LibraryCard(),
    CourseCard(),
    GradStatusCard(
        [
            petRequest("Master's degree - Extend six year limit", 
                {'grad': 'Approved',}, 
                visCheck = visBefore('2013-6-26'),
            ), 
            petRequest("Master's degree - Extend six year limit", 
                {'grad': 'Pending', 'dept': 'Approve'}
            ), 
            petRequest("Master's degree - Extend six year limit", 
                {'dept': 'Withdraw',}
            ), 
            petRequest("Master's degree - Extend six year limit", 
                {'dept': 'Approve', 'grad': 'Withdrawn'}
            ), 

        ], 
        [
            leaveRequest('Winter 2013 Leave', 'Paid', 
                visCheck = visBefore('2013-3-27')),
            leaveRequest('Autumn 2013 Leave', 'Paid',
                visCheck = visBefore('2013-12-18')),
            #TODO: verify above date
            leaveRequest('Winter 2014 Leave', 'Paid'),
            leaveRequest('Spring 2014 Leave', 'Paid'),
        ], 
        [
            degreeRequest('Masters Request, Winter 2015', 
                'Awaiting Dept Action (Final Exam)', 
                title = 'MASTER OF LANDSCAPE ARCHITECTURE/MASTER OF ARCHITECTURE'
            ), 
            degreeRequest('Masters Request, Winter 2015', 
                'Withdrawn',
                title = 'MASTER OF ARCHITECTURE'
            ),
            degreeRequest('Masters Request, Winter 2015', 
                'Withdrawn',
                title = 'MASTER OF ARCHITECTURE'
            ),
            degreeRequest('Masters Request, Winter 2015', 
                'Not Recommended by Dept',
                title = 'MASTER OF LANDSCAPE ARCHITECTURE'
            ),
            degreeRequest('Masters Request, Spring 2015', 
                'Recommended by Dept',
                title = 'MASTER OF ARCHITECTURE'
            ),
            degreeRequest('Masters Request, Spring 2015', 
                'Did Not Graduate',
                title = 'MASTER OF LANDSCAPE ARCHITECTURE'
            ),
        
        ]
    ),
    GradCommitteeCard({
        'Doctoral Supervisory Committee': [
            {
                'dept': 'Anthropology', 
                'chair': True, 'name': u'Bet Duncan', 
                'email': u'bbb@u.washington.edu'
            }, 
            {
                'dept': u'Anthropology', 'chair': True, 
                'name': u'Steve M. Goodman', 
                'email': u'sss@u.washington.edu'
            }, 
            {
                'dept': u'Health Services - Public Health', 
                'gsr': True, 
                'name': u'Malinda Korry'
            }, 
            {
                'dept': u'Global Health', 
                'name': u'James T. Pfeiffer', 
                'email': u'jjj@uw.edu'
            }
        ], 
        u"Master's Committee": [
            {
                'dept': u'Epidemiology - Public Health', 
                'chair': True, 
                'email': u'nnn@u.washington.edu', 
                'name': u'Nina L. Patrick', 
                'rcc': True
            }, 
            {
                'rcm': True, 
                'gsr': True, 
                'name': u'Bet Duncan', 
                'email': u'bbb@u.washington.edu', 
                'dept': u'Anthropology'
            }, 
            {
                'rcm': True, 
                'email': u'lll@oge.sld.pe', 
                'name': u'Louis Vivian', 
                'dept': u'Ministry of Health, Peru'
            }
        ], 
        u'Advisor': [
            {
                'rcm': True, 
                'email': u'bbb@u.washington.edu', 
                'name': u'Bet Duncan', 
                'dept': u'Anthropology'
            }
        ]
    }),
    SummerEFSCard(True, True),
    cardCD(
        EventsCard(),
        ('2013-03-19', '2013-04-30')
    ),
    ToRegisterCard(),
    VisualScheduleCard({
        'WI13': {
            'EMBA 503 A': None,
            'EMBA 533 A': None,
            'EMBA 590 A': None,
        },
        'SP13': {
            'TRAIN 101 A': None,
            'PHYS 121 A': None,
            'PHYS 121 AQ': None,
            'PHYS 121 AC': None,
            'TRAIN 100 A': None,
        }, 
        'SA13': {
            'TRAIN 102 A': None,
            'ELCBUS 451 A': None,
        },
        'SB13': {
            'TRAIN 101 A': None,
            'TRAIN 102 A': None,
        },
        'AU13': {
            'ENGL 207 A': None,
        },
    }),
    app_notices(),
    PCEBanner(),
    app_acal(),
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
    cardCD(
        FutureQuarterCard({
            'Autumn 2013': {
                'credits' : 5,
                'sections': 1,
            },
        }),
        (FirstDayQtr['SU13'], LastDayQtr['SU13'])
    ),
    cardCD(
        FutureQuarterCard({
            'Winter 2014': {
                'credits' : 15,
                'sections': 5,
            },
        }),
        (FirstDayQtr['AU13'], LastDayQtr['AU13'])
    ),
    cardCD(
        TextbookCard(),
        ('2013-1-1', LastDayQtr['SU13'])
    ),
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
        }, 
        'SA13': {
            'ELCBUS 451': None,
        },
        'SB13': {
            'ELCBUS 451': None,
            'TRAIN 101': None,
            'TRAIN 102': None,
        },
        'AU13': {
            'ENGL 207': None,
        },
    }),

    FinalExamCard(),
    ThriveCardExpected(),
        
]

cardList['jinter'] = [
    HFSCard({'emp': '$1.00'}),
    ToRegisterCard(),
    TuitionCard(),
    LibraryCard(),
    errorCard('GradStatusCard'),
    errorCard('GradCommitteeCard'),
    PCEBanner(),
    app_notices(),
    app_acal(),
    SummerEFSCard(summerReg = False, considerEFS = True), 
    #VisualScheduleCard(),
    InternationalStuCard(),
    EmpFacStudentCard(True, True),
    
    cardAuto(
        RegStatusCard(),
        RegCardShow,
        RegCardHide
    ), 
    cardAuto(
        SummerRegStatusCard(),
        SummerRegShow,
        SummerRegHide
    ),
    cardAlways(CriticalInfoCard()),
    ThriveCardExpected(),
    #cardCDM(
    #    CourseCard(),
    #    getMultiDateRange(LastDayInstr + 1, LastDayQtr, exclude = ['SU13', 'WI13'])
    #    + [myuwDateRange('2013-6-19', '2013-6-23')], 
    #)
    NoCourseCard(), 
]


cardList['seagrad'] = [
    errorCard('TuitionCard'),
    app_acal(),
    ThriveCardExpected(),
    NoCourseCard(),
    #cardCDM(
    #    VisualScheduleCard(),
    #    getMultiDateRange(FirstDayQtr, LastDayInstr, exclude = ['SU'])
    #), 
        
    #FinalExamCard(),
    GradStatusCard(
        [
            petRequest("Doctoral degree - Extend ten year limit", 
                {'dept': 'Pending',}
            ), 
            petRequest("Doctoral degree - Extend ten year limit", 
                {'dept': 'Withdraw',},
                visCheck = visBefore('2013-4-25'),
            ), 
            petRequest("Doctoral degree - Extend ten year limit", 
                {'grad': 'Pending', 'dept': 'Deny'}
            ), 
            petRequest("Doctoral degree - Extend ten year limit", 
                {'grad': 'Not approved', 'dept': 'Deny'},
                visCheck = visBefore('2013-4-25'),
            ), 
            petRequest("Doctoral degree - Extend ten year limit", 
                {'grad': 'Approved'},
                visCheck = visBefore('2013-4-25'),
            ), 
            petRequest("Doctoral degree - Extend ten year limit", 
                {'dept': 'Approve', 'grad': 'Pending'}
            ), 
            petRequest("Doctoral degree - Extend ten year limit", 
                {'grad': 'Approved'},
                visCheck = visBefore('2013-4-25'),
            ), 
        ], 
        [
            leaveRequest('Spring 2013 Leave', 'Requested'),
            leaveRequest('Spring 2013 Leave', 'Withdrawn',
                visCheck = visBefore('2013-8-28')),
            leaveRequest('Winter 2013 Leave', 'Paid', 
                visCheck = visBefore('2013-3-27')),
            leaveRequest('Spring 2013 Leave', 'Approved\n Pay Your Fee To Confirm', 
                visCheck = visBefore('2013-6-8')),
        ], 
        [
            degreeRequest('Masters Request, Spring 2013', 
                'Awaiting Dept Action', 
                title = 'Master Of Landscape Architecture/Master Of Architecture'
            ), 
            degreeRequest('Masters Request, Spring 2013', 
                'Awaiting Dept Action (Final Exam)',
                title = 'Master Of Landscape Architecture/Master Of Architecture'
            ),
            degreeRequest('Masters Request, Spring 2013', 
                'Awaiting Dept Action (General Exam)',
                title = 'Master Of Landscape Architecture/Master Of Architecture'
            ),
            degreeRequest('Masters Request, Spring 2013', 
                'Recommended by Dept',
                title = 'Master Of Architecture'
            ),
            degreeRequest('Masters Request, Spring 2013', 
                'Withdrawn',
                title = 'Master Of Architecture',
                visCheck = visBefore('2013-4-5'),
            ),
            degreeRequest('Masters Request, Spring 2013', 
                'Candidacy Granted',
                title = 'Master Of Landscape Architecture',
                visCheck = visBefore('2013-8-28'),
            ),
            degreeRequest('Masters Request, Spring 2013', 
                'Graduated by Grad School',
                title = 'Master Of Landscape Architecture',
                visCheck = visBefore('2013-8-28'),
            ),
            degreeRequest('Masters Request, Spring 2013', 
                'Did Not Graduate',
                title = 'Master Of Science In Construction Management',
                visCheck = visBefore('2013-8-28'),
            ),
        
        ]
    ),
    GradCommitteeCard({
        'Doctoral Supervisory Committee': [
            {
                'dept': 'Anthropology', 
                'chair': True, 
                'rcc': True,
                'name': u'Bet Duncan', 
                'email': u'bbb@u.washington.edu'
            }, 
            {
                'dept': u'Anthropology', 
                'chair': True, 
                'name': u'Steve M. Goodman', 
                'email': u'sss@u.washington.edu'
            }, 
            {
                'dept': u'Health Services - Public Health', 
                'gsr': True, 
                'name': u'Malinda Korry'
            }, 
            {
                'dept': u'Global Health', 
                'name': u'James T. Pfeiffer', 
                'email': u'jjj@uw.edu'
            }
        ], 
        u"Master's Committee": [
            {
                'dept': u'Epidemiology - Public Health', 
                'chair': True, 
                'email': u'nnn@u.washington.edu', 
                'name': u'Nina L. Fitzpatrick', 
            }, 
            {
                'gsr': True, 
                'name': u'Bet Shell-Duncan', 
                'email': u'bbb@u.washington.edu', 
                'dept': u'Anthropology'
            }, 
            {
                'email': u'lll@oge.sld.pe', 
                'name': u'Louis ReVivian', 
                'dept': u'Ministry of Health, Peru',
            }
        ], 
        u'Advisor': [
            {
                'email': u'bbb@u.washington.edu', 
                'name': u'Bet Duncan', 
                'dept': u'Anthropology'
            }
        ]
    }),
]
#del cardList['javerage']
#del cardList['seagrad']
#del cardList['jinter']

# We want these to be dictionaries, but no need to cause a bunch of 
# extra typing when listing them. 
# It puts them in a list so that cards that move around depending
# on date can have multiple entries. 
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
    if isinstance(date, str):
        date = myuwDate(date)
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

    for name, card in userCardsVisible.items():
        # If it's a card proxy, replace it with the real card
        if isinstance(card, cardProxy):
            userCardsVisible[name] = card.card
            
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
            if hasattr(card, 'significantDates'):
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
def findDiffs(expected, actual):

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
            common[cardName] = cardPair(expectedCard, actualCard)

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
        elif (not(isinstance(pairDiff, str))
            and not(isinstance(pairDiff, unicode))):

            raise TypeError(
                'Diff for %s returned a non-string value "%s"\n' %(name, diffs)
            )
        elif pairDiff:
            diffs += 'Found differences in card %s:\n' %name
            diffs += pairDiff

    return diffs


