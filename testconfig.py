#!/usr/bin/python 

# Some settings
# Enable this to do some performance profiling
perf = False
# Run each user in parallel
parallel = True
# Split tests into parallel processes
# The webserver process generally doesn't use that much, 
# and the processes are niced anyway, so whatever you would
# use for make -jX will probably work here. 
parallelNum = 9
#parallelNum = 9
# Number of concurrent tests running at any given time will be at most
# the number of users to test times parallelDateSplit

# Delay between starting processes for parallel mode
parallelDelay = 3

# For auto date tests, restrict dates to this range
defaultStartDate = '2013-1-7'
defaultEndDate = '2013-12-17'

# Testing URL
testUrl = 'http://localhost:8081' 
