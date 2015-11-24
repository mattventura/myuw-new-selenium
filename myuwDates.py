#!/usr/bin/python

from myuwClasses import multiDate, myuwDate


# First day of classes
ClassesBegin = multiDate({
    'WI13': '2013-01-07',
    'SP13': '2013-04-01',
})

# Day when myuw switches quarter, 
# also day after grade sub deadline. 
FirstDayQtr = multiDate({
    'WI13': '2013-01-01',
    'SP13': '2013-03-27',
})

# Day before myuw switches quarter,
# also grade sub deadline. 
LastDayQtr = multiDate({
    'WI13': '2013-03-27', 
    'SP13': '2013-06-19',
})

# Reg period 1 begin
RegPd1 = multiDate({
    'WI13': '2013-02-15',
    'SP13': '2013-04-15',
})

# First day of finals
FinalsBegin = multiDate({
    'WI13': '2013-03-18',
    'SP13': '2013-06-10',
})

# Break begins, also first day after
# the end of finals. 
BreakBegins = multiDate({
    'WI13': '2013-03-23',
    'SP13': '2013-06-10',
})

# First day of classes for the upcoming quarter
NextQtrClassesBegin = multiDate({
    'WI13': '2013-04-01',
    'SP13': '2013-06-24',
})
