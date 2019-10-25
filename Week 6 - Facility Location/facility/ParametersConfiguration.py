from Util import Util
from EnumSettings import Strategy,ImprovementType,SolvingParadigm

class ParametersConfiguration:
    MAX_FACILITIES_BY_SUBPROBLEM = 100.0   
    QUANTILE_INTERVALS = 5
    #facilityCount = 0 
    #params = None
    #instanceSize = 0
    
    def __init__(self,facilityCount,instanceSize):
        self.instanceSize = instanceSize
        self.facilityCount = facilityCount
        self.params = None
        self.__setStrategyParameters(instanceSize)
        

    def __getQuantilesIntervals(self):
        percentage = 0
        if(self.facilityCount <= self.MAX_FACILITIES_BY_SUBPROBLEM):
            percentage = 1.0
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
                self.__getInstanceParameters(Strategy.Alpha,instanceSize)
            else:
                self.__getInstanceParameters(Strategy.Beta,instanceSize)

    def __getInstanceParameters(self,strategy,instanceSize):  
        if strategy == Strategy.Alpha:
            self.__AlphaSetup(instanceSize)
        elif strategy == Strategy.Beta:
            self.__BetaSetup(instanceSize)
    
    def __DefaultSetup(self,instanceSize):
        self.params = {}
        self.params["improvementType"] = ImprovementType.Best
        self.params["executionTimeLimit"] = Util.getTimeInSeconds(4,30,0) #4 hours and 30 minutes of time limit
        self.params["noImprovementTimeLimit"] = Util.getTimeInSeconds(0,20,0)
        self.params["strategy"] = Strategy.Default
        self.params["paradigm"] = SolvingParadigm.MIP
        self.params["quantile_intervals"] = self.__getQuantilesIntervals()


    def __AlphaSetup(self,instanceSize):
        self.__DefaultSetup(instanceSize)
        self.params["strategy"] = Strategy.Alpha
        self.params["paradigm"] = SolvingParadigm.MIP
        
    def __BetaSetup(self,instanceSize):
        self.__DefaultSetup(instanceSize)
        self.params["strategy"] = Strategy.Beta
        self.params["paradigm"] = SolvingParadigm.Hybrid
        self.params["improvementType"] = ImprovementType.First
