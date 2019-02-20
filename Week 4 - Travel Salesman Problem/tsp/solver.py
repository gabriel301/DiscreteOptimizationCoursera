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
import gc
import queue 


#Data Structures Definitions
class Edge:
    def __init__(self,p1,p2):
        self.lenght = -1
        self.penalty = 0
        self.p1 = p1
        self.p2 = p2
        self.length = -1
        self.util = -1

    def GetLength(self):
        if self.length == -1:
            self.length = math.sqrt((self.p1.x - self.p2.x)**2 + (self.p1.y - self.p2.y)**2)
        return self.length

    def ActivateNodes(self):
        self.p1.active = True
        self.p2.active = True

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
        self.tourEdges = {}
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
   
    solutionSequence,objValue = GuidedLocalSearch(graph)


    # prepare the solution in the specified output format
    output_data = '%.2f' % objValue + ' ' + str(0) + '\n'
    output_data += ' '.join(map(str, solutionSequence))

    del graph
    gc.collect()
    return output_data

#Get the Initial Solution
#For symmetry breaking, only the egdes a -> b, where a < b, are created.
#However, the edge is referenced by both nodes
def GetInitialSolution(graph):
    print("=========================================================")
    print("Instance: {} - Initial Solution Start".format(graph.length))

    for index in range(0, graph.length-1):
        edge = Edge(graph.nodes[index],graph.nodes[index+1])
        graph.nodes[index].adjacentList[index+1] = edge
        graph.nodes[index+1].adjacentList[index] = edge
        graph.tourLength = graph.tourLength + edge.GetLength()
        print("Edge: {} <-> {} - Length: {}".format(edge.p1.id,edge.p2.id,edge.GetLength()))
        print("Tour Length: {}".format(graph.tourLength))
        graph.tourEdges[str(index)+"-"+str(index+1)] = edge
        graph.tourNodes[index] = index
        graph.tourNodes[index+1] = index+1

    edge = Edge(graph.nodes[0],graph.nodes[-1])
    graph.nodes[0].adjacentList[graph.nodes[-1].id] = edge
    graph.nodes[graph.nodes[-1].id].adjacentList[0] = edge
    graph.tourEdges[str(graph.nodes[0].id)+"-"+str(graph.nodes[-1].id)] = edge
    graph.tourLength = graph.tourLength + edge.GetLength()
    graph.tourNodes[graph.nodes[-1].id] = graph.nodes[-1].id
    print("Edge: {} <-> {} - Length: {}".format(edge.p1.id,edge.p2.id,edge.GetLength()))
    print("Tour Length: {}".format(graph.tourLength))
    print("Instance: {} - Initial Solution End".format(graph.length))
    print("=========================================================")
    return graph.tourNodes.keys(), graph.tourLength

#1/8 <= beta <= 1/2
def GuidedLocalSearch(graph,iterations = 10000,beta = 0.5):
    currentSolutionSequence, currentObjFunction = GetInitialSolution(graph)  
    for i in range(0,iterations):
        alpha = beta * (currentObjFunction/len(graph.tourEdges))
        solutionSequence, objFunction = FastLocalSearch(graph,alpha)

        if currentObjFunction > objFunction:
            currentObjFunction = objFunction
            currentSolutionSequence = solutionSequence
        else:
            break       

        maxUtilValue = 0
        for edge in graph.tourEdges:
            aux = GetUtilValue(edge)
            if aux > maxUtilValue:
                maxUtilValue = aux

        PenalizeFeatures(graph,maxUtilValue)

    return currentSolutionSequence, currentObjFunction

def Swap2Opt(graph,node,alpha=1):
    activatedNodes = []
    
    return activatedNodes

def FastLocalSearch(graph,alpha):
    currentSolutionSequence = graph.tourNodes.keys()
    currentAugmentedObj = GetAlgumentedObjectiveFunctionValue(graph,alpha)
    activeNeighbourhoods = GetActivateNeighbourhoods(graph)
    while len(activeNeighbourhoods.keys()) > 0:
        key = activeNeighbourhoods.keys()[0]
        node = activeNeighbourhoods.get(key)
        del activeNeighbourhoods[key]
        node.active = False
        activatedNodes = Swap2Opt(graph,node,alpha)
        newAugmentedObjValue = GetAlgumentedObjectiveFunctionValue(graph,alpha)
        if(currentAugmentedObj > newAugmentedObjValue):
            currentAugmentedObj = newAugmentedObjValue
            currentSolutionSequence = graph.tourNodes.keys()
            for node in activatedNodes:
                node.active = True
                activeNeighbourhoods[node.id] = node
        
    return currentSolutionSequence, currentAugmentedObj


def GetActivateNeighbourhoods(graph):
    d = OrderedDict()
    for node in graph.nodes:
        if node.active == True:
            d[node.id] = node
    return d


def PenalizeFeatures(graph, maxUtil):
    for edge in graph.tourEdges:
        if edge.util == maxUtil:
            edge.penalty += 1
            edge.activeNeighbourhoods()


#Calculate the Penalty for each edge presented in the local optima solution
def GetUtilValue(edge):
    edge.util = edge.getLength()/(1+edge.penalty)
    return edge.util

def GetObjectiveFunctionValue(graph):
    length = 0
    for edge in graph.tourEdges:
        length += edge.getLength()
    return length

def GetAlgumentedObjectiveFunctionValue(graph,alpha):
    length = 0
    for edge in graph.tourEdges:
        length += (edge.getLength() + (alpha*edge.penalty))
    return length

#Evaluation of the move using Augmented Objective Function
def EvaluateMovePenalized(graph,removedEgdes,addedEdges,alpha=1):
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

