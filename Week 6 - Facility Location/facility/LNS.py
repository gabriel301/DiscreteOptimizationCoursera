from Forest import Forest
from Util import Util
from MIP import MIP
from EnumSettings import Strategy,ImprovementType,SolvingParadigm,InitialSolutionFunction,MipSolver
from Preprocessing import Preprocessing
from Tree import Tree
import math
import copy
import time
import datetime
from Clock import Clock

class LNS:

    EPS = 1.e-10
    DEBUG_MESSAGES = False
    ASSIGNMENT_REWARD = 1
    INITIAL_REWARD = 0.5
    NO_ASSIGNMENT_REWARD = 0.25
    MAX_PROBLEM_SIZE = 25000
    
    def __init__(self,facilities,customers,params):
        self.facilities = dict(zip([facility.index for facility in facilities], [facility for facility in facilities]))
        self.customers = customers
        self.subproblemSolutionForest = Forest()
        self.currentIteration = 0
        self.mip = MIP(facilities,customers,"Instance_%s_%s" %(len(facilities),len(customers)),params["mipSolver"])
        self.facilitiesCount = len(facilities)
        self.quantiles = []
        self.params = params
        self.totalDemand = sum([customer.demand for customer in customers])
        self.currentObjectiveFunction = 0
        self.currentSolutionAssignment = []
    
    def __InitializeProblem(self,facilities,customers):
        self.currentIteration = 0
        self.clusterAreas = Preprocessing.getClusters(facilities.values(),self.params["quantile_intervals"])
        if(self.params["initialSolutionFunction"] == InitialSolutionFunction.Radius):
            Preprocessing.getDistanceQuantiles(facilities,self.params["quantile_intervals"])
            self.subproblemSolutionForest.buildForestFromArray(Util.formatSolutionFromMIP(Preprocessing.getRadiusDistanceInitialSolution(facilities,customers,self.clusterAreas.get(0))),self.facilities,self.customers)
        else:
            self.subproblemSolutionForest.buildForestFromArray(Util.formatSolutionFromMIP(Preprocessing.getNearestNeighbourInitialSolution(facilities,customers,self.params["initialSolutionFunction"])),self.facilities,self.customers)

        for facility in facilities.keys():
            self.facilities[facility] = self.facilities[facility]._replace(frequency=self.INITIAL_REWARD)


    def __getQuantiles(self):
        firstQuantile = Util.truncate(1.0/float(len(self.clusterAreas)),10) 

        quantileIntervals = len(self.clusterAreas)
    
        quantile = firstQuantile

        for interval in range(0,quantileIntervals-1):
            self.quantiles.append(quantile)
            quantile = Util.truncate(quantile + firstQuantile,10)

        self.quantiles.append(Util.truncate(quantile - firstQuantile,10))


    def __getCandidateFacilities(self,cluster,demand,threshold,fulfillDemand = True):
     
        freqs = [self.facilities[i].frequency for i in cluster]
        candidateIndexes = Util.filterbyThreshold(freqs,threshold,self.currentIteration+1)
        result = [cluster[i] for i in candidateIndexes]

        candidatesCapacity = 0
        for index in result:
            candidatesCapacity = candidatesCapacity + self.facilities[index].capacity

        print("Demand: %s || Capacity: %s"%(demand,candidatesCapacity))
        
        if(candidatesCapacity < demand):
            if fulfillDemand:
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
            else:
                return None

        return result


    def __updateFrequency(self,facilities,reward):

        for index in facilities:
            if(index not in self.facilities.keys()):
                input("key does not exists!")
            freq = self.facilities[index].frequency + reward
            self.facilities[index] = self.facilities[index]._replace(frequency=freq)

    def __destroy(self,cluster):
        
        if(self.DEBUG_MESSAGES):
            print("=============================")
            print("Destroy Method Started...")

        clusterDemand = 0   
        for facilityIndex in cluster:
            if(facilityIndex in self.subproblemSolutionForest.getTrees().keys()):
                for node in self.subproblemSolutionForest.getTrees().get(facilityIndex).getNodes().values():
                    clusterDemand = clusterDemand + node.demand

        #candidateFacilities = self.__getCandidateFacilities(cluster,clusterDemand,Util.truncate(self.quantiles[self.currentIteration],5))
        candidateFacilities = copy.deepcopy(cluster)
        print("Current Forest: %s/%s - Candidate Facilities: %s/%s"%(self.subproblemSolutionForest.getTreesCount(),self.subproblemSolutionForest.getTotalNodes(),len(candidateFacilities),len(cluster)))
       
        reassignmentCandidates = Forest()

        for facilityIndex in candidateFacilities:
            if(facilityIndex not in reassignmentCandidates.getTrees().keys()):
                    reassignmentCandidates.addTree(Tree(self.facilities[facilityIndex]))
                    
        for facilityIndex in cluster:
            if(facilityIndex in self.subproblemSolutionForest.getTrees().keys()):
                for node in self.subproblemSolutionForest.getTrees().get(facilityIndex).getNodes().values():
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
        self.mip.initialize(candidatesFacility,candidatesCustomer,"Instance_%s_%s" %(len(candidatesFacility),len(candidatesCustomer)),self.params["mipSolver"])
        obj,assignments,status = self.mip.optimize(self.params["mipTimeLimit"])

        if(self.DEBUG_MESSAGES):
            print("Repair Method Finished...")
            print("=============================")

        return obj,assignments,status
    
    def __evaluate(self,newObj,assignments,candidateForest,cluster):
        if(self.DEBUG_MESSAGES):
            print("=============================")
            print("Evaluate Method Started...")
            print("Current Partial Objective: %s || Candidate Partial Objective %s"%(newObj,candidateForest.getTotalCost()))

        if(newObj-candidateForest.getTotalCost() <= self.EPS):
                    
            newSolution = Forest()
            newSolution.buildForestFromArray(self.subproblemSolutionForest.getAssignmentsArray(),self.facilities,self.customers)
            partialSolution = Forest()
            partialSolution.buildForestFromDict(Util.getDictSolutionFromMIP(assignments),self.facilities,self.customers)
            currentForestObj = self.subproblemSolutionForest.getTotalCost()

            newFacilities= set()
            previousFacilities = set()
               
            for tree in candidateForest.getTrees().values():
                newSolution.removeTree(tree.getRoot().index)
                previousFacilities.add(tree.getRoot().index)

                
            for tree in partialSolution.getTrees().values():
                newSolution.addTree(Tree(tree.getRoot()))
                newFacilities.add(tree.getRoot().index)
                for node in tree.getNodes().values():
                    newSolution.getTrees().get(tree.getRoot().index).addNode(node)

            #Facilities that were in the solution, but was not even selected as candidates
            clusterIntersection = set([tree.getRoot().index for tree in self.subproblemSolutionForest.getTrees().values()]).intersection(cluster)
            notInterestingFacilities  = clusterIntersection.difference(previousFacilities)

            for facilityIndex in notInterestingFacilities:
                newSolution.removeTree(facilityIndex)
                
            newSolution.updateStatistics()

            previousCandidates = list(previousFacilities.difference(newFacilities.intersection(previousFacilities)))

            if(len(previousCandidates)==0):
                previousCandidates = list(newFacilities)

            previousCandidates.extend(list(notInterestingFacilities))

            print("Current Objective: %s || Candidate Objective: %s"%(currentForestObj,newSolution.getTotalCost()))

            if(self.params["improvementType"] == ImprovementType.Best):
                if(Util.truncate(Util.truncate(newSolution.getTotalCost(),10) - Util.truncate(self.subproblemSolutionForest.getTotalCost(),10),10) <= self.EPS):
                    if(self.DEBUG_MESSAGES):
                        print("NEW SOLUTION FOUND!")
                    self.subproblemSolutionForest.buildForestFromArray(newSolution.getAssignmentsArray(),self.facilities,self.customers)
                    
                    newForestObj = self.subproblemSolutionForest.getTotalCost()
                
                    self.__updateFrequency(list(newFacilities),self.ASSIGNMENT_REWARD)

                    previousCandidates = list(previousFacilities.difference(newFacilities.intersection(previousFacilities)))

                    if(len(previousCandidates)==0):
                        previousCandidates = list(newFacilities)

                    previousCandidates.extend(list(notInterestingFacilities))
               
                    reward = Util.truncate(float(len(newFacilities))/float(len(previousCandidates)),3)

                    self.__updateFrequency(previousCandidates,reward)

                    if(self.DEBUG_MESSAGES):
                        print("Previous Objective: %s || New Objective: %s"%(currentForestObj,newForestObj))
                        print("Partial Solution")
                        partial =""
                        partial = '%.2f' %self.subproblemSolutionForest.getTotalCost() + ' ' + str(0) + '\n'
                        partial += ' '.join(map(str,self.subproblemSolutionForest.getAssignmentsArray()))
                        print(partial)
                else:
                    candidates = [tree.getRoot().index for tree in candidateForest.getTrees().values()]
                    #reward = (Util.truncate(float(candidateForest.getTreesCount()/self.facilitiesCount),3))*self.ASSIGNMENT_REWARD
                    reward = self.NO_ASSIGNMENT_REWARD
                    self.__updateFrequency(candidates,reward)

            elif self.params["improvementType"] == ImprovementType.First:
                self.subproblemSolutionForest.buildForestFromArray(newSolution.getAssignmentsArray(),self.facilities,self.customers)
                    
                newForestObj = self.subproblemSolutionForest.getTotalCost()
                
                self.__updateFrequency(list(newFacilities),self.ASSIGNMENT_REWARD)

                previousCandidates = list(previousFacilities.difference(newFacilities.intersection(previousFacilities)))

                if(len(previousCandidates)==0):
                    previousCandidates = list(newFacilities)

                previousCandidates.extend(list(notInterestingFacilities))
               
                reward = Util.truncate(float(len(newFacilities))/float(len(previousCandidates)),3)

                self.__updateFrequency(previousCandidates,reward)

                if(self.DEBUG_MESSAGES):
                    print("Previous Objective: %s || New Objective: %s"%(currentForestObj,newForestObj))
                    print("Partial Solution")
                    partial =""
                    partial = '%.2f' %self.subproblemSolutionForest.getTotalCost() + ' ' + str(0) + '\n'
                    partial += ' '.join(map(str,self.subproblemSolutionForest.getAssignmentsArray()))
                    print(partial)

                candidates = [tree.getRoot().index for tree in candidateForest.getTrees().values()]
                #reward = (Util.truncate(float(candidateForest.getTreesCount()/self.facilitiesCount),3))*self.ASSIGNMENT_REWARD
                reward = self.NO_ASSIGNMENT_REWARD
                self.__updateFrequency(candidates,reward)


        if(self.DEBUG_MESSAGES):
            print("Evaluate Method Finished...")
            print("=============================")

    def optimize(self):
        start = time.time()
        clock = Clock()
        clock.setStart(start)
        if(self.DEBUG_MESSAGES):
            print("=============================")
            print("LNS Optimize Method Started...")
      
        customerSubset = copy.deepcopy(self.customers)
        facilitySubet = copy.deepcopy(self.facilities)
        self.__InitializeProblem(facilitySubet,customerSubset)
        self.__getQuantiles()
        self.currentObjectiveFunction = self.subproblemSolutionForest.getTotalCost()
        self.currentSolutionAssignment = self.subproblemSolutionForest.getAssignmentsArray()
        initialQuantiles = copy.deepcopy(self.quantiles)
        quantileSize = len(initialQuantiles)
        quantilesCount = 0
        customerCount = len(self.customers)
        noImprovementIterations = 0
        while True:
            if(clock.isTimeOver(time.time(),self.params["executionTimeLimit"])):
                break

            iterationsCount = len(self.clusterAreas)
            for iteration in range(0,iterationsCount):
                self.currentIteration = iteration
                clustersCount = 0
                clustersSize = len(self.clusterAreas.get(iteration))
                for cluster in self.clusterAreas.get(iteration).values():
                    clustersCount = clustersCount + 1
                    print("Iteration: %s/%s || Instance: %s_%s"%(quantilesCount+1,quantileSize,self.facilitiesCount,customerCount))  
                    print("Subproblem: %s/%s"%(self.currentIteration+1,iterationsCount))                
                    candidateForest = self.__destroy(cluster)
                    if(candidateForest.getTreesCount()*candidateForest.getTotalNodes() > self.MAX_PROBLEM_SIZE):
                        print("Problem instance is larger than limit. Skipping...")
                        candidateFacilities = [tree.getRoot() for tree in candidateForest.getTrees().values()]
                        self.__updateFrequency(dict([(facility.index,facility) for facility in candidateFacilities]),self.NO_ASSIGNMENT_REWARD)
                        continue

                    cFacilities,cCustomers = candidateForest.getData()
                    
                    print("Current Cluster: %s/%s || Facilities: %s || Customers Assigned: %s"%(clustersCount,clustersSize,candidateForest.getTreesCount(),candidateForest.getTotalNodes()))
                    if(candidateForest.getTotalNodes() == 0):
                        if(self.DEBUG_MESSAGES):
                            print("No Customers Assigned... Continue")
                        continue

                    obj,assignment,status = self.__repair(cFacilities,cCustomers)

                    if(status=='optimal'):
                        self.__evaluate(obj,assignment,candidateForest,cluster)
                    else:
                        print("No Optimal Solution Found for this instance")
                        candidateFacilities = [tree.getRoot() for tree in candidateForest.getTrees().values()]
                        self.__updateFrequency(dict([(facility.index,facility) for facility in candidateFacilities]),self.ASSIGNMENT_REWARD)
                        
                    print("Subproblem Forest: %s/%s"%(self.subproblemSolutionForest.getTreesCount(),self.subproblemSolutionForest.getTotalNodes()))
                    print("Subproblem Objective Funciton: %s"%self.subproblemSolutionForest.getTotalCost())
                    print("Current Objective Function: %s"%self.currentObjectiveFunction)

                if(self.DEBUG_MESSAGES):
                    print("Partial Solution")
                    partial =""
                    partial = '%.2f' %self.subproblemSolutionForest.getTotalCost() + ' ' + str(0) + '\n'
                    partial += ' '.join(map(str,self.subproblemSolutionForest.getAssignmentsArray()))
                    print(partial)

            if(self.currentObjectiveFunction >= self.subproblemSolutionForest.getTotalCost() ):
                self.currentObjectiveFunction = self.subproblemSolutionForest.getTotalCost()
                self.currentSolutionAssignment = self.subproblemSolutionForest.getAssignmentsArray()
            else:
                noImprovementIterations = noImprovementIterations + 1

            print("====================================================")
            print("CURRENT OBJECTIVE FUNCTION: %s"%self.currentObjectiveFunction)
            print("====================================================")
            if(quantilesCount >= quantileSize):
                print("Maximum Iteration Count Reached! Stopping...")
                break

            if(noImprovementIterations > self.params["noImprovementIterationLimit"]):
                print("No improvement limit reached! Stopping the search...")
                break
                
            ##filtrar as facilities mais interessantes e jogar no facility subset
            candidates = [ facility.index for facility in facilitySubet.values()]
            lastCandidateCount = len(candidates)
            while quantilesCount < quantileSize and len(candidates) == lastCandidateCount:
                candidates = self.__getCandidateFacilities(candidates,self.totalDemand,Util.truncate(initialQuantiles[quantilesCount],5),False)
                quantilesCount = quantilesCount + 1

            if(candidates is None or len(candidates)==0 or  len(candidates)==lastCandidateCount):
                break

            facilitySubet = dict(zip([index for index in candidates],[facilitySubet[index] for index in candidates]))
            self.facilities = facilitySubet
            self.__InitializeProblem(facilitySubet,customerSubset)
            self.__getQuantiles()

        return self.currentObjectiveFunction,self.currentSolutionAssignment

