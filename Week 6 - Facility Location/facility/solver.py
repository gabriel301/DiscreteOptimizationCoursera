#!/usr/bin/python
# -*- coding: utf-8 -*-

from collections import namedtuple
from Util import Util
from MIP import MIP
from ParametersConfiguration import ParametersConfiguration
from EnumSettings import Strategy,ImprovementType,SolvingParadigm
from Preprocessing import Preprocessing
from Forest import Forest
from LNS import LNS
import time
import datetime

Point = namedtuple("Point", ['x', 'y'])
Facility = namedtuple("Facility", ['index', 'setup_cost', 'capacity', 'location','distance_quantiles'])
Customer = namedtuple("Customer", ['index', 'demand', 'location'])

def getGreedyInitialSolution(facilities,customers):
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
        obj += Preprocessing.length(customer.location, facilities[solution[customer.index]].location)
    return obj,solution

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
        facilities.append(Facility(i-1, float(parts[0]), int(parts[1]), Point(float(parts[2]), float(parts[3])),[]))
        totalCapacity = totalCapacity + float(parts[0])

    customers = []
    for i in range(facility_count+1, facility_count+1+customer_count):
        parts = lines[i].split()
        customers.append(Customer(i-1-facility_count, int(parts[0]), Point(float(parts[1]), float(parts[2]))))
        totalDemand = totalDemand + int(parts[0])

    print("TOTAL CAPACITY: %s || TOTAL DEMAND: %s"%(totalCapacity,totalDemand))
    paramsConfig = ParametersConfiguration(facility_count,facility_count*customer_count)
    params = paramsConfig.getParameters()
    
    #Preprocessing.getDistanceQuantiles(facilities,params["quantile_intervals"])
    #print("Facility: %s"%facilities[0].index)
    #for quantile in facilities[0].distance_quantiles:
    #    inside = []
    #    for facility in facilities:
    #        if Util.isInsideCircle(facilities[0].location,quantile,facility.location):
    #            inside.append(facility.index)
    #    print("Quantile: %s - Facilities nearby: %s"%(quantile,inside))

    print("============================================================================================================================================================")
    print("Instace Size: %s || Strategy: %s || Paradigm: %s || Improvement Type: %s" % (paramsConfig.instanceSize,params["strategy"],params["paradigm"],params["improvementType"]))
    print("============================================================================================================================================================")
    if(params["paradigm"] == SolvingParadigm.MIP):
        instance = MIP(facilities,customers,"Instance_%s_%s" %(facility_count,customer_count))
        instance.createModel()
        obj,assignments = instance.optimize()
        output_data = '%.2f' % obj + ' ' + str(1) + '\n'
        output_data += ' '.join(map(str,Util.formatSolutionFromMIP(assignments)))
    
    elif (params["paradigm"] == SolvingParadigm.Hybrid):
        obj,assignments = getGreedyInitialSolution(facilities,customers)
        Preprocessing.getDistanceQuantiles(facilities,params["quantile_intervals"])
        search = LNS(assignments,facilities,customers,params["improvementType"])
        obj,assignments = search.optimize()
        #forest = Forest()
        #forest.buildForestFromArray(Util.formatSolutionFromMIP(assignments),facilities,customers)
        #for facility in facilities:
            #print("Facility %s - Quantiles: %s" % (facility.index,facility.distance_quantiles))
        output_data = '%.2f' % obj + ' ' + str(0) + '\n'
        output_data += ' '.join(map(str,assignments))

    elif (params["paradigm"] == SolvingParadigm.Heuristic):
        obj,assignments = getGreedyInitialSolution(facilities,customers)
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

