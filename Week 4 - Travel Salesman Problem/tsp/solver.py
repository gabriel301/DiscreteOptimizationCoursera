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
import random 
import time

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
        self.adjacentList = {} #Edges that are adjacent to this node - Store the edge because once it is calculated, we do not need to computate it again
        self.active = True #Active flag for the Fast Local Search procedure
    
    def GetAdjacentNodes(self):
        adjacentNodes = []
        for key in self.adjacentList:
            node = self.adjacentList[key].node1 if  self.adjacentList[key].node1.id != self.id else self.adjacentList[key].node2
            adjacentNodes.append(node)
        return adjacentNodes

class Graph:
    def __init__ (self):
        self.nodes = [] #All nodes of the graph
        self.tourEdges = {} #Edges of the current solution
        #self.tourNodes = OrderedDict() #Nodes, in order, of the current solution
        self.tourNodes = []
        self.length = 0 #Number of nodes of the graph
        self.tourLength = 0 #Length of the current tour
        self.edgesPool ={} #Stores all edges that have been used in a solution

    def addNode (self,node):
        self.nodes.append(node)
        self.length = self.length+1

    def addEgdeinTour(self,edge):
        #print("Add Edge in Tour: Edges Tour Count: {}, Pool Count: {} Edge to be Added: {}".format(len(self.tourEdges),len(self.edgesPool),edge.id))     
        self.tourEdges[edge.id] = edge
        self.edgesPool[edge.id] = edge
        self.nodes[edge.node1.id].adjacentList[edge.id] = edge
        self.nodes[edge.node2.id].adjacentList[edge.id] = edge
        self.tourLength = self.tourLength + edge.GetLength()
        #print("Add Edge in Tour: New Edges Tour Count {} Pool Count: {}:".format(len(self.tourEdges),len(self.edgesPool)))
        #input("Press Enter...")

    def addNodeinTour(self,node):
         #self.tourNodes[node.id] = node
         self.tourNodes.append(node)

    def deleteEdgeinTour(self,edge):
        
        distance = edge.GetLength()
        self.tourLength = self.tourLength - distance
        id = edge.id
        del edge.node1.adjacentList[id]
        del edge.node2.adjacentList[id]  
        #print("Delete Edge in Tour: Edges Tour Count: {}, Pool Count: {} Edge to be Deleted: {}".format(len(self.tourEdges),len(self.edgesPool),id))     
        del self.tourEdges[id]
        #print("Delete Edge in Tour: New Edges Tour Count {} Pool Count: {} (Before GC):".format(len(self.tourEdges),len(self.edgesPool)))
        gc.collect()
        #print("Delete Edge in Tour: New Edges Tour Count: {} Pool Count: {} (After GC)".format(len(self.tourEdges),len(self.edgesPool)))

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
    def SwapNodesInTour(self,node1,node2):
        a, b = self.tourNodes.index(node1), self.tourNodes.index(node2)
        self.tourNodes[b], self.tourNodes[a] = self.tourNodes[a], self.tourNodes[b]
    
    def PrintTour(self):
        nodeIds = []
        for node in self.tourNodes:
            nodeIds.append(node.id)
        print(nodeIds)

    def GetTourIds(self):
        nodeIds = []
        for node in self.tourNodes:
            nodeIds.append(node.id)
        return nodeIds

def solve_it(input_data):
    # Modify this code to run your optimization algorithm
    start = time.time()

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
    solutionSequence,objValue = GuidedLocalSearch(graph)

    # prepare the solution in the specified output format
    output_data = '%.2f' % objValue + ' ' + str(0) + '\n'
    output_data += ' '.join(map(str, solutionSequence))

    del graph
    gc.collect()
    end = time.time()
    hours, rem = divmod(end-start, 3600)
    minutes, seconds = divmod(rem, 60)
    print("Execution Time: {:0>2}:{:0>2}:{:05.2f}".format(int(hours),int(minutes),seconds))
    return output_data

#Get the Initial Solution
#For symmetry breaking, only the egdes a -> b, where a < b, are created.
#However, the edge is referenced by both nodes
def GetInitialSolution(graph):
    print("=========================================================")
    print("Instance: {} - Initial Solution Start".format(graph.length))
    ##input("Press Enter to Continue")
    for index in range(0, graph.length-1):
        edge = Edge(graph.nodes[index],graph.nodes[index+1]) 
        graph.addEgdeinTour(edge)
        graph.addNodeinTour(graph.nodes[index])
        #print("Edge: {} Length: {}".format(edge.id,edge.GetLength()))
        #print("Tour Length: {}".format(graph.tourLength))

    edge = Edge(graph.nodes[0],graph.nodes[-1])
    graph.addEgdeinTour(edge)
    graph.addNodeinTour(graph.nodes[-1])
    #graph.addNodeinTour(graph.nodes[0])
    # print("Edge: {} Length: {}".format(edge.id,edge.GetLength()))
    # print("Tour Length: {}".format(graph.tourLength))
    print("Instance: {} - Initial Solution End".format(graph.length))
    print("=========================================================")
    return graph.GetTourIds(),GetObjectiveFunctionValue(graph)

def GetNearestNeighbourhoodSolution(graph):
    print("=========================================================")
    print("Instance: {} - Nearest Neighbour Solution Start".format(graph.length))
    ##input("Press Enter to Continue")
    activeNodes = graph.length
    currentNode = graph.nodes[0]
    while activeNodes > 0:
        bestEdge = None
        currentNode.active = False
        #print("Current Node: {}".format(currentNode.id))
        for j in range(0, graph.length):
            
            if(graph.nodes[j].active == False):
                continue

            if(currentNode.id == graph.nodes[j].id):
                continue

            edge = Edge(currentNode,graph.nodes[j]) 
            if bestEdge is None:
                bestEdge = edge
            else:
                if(bestEdge.GetLength() > edge.GetLength()):
                    del bestEdge
                    bestEdge = edge
        gc.collect()
        if(bestEdge is None):
            lastNode = graph.tourNodes[0]
            bestEdge = Edge(currentNode,lastNode)

        #print("New Edge: {}".format(bestEdge.id)) 
        graph.addEgdeinTour(bestEdge)
        graph.addNodeinTour(currentNode)       
        activeNodes-=1
        currentNode = bestEdge.node1 if bestEdge.node1.id != currentNode.id else bestEdge.node2
        
        
        print("Tour Length: {}".format(graph.tourLength))

    for j in range(0, graph.length):
        graph.nodes[j].active = True

    print("Instance: {} - Nearest Neighbour Solution End".format(graph.length))
    print("=========================================================")
    return graph.GetTourIds(),GetObjectiveFunctionValue(graph)

#1/8 <= beta <= 1/2
def GuidedLocalSearch(graph,iterations = 50000,beta = 0.5,randomSwapsLimit=10,firstImprovement = True):
    print("=========================================================")
    print("Instance: {} - Start Guided Local Search".format(graph.length))
    #currentSolutionSequence, currentObjFunction = GetInitialSolution(graph) 
    currentSolutionSequence, currentObjFunction = GetNearestNeighbourhoodSolution(graph) 
    print("Current Objective Value: {}".format(currentObjFunction))
    alpha = 0
    lastImprovement = 0
    noImprovementLimit = 0 
    randomSwaps = 0
    if (graph.length > 200):
        #noImprovementLimit = ((0.25*math.sqrt(graph.length))/graph.length)*iterations
        noImprovementLimit = 0.01*iterations
    else:
        noImprovementLimit = noImprovementLimit = 0.1*iterations
    for i in range(0,iterations):
        
        solutionSequence, objFunction = FastLocalSearch(graph,alpha,firstImprovement)

        #print("CANDIDATE Objective Value: {}".format(objFunction))
        if currentObjFunction > objFunction:
            currentObjFunction = objFunction
            currentSolutionSequence = solutionSequence
            print("Current Objective Value: {}".format(currentObjFunction))
            lastImprovement = i

        #Random Pertubation Restart
        if not firstImprovement:
            if(i-lastImprovement >= noImprovementLimit):
                if(randomSwaps < randomSwapsLimit):
                    RandomSwaps(graph)
                    randomSwaps +=1
                    lastImprovement = i
                    alpha = 0
                    #noImprovementLimit = 0.5*noImprovementLimit
                    continue
                print("No improvement after {} iterations. Stopping execution.".format(i-lastImprovement))
                break

        alpha = beta * (currentObjFunction/len(graph.tourEdges))
        maxUtilValue = 0
        for key in graph.tourEdges.keys():
            aux = GetUtilValue(graph.tourEdges[key])
            if aux > maxUtilValue:
                maxUtilValue = aux
        
        PenalizeFeatures(graph,maxUtilValue)
    print("Instance: {} - End Guided Local Search".format(graph.length))
    print("=========================================================")
    return currentSolutionSequence, currentObjFunction

def RandomSwaps(graph):
    print("=========================================================")
    print("Instance: {} - Start Random Swaps".format(graph.length))
    limit = int(0.25*graph.length)
    i=0
    while i < limit: 
        pos1 = random.randint(0,graph.length-1)
        pos2 = random.randint(0,graph.length-1)
        
        while pos1 == pos2:
            pos2 = random.randint(0,graph.length-1)
        #print("Graph Length: {} Pos 1: {} Pos 2: {} I: {} Limit: {}".format(graph.length,pos1,pos2,i,limit))
        removedEdges, addedEdges = GetMove(graph,graph.tourNodes[pos1],graph.tourNodes[pos2])
        #print("Graph Length: {} Pos 1: {} Pos 2: {} I: {} Limit: {}".format(graph.length,pos1,pos2,i,limit))
        #print("Removed Edges: {} Added Edges: {} ".format(len(removedEdges),len(addedEdges)))
        for oldEdge in removedEdges:
            graph.deleteEdgeinTour(oldEdge)

        for newEdge in addedEdges:
            graph.addEgdeinTour(newEdge)
        graph.SwapNodesInTour(graph.tourNodes[pos1],graph.tourNodes[pos2])
        #print("Graph Length: {} Pos 1: {} Pos 2: {} I: {} Limit: {}".format(graph.length,pos1,pos2,i,limit))
        i+=1

    for node in graph.nodes:
        node.active = True

    for key in graph.edgesPool:
        graph.edgesPool[key].penalty = 0
    #     graph.tourEdges[key].ActivateNodes()

    print("Current Objective Value: {}".format(graph.tourLength))
    print("Instance: {} - End Random Swaps".format(graph.length))
    print("=========================================================")

#Best Improvement or First Improvement Strategy
def Swap2Opt(graph,node,alpha=1,fisrtImprovement=True):
    activatedNodes = {}
    currentNode = graph.tourNodes.index(node)
    swapNodes = []
    currentRemovedEdges = [] 
    currentAddedEdges = []
    deltaCost = 0
    currentDeltaCost = 0
    for i in range(0,len(graph.tourNodes)):
        if currentNode == i:
            continue
        removedEdges, addedEdges = GetMove(graph,graph.tourNodes[currentNode],graph.tourNodes[i])
        deltaCost = EvaluateMovePenalized(removedEdges,addedEdges,alpha)

        if(deltaCost < currentDeltaCost):
            currentDeltaCost = deltaCost
            swapNodes = []
            swapNodes.append(graph.tourNodes[currentNode])
            swapNodes.append(graph.tourNodes[i])
            currentRemovedEdges = list(removedEdges) 
            currentAddedEdges = list(addedEdges)
            if fisrtImprovement == True:
                break

    for newEdge in currentAddedEdges:
        activatedNodes[newEdge.node1.id] = newEdge.node1
        activatedNodes[newEdge.node2.id] = newEdge.node2
        newEdge.ActivateNodes()

    return activatedNodes,currentDeltaCost,currentRemovedEdges,currentAddedEdges,swapNodes

#This method returns what edges must be added/removed in order to perform the swap movement.
#It does not change the tour. The tour is change only if an improvement is made by the swap
#Check whether the edge exists in graph.edgesPool before creation.
def GetMove(graph,currentNode,swapNode):
    removedEdges = []
    addedEdges = []
    #Get Adjacent nodes in order to create the new edges
    currentNodeAdjacency = currentNode.GetAdjacentNodes()
    swapNodeAdjacency = swapNode.GetAdjacentNodes()
    
    #Include the current adjacent edges in the edges to be removed
    for key in currentNode.adjacentList:
        #Only Removes the edge if current node and swap node are not adjcent
        if(currentNode.adjacentList[key].node1.id != swapNode.id and currentNode.adjacentList[key].node2.id != swapNode.id):
            removedEdges.append(currentNode.adjacentList[key])

    for key in swapNode.adjacentList:
        #Only Removes the edge if current node and swap node are not adjcent
        if(swapNode.adjacentList[key].node1.id != currentNode.id and swapNode.adjacentList[key].node2.id != currentNode.id):
            removedEdges.append(swapNode.adjacentList[key])

    #Edges to Add
    #Swap positions
    for node in currentNodeAdjacency:
        #It only creates the edge if current node and swap node are not adjacents
        if(node.id != swapNode.id):
            newEdge = graph.getEdgeFromPool(swapNode.id,node.id)
            if(newEdge is None):
                newEdge = Edge(swapNode,node)
            addedEdges.append(newEdge)
            # print("Edge to be Added: {} ".format(newEdge.id))
    
    for node in swapNodeAdjacency:
        #It only creates the edge if current node and swap node are not adjacents
        if(node.id != currentNode.id):
            newEdge = graph.getEdgeFromPool(currentNode.id,node.id)
            if(newEdge is None):
                newEdge = Edge(currentNode,node)
            addedEdges.append(newEdge)

    return removedEdges,addedEdges

def FastLocalSearch(graph,alpha,firstImprovement = True):
    currentSolutionSequence = graph.GetTourIds()
    activeNeighbourhoods = GetActivateNeighbourhoods(graph)
    currentObjValue = GetObjectiveFunctionValue(graph)
    while len(activeNeighbourhoods.keys()) > 0:
        key = list(activeNeighbourhoods.keys())[0]
        node = activeNeighbourhoods[key]
        del activeNeighbourhoods[key]
        node.active = False
        
        activatedNodes, deltaCost,removedEdges,addedEdges,swapNodes = Swap2Opt(graph,node,alpha,firstImprovement)
        if(deltaCost < 0):
            for oldEdge in removedEdges:
                graph.deleteEdgeinTour(oldEdge)

            for newEdge in addedEdges:
                graph.addEgdeinTour(newEdge)

            graph.SwapNodesInTour(swapNodes[0],swapNodes[1])
            currentSolutionSequence = graph.GetTourIds()
            currentObjValue = graph.tourLength
            for key in activatedNodes.keys():
                activeNeighbourhoods[key] = activatedNodes[key]

    return currentSolutionSequence, currentObjValue


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

#Evaluation of the Original Objective Function
def Evaluate(removedEdges,addedEdges):
    removed = 0
    added = 0
    for edge in removedEdges:
        removed = removed + edge.GetLength()

    for edge in addedEdges:
        added = added + edge.GetLength()

    delta = added - removed
    
    return delta
#Evaluation of the move using Augmented Objective Function
def EvaluateMovePenalized(removedEdges,addedEdges,alpha=1):

    removed = 0
    added = 0
    for edge in removedEdges:
        removed = removed + edge.GetLength() + (alpha*edge.penalty)

    for edge in addedEdges:
        added = added + edge.GetLength() + (alpha*edge.penalty)

    delta = added - removed

    
    return delta

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        file_location = sys.argv[1].strip()
        with open(file_location, 'r') as input_data_file:
            input_data = input_data_file.read()
        print(solve_it(input_data))
    else:
        print('This test requires an input file.  Please select one from the data directory. (i.e. python solver.py ./data/tsp_51_1)')

