from enum import Enum

#   Class used to set different strategies to different instances os the problem.
#   One strategy sets different parameters (Maximun Runtime, Local Search Procedure, etc)
class Strategy(Enum):
    Default = "Default"
    Alpha = "Alpha"
    Beta = "Beta"
    Gamma = "Gamma"
    Delta = "Delta"
    Epsilon = "Epsilon"

#   Enum to change the behaviour of the local search method to work with either first improment approach or best improvement approach
class ImprovementType(Enum):
    Best = "Best Improvement"
    First = "First Improvement"

#   Enum to choose the solving paradigm
class SolvingParadigm(Enum):
    MIP = "MIP"
    Heuristic = "Heuristic"
    Hybrid = "Hybrid"