from Forest import Forest
from Util import Util
from MIP import MIP
from EnumSettings import ImprovementType
from Tree import Tree
import math

class LNS:

    EPS = 1.e-6
    DEBUG_MESSAGES = False
    ASSIGNMENT_REWARD = 1

    def __init__(self,initialSolutionArray,facilities,customers,improvementType,clusterAreas,quantiles):
        self.facilities = facilities
        self.customers = customers
        self.currentSolutionForest = Forest()
        self.currentSolutionForest.buildForestFromArray(initialSolutionArray,facilities,customers)
        self.currentIteration = 0
        self.mip = MIP(facilities,customers,"Instance_%s_%s" %(len(facilities),len(customers)))
        self.improvementType = improvementType
        self.clusterAreas = clusterAreas
        self.facilitiesAssignmentFrequency = [1]*len(facilities)
        self.facilitiesCount = len(facilities)
        self.quantiles = []

    def __getQuantiles(self):
        firstQuantile = Util.truncate(1.0/float(len(self.clusterAreas)),10) 

        quantileIntervals = len(self.clusterAreas)
    
        quantile = firstQuantile

        for interval in range(0,quantileIntervals-1):
            self.quantiles.append(quantile)
            quantile = Util.truncate(quantile + firstQuantile,10)

        self.quantiles.append(Util.truncate(quantile - firstQuantile,10))

        #print(self.quantiles)
        #input("....")

    def __getCandidateFacilities(self,cluster,demand):

        
        threshold = Util.truncate(self.quantiles[self.currentIteration],5)
        freqs = [self.facilitiesAssignmentFrequency[i] for i in cluster]
        candidateIndexes = Util.filterbyThreshold(freqs,threshold,self.currentIteration+1)
        result = [cluster[i] for i in candidateIndexes]

        candidatesCapacity = 0
        for index in result:
            candidatesCapacity = candidatesCapacity + self.facilities[index].capacity

        print("Demand: %s || Capacity: %s"%(demand,candidatesCapacity))
        
        if(candidatesCapacity < demand):
            remainingFacilitiesIndex = set(cluster).difference(set(cluster).intersection(set(result)))
            remainingFacilities = [self.facilities[i] for i in remainingFacilitiesIndex]
            remainingFacilities.sort(key=lambda x: x.cost_per_capacity, reverse=True)
            print("Demand above Capacity")
            for facility in remainingFacilities:
                result.append(facility.index)
                candidatesCapacity = candidatesCapacity + facility.capacity
                if(candidatesCapacity >= demand):
                    print("Demand: %s || New Capacity: %s"%(demand,candidatesCapacity))
                    break

        return result


    def __updateFrequency(self,facilities,reward):

        for index in facilities:
            self.facilitiesAssignmentFrequency[index] = self.facilitiesAssignmentFrequency[index] + reward

    def __destroy(self,cluster):
        
        
        if(self.DEBUG_MESSAGES):
            print("=============================")
            print("Destroy Method Started...")

        clusterDemand = 0   
        for facilityIndex in cluster:
            if(facilityIndex in self.currentSolutionForest.getTrees().keys()):
                for node in self.currentSolutionForest.getTrees().get(facilityIndex).getNodes().values():
                    clusterDemand = clusterDemand + node.demand

        candidateFacilities = self.__getCandidateFacilities(cluster,clusterDemand)

        print("Current Forest: %s/%s - Candidate Facilities: %s/%s"%(self.currentSolutionForest.getTreesCount(),self.currentSolutionForest.getTotalNodes(),len(candidateFacilities),len(cluster)))
       
        reassignmentCandidates = Forest()

        for facilityIndex in candidateFacilities:
            if(facilityIndex not in reassignmentCandidates.getTrees().keys()):
                    reassignmentCandidates.addTree(Tree(self.facilities[facilityIndex]))
                    
        for facilityIndex in cluster:
            if(facilityIndex in self.currentSolutionForest.getTrees().keys()):
                for node in self.currentSolutionForest.getTrees().get(facilityIndex).getNodes().values():
                    reassignmentCandidates.getTrees().get(candidateFacilities[0]).addNode(node)
            
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
    
    def __evaluate(self,newObj,assignments,candidateForest,cluster):
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
                newFacilities= set()
                previousFacilities = set()
               
                for tree in candidateForest.getTrees().values():
                    self.currentSolutionForest.removeTree(tree.getRoot().index)
                    previousFacilities.add(tree.getRoot().index)

                
                for tree in newSolution.getTrees().values():
                    self.currentSolutionForest.addTree(Tree(tree.getRoot()))
                    newFacilities.add(tree.getRoot().index)
                    for node in tree.getNodes().values():
                        self.currentSolutionForest.getTrees().get(tree.getRoot().index).addNode(node)

                #Facilities that were in the solution, but was not even selected as candidates
                clusterIntersection = set([tree.getRoot().index for tree in self.currentSolutionForest.getTrees().values()]).intersection(cluster)
                notInterestingFacilities  = clusterIntersection.difference(previousFacilities)

                for facilityIndex in notInterestingFacilities:
                    self.currentSolutionForest.removeTree(facilityIndex)
                
                self.currentSolutionForest.updateStatistics()

                newForestObj = self.currentSolutionForest.getTotalCost()
                
                self.__updateFrequency(list(newFacilities),self.ASSIGNMENT_REWARD)


                previousCandidates = list(previousFacilities.difference(newFacilities.intersection(previousFacilities)))

                if(len(previousCandidates)==0):
                    previousCandidates = list(newFacilities)

                previousCandidates.extend(list(notInterestingFacilities))

                #reward = (1-Util.truncate(float(len(cluster)/self.facilitiesCount),3))*self.ASSIGNMENT_REWARD
               
                reward = Util.truncate(float(len(newFacilities))/float(len(previousCandidates)),3)
                #self.__updateFrequency(previousCandidates,Util.truncate(float(len(newFacilities))/float(len(previousCandidates)),3))
                self.__updateFrequency(previousCandidates,reward)

                if(self.DEBUG_MESSAGES):
                    print("Previous Objective: %s || New Objective: %s"%(currentForestObj,newForestObj))
                    print("Partial Solution")
                    partial =""
                    partial = '%.2f' %self.currentSolutionForest.getTotalCost() + ' ' + str(0) + '\n'
                    partial += ' '.join(map(str,self.currentSolutionForest.getAssignmentsArray()))
                    print(partial)


        if(self.DEBUG_MESSAGES):
            print("Evaluate Method Finished...")
            print("=============================")

    def optimize(self):
        
        if(self.DEBUG_MESSAGES):
            print("=============================")
            print("LNS Optimize Method Started...")

        self.__getQuantiles()
        iterationsCount = len(self.clusterAreas)
        customerCount = len(self.customers)
        for iteration in range(0,iterationsCount):
            self.currentIteration = iteration
            clustersCount = 0
            clustersSize = len(self.clusterAreas.get(iteration))
            for cluster in self.clusterAreas.get(iteration).values():
                clustersCount = clustersCount + 1
                print("Instance: %s_%s"%(self.facilitiesCount,customerCount))  
                print("Iteration: %s/%s"%(self.currentIteration+1,iterationsCount))                
                candidateForest = self.__destroy(cluster)
                cFacilities,cCustomers = candidateForest.getData()
                
                print("Current Cluster: %s/%s || Facilities: %s || Customers Assigned: %s"%(clustersCount,clustersSize,candidateForest.getTreesCount(),candidateForest.getTotalNodes()))
                if(candidateForest.getTotalNodes() == 0):
                    if(self.DEBUG_MESSAGES):
                        print("No Customers Assigned... Continue")
                    continue

                obj,assignment = self.__repair(cFacilities,cCustomers)
                self.__evaluate(obj,assignment,candidateForest,cluster)
                
                print("Current Forest: %s/%s"%(self.currentSolutionForest.getTreesCount(),self.currentSolutionForest.getTotalNodes()))
                print("Current Objective Funciton: %s"%self.currentSolutionForest.getTotalCost())
            if(self.DEBUG_MESSAGES):
                print("Partial Solution")
                partial =""
                partial = '%.2f' %self.currentSolutionForest.getTotalCost() + ' ' + str(0) + '\n'
                partial += ' '.join(map(str,self.currentSolutionForest.getAssignmentsArray()))
                print(partial)

        return self.currentSolutionForest.getTotalCost(),self.currentSolutionForest.getAssignmentsArray()  