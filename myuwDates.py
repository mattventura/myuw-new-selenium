#!/usr/bin/python

from myuwClasses import multiDate, myuwDate

# These are in chronological order

# Day when myuw switches quarter, 
# also day after grade sub deadline. 
FirstDayQtr = multiDate({
    'WI13': '2013-01-01',
    'SP13': '2013-03-27',
})


# First day of classes
ClassesBegin = multiDate({
    'WI13': '2013-01-07',
    'SP13': '2013-04-01',
})

# Reg period 1 begin
RegPd1 = multiDate({
    'WI13': '2013-02-15',
    'SP13': '2013-04-15',
})

# Last day of instruction
LastDayInstr = multiDate({
    'WI13': '2013-03-15',
    'SP13': '2013-06-07',
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
    'SP13': '2013-06-15',
})

# Day before myuw switches quarter,
# also grade sub deadline. 
LastDayQtr = multiDate({
    'WI13': '2013-03-26', 
    'SP13': '2013-06-18',
})

# First day of classes for the upcoming quarter
NextQtrClassesBegin = multiDate({
    'WI13': '2013-04-01',
    'SP13': '2013-06-24',
})
