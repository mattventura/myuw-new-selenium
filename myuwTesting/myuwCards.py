#!/usr/bin/python

from .myuwFunctions import isCardVisible, packElement, formatDiffs, \
rangesToSigDates, filterListVis
from .myuwDates import *
import re
from .myuwClasses import *

from selenium.common.exceptions import NoSuchElementException

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

# TODO: Move these somewhere else
stuHuskyCardLink = 'https://www.hfs.washington.edu/olco/Secure/AccountSummary.aspx'
empHuskyCardLink = 'fill me in'

# Shorthand versions of these
balanceLabels = {
    'Student Husky Card': 'stu',
    'Employee Husky Card': 'emp',
    'Resident Dining': 'din',
}

# TODO: last transaction date
@isaCard
class HFSCard(myuwCard):
    '''Housing and Food Services card (husky card balances card)'''

    title = 'Husky Card & Dining'

    def __init__(self, balanceDict = {}, 
        addFundsUrl = stuHuskyCardLink, title = title):
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
    def fromElement(cls, date, e):
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
                raise Exception('Unknown husky card balance %s' %label)

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
    
    def __init__(self, stuEmp = False, instructor = False):
        '''stuEmp is whether or not they have the student employee part
        of the card, same for instructor. '''
        self.stuEmp = stuEmp
        self.instructor = instructor

    @classmethod
    @packElement
    def fromElement(cls, date, e):
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
    def fromElement(cls, date, e):
        qtrEls = e.find_elements_by_xpath('.//div[@data-name="FutureCard"]')
        qtrs = {}
        for qtrEl in qtrEls:
            titleEl = qtrEl.find_element_by_xpath('.//h4')
            qtrName = titleEl.text
            subElements = qtrEl.find_elements_by_xpath('.//p/span')
            creditsText, sectionsText = [el.text for el in subElements]
            credits = re.search('registered for (.*) credit', creditsText).groups()[0]
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
    def __init__(self, summerReg = True, considerEFS = True):
        '''summerReg and considerEFS refer to whether the user
        should see those parts of the card. '''
        self.sumReg = summerReg
        self.efs = considerEFS

    @classmethod
    @packElement
    def fromElement(cls, date, e):
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
                if grade == None:
                    qtrGrades[className] = self.noGradeStr

        self.gradeDict = gradeDict
        self.quarter = None

    @classmethod
    @packElement
    def fromElement(cls, date, e):
        # We have to adjust the date a bit, since the final grades
        # card will appear a bit past the end of the quarter
        qtr = dateToQtr(date - 10)
        if qtr.startswith('SU'):
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
        diffs = ''
        trueQtr = self.quarter or other.quarter
            
        gradesA = self.getGradesForQuarter(trueQtr)
        gradesB = other.getGradesForQuarter(trueQtr)

        diffs += formatDiffs('Final grades', gradesA, gradesB)
        return diffs

    def shouldAppear(self, date):
        if super(self.__class__, self).shouldAppear(date):
            return True

        year = date.shortYear
        hasSummerAGrades = ('SA' + str(year)) in self.gradeDict
        summerAGradeDates = getMultiDateRange(SummerBTermBegins, NextQtrClassesBegin - 1)
        inDateRange = False
        for dr in summerAGradeDates:
            if date in dr:
                inDateRange = True
        
        if hasSummerAGrades and inDateRange:
            return True
        else:
            return False

    visCheck = visAuto(LastDayInstr + 1, NextQtrClassesBegin - 1, exclude = ['SU'])

@isaCard
class SummerRegStatusCard(myuwCard):
    '''Summer Registration Status card. Covers both the positions
    in which the card can appear. '''
    
    altNames = [
        'SummerRegStatusCardA',
        'SummerRegStatusCard1'
    ]

@isaCard
class CriticalInfoCard(myuwCard):
    '''Update Critical Info Card'''
    
    def __init__(self, email = True,
        directory = True, residency = True):
        '''email: Set Up UW Email section
        directory: Update Student Directory section
        residency: Non-resident classification section'''
        self.email = email
        self.directory = directory
        self.residency = residency

    @classmethod
    @packElement
    def fromElement(cls, date, e):
        headers = e.find_elements_by_xpath('.//span[@class="notice-title"]')

        # Find section titles, compare to known values
        titles = [e.text for e in headers]

        email = 'Set Up UW Email' in titles
        directory = 'Update Student Directory' in titles
        residency = 'Non-Resident Classification' in titles

        newObj = cls(email, directory, residency)
        return newObj

    autoDiffs = {
        'email': 'Set Up UW Email notice',
        'directory': 'Student Directory notice',
        'residency': 'Residency notice',
    }

@isaCard
class NoCourseCard(myuwCard):
    '''No Course Card. Not called directly, rather it is created 
    and returned in the fromElement methods of VisualScheduleCard 
    and FinalExamCard.'''
    visCheck = visAuto(FirstDayQtr, FinalsEnd)
    pass

class NoCourseCardGrad(myuwCard):
    '''Possible different version for grads?'''
    name = 'NoCourseCard'
    visCheck = visAuto(FirstDayQtr, FinalsEnd, exclude = ['SU']) \
        + visCD(ClassesBegin['SU13'], LastDayInstr['SU13'])
    

@isaCard
class VisualScheduleCard(myuwCard):
    '''Visual Schedule Card. Does not encompass the final-exam-only VS, 
    that's the FinalExamCard. '''
    
    def __init__(self, quartersDict = None):
        '''quartersDict is of the form:
            {'WI13': {'PHYS 123 A': None, 'PHYS 456 AC': None}}
        None is just a placeholder, there may be data such as room
        number there later. Expected data should define one instance
        of this card will all quarters.'''
        self.quartersDict = quartersDict
        self.quarter = None

    @classmethod
    @packElement
    def fromElement(cls, date, e):
        '''This fromElement method will return a NoCourseCard instead of a 
        VisualScheduleCard if applicable. '''
        if checkNCC(e):
            return NoCourseCard()
            
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
        if self.quartersDict == None:
            return {}
        else:
            try:
                classes = self.quartersDict[qtr]
                return classes
            except KeyError:
                return None

    def findDiffs(self, other):
        trueQtr = self.quarter or other.quarter
        classesA = self.getQtrInfo(trueQtr)
        classesB = other.getQtrInfo(trueQtr)
        diffs = ''
        diffs = formatDiffs('Visual Schedule Content', classesA, classesB)
        return diffs

    visCheck = visAuto(FirstDayQtr, LastDayInstr)

    def shouldAppear(self, date):
        # If the normal visibility function determines that the card shouldn't appear,
        # just go with that. 
        if super(self.__class__, self).shouldAppear(date):
            # If the vis func says it should, then we still need to handle the case where
            # if it is summer but the user has no summer classes, then the vis sched
            # shouldn't appear. 
            # badDateRange handles the dates with problems due to 
            # spring deadline tomorrow thing
            badDateRange = myuwDateRange(
                LastDayQtr['SP13'],
                ClassesBegin['SU13'] - 1
            )
            if date in badDateRange:
                return False
            else:
                return True
        else:
            return False

    autoDiffs = {'quartersDict': 'Visual Schedule Classes'}

@isaCard
class FinalExamCard(myuwCard):
    '''Final exam card. Like VisualScheduleCard but is the 
    finals-only version of it. Does not currently check any
    data.'''
    visCheck = visAuto(LastDayInstr + 1, BreakBegins - 1, exclude = ['SU'])
    #TODO: actually check data here
    @classmethod
    def fromElement(cls, date, e):
        '''Will return a NoCourseCard if applicable. '''
        if checkNCC(e):
            return NoCourseCard()

        return cls()

def checkNCC(e):
    '''Check if a card is actually the NoCourseCard
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
        visAuto(FirstDayQtr, ClassesBegin + 6, exclude = ['SU13']), 
        visCD(ClassesBegin['SU13'], ClassesBegin['SU13'] + 6)
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
    def fromElement(cls, date, el):
        # Break into individual committees
        commSections = el.find_elements_by_xpath('.//ul[@class="card-list"]/li')
        commDict = {}
        for section in commSections:
            # Get committee name
            commName = section.find_element_by_xpath('./h4').text
            # Get committee members
            memberSections = section.find_elements_by_xpath('./ol/li[@class="committee-member"]')
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
    
    def __init__(self, petitions, leaves, degrees, date = None):
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
    def fromElement(cls, date, el):
        date = myuwDate(date)

        petEls = el.find_elements_by_xpath('.//div[@id="petition-reqs"]/ul/li/div')
        leaveEls = el.find_elements_by_xpath('.//div[@id="leave-reqs"]/ul/li/div')
        degreeEls = el.find_elements_by_xpath('.//div[@id="degree-reqs"]/ul/li/div')

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
        reqsOut = []
        for reqEl in reqEls:
            req = reqClass.fromElement(reqEl)
            reqsOut.append(req)
        return reqsOut

    # For the expected one, at the top level of each dictionary, rather than specifying an
    # item directly, you can specify 
    def filterToDate(self, date):
        '''Returns a new GradStatusCard based on expected date which
        contains only the requests that should be visible on the 
        specified date. 
        Does not modify the original.'''
        petitions = filterListVis(self.petitions, date)
        leaves = filterListVis(self.leaves, date)
        degrees = filterListVis(self.degrees, date)

        newObj = self.__class__(petitions, leaves, degrees)
        newObj.needsFiltering = False
        return newObj

    autoDiffs = {
        'petitions'    : 'Petition Requests',
        'leaves'        : 'Leave Requests',
        'degrees'    : 'Degree Requests',
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

        return super(self.__class__, self).findDiffs(other)

@isaCard
class ThriveCard(myuwCard):
    '''Class for a Thrive card. 
    This should never be an expected card. See ThriveCardExpected. '''
    def __init__(self, date = None, content = None):
        
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
            raise Exception('Illegal arguments %s and %s for thrive card' %(date, content))

    # Format: dateRange to card
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
    def fromElement(cls, date, e):
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

    @property
    def significantDates(self):
        return rangesToSigDates(self.expectedContent.keys())


@isaCard
class CourseCard(myuwCard):
    '''Course Cards'''

    altNames = ['CourseCards']

    @classmethod
    @packElement
    def fromElement(cls, date, e):
        '''Can return a NoCourseCard'''
        if checkNCC(e):
            return NoCourseCard()

        return cls()

# Simple cards that have fixed content as well
# as cards that simply aren't done yet. 
stubCards = [
    'TuitionCard', 
    'EventsCard',
    'RegStatusCard',
    'PCEBanner',
    'app_notices',
    'app_acal',
    'ToRegisterCard',
    'InternationalStuCard',
]

class stubCard(myuwCard):
    pass

def mkStub(name):
    return type(name, (stubCard, ), {})

for cardName in stubCards:
    newCardClass = mkStub(cardName)
    globals()[cardName] = newCardClass
    # isaCard modifies in place so we don't care about its return. 
    isaCard(newCardClass)

del newCardClass
