#!/usr/bin/python
# -*- coding: utf-8 -*-

from collections import namedtuple
from Util import Util
from MIP import MIP
from ParametersConfiguration import ParametersConfiguration
from EnumSettings import Strategy,ImprovementType,SolvingParadigm,InitialSolutionFunction
from Preprocessing import Preprocessing
from Forest import Forest
from LNS import LNS
import time
import datetime
import math

Point = namedtuple("Point", ['x', 'y'])
Facility = namedtuple("Facility", ['index', 'setup_cost', 'capacity', 'location','distance_quantiles','cost_per_capacity','frequency'])
Customer = namedtuple("Customer", ['index', 'demand', 'location'])

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

def getRadiusDistanceInitialSolution(facilities,customers,clusters):
    customersToBeAssigned = {}
    customersAssigned = []
    assigments = []
    clusterCapacity = [0]*len(clusters)

    for customer in customers:
        customersToBeAssigned[customer.index] = customer.index
    
    for key in clusters.keys():
        for facility in clusters.get(key):
            clusterCapacity[key] =  clusterCapacity[key] + facilities[facility].capacity

    quantileIntervalSize = len(facilities[0].distance_quantiles)
    quantileIntervalCount = 0
    factor = 1.00
    additional = 0.05
    while (len(customersToBeAssigned) > 0):
        for cluster in clusters.keys():
            for facilityIndex in clusters.get(cluster):
                for customerIndex in customersToBeAssigned.keys():
                    if(Util.isInsideCircle(facilities[facilityIndex].location,facilities[facilityIndex].distance_quantiles[quantileIntervalCount]*factor,customers[customerIndex].location)):
                        if(clusterCapacity[cluster] > customers[customerIndex].demand):
                            assigments.append((facilityIndex,customerIndex))
                            customersAssigned.append(customerIndex)
                            clusterCapacity[cluster]  = clusterCapacity[cluster] - customers[customerIndex].demand

                for customerIndex in customersAssigned:
                    customersToBeAssigned.pop(customerIndex,None)

                customersAssigned.clear()

        if(quantileIntervalCount+1 < quantileIntervalSize):
            quantileIntervalCount = quantileIntervalCount + 1
        else:
            factor = factor + additional

    return assigments

def getNearestNeighbourInitialSolution(facilities,customers,distanceType):
    customersToBeAssigned = {}
    assigments = []
    customersAssigned = []
    remainingCapacity = [facility.capacity for facility in facilities]
    for customer in customers:
        customersToBeAssigned[customer.index] = customer.index

    while (len(customersToBeAssigned) > 0):
        for customerIndex in customersToBeAssigned.keys():
            minDistanceIndex = -1
            currMinDistance = float("inf")
            for facility in facilities:
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

def getClusters(facilities,quantileIntervals):
    size = len(facilities)
    clusterAreas = {}
    lastClusterSize = 0
    clusterSizes = []
    for index in range(0,len(quantileIntervals)):
        numberClusters = round(size/(quantileIntervals[index]*size))
        if (numberClusters == lastClusterSize):
            continue
        lastClusterSize = numberClusters
        clusterSizes.append(numberClusters)

    for index in range(0,len(clusterSizes)):
        clusterAreas[index] = Preprocessing.getFacilityClusters(facilities,clusterSizes[index])

    return clusterAreas

def solve_it(input_data):
    start = time.time()

    print("Start DateTime: {}".format(datetime.datetime.now()))

    # parse the input
    lines = input_data.split('\n')

    parts = lines[0].split()
    facility_count = int(parts[0])
    customer_count = int(parts[1])
    totalCapacity = 0
    totalDemand = 0
    facilities = []

    for i in range(1, facility_count+1):
        parts = lines[i].split()
        facilities.append(Facility(i-1, float(parts[0]), int(parts[1]), Point(float(parts[2]), float(parts[3])),[],Util.truncate(float(parts[0])/int(parts[1]),3),1.0))
        totalCapacity = totalCapacity + float(parts[0])

    customers = []
    for i in range(facility_count+1, facility_count+1+customer_count):
        parts = lines[i].split()
        customers.append(Customer(i-1-facility_count, int(parts[0]), Point(float(parts[1]), float(parts[2]))))
        totalDemand = totalDemand + int(parts[0])

    #print("TOTAL CAPACITY: %s || TOTAL DEMAND: %s"%(totalCapacity,totalDemand))
    paramsConfig = ParametersConfiguration(facility_count,facility_count*customer_count)
    params = paramsConfig.getParameters()
    

    print("============================================================================================================================================================")
    print("Instace Size: %s || Strategy: %s || Paradigm: %s || Improvement Type: %s" % (paramsConfig.instanceSize,params["strategy"],params["paradigm"],params["improvementType"]))
    print("============================================================================================================================================================")
    if(params["paradigm"] == SolvingParadigm.MIP):
        instance = MIP(facilities,customers,"Instance_%s_%s" %(facility_count,customer_count))
        instance.createModel()
        obj,assignments = instance.optimize(params["mipTimeLimit"])
        output_data = '%.2f' % obj + ' ' + str(1) + '\n'
        output_data += ' '.join(map(str,Util.formatSolutionFromMIP(assignments)))
    
    elif (params["paradigm"] == SolvingParadigm.Hybrid):
        
        Preprocessing.getDistanceQuantiles(facilities,params["quantile_intervals"])
        clusterAreas = getClusters(facilities,params["quantile_intervals"])
        if(params["initialSolutionFunction"] == InitialSolutionFunction.Radius):
            initialSolution = getRadiusDistanceInitialSolution(facilities,customers,clusterAreas.get(0))
        else:
            initialSolution = getNearestNeighbourInitialSolution(facilities,customers,params["initialSolutionFunction"])
           
        search = LNS(Util.formatSolutionFromMIP(initialSolution),facilities,customers,params["improvementType"],clusterAreas,params["quantile_intervals"],params["mipTimeLimit"])
        obj,assignments = search.optimize()
        output_data = '%.2f' % obj + ' ' + str(0) + '\n'
        output_data += ' '.join(map(str,assignments))

    elif (params["paradigm"] == SolvingParadigm.Heuristic):
        obj,assignments = getTrivialInitialSolution(facilities,customers)
        output_data = '%.2f' % obj + ' ' + str(0) + '\n'
        output_data += ' '.join(map(str,assignments))

    end = time.time()
    hours, minutes, seconds = Util.getIntervalDuration(start,end)
    print("End DateTime: {}".format(datetime.datetime.now()))
    print("EXECUTION TIME: {:0>2}:{:0>2}:{:05.2f}s".format(int(hours),int(minutes),seconds))
    return output_data

import sys

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        file_location = sys.argv[1].strip()
        with open(file_location, 'r') as input_data_file:
            input_data = input_data_file.read()
        print(solve_it(input_data))
    else:
        print('This test requires an input file.  Please select one from the data directory. (i.e. python solver.py ./data/fl_16_2)')

