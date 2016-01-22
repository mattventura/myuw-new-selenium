#!/usr/bin/python

from myuwFunctions import isCardVisible, packElement, formatDiffs, \
rangesToSigDates
from myuwDates import *
import re
from myuwClasses import *

from selenium.common.exceptions import NoSuchElementException


# Dictionary of IDs to card classes
# This includes alternate names for cards
cardDict = {}
# Function to add something to this, automatically including all
# alternate names
def addToCardDict(card):
    for name in card.getAllNames():
        # On second thought, we might want duplicates
        #if name in cardDict:
        #    raise Exception('Tried to put card name %s into known cards list twice' %name)
        cardDict[name] = card
    # Return the card so this function can be used as a decorator
    return card

# Set name property automatically, if not manually specified
def autoCardName(card):
    if not(hasattr(card, 'name')):
        card.name = card.__name__

# Convenience all-in-one function for specifying a card. 
# 1. Puts them in the dictionary of cards. 
# 2. Automatically sets the name property of the class if not already set. 
# Because it modifies the class in-place rather than returning a new object, 
# if you want to use it in non-decorator form you can do isaCard(foo) rather than
# foo = isaCard(foo). 
def isaCard(innerClass):
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

# If a and b are different, write a message using
# 'label' to describe what component is different

# TODO: last transaction date
@isaCard
class HFSCard(myuwCard):
    
    title = 'Husky Card & Dining'

    def __init__(self, balanceDict = {}, 
        addFundsUrl = stuHuskyCardLink, title = title):

        if addFundsUrl == 'emp':
            self.addFundsUrl = empHuskyCardLink
        else:
            self.addFundsUrl = addFundsUrl

        # TODO: make this better
        self.balanceDict = balanceDict

        try:
            self.stuBalance = balanceDict['stu']
        except KeyError:
            self.stuBalance = None

        try:
            self.empBalance = balanceDict['emp']
        except KeyError:
            self.empBalance = None

        try:
            self.dinBalance = balanceDict['din']
        except KeyError:
            self.dinBalance = None

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
    
    # Takes two arguments, whether they have the student
    # employee part of the card, and whether they have
    # the instructor part of the card
    def __init__(self, stuEmp = False, instructor = False):
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

    altNames = [
        'FutureQuarterCardA',
        'FutureQuarterCard1',
    ]

    def __init__(self, quarterData, ):
        self.qtrs = quarterData
            

    @classmethod
    @packElement
    def fromElement(cls, date, e):
        qtrEls = e.find_elements_by_xpath('.//div[@data-name="FutureCard"]')
        qtrs = {}
        for qtrEl in qtrEls:
            #try:
            titleEl = qtrEl.find_element_by_xpath('.//h4')
            qtrName = titleEl.text
            subElements = qtrEl.find_elements_by_xpath('.//p/span')
            creditsText, sectionsText = [el.text for el in subElements]
            credits = re.search('registered for (.*) credit', creditsText).groups()[0]
            sections = re.search('\((.*) section', sectionsText).groups()[0]
            credits = int(credits)
            sections = int(sections)
            #except:
            #    raise Exception('Could not parse future quarter cards')

            qtrDict = {
                'credits': credits,
                'sections': sections
            }
            qtrs[qtrName] = qtrDict
        return cls(qtrs)

    #autoDiffs = {'qtrs': 'Future Quarter Data'}

@isaCard
class SummerEFSCard(myuwCard):
    def __init__(self, summerReg = True, considerEFS = True):
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

    noGradeStr = 'No grade yet\nX'

    def __init__(self, gradeDict):
        # Use None as a shortcut for the "No grade yet" text 
        # defined above. 
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
        try:
            grades = self.gradeDict[qtr]
        except:
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
        



    dateRanges = getMultiDateRange(LastDayInstr + 1, NextQtrClassesBegin - 1, exclude = ['SU'])
    visCheck = visCDM(dateRanges)
    #significantDates = rangesToSigDates(dateRanges)
    #visCheck = visAuto(LastDayInstr + 1, NextQtrClassesBegin - 1)
        
    
    
@isaCard
class SummerRegStatusCard(myuwCard):
    
    altNames = [
        'SummerRegStatusCardA',
        'SummerRegStatusCard1'
    ]

@isaCard
class CriticalInfoCard(myuwCard):
    
    def __init__(self, email = True,
        directory = True, residency = True):
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
    pass

@isaCard
class VisualScheduleCard(myuwCard):
    
    #altNames = ['FinalExamCard']
    def __init__(self, quartersDict = None):
        # TODO
        self.quartersDict = quartersDict
        self.quarter = None

    @classmethod
    @packElement
    def fromElement(cls, date, e):
        if checkNCC(e):
            return NoCourseCard()
            
        qtr = dateToTerm(date)
        #qtr = dateToQtr(date + 1)
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

    dateRanges = getMultiDateRange(FirstDayQtr, LastDayInstr)
    #dateRanges = getMultiDateRange(FirstDayQtr, LastDayInstr, exclude = ['SU13'])
    # Fix for 'SP13 grade sub deadline is always tomorrow' thing
    #dateRanges.append(dateRange(ClassesBegin['SU13'], ClassesBegin['SU13'] + 6))
    visCheck = visCDM(dateRanges)
    #significantDates = rangesToSigDates(dateRanges)

    '''
    def shouldAppear(self, date):
        # If the normal visibility function determines that the card shouldn't appear,
        # just go with that. 
        if super(self.__class__, self).shouldAppear(date):
            # If the vis func says it should, then we still need to handle the case where
            # if it is summer but the user has no summer classes, then the vis sched
            # shouldn't appear. 
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
    '''

    autoDiffs = {'quartersDict': 'Visual Schedule Classes'}
        

# TODO: Final exam card 

@isaCard
class LibraryCard(myuwCard):
    
    pass
    # TODO: figure out what this card can display
    #def __init__(self):
        
    
@isaCard
class TextbookCard(myuwCard):
    #visCheck = visAuto(FirstDayQtr, ClassesBegin)
    dateRanges = getMultiDateRange(FirstDayQtr, ClassesBegin + 6, exclude = ['SU13'])
    # Fix for 'SP13 grade sub deadline is always tomorrow' thing
    dateRanges.append(myuwDateRange(ClassesBegin['SU13'], ClassesBegin['SU13'] + 6))
    visCheck = visCDM(dateRanges)

@isaCard
class GradCommitteeCard(myuwCard):
    def __init__(self, commDict):
        self.commDict = commDict
    
    autoDiffs = {'commDict': 'Grad Committee Members'}

    @classmethod
    def fromElement(cls, date, el):
        # Brak into individual committees
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
    
    def __init__(self, petitions, leaves, degrees, date = None):
        self.petitions = petitions
        self.leaves = leaves
        self.degrees = degrees
        self.date = date
        self.needsFiltering = not(date)

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
        # TODO: need to find a way to get the date in here
        # We'll just use a special version in fromElements that adds in date stuff
        petitions = cls.processRequests(petEls, petRequest)
        leaves = cls.processRequests(leaveEls, leaveRequest)
        degrees = cls.processRequests(degreeEls, degreeRequest)

        newObj = cls(petitions, leaves, degrees, date)
        return newObj


    
    @staticmethod
    def processRequests(reqEls, reqClass):
        reqsOut = []
        for reqEl in reqEls:
            req = reqClass.fromElement(reqEl)
            reqsOut.append(req)
        return reqsOut
        

    # For the expected one, at the top level of each dictionary, rather than specifying an
    # item directly, you can specify 
    def filterToDate(self, date):
        petitions = self.filterList(self.petitions, date)
        leaves = self.filterList(self.leaves, date)
        degrees = self.filterList(self.degrees, date)

        newObj = self.__class__(petitions, leaves, degrees)
        newObj.needsFiltering = False
        return newObj

    # Returns a new dictionary returning only the visible items from the original
    @staticmethod
    def filterList(old, date):
        new = []
        for req in old:
            if req.shouldAppear(date):
                new.append(req)
        return new

    
    autoDiffs = {
        'petitions'    : 'Petition Requests',
        'leaves'        : 'Leave Requests',
        'degrees'    : 'Degree Requests',
    }

    def findDiffs(self, other):
        date = self.date or other.date
        if self.needsFiltering:
            self = self.filterToDate(date)
        if other.needsFiltering:
            other = other.filterToDate(date)

        return super(self.__class__, self).findDiffs(other)

class thriveContent(autoDiff):
    @uesc
    def __init__(self, title, desc = '', tryThis = '', links = []):
        
        self.title = title
        self.desc = desc
        self.tryThis = tryThis
        self.links = links

    # Temporary
    #def findDiffs(self, other):
    #    return ''

    autoDiffs = {
        'title': 'Thrive card title',
        #'desc': 'Thrive card first section',
        #'tryThis': 'Thrive card "Try This" section',
        #'links': 'Thrive card links'
    }


@isaCard
class ThriveCard(myuwCard):
    def __init__(self, date = None, content = None):
        
        # Need to handle 3 scenarios:
        # 1. Actual card, in which case we get a date and a content
        # 2. Expected card list, in which case we get neither
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

# TODO: move this to its own file
class ThriveCardExpected(ThriveCard):
    
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

@isaCard
class FinalExamCard(myuwCard):
    #visCheck = visAuto(FirstDayQtr, ClassesBegin)
    dateRanges = getMultiDateRange(LastDayInstr + 1, BreakBegins - 1, exclude = ['SU'])
    visCheck = visCDM(dateRanges)
    #significantDates = rangesToSigDates(dateRanges)

    @classmethod
    def fromElement(cls, date, e):
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
class CourseCard(myuwCard):
    

    @classmethod
    @packElement
    def fromElement(cls, date, e):
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
    'NoCourseCard',
    'ToRegisterCard',
    'LibraryCard',
    'CourseCard',
    'InternationalStuCard',
]

for cardName in stubCards:

    vars()[cardName] = newCardClass = type(cardName, (myuwCard, ), {})
    # isaCard modifies in place so we don't care about its return. 
    isaCard(newCardClass)

del newCardClass
