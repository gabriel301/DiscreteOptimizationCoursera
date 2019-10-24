import time
import datetime
#   Class to help to monitor the runtimes of the algorithm
class Clock():
    def __init__ (self):
        self.start = None

    def isTimeOver(self,end,duration):
        return end-self.start >= duration

    def setStart(self,start):
        self.start = start

    def getStart(self):
        return self.start