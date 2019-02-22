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

#This is structure is an attemp to avoid calculating all possible edges to the problem in one shot, ie, precompute the distance matrix
#The idea is store only the edges that are part of the current solution or edges that have been a part of one solution.
#This is necessary due the penalties that the Guided Local Search attributes to edges.
#Thus, edges (moves) that not improve the current solution are calculated (for evaluation), but discarted since no penalty will be attributed to them.
#Altough it can save memory, it increase the computation time, since some edges might be calculated more than once while the algorithm is running.
class Edge:
    def __init__(self,p1,p2):
        self.length = -1 #Distance between node 1 and node 2
        self.penalty = 0 #Guided local search penalty
        
        # node1.id < node2.id for symmetry breaking. This reduces the number of edges in half
        #Eg: Edge 1->2 is the same as Edge 2->1 in this problem. Thus, we only store the edge
        #2->1 and reference this edge in the both nodes
        if p1.id < p2.id:
            self.node1 = p1 #Node 1
            self.node2 = p2 #node 2 
        else:
            self.node1 = p2 #Node 1
            self.node2 = p1 #node 2 
        self.id = str(self.node1.id)+"-"+str(self.node2.id)
        self.util = -1 #Guided Local Search utility function value

    def GetLength(self):
        if self.length == -1:
            self.length = math.sqrt((self.node1.x - self.node2.x)**2 + (self.node1.y - self.node2.y)**2)
        return self.length

    #Activate the points (nodes) that represent sub-neighbourhoods
    def ActivateNodes(self):
        self.node1.active = True
        self.node2.active = True

class Node:
    def __init__(self,id = -1,x=0.0,y=0.0):
        self.x = x #Euclidean X coordinate
        self.y = y #Euclidean Y coordinate
        self.id = id #Node ID
        self.adjacentList = {} #Edges that are adjacent to this node
        self.active = True #Active flag for the Fast Local Search procedure

class Graph:
    def __init__ (self):
        self.nodes = [] #All nodes of the graph
        self.tourEdges = {} #Edges of the current solution
        self.tourNodes = OrderedDict() #Nodes, in order, of the current solution
        self.length = 0 #Number of nodes of the graph
        self.tourLength = 0 #Length of the current tour
        self.edgesPool ={} #Stores all edges that have been used in a solution

    def addNode (self,node):
        self.nodes.append(node)
        self.length = self.length+1

    def addEgdeinTour(self,edge):
        self.tourEdges[edge.id] = edge
        self.edgesPool[edge.id] = edge
        self.nodes[edge.node1.id].adjacentList[edge.id] = edge
        self.nodes[edge.node2.id].adjacentList[edge.id] = edge
        self.tourLength = self.tourLength + edge.GetLength()
    
    def addNodeinTour(self,node):
         self.tourNodes[node.id] = node

    def deleteEdgeinTour(self,edge):
        distance = edge.GetLength()
        self.tourLength = self.tourLength - distance
        id = edge.id
        del edge.node1.adjacentList[id]
        del edge.node2.adjacentList[id]       
        del self.tourEdges[id]
        gc.collect()

    def getFirstTourElement(self):
        return next(iter(self.tourNodes))

    def getLastTourElement(self):
        return next(reversed(self.tourNodes))

    def getEdgeFromPool(self,nodeId1,nodeId2):
        if (nodeId1 < nodeId2):
            key = str(nodeId1)+"-"+str(nodeId2)
            if key in self.edgesPool:
                return self.edgesPool[key]
            else:
                return None
        else:
            key = str(nodeId2)+"-"+str(nodeId1)
            if key in self.edgesPool:
                return self.edgesPool[key]
            else:
                return None
    def rearrangeTourNodes(self,newRoute):
        ordered = OrderedDict((k, self.tourNodes[k]) for k in newRoute)
        self.tourNodes = ordered
        gc.collect()

def solve_it(input_data):
    # Modify this code to run your optimization algorithm

    graph = Graph()
    # parse the input
    lines = input_data.split('\n')

    nodeCount = int(lines[0])

    for i in range(1, nodeCount+1):
        line = lines[i]
        parts = line.split()

        #Build the graph (Without the edges)
        graph.addNode(Node(i-1,float(parts[0]),float(parts[1])))

    #Guided Fast Local Search (GFLS)
    solutionSequence,objValue = GuidedLocalSearch(graph,100,0.5)
    #solutionSequence,objValue = GetInitialSolution(graph)

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
    #print("=========================================================")
    #print("Instance: {} - Initial Solution Start".format(graph.length))
    ##input("Press Enter to Continue")
    for index in range(0, graph.length-1):
        edge = Edge(graph.nodes[index],graph.nodes[index+1]) 
        graph.addEgdeinTour(edge)
        graph.addNodeinTour(graph.nodes[index])
        graph.addNodeinTour(graph.nodes[index+1])
        #print("Edge: {} Length: {}".format(edge.id,edge.GetLength()))
        #print("Tour Length: {}".format(graph.tourLength))

    edge = Edge(graph.nodes[0],graph.nodes[-1])
    graph.addEgdeinTour(edge)
    graph.addNodeinTour(graph.nodes[-1])
    graph.addNodeinTour(graph.nodes[0])
    # print("Edge: {} Length: {}".format(edge.id,edge.GetLength()))
    # print("Tour Length: {}".format(graph.tourLength))
    # print("Instance: {} - Initial Solution End".format(graph.length))
    # print("=========================================================")
    return graph.tourNodes.keys(), graph.tourLength

#1/8 <= beta <= 1/2
def GuidedLocalSearch(graph,iterations = 1000,beta = 0.5):
    print("=========================================================")
    print("Instance: {} - Start Guided Local Search".format(graph.length))
    currentSolutionSequence, currentObjFunction = GetInitialSolution(graph) 
    print("Current Objective Value: {}".format(currentObjFunction))

    for i in range(0,iterations):
        alpha = beta * (currentObjFunction/len(graph.tourEdges))
        solutionSequence, objFunction = FastLocalSearch(graph,alpha)

        if currentObjFunction > objFunction:
            currentObjFunction = objFunction
            currentSolutionSequence = solutionSequence
            print("GLS New Current Objective Value: {}".format(currentObjFunction))
            #input("Press Enter...")
        # else:
        #     break       

        maxUtilValue = 0
        for key in graph.tourEdges.keys():
            aux = GetUtilValue(graph.tourEdges[key])
            if aux > maxUtilValue:
                maxUtilValue = aux

        PenalizeFeatures(graph,maxUtilValue)

    print("Instance: {} - End Guided Local Search".format(graph.length))
    print("=========================================================")
    return currentSolutionSequence, currentObjFunction

def Swap2Opt(graph,node,alpha=1):
    activatedNodes = {}
    currentObjValue = GetAlgumentedObjectiveFunctionValue(graph,alpha)
    for key in node.adjacentList.keys():
        print("2-OPT: CURRENT EDGE: {}".format(key))
        newRoute, removedEdges, addedEdges = GetMove(graph,node,node.adjacentList[key])
        # skip = False
        # for edge in addedEdges:
        #     if (edge.id in graph.tourEdges):
        #         skip = True
        #         break
        # if skip:
        #     continue
        moveCost = EvaluateMovePenalized(graph,removedEdges,addedEdges,alpha)

        if(moveCost < currentObjValue):
            currentObjValue = moveCost
            for oldEdge in removedEdges:
                graph.deleteEdgeinTour(oldEdge)

            for newEdge in addedEdges:
                activatedNodes[newEdge.node1.id] = newEdge.node1
                activatedNodes[newEdge.node2.id] = newEdge.node2
                newEdge.ActivateNodes()
                graph.addEgdeinTour(newEdge)

            graph.rearrangeTourNodes(newRoute)
            return activatedNodes,currentObjValue

    return activatedNodes,currentObjValue

#TODO Realize what subsequence must be reversed and find what edges will be added/removed
#Check whether the edge exists in graph.edgesPool before creation to add (locate by id)
def GetMove(graph,node,edge):
    print("=========================================================")
    print("Instance: {} - Start Get Move".format(graph.length))
    removedEdges = []
    addedEdges = []
    #Remove the adjacent edges
    removedEdges.append(edge)
    tourNodes = tuple(graph.tourNodes)
    firstElementId = graph.getFirstTourElement()
    lastElementId = graph.getLastTourElement()
    circleEdge = None
    #Remove the circular edge
    if(firstElementId < lastElementId):
        circleEdge = graph.tourEdges[str(firstElementId)+"-"+str(lastElementId)]
    else:
         circleEdge = graph.tourEdges[str(lastElementId)+"-"+str(firstElementId)]
    removedEdges.append(circleEdge)

    adjacentNode = edge.node1 if edge.node1.id != node.id else edge.node2
    
    #Reverse the list
    adjacentNodePos = tourNodes.index(adjacentNode.id)
    currentNodePos = tourNodes.index(node.id)
    route = list(graph.tourNodes.keys())
    newRoute = []
    if(currentNodePos < adjacentNodePos):
        newRoute.extend(route[0:currentNodePos+1])
        newRoute.extend(route[len(route)-1:currentNodePos:-1])
    else:
        newRoute.extend(route[0:adjacentNodePos+1])
        newRoute.extend(route[len(route)-1:adjacentNodePos:-1])    
    #Edges to Add
    #Adjacent edge
    adjacentEdge = graph.getEdgeFromPool(newRoute[currentNodePos],newRoute[adjacentNodePos])
    if(adjacentEdge is None):
        adjacentEdge = Edge(graph.nodes[newRoute[currentNodePos]],graph.nodes[newRoute[adjacentNodePos]])
    #Circular Edge
    circularEdge = graph.getEdgeFromPool(newRoute[0],newRoute[len(newRoute)-1])
    if(circularEdge is None):
        circularEdge = Edge(graph.nodes[newRoute[0]],graph.nodes[newRoute[len(newRoute)-1]])
    addedEdges.append(adjacentEdge)
    addedEdges.append(circularEdge)

    print("Current Route: {}".format(list(graph.tourNodes.keys())))
    print("New Route: {}".format(newRoute))
    print("Instance: {} - End Get Move".format(graph.length))
    print("=========================================================")
    return newRoute,removedEdges,addedEdges

def FastLocalSearch(graph,alpha):
    #print("=========================================================")
    #print("Instance: {} - Start Fast Local Search".format(graph.length))
    currentSolutionSequence = graph.tourNodes.keys()
    currentAugmentedObj = GetAlgumentedObjectiveFunctionValue(graph,alpha)
    currentObjFunction = graph.tourLength
    activeNeighbourhoods = GetActivateNeighbourhoods(graph)
    #print("Current Augmented Objective Value: {} - Active Neighbourhoods {} ".format(currentAugmentedObj,len(activeNeighbourhoods)))
    while len(activeNeighbourhoods.keys()) > 0:
        key = list(activeNeighbourhoods.keys())[0]
        node = activeNeighbourhoods[key]
        del activeNeighbourhoods[key]
        node.active = False
        # if node.id == graph.getFirstTourElement() or node.id == graph.getLastTourElement():
        #     continue
         
        activatedNodes, newAugmentedObjValue = Swap2Opt(graph,node,alpha)
        if(currentAugmentedObj > newAugmentedObjValue):
            currentAugmentedObj = newAugmentedObjValue
            currentSolutionSequence = graph.tourNodes.keys()
            currentObjFunction = graph.tourLength
            for key in activatedNodes.keys():
                activeNeighbourhoods[key] = activatedNodes[key]
            #print("FLS - New Current Objective Value: {} ".format(currentObjFunction))
            #print("FLS - New Current Augmented Objective Value: {} - Active Neighbourhoods {} ".format(currentAugmentedObj,len(activeNeighbourhoods)))
    #print("Instance: {} -  End Fast Local Search".format(graph.length))
    #print("=========================================================")
    return currentSolutionSequence, GetObjectiveFunctionValue(graph)


def GetActivateNeighbourhoods(graph):
    d = OrderedDict()
    for node in graph.nodes:
        if node.active == True:
            d[node.id] = node
    return d

#Penalizes the edges in the solution with the maximum utility value and activated the nodes (sub-neighbourhoods) at their ends
def PenalizeFeatures(graph, maxUtil):
    for key in graph.tourEdges.keys():
        if graph.tourEdges[key].util == maxUtil:
            graph.tourEdges[key].penalty += 1
            graph.tourEdges[key].ActivateNodes()


#Calculate the Penalty for each edge presented in the local optima solution
def GetUtilValue(edge):
    edge.util = edge.GetLength()/(1+edge.penalty)
    return edge.util

def GetObjectiveFunctionValue(graph):
    length = 0
    for key in graph.tourEdges.keys():
        length += graph.tourEdges[key].GetLength()
    return length

def GetAlgumentedObjectiveFunctionValue(graph,alpha):
    length = 0
    for key in graph.tourEdges.keys():
        length += (graph.tourEdges[key].GetLength() + (alpha*graph.tourEdges[key].penalty))
    return length

#Evaluation of the move using Augmented Objective Function
def EvaluateMovePenalized(graph,removedEdges,addedEdges,alpha=1):
    print("=========================================================")
    print("Instance: {} - Start Penalized Evaluation".format(graph.length))
    removed = 0
    added = 0
    for edge in removedEdges:
        removed = removed + edge.GetLength() + (alpha*edge.penalty)
        print("Edge to be Removed: {} ".format(edge.id))
    print("Cost to be Removed: {} ".format(removed))
    for edge in addedEdges:
        added = added + edge.GetLength() + (alpha*edge.penalty)
        print("Edge to be Added: {} ".format(edge.id))
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

