#!/usr/bin/python 

# Some settings
# Enable this to do some performance profiling
perf = False
# Runs dummy debug code instead of real test
debug = False
# Run each user in parallel
parallel = True
# Split up tests for each user into separate parallel processes
parallelDateSplit = 3
# Number of concurrent tests running at any given time will be at most
# the number of users to test times parallelDateSplit

# Delay between starting processes for parallel mode
parallelDelay = 4

# For auto date tests, restrict dates to this range
defaultStartDate = '2013-1-1'
defaultEndDate = '2013-12-17'
