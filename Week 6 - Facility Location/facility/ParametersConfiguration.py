from Util import Util
from EnumSettings import Strategy,ImprovementType,SolvingParadigm,InitialSolutionFunction,MipSolver
import time
import datetime

class ParametersConfiguration:
    
    def __init__(self,facilityCount,instanceSize):
        self.instanceSize = instanceSize
        self.facilityCount = facilityCount
        self.params = None
        self.__setStrategyParameters(instanceSize)
        

    def __getQuantilesIntervals(self):
        firstQuantile = Util.truncate(self.params["initial_facilities_subproblem"]/float(self.facilityCount),10) 
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
            elif(instanceSize <= 100000):
                self.__getInstanceParameters(Strategy.Beta,instanceSize)
            else:
                self.__getInstanceParameters(Strategy.Delta,instanceSize)

    def __getInstanceParameters(self,strategy,instanceSize):  
        if strategy == Strategy.Alpha:
            self.__AlphaSetup(instanceSize)
        elif strategy == Strategy.Beta:
            self.__BetaSetup(instanceSize)
        elif strategy == Strategy.Delta:
            self.__DeltaSetup(instanceSize)
    
    def __DefaultSetup(self,instanceSize):
        self.params = {}
        self.params["improvementType"] = ImprovementType.First
        self.params["executionTimeLimit"] = Util.getTimeInSeconds(4,50,0) #4 hours and 30 minutes of time limit
        self.params["noImprovementIterationLimit"] = 2
        self.params["mipTimeLimit"] = Util.getTimeInSeconds(4,0,0) 
        self.params["strategy"] = Strategy.Default
        self.params["paradigm"] = SolvingParadigm.MIP
        self.params["initial_facilities_subproblem"] = 5 #Maximum desired number of facilities 'in' the first cluster
        self.params["initialSolutionFunction"] = InitialSolutionFunction.Euclidean
        self.params["mipSolver"] = MipSolver.CPLEX
        

    def __AlphaSetup(self,instanceSize):
        self.__DefaultSetup(instanceSize)
        self.params["strategy"] = Strategy.Alpha
        self.params["paradigm"] = SolvingParadigm.MIP
        self.params["quantile_intervals"] = self.__getQuantilesIntervals()
        
    def __BetaSetup(self,instanceSize):
        self.__DefaultSetup(instanceSize)
        self.params["strategy"] = Strategy.Beta
        self.params["paradigm"] = SolvingParadigm.Hybrid
        self.params["improvementType"] = ImprovementType.First
        self.params["quantile_intervals"] = self.__getQuantilesIntervals()
    
    def __DeltaSetup(self,instanceSize):
        self.__DefaultSetup(instanceSize)
        self.params["strategy"] = Strategy.Delta
        self.params["paradigm"] = SolvingParadigm.Hybrid
        self.params["improvementType"] = ImprovementType.First
        self.params["initial_facilities_subproblem"] = 7
        self.params["quantile_intervals"] = self.__getQuantilesIntervals()

