from Forest import Forest
from Util import Util
from MIP import MIP
from EnumSettings import ImprovementType
from Tree import Tree

class LNS:

    EPS = 1.e-6
    DEBUG_MESSAGES = True

    def __init__(self,initialSolutionArray,facilities,customers,improvementType):
        self.facilities = facilities
        self.customers = customers
        self.currentSolutionForest = Forest()
        self.currentSolutionForest.buildForestFromArray(initialSolutionArray,facilities,customers)
        self.bestSolutionForest = None
        self.currentQuantile = 0
        self.mip = MIP(facilities,customers,"Instance_%s_%s" %(len(facilities),len(customers)))
        self.improvementType = improvementType

    def __destroy(self,centerFacility):

        if(self.DEBUG_MESSAGES):
            print("=============================")
            print("Destroy Method Started...")
            print("Current Forest: %s/%s"%(self.currentSolutionForest.getTreesCount(),self.currentSolutionForest.getTotalNodes()))

        reassignmentCandidates = Forest()
        for adjacentFacility in self.facilities:
            if Util.isInsideCircle(centerFacility.location,centerFacility.distance_quantiles[self.currentQuantile],adjacentFacility.location):
                if(adjacentFacility.index not in reassignmentCandidates.getTrees().keys()):
                    reassignmentCandidates.addTree(Tree(adjacentFacility))
                    
                if(adjacentFacility.index in self.currentSolutionForest.getTrees().keys()):
                    for node in self.currentSolutionForest.getTrees().get(adjacentFacility.index).getNodes().values():
                        reassignmentCandidates.getTrees().get(adjacentFacility.index).addNode(node)
        
        if(self.DEBUG_MESSAGES):
            print("Facilities: %s - Customers %s"%(reassignmentCandidates.getTreesCount(),reassignmentCandidates.getTotalNodes()))
            print("Destroy Method Finished...")
            print("=============================")

        return reassignmentCandidates
    
    def __repair(self,candidatesFacility,candidatesCustomer):
        if(self.DEBUG_MESSAGES):
            print("=============================")
            print("Repair Method Started...")
        self.mip.clear()
        self.mip.initialize(candidatesFacility,candidatesCustomer,"Instance_%s_%s" %(len(candidatesFacility),len(candidatesCustomer)))
        self.mip.createModel()
        obj,assignments = self.mip.optimize()

        if(self.DEBUG_MESSAGES):
            print("Repair Method Finished...")
            print("=============================")

        return obj,assignments
    
    def __evaluate(self,newObj,assignments,candidateForest):
        if(self.DEBUG_MESSAGES):
            print("=============================")
            print("Evaluate Method Started...")
            print("Current OBJ: %s || Candidate Cost %s"%(newObj,candidateForest.getTotalCost()))

        if(newObj-candidateForest.getTotalCost() < self.EPS):
            if(self.DEBUG_MESSAGES):
                print("NEW SOLUTION FOUND")
            if(self.improvementType == ImprovementType.First):
                newSolution = Forest()
                newSolution.buildForestFromDict(Util.getDictSolutionFromMIP(assignments),self.facilities,self.customers)
                
                currentForestObj = self.currentSolutionForest.getTotalCost()

                for tree in candidateForest.getTrees().values():
                    self.currentSolutionForest.removeTree(tree.getRoot().index)

                for tree in newSolution.getTrees().values():
                    self.currentSolutionForest.addTree(tree)

                newForestObj = self.currentSolutionForest.getTotalCost()

                if(self.DEBUG_MESSAGES):
                    print("Previous Objective: %s || New Objective: %s"%(currentForestObj,newForestObj))

            elif(self.improvementType == ImprovementType.Best):

                if(self.bestSolutionForest is None):
                    currentForestObj = self.currentSolutionForest.getTotalCost()
                else:
                    currentForestObj = self.bestSolutionForest.getTotalCost()         
                
                self.bestSolutionForest = Forest()
                newSolution = Forest()
                newSolution.buildForestFromDict(Util.getDictSolutionFromMIP(assignments),self.facilities,self.customers)
                self.bestSolutionForest.buildForestFromArray(self.currentSolutionForest.getAssignmentsArray(),self.facilities,self.customers)

                for tree in candidateForest.getTrees().values():
                    self.bestSolutionForest.removeTree(tree.getRoot().index)

                for tree in newSolution.getTrees().values():
                    self.bestSolutionForest.addTree(tree)

                newForestObj  = self.currentSolutionForest.getTotalCost()

                if(self.DEBUG_MESSAGES):
                    print("Previous Best Objective: %s || New Best Objective: %s"%(currentForestObj,newForestObj))

        if(self.DEBUG_MESSAGES):
            print("Evaluate Method Finished...")
            print("=============================")

    def optimize(self):
        
        if(self.DEBUG_MESSAGES):
            print("=============================")
            print("LNS Optimize Method Started...")

        quantilesCount = len(self.facilities[0].distance_quantiles)
        for quantile in range(0,quantilesCount):
            self.currentQuantile = quantile
            if(self.DEBUG_MESSAGES):
                print("Quantile: %s/%s"%(self.currentQuantile,quantilesCount))
            for facility in self.facilities:
                candidateForest = self.__destroy(facility)
                cFacilities,cCustomers = candidateForest.getData()
                
                if(self.DEBUG_MESSAGES):
                    print("Current Facility: %s || Facilities Nearby: %s || Customers Assigned: %s"%(facility.index,candidateForest.getTreesCount(),candidateForest.getTotalNodes()))
                obj,assignment = self.__repair(cFacilities,cCustomers)
                self.__evaluate(obj,assignment,candidateForest)

            if(self.improvementType == ImprovementType.Best):
                if self.bestSolutionForest is not None:
                    self.currentSolutionForest = Forest()
                    self.currentSolutionForest.buildForestFromArray(self.bestSolutionForest.getAssignmentsArray,self.facilities,self.customers)
                    self.bestSolutionForest = None

        return self.currentSolutionForest.getTotalCost(),self.currentSolutionForest.getAssignmentsArray()  