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
    'SP13': '2013-02-15',
    'SU13': '2013-04-15',
})

# Reg period 2 begin
RegPd2 = multiDate({
    'SP13': '2013-03-04',
    'SU13': '2013-05-23',
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

# Special dates

RegCardDates = {}
SummerRegCardDates = {}
for key, value in RegPd1.items():
    # If it's summer, put it in a special summer 
    # quarter reg card date
    if key[0:2] == 'SU':
        SummerRegCardDates[key] = value - 7
    else:
        RegCardDates[key] = value - 14

RegCardShow = multiDate(RegCardDates)
SummerRegShow = multiDate(SummerRegCardDates)



# Try to convert 
def dateToQtr(date):
    date = myuwDate(date)
    for qtr, start in FirstDayQtr.items():
        try:
            end = LastDayQtr[qtr]
            if start <= date <= end:
                return qtr
        except: 
            continue
    raise Exception("Couldn't find quarter for date %s" %date)

