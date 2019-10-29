import math
import numpy as np
from sklearn.cluster import MiniBatchKMeans
from EnumSettings import InitialSolutionFunction
from Util import Util

class Preprocessing:

    #Calculate the Euclidean distance between two points
    @staticmethod    
    def getEuclideanDistance(point1, point2):
        return math.sqrt((point1.x - point2.x)**2 + (point1.y - point2.y)**2)

    #Return quantiles for distances between facilities
    @staticmethod   
    def getDistanceQuantiles(facilities,intervals):
        print("Genarating Distance Quantiles...")
        for f1 in facilities.values():
            distances = []
            for f2 in facilities.values():
                if f1.index == f2.index:
                    continue
                distances.append(Preprocessing.getEuclideanDistance(f1.location,f2.location))
            f1.distance_quantiles.extend(np.quantile(a=distances,q=intervals, interpolation='midpoint').tolist())

    #Return quantiles for distances between facilities
    @staticmethod   
    def getFacilityClusters(facilities,numberClusters):
        print("Genarating %s Clusters..."%numberClusters)
        clusters = {}
        dataPoints = np.array([[facility.location.x,facility.location.y] for facility in facilities])
        indexes = [facility.index for facility in facilities]
        kmeans = MiniBatchKMeans(n_clusters=numberClusters, random_state=0,tol=1.e-6).fit(dataPoints)
        for i in range(0,len(indexes)):
            if kmeans.labels_[i]not in clusters.keys():
                clusters[kmeans.labels_[i]] = []
            clusters.get(kmeans.labels_[i]).append(indexes[i])
        
        return clusters

    #Calculate the Manhatan distance between two points
    @staticmethod
    def getManhatanDistance(p1,p2):
       return  math.fabs(p1.x-p2.x) + math.fabs(p1.y-p2.y)

    #Get a trivial solution
    @staticmethod
    def getTrivialInitialSolution(facilities,customers):
        # build a trivial solution
        # pack the facilities one by one until all the customers are served
        solution = [-1]*len(customers)
        capacity_remaining = [f.capacity for f in facilities]

        facility_index = 0
        for customer in customers:
            if capacity_remaining[facility_index] >= customer.demand:
                solution[customer.index] = facility_index
                capacity_remaining[facility_index] -= customer.demand
            else:
                facility_index += 1
                assert capacity_remaining[facility_index] >= customer.demand
                solution[customer.index] = facility_index
                capacity_remaining[facility_index] -= customer.demand

        used = [0]*len(facilities)
        for facility_index in solution:
            used[facility_index] = 1

        # calculate the cost of the solution
        obj = sum([f.setup_cost*used[f.index] for f in facilities])
        for customer in customers:
            obj += Preprocessing.getEuclideanDistance(customer.location, facilities[solution[customer.index]].location)
        return obj,solution

    #Get Initial Solution based on the radius distance
    @staticmethod
    def getRadiusDistanceInitialSolution(facilities,customers,clusters):
        customersToBeAssigned = {}
        customersAssigned = []
        assigments = []
        facilityCapacity = dict((facility.index,facility.capacity) for facility in facilities.values())
        facilitiesArray  = [facility for facility in facilities.values()]

        for customer in customers:
            customersToBeAssigned[customer.index] = customer.index

        quantileIntervalSize = len(facilities[0].distance_quantiles)
        quantileIntervalCount = 0
        factor = 1.00
        additional = 0.05
        facilitiesArray.sort(key=lambda x: x.cost_per_capacity, reverse=True)
        while (len(customersToBeAssigned) > 0):
            for facility in facilitiesArray:
                for customerIndex in customersToBeAssigned.keys():
                    if(Util.isInsideCircle(facility.location,facility.distance_quantiles[quantileIntervalCount]*factor,customers[customerIndex].location)):
                        if(facilityCapacity[facility.index] > customers[customerIndex].demand):
                            assigments.append((facility.index,customerIndex))
                            customersAssigned.append(customerIndex)
                            facilityCapacity[facility.index]  = facilityCapacity[facility.index]  - customers[customerIndex].demand

                for customerIndex in customersAssigned:
                    customersToBeAssigned.pop(customerIndex,None)

                customersAssigned.clear()

            if(quantileIntervalCount+1 < quantileIntervalSize):
                quantileIntervalCount = quantileIntervalCount + 1
            else:
                factor = factor + additional

        return assigments

    #Get Initial Solution using Euclidean Distance or Manhatan Distance
    @staticmethod
    def getNearestNeighbourInitialSolution(facilities,customers,distanceType):
        customersToBeAssigned = {}
        assigments = []
        customersAssigned = []
        remainingCapacity = dict([(facility.index,facility.capacity) for facility in facilities.values()]) 
        for customer in customers:
            customersToBeAssigned[customer.index] = customer.index

        while (len(customersToBeAssigned) > 0):
            for customerIndex in customersToBeAssigned.keys():
                minDistanceIndex = -1
                currMinDistance = float("inf")
                for facility in facilities.values():
                    if(distanceType == InitialSolutionFunction.Manhatan):
                        currDistance = Preprocessing.getManhatanDistance(facility.location,customers[customerIndex].location)
                    else:
                        currDistance = Preprocessing.getEuclideanDistance(facility.location,customers[customerIndex].location)

                    if currDistance < currMinDistance and remainingCapacity[facility.index] >= customers[customerIndex].demand:
                        currMinDistance = currDistance
                        minDistanceIndex = facility.index

                assigments.append((minDistanceIndex,customerIndex))
                remainingCapacity[minDistanceIndex] = remainingCapacity[minDistanceIndex] - customers[customerIndex].demand
                customersAssigned.append(customerIndex)

            for customerIndex in customersAssigned:
                customersToBeAssigned.pop(customerIndex,None)

            customersAssigned.clear()
        return assigments


    #Get Facilities Clusters base in the quantiles
    @staticmethod
    def getClusters(facilities,quantileIntervals):
        size = len(facilities)
        clusterAreas = {}
        lastClusterSize = 0
        clusterSizes = []
        for index in range(0,len(quantileIntervals)):
            numberClusters = round(size/(quantileIntervals[index]*size))
            if (numberClusters == lastClusterSize or numberClusters > size):
                continue
            lastClusterSize = numberClusters
            clusterSizes.append(numberClusters)

        for index in range(0,len(clusterSizes)):
            clusterAreas[index] = Preprocessing.getFacilityClusters(facilities,clusterSizes[index])

        return clusterAreas


            