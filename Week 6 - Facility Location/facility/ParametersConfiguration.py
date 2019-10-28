from Util import Util
from EnumSettings import Strategy,ImprovementType,SolvingParadigm

class ParametersConfiguration:
    INITIAL_FACILITIES_BY_SUBPROBLEM = 5  #Maximum desired number of facilities 'in' the first cluster
   
    def __init__(self,facilityCount,instanceSize):
        self.instanceSize = instanceSize
        self.facilityCount = facilityCount
        self.params = None
        self.__setStrategyParameters(instanceSize)
        

    def __getQuantilesIntervals(self):
        firstQuantile = Util.truncate(self.INITIAL_FACILITIES_BY_SUBPROBLEM/float(self.facilityCount),10) 
        if(firstQuantile > 1.0):
            firstQuantile = 1
        quantileIntervals = round(1.0/firstQuantile)
    
        intervals = [0]*quantileIntervals
        quantile = firstQuantile

        for interval in range(0,quantileIntervals):
            intervals[interval] = quantile
            quantile = Util.truncate(quantile + firstQuantile,10)
            if(quantile > 1.0):
                break
            
        result = [interval for interval in intervals if interval > 0 ]    

        return result

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
        self.params["mipTimeLimit"] = Util.getTimeInSeconds(0,15,0) #30 limits for each Mip Execution
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
