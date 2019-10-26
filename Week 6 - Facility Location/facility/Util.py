import math
import time
import datetime

class Util:

    #Format an assignment solved by MIP strategy to output correctly
    @staticmethod
    def formatSolutionFromMIP(assignments):
        solutionDict = {}

        for (facility,customer) in assignments:
            solutionDict[customer] = facility
        size = len(solutionDict)
        solution = [solutionDict[i] for i in range(0,size)]
        return solution
  

    @staticmethod
    #Get a Dictionary with the MIP Solution
    def getDictSolutionFromMIP(assignments):
        solutionDict = {}

        for (facility,customer) in assignments:
            solutionDict[customer] = facility

        return solutionDict
        
    # Return the time from hour, second and secods to seconds
    @staticmethod    
    def getTimeInSeconds(hours,minutes,seconds):
        return (((hours*3600)+(minutes*60)+seconds))

    # Return the time interval between start and end (both in seconds) in hour, minute and second
    @staticmethod    
    def getIntervalDuration(start,end):
        hours, rem = divmod(end-start, 3600)
        minutes, seconds = divmod(rem, 60)
        return int(hours),int(minutes),seconds

    #Return whether a point is inside a circle 
    @staticmethod
    def isInsideCircle(center,radius,point):
        EPS = 1.e-6
        dx = point.x - center.x
        dy = point.y - center.y
        diameter = radius*radius
        euc = (dx * dx) + (dy*dy)
        return euc-diameter <= EPS

    #Truncates/pads a float f to n decimal places without rounding
    @staticmethod
    def truncate(f, n):
        s = '{}'.format(f)
        if 'e' in s or 'E' in s:
            return '{0:.{1}f}'.format(f, n)
        i, p, d = s.partition('.')
        return float('.'.join([i, (d+'0'*n)[:n]]))
