from Util import Util
from EnumSettings import Strategy,ImprovementType,SolvingParadigm

class ParametersConfiguration:
    MAX_FACILITIES_BY_SUBPROBLEM = 100.0   
    QUANTILE_INTERVALS = 5
    facilityCount = 0 
    params = None
    instanceSize = 0
    
    def __init__(self,facilityCount,instanceSize):
        self.instanceSize = instanceSize
        self.facilityCount = facilityCount
        self.__setStrategyParameters(instanceSize)

    def __getQuantilesIntervals(self):
        percentage = 0
        if(self.facilityCount <= self.MAX_FACILITIES_BY_SUBPROBLEM):
            percentage = 1
        else:
            percentage = self.MAX_FACILITIES_BY_SUBPROBLEM/float(self.facilityCount)

        fistQuantile = percentage/float(self.QUANTILE_INTERVALS) 

        intervals = [0]*self.QUANTILE_INTERVALS
        quantile = fistQuantile

        for interval in range(0,self.QUANTILE_INTERVALS):
            intervals[interval] = quantile
            quantile = quantile + fistQuantile

        return intervals

    def getParameters(self):
        return self.params

    def __setStrategyParameters(self,instanceSize): 
        if(self.params is None): 
            if (instanceSize <= 50000): 
                self.params = self.__getInstanceParameters(Strategy.Alpha,instanceSize)
            else:
                self.params =  self.__getInstanceParameters(Strategy.Beta,instanceSize)

    def __getInstanceParameters(self,strategy,instanceSize):  
        if strategy == Strategy.Alpha:
            return self.__AlphaSetup(instanceSize)
        elif strategy == Strategy.Beta:
            return self.__BetaSetup(instanceSize)
    
    def __DefaultSetup(self,instanceSize):
        params = {}
        params["improvementType"] = ImprovementType.Best
        params["executionTimeLimit"] = Util.getTimeInSeconds(4,30,0) #4 hours and 30 minutes of time limit
        params["noImprovementTimeLimit"] = Util.getTimeInSeconds(0,20,0)
        params["strategy"] = Strategy.Default
        params["paradigm"] = SolvingParadigm.MIP
        params["quantile_intervals"] = self.__getQuantilesIntervals()
        return params

    def __AlphaSetup(self,instanceSize):
        params = self.__DefaultSetup(instanceSize)
        params["strategy"] = Strategy.Alpha
        params["paradigm"] = SolvingParadigm.MIP
        
        return params

    def __BetaSetup(self,instanceSize):
        params = self.__DefaultSetup(instanceSize)
        params["strategy"] = Strategy.Beta
        params["paradigm"] = SolvingParadigm.Hybrid
        return params