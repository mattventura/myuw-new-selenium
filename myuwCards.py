#!/usr/bin/python

from myuwFunctions import isCardVisible, packElement, formatDiffs
from myuwDates import dateToQtr
import re
from myuwClasses import myuwCard

#class hiddenCard(object):
#    def __init__(self, name):
#        self.name = name
#    visible = False



    


# Dictionary of IDs to card classes
# This includes alternate names for cards
cardDict = {}

# Convenience function for specifying a card. 
# Puts them in the dictionary of cards. Also automatically
# sets the name property of the class if not already set. 
def isaCard(innerClass):
    if not(hasattr(innerClass, 'name')):
        innerClass.name = innerClass.__name__
    for name in innerClass.getAllNames():
        cardDict[name] = innerClass
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
        balancesContainer = e.find_element_by_xpath(
            './/ul[@class="card_list"]')
        balancesElements = balancesContainer.find_elements_by_xpath(
            './li/div')
        balanceDict = {}
        for be in balancesElements:
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
'''
    def findDiffs(self, other):
        diffs = ''
        diffs += formatDiffs(
            'HFS card title',
            self.title,
            other.title
        )
        diffs += formatDiffs(
            'HFS balances',
            self.balanceDict,
            other.balanceDict
        )
        diffs += formatDiffs(
            'HFS add funds url', 
            self.addFundsUrl, 
            other.addFundsUrl
        )
        return diffs
        '''


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
'''
    def findDiffs(self, other):
        diffs = ''
        diffs += formatDiffs(
            'Has Student Employee section',
            self.stuEmp,
            other.stuEmp
        )
        diffs += formatDiffs(
            'Has Instructor/TA section', 
            self.instructor, 
            other.instructor
        )
        return diffs
'''

@isaCard
class FutureQuarterCard(myuwCard):

    altNames = [
        'FutureQuarterCardA',
        'FutureQuarterCard1',
    ]

    def __init__(self, quarterData):
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

    autoDiffs = {'qtrs': 'Future Quarter Data'}
    '''
    def findDiffs(self, other):
        diffs = ''
        diffs += formatDiffs('Future Quarter Data', self.qtrs, other.qtrs)
        return diffs
    '''

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


    def findDiffs(self, other):
        diffs = ''
        trueQtr = self.quarter or other.quarter
        try:
            gradesA = self.gradeDict[trueQtr]
        except:
            pass
            #TODO: write better exceptions here
            #raise Exception("gradesA problem")
        try:
            gradesB = other.gradeDict[trueQtr]
        except:
            pass
            #raise Exception("gradesB problem")

        diffs += formatDiffs('Final grades', gradesA, gradesB)
        return diffs
        
    
    
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
    #def findDiffs(self, other):
    #    diffs = ''
    #    diffs += formatDiffs('Set Up UW Email notice', self.email, other.email)
    #    diffs += formatDiffs('Student Directory notice', self.directory, other.directory)
    #    diffs += formatDiffs('Residency notice', self.residency, other.residency)
    #    return diffs
        

# Simple cards that have fixed content as well
# as cards that simply aren't done yet. 
stubCards = [
    'VisualScheduleCard',
    'TuitionCard', 
    'EventsCard',
    'GradCommitteeCard',
    'GradStatusCard',
    'TextbookCard',
    'RegStatusCard',
    'FinalExamCard',
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
    
    # Can't just do @isaCard because __name__ isn't set until
    # after the class is created
    class newCardClass(myuwCard):
        pass
    newCardClass.__name__ = cardName
    isaCard(newCardClass)
    vars()[cardName] = newCardClass

del newCardClass
