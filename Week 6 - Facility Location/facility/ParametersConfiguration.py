from Util import Util
from EnumSettings import Strategy,ImprovementType,SolvingParadigm

class ParametersConfiguration:
    params = None
    instanceSize = 0

    def __init__(self,instanceSize):
        self.instanceSize = instanceSize
        self.__setStrategyParameters(instanceSize)


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