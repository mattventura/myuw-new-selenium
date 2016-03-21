#!/usr/bin/python

from classes import thriveContent, link, myuwDateRange
from cards import ThriveCard
from dates import ClassesBegin

class ThriveCardExpected(ThriveCard):
    '''Expected data for Thrive'''

    thriveCards = {}
    thriveCards['WI13'] = [
        thriveContent('New Year, Fresh Start',
            #'Happy New Year! The new year is an opportunity to reflect on your aspirations for 2016.',
            'Happy New Year! The new year is an opportunity to reflect on your aspirations for 2016.',
            u'Finish this sentence: This year, I wish to ______. When you come to Mary Gates Hall this week \u2013 for advising, career coaching, or CLUE tutoring \u2013 share your aspirations on the board outside of First Year Programs (MGH 120), or using #ThriveUW.',
            [ link('New Year\u2019s Resolutions for College Students', 
                'http://collegelife.about.com/od/cocurricularlife/a/10-Sample-New-Years-Resolutions-For-College-Students.htm', True)
            ]
        ),
        thriveContent('Learn to Lead'),
        thriveContent('Activate your Activism'),
        None,
        thriveContent('Research smarter, not harder!'),
        thriveContent('Internships and Exploration'),
        thriveContent('Revisiting Plans, Exploring Options'),
        thriveContent('Battle the Winter Blues'),
        thriveContent('What\'s Your Dream Summer?'),
        thriveContent('Finals: Pace Your Prep'),
    ]
    thriveCards['SP13'] = [
        thriveContent('Keep Calm and Cherry On'),
        thriveContent('Springboard Your Sophomore Self'),
        thriveContent('Fail Forward'),
        thriveContent('People Power: Connections Count'),
        thriveContent('Research Made Easier'),
        thriveContent('Experience is Golden'),
        thriveContent('De-stress with Mindfulness'),
        thriveContent('Make the Most of Your Summer'),
        None,
        None,
        None,
        thriveContent('Celebrate Your Growth'),
    ]

    # XXX
    del thriveCards['SP13']
    #del thriveCards['WI13']

    ec = {}
    for key, value in thriveCards.items():
        startDate = ClassesBegin[key] - 1
        curDate = startDate
        for card in value:
            if card is not None:
                dr = myuwDateRange(curDate, curDate + 6)
                ec[dr] = card
            curDate = curDate + 7

    expectedContent = ec
