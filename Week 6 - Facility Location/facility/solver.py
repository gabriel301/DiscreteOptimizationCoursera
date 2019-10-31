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
        instance = MIP(facilities,customers,"Instance_%s_%s" %(facility_count,customer_count),params["mipSolver"])
        obj,assignments,_ = instance.optimize(params["mipTimeLimit"])
        output_data = '%.2f' % obj + ' ' + str(1) + '\n'
        output_data += ' '.join(map(str,Util.formatSolutionFromMIP(assignments)))
    
    elif (params["paradigm"] == SolvingParadigm.Hybrid):
         
        search = LNS(facilities,customers,params)
        obj,assignments = search.optimize()
        output_data = '%.2f' % obj + ' ' + str(0) + '\n'
        output_data += ' '.join(map(str,assignments))

    elif (params["paradigm"] == SolvingParadigm.Heuristic):
        obj,assignments = Preprocessing.getTrivialInitialSolution(facilities,customers)
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

