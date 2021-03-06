#!/usr/bin/python

import re

from selenium.common.exceptions import NoSuchElementException

from .functions import isCardVisible, packElement, formatDiffs, \
    rangesToSigDates, filterListVis
from .dates import *
from .classes import *
from .data import stuHuskyCardLink, empHuskyCardLink

# Dictionary of IDs to card classes
# This includes alternate names for cards
cardDict = {}


# Function to add something to this, automatically including all
# alternate names
def addToCardDict(card):
    '''Add a card class to the card dict.
    Can be used standalone or as a decorator. '''
    for name in card.getAllNames():
        cardDict[name] = card
    # Return the card so this function can be used as a decorator
    return card


# Set name property automatically, if not manually specified
def autoCardName(card):
    '''Set a card class's 'name' property based off its __name__.
    Can be used standalone or as a decorator. '''

    if not(hasattr(card, 'name')):
        card.name = card.__name__
    # Return the card so this function can be used as a decorator
    return card


# Does both of the above
def isaCard(innerClass):
    '''Sets a card class's name automatically with autoCardName,
    then adds it to the card dict.
    Can be used standalone or as a decorator. '''
    autoCardName(innerClass)
    addToCardDict(innerClass)
    return innerClass

# Shorthand versions of these
balanceLabels = {
    'Student Husky Card': 'stu',
    'Employee Husky Card': 'emp',
    'Resident Dining': 'din',
}


# Not going to do last transaction date, because it would vary based on
# when you view the page.
@isaCard
class HFSCard(myuwCard):
    '''Housing and Food Services card (husky card balances card)'''

    title = 'Husky Card & Dining'

    def __init__(self, balanceDict={},
                 addFundsUrl=stuHuskyCardLink, title=title):
        '''balanceDict should be provided in the form:
            {'stu' = '$123.45', 'emp' = '$0.00', 'fac' = '$9.87'},
        leaving out balances the user doesn't have.
        addFundsUrl can be supplied either as the exact URL, or as
        'emp' to automatically fill in the employee add funds URL. '''

        if addFundsUrl == 'emp':
            self.addFundsUrl = empHuskyCardLink
        else:
            self.addFundsUrl = addFundsUrl

        self.balanceDict = balanceDict

    @classmethod
    @packElement
    def fromElement(cls, e, date):
        titleEl = e.find_element_by_xpath('./div[@data-type="card"]/h3')
        titleText = titleEl.text

        # Find balances on the card
        balContainer = e.find_element_by_xpath(
            './/ul[@class="card_list"]'
        )
        balEls = balContainer.find_elements_by_xpath(
            './li/div'
        )
        balanceDict = {}
        for be in balEls:
            label = be.find_element_by_css_selector(
                'div.pull-left h4.card-badge-label').text
            balance = be.find_element_by_class_name('pull-right').text

            # Look up the shorthand version of the
            # account name (stu/emp/din).
            try:
                balanceId = balanceLabels[label]
            except KeyError:
                raise Exception('Unknown husky card balance %s' % label)

            balanceDict[balanceId] = balance

        # Find 'Add funds' link
        linkElement = e.find_element_by_xpath(
            './/div[@class="card-badge-action"]/a')
        linkUrl = linkElement.get_attribute('href')

        return cls(balanceDict, linkUrl, titleText)

    autoDiffs = {
        'title': 'HFS Card Title',
        'balanceDict': 'HFS Card Balances',
        'addFundsUrl': 'HFS Add Funds URL',
    }


# Student employee/instructor card
@isaCard
class EmpFacStudentCard(myuwCard):
    '''Employee/Faculty information card'''

    def __init__(self, stuEmp=False, instructor=False):
        '''stuEmp is whether or not they have the student employee part
        of the card, same for instructor. '''
        self.stuEmp = stuEmp
        self.instructor = instructor

    @classmethod
    @packElement
    def fromElement(cls, e, date):
        innerText = e.text
        stuEmp = 'Student Employees' in innerText
        instructor = 'Instructor or TA for a class' in innerText
        return cls(stuEmp, instructor)

    autoDiffs = {
        'stuEmp': 'Student Employee Section',
        'instructor': 'Instructor Section',
    }


@isaCard
class FutureQuarterCard(myuwCard):
    '''Future Quarter Card'''

    altNames = [
        'FutureQuarterCardA',
        'FutureQuarterCard1',
    ]

    def __init__(self, quarterData, ):
        '''Right now, FutureQuarterCard requires you to manually specify
        multiple instances of the card using cardCD in the expected data.
        Each one should have the future quarter data that is supposed to
        appear specifically at that time. This is easier than handling every
        possible case with summer terms in here.'''
        self.qtrs = quarterData

    @classmethod
    @packElement
    def fromElement(cls, e, date):
        qtrEls = e.find_elements_by_xpath('.//div[@data-name="FutureCard"]')
        qtrs = {}
        for qtrEl in qtrEls:
            titleEl = qtrEl.find_element_by_xpath('.//h4')
            qtrName = titleEl.text
            subElements = qtrEl.find_elements_by_xpath('.//p/span')
            creditsText, sectionsText = [el.text for el in subElements]
            credits_re = re.search('registered for (.*) credit', creditsText)
            credits = credits_re.groups()[0]
            sections = re.search('\((.*) section', sectionsText).groups()[0]
            credits = int(credits)
            sections = int(sections)

            qtrDict = {
                'credits': credits,
                'sections': sections
            }
            qtrs[qtrName] = qtrDict
        return cls(qtrs)

    autoDiffs = {'qtrs': 'Future Quarter Data'}


@isaCard
class SummerEFSCard(myuwCard):
    '''Critical Summer Reg info/Early Fall Start information card. '''
    def __init__(self, summerReg=True, considerEFS=True):
        '''summerReg and considerEFS refer to whether the user
        should see those parts of the card. '''
        self.sumReg = summerReg
        self.efs = considerEFS

    @classmethod
    @packElement
    def fromElement(cls, e, date):
        text = e.text
        sumReg = 'Review Critical Summer' in text
        efs = 'Consider Early Fall Start' in text
        return cls(sumReg, efs)

    autoDiffs = {
        'sumReg': 'Has Summer Reg Info section',
        'efs': 'Has EFS Section',
    }


@isaCard
class GradeCard(myuwCard):
    '''Final Grades Card'''

    noGradeStr = 'No grade yet\nX'

    def __init__(self, gradeDict):
        '''gradeDict is specified as a dictionary of the form:
            { 'WI13': {'PHYS 123': '4.0'} }
        All quarters should be specified in one expected card, and
        the card class figures out the rest for you. The grade should
        be specified as a string exactly as it appears.
        None is shorthand for No grade yet/X.'''
        for qtrGrades in gradeDict.values():
            for className, grade in qtrGrades.items():
                if grade is None:
                    qtrGrades[className] = self.noGradeStr

        self.gradeDict = gradeDict
        self.quarter = None
        self.visCheck = self.makeVisCheck()

    @classmethod
    @packElement
    def fromElement(cls, e, date):
        # We have to adjust the date a bit, since the final grades
        # card will appear a bit past the end of the quarter

        qtr = dateToQtr(date - 10)

        # Correct for large break between summer and autumn
        if 'AU' in qtr:
            qtr = dateToQtr(date - 40)

        # If it's past the last day of instruction for summer, that means
        # the grades displayed will include summer B/full grades.
        if 'SU' in qtr:
            if date >= LastDayInstr[qtr] + 1:
                qtr = 'SB13'
            else:
                qtr = 'SA13'

        qtrEls = e.find_elements_by_xpath('.//li[@class="clearfix"]')
        thisQtrDict = {}
        for el in qtrEls:
            leftEl = el.find_element_by_xpath('.//div[@class="pull-left"]')
            rightEl = el.find_element_by_xpath('.//div[@class="pull-right"]')
            className = leftEl.text
            classGrade = rightEl.text
            thisQtrDict[className] = classGrade

        qtrDict = {
            qtr: thisQtrDict
        }
        newObj = cls(qtrDict)
        newObj.quarter = qtr
        return newObj

    def getGradesForQuarter(self, qtr):
        '''Get the final grades for a specific quarter. Returns
        an empty dictionary if we don't have that quarter. '''
        try:
            grades = self.gradeDict[qtr]
        except KeyError:
            grades = {}
        return grades

    def findDiffs(self, other):
        '''Find quarter to compare, then compare data. '''
        diffs = ''
        trueQtr = self.quarter or other.quarter

        gradesA = self.getGradesForQuarter(trueQtr)
        gradesB = other.getGradesForQuarter(trueQtr)

        diffs += formatDiffs('Final grades', gradesA, gradesB)
        return diffs

    def makeVisCheck(self):
        '''Assemble a visCheck based on our expected data'''
        visChecks = []
        for gradesQtr in self.gradeDict.keys():
            short = gradesQtr[0:2]
            year = gradesQtr[2:4]

            if short in ('WI', 'AU', 'SP'):
                show = LastDayInstr[gradesQtr] + 1
                hide = NextQtrClassesBegin[gradesQtr]

            elif short == 'SA':
                show = SummerBTermBegins['SU' + year]
                hide = NextQtrClassesBegin['SU' + year]

            elif short == 'SB':
                show = LastDayInstr['SU' + year]
                hide = NextQtrClassesBegin['SU' + year]

            else:
                exStr = ('Invalid short quarter name %s from quarter %s.'
                         % (short, gradesQtr))
                raise Exception(exStr)

            visNew = visCD(show, hide)
            visChecks.append(visNew)

        visCheck = visUnion(*visChecks)
        return visCheck


class GradeCardDummy(GradeCard):
    '''Dummy version of the grade card that has quarters but no actual
    grades for them. Useful for wrapping with errorCard. '''
    def __init__(self, qtrs=['AU13', 'WI13', 'SP13', 'SA13', 'SB13']):
        gradeDict = {qtr: {} for qtr in qtrs}
        super(GradeCardDummy, self).__init__(gradeDict)


@isaCard
class RegStatusCard(myuwCard):
    '''Registration status card'''

    # quarters is the quarters that the reg card corresponds to, not the
    # quarters in which it should appear.
    def __init__(self, qtrs=[], holds=0, qtr=None, myplanContent=False,
                 date=None):
        self.qtrs = qtrs
        self.holds = holds
        self.qtr = qtr
        self.myplanContent = myplanContent
        self.date = date
        # If there are holds, card should always appear
        if holds:
            self.visCheck = visAlways

    @classmethod
    def fromElement(cls, e, date):

        title = e.find_element_by_tag_name('h3').text
        # Quarter = middle word of title
        # Year = last word
        titleSplit = title.split(' ')
        qtr = titleSplit[1]
        year = titleSplit[2]
        # Abbreviate to 2 letters
        qtr = qtr[0:2].upper()
        # Use last 2 digits
        year = year[2:4]
        # Assemble date of the form 'SU13'
        qtrString = qtr + year
        eleclasses = [
            'a.reg_disclosure',
            'a.reg_disclosure_summerA',
            'a.reg_disclosure_summer1',
            'a.show_reg_holds'
        ]
        for eleclass in eleclasses:
            try:
                banner = e.find_element_by_css_selector(eleclass)
                break
            except NoSuchElementException:
                continue
        else:
            return cls(holds=0, qtr=qtrString)

        bannerText = banner.text
        # Need to pull out x from "x holds"
        numHolds = int(bannerText.split(' ')[-2])

        hasMyplan = 'In MyPlan' in e.text

        return cls(holds=numHolds, qtr=qtrString, date=date,
                   myplanContent=hasMyplan)

    def shouldAppear(self, date):

        for qtr in self.qtrs:
            qtrShow = self.show[qtr]
            qtrHide = self.hide[qtr]

            if date in myuwDateRange(qtrShow, qtrHide):
                return True

        return False

    @classmethod
    def isPeakLoad(cls, date):
        return cls.loadPeriods(date)

    def findDiffs(self, other):
        peak = self.isPeakLoad(other.date)
        expVis = self.myplanContent
        actualVis = other.myplanContent

        if peak:
            if actualVis:
                diffs = 'Myplan content appeared during peak load time.\n'

            else:
                diffs = ''

        else:
            if actualVis and not expVis:
                diffs = 'Myplan content showed unexpectedly.\n'

            elif expVis and not actualVis:
                diffs = 'Myplan content did not show but was expected.\n'

            else:
                diffs = formatDiffs('Myplan content visibility',
                                    expVis,
                                    actualVis)

        diffs += super(RegStatusCard, self).findDiffs(other)
        return diffs

    show = RegCardShow
    hide = RegCardHide

    regVis = visAuto(RegPd1open, RegPd1end - 1)
    reg1days = regVis.allDays()
    # reg1days = RegPd1open.values() + (RegPd1open + 2).values()
    loadPairs = [(d - timedelta(minutes=30), d + timedelta(minutes=30)) for
                 d in reg1days]
    loadPeriods = visCDM(loadPairs)

    reg1sigDays = RegPd1open.values() + (RegPd1open + 2).values()
    # ugly
    sigDates = sum([[d - timedelta(minutes=35),
                     d - timedelta(minutes=25),
                     d + timedelta(minutes=25),
                     d + timedelta(minutes=35)]
                    for d in reg1sigDays], [])
    extraSigDates = sigDates

    """
    sigPairs = [(d - timedelta(minutes=30), d + timedelta(minutes=30)) for\
        d in reg1days]
    sigPeriods = visCDM(sigPairs)
    extraSigDates = sigPeriods.sigDates
    """

    visCheck = visAuto(RegCardShow, RegCardHide)

    autoDiffs = {
        'holds': 'Number of registration holds',
    }


@isaCard
class SummerRegStatusCard(RegStatusCard):
    '''Summer Registration Status card. Covers both the positions
    in which the card can appear. '''

    def __init__(self, **kwargs):
        kwargs['qtrs'] = ['SU13']
        super(SummerRegStatusCard, self).__init__(**kwargs)

    @classmethod
    def fromElement(cls, e, date):
        if getCardName(e) == 'SummerRegStatusCardA':
            pos = 'top'
        elif getCardName(e) == 'SummerRegStatusCard1':
            pos = 'bot'
        else:
            pos = 'invalid'

        # Need to un-classmethod this
        newCard = RegStatusCard.fromElement.__func__(cls, e, date)
        newCard.pos = pos
        # newCard.date = date
        return newCard

    name = 'SummerRegStatusCard'
    altNames = [
        'SummerRegStatusCardA',
        'SummerRegStatusCard1'
    ]

    def findDiffs(self, other):
        diffs = super(SummerRegStatusCard, self).findDiffs(other)
        expPos = 'top' if self.topCheck(other.date) else 'bot'
        diffs += formatDiffs('Summer Reg Card Position', expPos, other.pos)
        return diffs

    show = SummerRegShow
    hide = SummerRegHide

    visCheck = visAuto(SummerRegShow, SummerRegHide)
    topCheck = visAuto(SummerRegShow, SummerRegSwitch)

    extraSigDates = topCheck.significantDates

    """
    @property
    def significantDates(self):
        return self.visCheck.significantDates + self.topCheck.significantDates
        """


@isaCard
class CriticalInfoCard(myuwCard):
    '''Update Critical Info Card'''

    def __init__(self, email=True,
                 directory=True, residency=True):
        '''email: Set Up UW Email section
        directory: Update Student Directory section
        residency: Non-resident classification section'''
        self.email = email
        self.directory = directory
        self.residency = residency

    @classmethod
    @packElement
    def fromElement(cls, e, date):
        headers = e.find_elements_by_xpath('.//span[@class="notice-title"]')

        # Find section titles, compare to known values
        titles = [e.text for e in headers]

        email = 'Set Up UW Email' in titles
        directory = 'Update Student Directory' in titles
        residency = 'Non-Resident Classification' in titles

        return cls(email, directory, residency)

    autoDiffs = {
        'email': 'Set Up UW Email notice',
        'directory': 'Student Directory notice',
        'residency': 'Residency notice',
    }


@isaCard
class VisualScheduleCard(myuwCard):
    '''Visual Schedule Card. Does not encompass the final-exam-only VS,
    that's the FinalExamCard. '''

    def __init__(self, quartersDict=None):
        '''quartersDict is of the form:
            {'WI13': {'PHYS 123 A': None, 'PHYS 456 AC': None}}
        None is just a placeholder, there may be data such as room
        number there later. Expected data should define one instance
        of this card will all quarters.'''
        self.quartersDict = quartersDict
        self.quarter = None

    @classmethod
    @packElement
    def fromElement(cls, e, date):
        '''This fromElement method will return a NoCourseCard instead of a
        VisualScheduleCard if applicable. '''
        if checkNCC(e):
            return NoCourseCard()

        if 'Early Fall Start' in e.text:
            qtr = 'EFS'
        else:
            qtr = dateToTerm(date)
        classEls = e.find_elements_by_css_selector('div.visual-course-id')
        classEls += e.find_elements_by_css_selector('div.course-info')
        thisQtrClasses = {}
        for el in classEls:
            text = el.text
            if text:
                classInfo = None
                thisQtrClasses[text] = classInfo

        qtrDict = {
            qtr: thisQtrClasses
        }
        newObj = cls(qtrDict)
        newObj.quarter = qtr
        return newObj

    def getQtrInfo(self, qtr):
        if self.quartersDict is None:
            return {}
        else:
            return self.quartersDict.get(qtr)

    def findDiffs(self, other):
        trueQtr = self.quarter or other.quarter
        classesA = self.getQtrInfo(trueQtr)
        classesB = other.getQtrInfo(trueQtr)
        diffs = ''
        diffs = formatDiffs('Visual Schedule Content', classesA, classesB)
        return diffs

    visCheck = visAuto(FirstDayQtr, LastDayInstr + 1)

    def shouldAppear(self, date):
        # If the normal visibility function determines that the card
        # shouldn't appear, just go with that.
        if super(VisualScheduleCard, self).shouldAppear(date):
            # If the vis func says it should, then we still need to handle
            # the case where if it is summer but the user has no summer
            # classes, then the vis sched shouldn't appear.
            # badDateRange handles the dates with problems due to
            # spring deadline tomorrow thing
            badDateRange = myuwDateRange(
                LastDayQtr['SP13'],
                ClassesBegin['SU13']  # - 1
            )
            if date in badDateRange:
                return False
            else:
                # This is now a little smarter, it will automatically hide
                # itself if there are no classes for the current quarter
                term = dateToTerm(date)
                return term in self.quartersDict and bool(self.quartersDict)
        else:
            return False

    autoDiffs = {'quartersDict': 'Visual Schedule Classes'}


@isaCard
class FinalExamCard(myuwCard):
    '''Final exam card. Like VisualScheduleCard but is the
    finals-only version of it. Does not currently check any
    data.'''
    visCheck = visAuto(LastDayInstr + 1, BreakBegins, exclude=['SU'])
    # TODO: actually check data here

    @classmethod
    def fromElement(cls, e, date):
        '''Will return a NoCourseCard if applicable. '''
        if checkNCC(e):
            return NoCourseCard()

        return cls()


def checkNCC(e):
    '''Check if a card element is actually the NoCourseCard
    (No Registration Found; You don't appear to be registered)
    '''
    try:
        e.find_element_by_xpath('.//div[@data-name="NoCourseCard"]')
        return True
    except NoSuchElementException:
        return False


@isaCard
class LibraryCard(myuwCard):
    '''Library Account card'''
    pass
    # TODO: figure out what this card can display and write diffs accordingly


@isaCard
class TextbookCard(myuwCard):
    '''Textbooks card'''
    # TODO: check data
    visCheck = visUnion(
        visAuto(FirstDayQtr, ClassesBegin + 8, exclude=['SU13']),
        visCD(ClassesBegin['SU13'], ClassesBegin['SU13'] + 8)
    )


@isaCard
class GradCommitteeCard(myuwCard):
    '''Grad Committees Card'''
    def __init__(self, commDict):
        '''commDict is of the form:
        {'Doctoral Supervisory Committee': # one key for each committee
            [ # This list should have one dict for each member
                {
                    'dept': 'Anthropology',
                    'chair': True,
                    'rcc': True, # Reading committee chair
                    'gsr': True,
                    'name': u'John Doe',
                    'email' :123@test.com
                } # If chair/gsr/rcc are not specified, False is assumed
            ]
        }'''

        self.commDict = commDict

    autoDiffs = {'commDict': 'Grad Committee Members'}

    @classmethod
    def fromElement(cls, e, date):
        # Break into individual committees
        commSections = e.find_elements_by_xpath('.//ul[@class="card-list"]/li')
        commDict = {}
        for section in commSections:
            # Get committee name
            commName = section.find_element_by_xpath('./h4').text
            # Get committee members
            memberSections = section.find_elements_by_xpath(
                './ol/li[@class="committee-member"]')
            members = []
            for member in memberSections:
                memberLines = member.find_elements_by_xpath('./span')
                # Get text of each line
                memberDetails = [e.text for e in memberLines]
                memberDict = {}
                # Name is on the first line, along with committee role
                nameLine = memberDetails[0]
                nameParts = nameLine.split(', ')
                # First chunk before a comma (if any) is the name of the person
                memberDict['name'] = nameParts[0]
                # Anything after that is a role
                for role in nameParts[1:]:
                    if role == 'GSR':
                        memberDict['gsr'] = True
                    elif role == 'Reading Committee Member':
                        memberDict['rcm'] = True
                    elif role == 'Reading Committee Chair':
                        memberDict['rcc'] = True
                    elif role == 'Chair':
                        memberDict['chair'] = True

                # Other 2 lines are optional
                # If it contains @, consider it to be the email
                # Otherwise, consider it to be the department.
                for line in memberDetails[1:]:
                    if line.find('@') == -1:
                        memberDict['dept'] = line
                    else:
                        memberDict['email'] = line

                members.append(memberDict)

            commDict[commName] = members

        return cls(commDict)


# Do later
@isaCard
class GradStatusCard(myuwCard):
    '''Graduate Status Card. Encompasses petition, leave, and
    degree/exam requests. '''

    def __init__(self, petitions, leaves, degrees, date=None):
        '''petitions, leaves, degrees are lists of
        petRequest, leaveRequest, and degreeRequest instances,
        respectively. '''
        self.petitions = petitions
        self.leaves = leaves
        self.degrees = degrees
        self.date = date
        self.needsFiltering = not(date)

    @property
    def significantDates(self):
        sigDates = []
        for req in (self.petitions + self.leaves + self.degrees):
            sigDates += req.significantDates
        return sigDates

    # Shorthand replacements for longer strings
    replacements = {
        'Graduate School Decision': 'grad',
        'Department Recommendation': 'dept',
    }

    @classmethod
    @packElement
    def fromElement(cls, e, date):
        date = myuwDate(date)

        petEls, leaveEls, degreeEls =\
            [e.find_elements_by_xpath('.//div[@id="%s"]/ul/li/div' % el_id) for
             el_id in ('petition-reqs', 'leave-reqs', 'degree-reqs')]

        requestEls = petEls + leaveEls + degreeEls

        # Iterate through petitions
        petitions = cls.processRequests(petEls, petRequest)
        leaves = cls.processRequests(leaveEls, leaveRequest)
        degrees = cls.processRequests(degreeEls, degreeRequest)

        # Need to add date for data to be useful
        newObj = cls(petitions, leaves, degrees, date)
        return newObj

    @staticmethod
    def processRequests(reqEls, reqClass):
        '''For each reqEl, make a reqClass out of it using the reqClass's
        fromElement classmethod. '''
        return [reqClass.fromElement(reqEl) for reqEl in reqEls]

    # For the expected one, at the top level of each dictionary, rather than
    # specifying an item directly, you can specify
    def filterToDate(self, date):
        '''Returns a new GradStatusCard based on expected date which
        contains only the requests that should be visible on the
        specified date.
        Does not modify the original.'''
        petitions = filterListVis(self.petitions, date)
        leaves = filterListVis(self.leaves, date)
        degrees = filterListVis(self.degrees, date)

        newObj = GradStatusCard(petitions, leaves, degrees)
        newObj.needsFiltering = False
        return newObj

    autoDiffs = {
        'petitions': 'Petition Requests',
        'leaves':  'Leave Requests',
        'degrees': 'Degree Requests',
    }

    def findDiffs(self, other):
        # Filter the expected data based on the date specified in the
        # actual data, then compare them as we normally would using
        # autoDiffs.
        date = self.date or other.date
        if self.needsFiltering:
            self = self.filterToDate(date)
        if other.needsFiltering:
            other = other.filterToDate(date)

        return super(GradStatusCard, self).findDiffs(other)


@isaCard
class ThriveCard(myuwCard):
    '''Class for a Thrive card. This should never be an expected card.
    See thrive.ThriveCardExpected for that. '''
    def __init__(self, date=None, content=None):

        # Need to handle 3 scenarios:
        # 1. Actual card, in which case we get a date and a content
        #    Content is a thriveContent instance.
        # 2. Expected card list, in which case we get neither
        #    (See ThriveCardExpected class below)
        # 3. Any other combination, which raises an exception
        if date is None and content is None:
            self.actual = False

        elif date is not None and content is not None:
            self.actual = True
            self.content = content
            self.date = date

        else:
            raise Exception('Illegal arguments %s and %s for thrive card'
                            % (date, content))

    # Format: dateRange to card
    # ThriveCardExpected does this automatically based on mappings from
    # a quarter to a list of cards.
    expectedContent = {}

    def getExpected(self, date):
        for key, value in self.expectedContent.items():
            if date in key:
                return value
        return None

    def findDiffs(self, other):

        if self.actual and not(other.actual):
            actual = self
            expected = other
        elif other.actual and not(self.actual):
            actual = other
            expected = self
        else:
            raise Exception('Got two actual or two expected')

        date = actual.date

        expectedContent = expected.getExpected(date)
        actualContent = actual.content

        diffs = expectedContent.findDiffs(actualContent)
        return diffs

    @classmethod
    def fromElement(cls, e, date):
        h4s = e.find_elements_by_xpath('.//h4')
        title = h4s[0].text
        ps = e.find_elements_by_xpath('.//p')
        desc = ps[0].text
        tryThis = ps[1].text
        links = []
        for el in e.find_elements_by_xpath('.//ul/li/a'):
            links.append(link.fromElement(el))

        content = thriveContent(title, desc, tryThis, links)
        card = ThriveCard(date, content)
        return card

    def shouldAppear(self, date):
        for key in self.expectedContent.keys():
            if date in key:
                return True
        return False

    # Since the keys of the expected content dictionary are date ranges,
    # we can use rangesToSigDates to generate test dates.
    @property
    def significantDates(self):
        return rangesToSigDates(self.expectedContent.keys())


@isaCard
class CourseCards(myuwCard):
    '''Course Cards'''

    @classmethod
    @packElement
    def fromElement(cls, e, date):
        '''Can return a NoCourseCard'''
        if checkNCC(e):
            return NoCourseCard()

        return cls()


@isaCard
class NoCourseCard(myuwCard):
    '''No Course Card. Not called directly, rather it is created and
    returned in the fromElement methods of VisualScheduleCard and
    FinalExamCard.'''
    pass


class NoCourseCardAlt(NoCourseCard):
    '''No course card with alternate dates for spring gradesub stuff. '''
    visCheck = visAlways - visCD('2013-6-19', '2013-6-24')


@isaCard
class uwemail(myuwCard):

    def __init__(self, emailType=None):
        # if emailType is None:
        #   raise AssertionError('emailType must be specified')

        self.emailType = emailType

    @classmethod
    def fromElement(cls, e, date):

        if 'Gmail' in e.text:
            emailType = 'gmail'

        elif 'Outlook' in e.text:
            emailType = 'outlook'

        else:
            emailType = None
            # raise AssertionError("Didn't find a known email type")

        return cls(emailType=emailType)

    autoDiffs = {'emailType': 'Email Type'}

gmail = uwemail('gmail')
outlook = uwemail('outlook')


# Simple cards that have fixed content as well
# as cards that simply aren't done yet.
stubCards = [
    'TuitionCard',
    'EventsCard',
    'PCEBanner',
    'app_notices',
    'app_acal',
    'ToRegisterCard',
    'InternationalStuCard',
    'ThankYouCard',
]


class stubCard(myuwCard):
    '''Class for quickly generating simple cards'''
    pass


def mkStub(name):
    '''Function for creating stub card classes'''

    docstring = 'Stub card class for card "%s"' % name
    return type(name, (stubCard, ), {'__doc__': docstring})


for cardName in stubCards:

    newCardClass = mkStub(cardName)
    globals()[cardName] = newCardClass
    # isaCard modifies in place so we don't care about its return.
    isaCard(newCardClass)


del newCardClass


class UnknownCardError(KeyError):
    def __init__(self, cardName):
        super(UnknownCardError, self).__init__(
            'Error: Card with name %s unknown' % cardName
        )


def getCardClass(cardName):
    try:
        return cardDict[cardName]
    except KeyError:
        raise UnknownCardError(cardName)


def cardIsError(el):
    return 'An error has occurred' in el.text


def cardFromElement(el, date):
    '''Automatically make a card from a WebElement'''

    cardName = getCardName(el)

    if isCardVisible(el):

        if cardIsError(el):

            try:
                baseCardName = getCardClass(cardName).name

            except UnknownCardError:
                baseCardName = cardName

            newCard = errorCard(baseCardName)

        else:

            cardClass = getCardClass(cardName)
            newCard = cardClass.fromElement(el, date)

            if newCard is None:
                raise Exception('%s.fromElement returned None' % cardClass)
            baseCardName = newCard.name

        retval = {baseCardName: newCard}
        return retval

    else:
        return {}
