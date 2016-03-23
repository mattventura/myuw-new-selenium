#!/usr/bin/python

import time

# Class for measuring how long certain things take
class perfCounter(object):
    def __init__(self, label = None):
        self.startTime = time.time()
        self.finished = False
        self.label = label

    def end(self):
        self.endTime = time.time()
        self.finished = True

    @property
    def elapsedTime(self):
        if self.finished:
            return self.endTime - self.startTime
        else:
            return time.time() - self.startTime

    @property
    def formatted(self):
        if self.label:
            return '%s took %s seconds' %(self.label, self.elapsedTime)
        else: 
            return str(self.elapsedTime)

    def endGetTime(self):
        self.end()
        return self.elapsedTime
    
    def endFmt(self):
        self.end()
        return self.formatted
