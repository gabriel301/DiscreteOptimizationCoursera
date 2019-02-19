#!/usr/bin/python
# -*- coding: utf-8 -*-

#################################################################################
# Travel Salesman Problem - Gabriel Augusto - 18/02/2019                        #
# gabriel301@gmail.com                                                          #
# Approach: Guided Local Search + Fast Local Search + 2-opt                     #
# Reference: http://www.bracil.net/CSP/papers/VouTsa-Gls-MetaHeuristic2003.pdf  #
#                                                                               #
#################################################################################

import math
from collections import namedtuple
from collections import OrderedDict
import sys


#Data Structures Definitions
class Edge:
    def __init__(self,p1,p2):
        self.lenght = -1
        self.penalty = 0
        self.p1 = p1
        self.p2 = p2
        self.length = -1

    def getLength(self):
        if self.length == -1:
            self.length = math.sqrt((self.p1.x - self.p2.x)**2 + (self.p1.y - self.p2.y)**2)
        return self.length

class Node:
    def __init__(self,id = -1,x=0.0,y=0.0):
        self.x = x
        self.y = y
        self.id = id #Node ID
        self.adjacentList = {}
        self.active = True

class Graph:
    def __init__ (self):
        self.nodes = []
        self.tourEdges = []
        self.tourNodes = OrderedDict()
        self.length = 0
        self.tourLength = 0

    def addNode (self,node):
        self.nodes.append(node)
        self.length = self.length+1

def solve_it(input_data):
    # Modify this code to run your optimization algorithm

    graph = Graph()
    # parse the input
    lines = input_data.split('\n')

    nodeCount = int(lines[0])

    for i in range(1, nodeCount+1):
        line = lines[i]
        parts = line.split()
        graph.addNode(Node(i-1,float(parts[0]),float(parts[1])))

    # build a trivial solution
    # visit the nodes in the order they appear in the file
    getInitialSolution(graph)
    solutionSequence = graph.tourNodes.keys()
    solutionLength = graph.tourLength


    # calculate the length of the tour
    obj = solutionLength

    # prepare the solution in the specified output format
    output_data = '%.2f' % obj + ' ' + str(0) + '\n'
    output_data += ' '.join(map(str, solutionSequence))

    return output_data

#Get the Initial Solution
#For symmetry breaking, only the egdes a -> b, where a < b are created.
#However, the tour is referenced by both nodes
def getInitialSolution(graph):
    print("=========================================================")
    print("Instance: {} - Initial Solution Start".format(graph.length))

    for index in range(0, graph.length-1):
        edge = Edge(graph.nodes[index],graph.nodes[index+1])
        graph.nodes[index].adjacentList[index+1] = edge
        graph.nodes[index+1].adjacentList[index] = edge
        graph.tourLength = graph.tourLength + edge.getLength()
        print("Edge: {} <-> {} - Length: {}".format(edge.p1.id,edge.p2.id,edge.getLength()))
        print("Tour Length: {}".format(graph.tourLength))
        graph.tourEdges.append(edge)
        graph.tourNodes[index] = index
        graph.tourNodes[index+1] = index+1

    edge = Edge(graph.nodes[0],graph.nodes[-1])
    graph.nodes[0].adjacentList[graph.nodes[-1].id] = edge
    graph.nodes[graph.nodes[-1].id].adjacentList[0] = edge
    graph.tourEdges.append(edge)
    graph.tourLength = graph.tourLength + edge.getLength()
    graph.tourNodes[graph.nodes[-1].id] = graph.nodes[-1].id
    print("Edge: {} <-> {} - Length: {}".format(edge.p1.id,edge.p2.id,edge.getLength()))
    print("Tour Length: {}".format(graph.tourLength))
    print("Instance: {} - Initial Solution End".format(graph.length))
    print("=========================================================")


def swap2opt(graph,node,alpha=1):
    return


#Evaluation of the Augmented Objective Function
def EvaluatePenalized(graph,removedEgdes,addedEdges,alpha=1):
    print("=========================================================")
    print("Instance: {} - Start Penalized Evaluation".format(graph.length))
    removed = 0
    added = 0
    for edge in removedEgdes:
        removed = removed + edge.getLength() + (alpha*edge.penalty)
    print("Cost to be Removed: {} ".format(removed))
    for edge in addedEdges:
        added = added + edge.getLength() + (alpha*edge.penalty)
    print("Cost to be Added: {} ".format(added))
    cost = graph.tourLength - removed + added
    print("Total Cost: {} ".format(cost))
    print("Instance: {} - End Penalized Evaluation".format(graph.length))
    print("=========================================================")
    
    return cost

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        file_location = sys.argv[1].strip()
        with open(file_location, 'r') as input_data_file:
            input_data = input_data_file.read()
        print(solve_it(input_data))
    else:
        print('This test requires an input file.  Please select one from the data directory. (i.e. python solver.py ./data/tsp_51_1)')

