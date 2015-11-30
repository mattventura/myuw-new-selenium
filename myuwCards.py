#!/usr/bin/python

from myuwFunctions import isCardVisible, dateToQtr
import re

#class hiddenCard(object):
#    def __init__(self, name):
#        self.name = name
#    visible = False

# Generic card class
class myuwCard(object):
    # Placeholder values to help identify cases where the 
    # required info was not given
    # Title is only meaningful if there is an actual
    # title on the card. 
    #title = 'FIX ME'
    # Name is the id of the card's <div>
    #name = 'FixMeCard'
    # Create a new object of the specified type from
    # a selenium element. 
    # For cards that have variable content, this behavior 
    # needs to be overridden in each card. 
    @classmethod
    def fromElement(cls, date, cardEl):
        return cls()

    #@classmethod
    #def fromElementVisible(cls, e):

    def findDiffs(self, other):
        return ''

    def __eq__(self, other):
        return not(self.findDiffs(other))
    
    altNames = []

    @classmethod
    def getAllNames(cls):
        return [cls.name] + cls.altNames[:]

    @property
    def allNames(self):
        return [self.name] + self.altNames[:]

cardDict = {}

# Laziness function for making card classes easier
# Puts them in the dictionary of cards. Also automatically
# sets the name property of the class if not already set. 
def isaCard(innerClass):
    if not(hasattr(innerClass, 'name')):
        innerClass.name = innerClass.__name__
    for name in innerClass.getAllNames():
        cardDict[name] = innerClass
    return innerClass

# Pack the element argument of a function into the resultant object
# for debugging purposes. 
def packElement(func):
    def inner(cls, date, e):
        newCardInstance = func(cls, date, e)
        newCardInstance.originalElement = e
        return newCardInstance
    return inner
    


stuHuskyCardLink = 'https://www.hfs.washington.edu/olco/Secure/AccountSummary.aspx'
empHuskyCardLink = 'fill me in'

balanceLabels = {
    'Student Husky Card': 'stu',
    'Employee Husky Card': 'emp',
    'Resident Dining': 'din',
}

def formatDiffs(label, a, b):
    if a == b:
        return ''
    else:
        outStr = 'Different %s (%s vs %s)\n' %(label, a, b)
        return outStr

# TODO: last transaction date
@isaCard
class HFSCard(myuwCard):
    
    title = 'Husky Card & Dining'
    #name = 'HFSCard'

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

        balancesContainer = e.find_element_by_xpath('.//ul[@class="card_list"]')
        balancesElements = balancesContainer.find_elements_by_xpath('./li/div')
        balanceDict = {}
        for be in balancesElements:
            label = be.find_element_by_css_selector('div.pull-left h4.card-badge-label').text
            balance = be.find_element_by_class_name('pull-right').text

            try: 
                balanceId = balanceLabels[label]
            except KeyError:
                raise Exception('Unknown husky card balance %s' %label)

            balanceDict[balanceId] = balance

        linkElement = e.find_element_by_xpath('.//div[@class="card-badge-action"]/a')
        linkUrl = linkElement.get_attribute('href')

        return cls(balanceDict, linkUrl, titleText)

    def findDiffs(self, other):
        diffs = ''
        diffs += formatDiffs('HFS card title', self.title, other.title)
        diffs += formatDiffs('HFS balances', self.balanceDict, other.balanceDict)
        diffs += formatDiffs('HFS add funds url', self.addFundsUrl, other.addFundsUrl)
        return diffs


# Student employee/instructor card
@isaCard
class EmpFacStudentCard(myuwCard):
    
    #title = 'Student Employee/Instructor Card'
    #name = 'EmpFacStudentCard'

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

    def findDiffs(self, other):
        diffs = ''
        diffs += formatDiffs('Has Student Employee section', self.stuEmp, other.stuEmp)
        diffs += formatDiffs('Has Instructor/TA section', self.instructor, other.instructor)
        return diffs


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

    def findDiffs(self, other):
        diffs = ''
        diffs += formatDiffs('Future Quarter Data', self.qtrs, other.qtrs)
        return diffs

@isaCard
class CriticalInfoCard(myuwCard):
    pass

@isaCard
class ToRegisterCard(myuwCard):
    pass

@isaCard
class LibraryCard(myuwCard):
    pass

@isaCard
class CourseCard(myuwCard):
    pass

@isaCard
class GradStatusCard(myuwCard):
    pass

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

    def findDiffs(self, other):
        diffs = ''
        diffs += formatDiffs('Has Summer Reg Info section', self.sumReg, other.sumReg)
        diffs += formatDiffs('Has EFS section', self.efs, other.efs)

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
        'SummerRegStatusCardB'
    ]

# Cards that I haven't done yet, so just generate these quickly
# This can also be used for cards which really have nothing to test
# on them other than visibility. 

stubCards = [
    'VisualScheduleCard',
    'TuitionCard', 
    'EventsCard',
    'GradCommitteeCard',
    'TextbookCard',
    'RegStatusCard',
    'FinalExamCard',
    'PCEBanner',
    'app_notices',
    'app_acal',
]

for cardName in stubCards:
    
    #@isaCard
    class newCardClass(myuwCard):
        pass
    newCardClass.__name__ = cardName
    isaCard(newCardClass)
    vars()[cardName] = newCardClass

del newCardClass
