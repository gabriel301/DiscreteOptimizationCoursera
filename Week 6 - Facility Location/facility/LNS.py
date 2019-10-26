from Forest import Forest
from Util import Util
from MIP import MIP
from EnumSettings import ImprovementType
from Tree import Tree

class LNS:

    EPS = 1.e-6
    DEBUG_MESSAGES = True

    def __init__(self,initialSolutionArray,facilities,customers,improvementType,clusterAreas):
        self.facilities = facilities
        self.customers = customers
        self.currentSolutionForest = Forest()
        self.currentSolutionForest.buildForestFromArray(initialSolutionArray,facilities,customers)
        self.bestSolutionForest = None
        self.currentLevel = 0
        self.mip = MIP(facilities,customers,"Instance_%s_%s" %(len(facilities),len(customers)))
        self.improvementType = improvementType
        self.clusterAreas = clusterAreas
    def __destroy(self,cluster):

        if(self.DEBUG_MESSAGES):
            print("=============================")
            print("Destroy Method Started...")
            print("Current Forest: %s/%s"%(self.currentSolutionForest.getTreesCount(),self.currentSolutionForest.getTotalNodes()))

        reassignmentCandidates = Forest()
        for facilityIndex in cluster:
            if(facilityIndex not in reassignmentCandidates.getTrees().keys()):
                    reassignmentCandidates.addTree(Tree(self.facilities[facilityIndex]))
                    
            if(facilityIndex in self.currentSolutionForest.getTrees().keys()):
                for node in self.currentSolutionForest.getTrees().get(facilityIndex).getNodes().values():
                    reassignmentCandidates.getTrees().get(facilityIndex).addNode(node)
            
        reassignmentCandidates.updateStatistics()

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

        if(newObj-candidateForest.getTotalCost() <= self.EPS):
            if(self.DEBUG_MESSAGES):
                print("NEW SOLUTION FOUND")
                
            if(self.improvementType == ImprovementType.First):
                newSolution = Forest()
                newSolution.buildForestFromDict(Util.getDictSolutionFromMIP(assignments),self.facilities,self.customers)
                
                currentForestObj = self.currentSolutionForest.getTotalCost()

                for tree in candidateForest.getTrees().values():
                    self.currentSolutionForest.removeTree(tree.getRoot().index)

                for tree in newSolution.getTrees().values():
                    self.currentSolutionForest.addTree(Tree(tree.getRoot()))
                    for node in tree.getNodes().values():
                        self.currentSolutionForest.getTrees().get(tree.getRoot().index).addNode(node)

                self.currentSolutionForest.updateStatistics()

                newForestObj = self.currentSolutionForest.getTotalCost()

                if(self.DEBUG_MESSAGES):
                    print("Previous Objective: %s || New Objective: %s"%(currentForestObj,newForestObj))
                    print("Partial Solution")
                    partial =""
                    partial = '%.2f' %self.currentSolutionForest.getTotalCost() + ' ' + str(0) + '\n'
                    partial += ' '.join(map(str,self.currentSolutionForest.getAssignmentsArray()))
                    print(partial)

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

                for tree in newSolution.getTrees().values():
                    self.bestSolutionForest.addTree(Tree(tree.getRoot()))
                    for node in tree.getNodes().values():
                        self.bestSolutionForest.getTrees().get(tree.getRoot().index).addNode(node)

                self.currentSolutionForest.updateStatistics()

                newForestObj  = self.bestSolutionForest.getTotalCost()

                if(self.DEBUG_MESSAGES):
                    print("Previous Best Objective: %s || New Best Objective: %s"%(currentForestObj,newForestObj))
                    

        if(self.DEBUG_MESSAGES):
            print("Evaluate Method Finished...")
            print("=============================")

    def optimize(self):
        
        if(self.DEBUG_MESSAGES):
            print("=============================")
            print("LNS Optimize Method Started...")

        levelsCount = len(self.clusterAreas)
        for level in range(0,levelsCount):
            self.currentLevel = level
            clustersCount = 0
            clustersSize = len(self.clusterAreas.get(level))
            for cluster in self.clusterAreas.get(level).values():
                clustersCount = clustersCount + 1                    
                candidateForest = self.__destroy(cluster)
                cFacilities,cCustomers = candidateForest.getData()
                
                if(self.DEBUG_MESSAGES):
                    print("Level: %s/%s"%(self.currentLevel+1,levelsCount))
                    print("Current Cluster: %s/%s || Facilities: %s || Customers Assigned: %s"%(clustersCount,clustersSize,candidateForest.getTreesCount(),candidateForest.getTotalNodes()))
                if(candidateForest.getTotalNodes() == 0):
                    if(self.DEBUG_MESSAGES):
                        print("No Customers Assigned... Continue")
                    continue
                obj,assignment = self.__repair(cFacilities,cCustomers)
                self.__evaluate(obj,assignment,candidateForest)

            if(self.improvementType == ImprovementType.Best):
                if self.bestSolutionForest is not None:
                    self.currentSolutionForest = Forest()
                    self.currentSolutionForest.buildForestFromArray(self.bestSolutionForest.getAssignmentsArray(),self.facilities,self.customers)
                    self.bestSolutionForest = None
            
            if(self.DEBUG_MESSAGES):
                print("Partial Solution")
                partial =""
                partial = '%.2f' %self.currentSolutionForest.getTotalCost() + ' ' + str(0) + '\n'
                partial += ' '.join(map(str,self.currentSolutionForest.getAssignmentsArray()))
                print(partial)
        return self.currentSolutionForest.getTotalCost(),self.currentSolutionForest.getAssignmentsArray()  