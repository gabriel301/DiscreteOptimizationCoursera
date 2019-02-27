#!/usr/bin/python
# -*- coding: utf-8 -*-

###############################################################################################################
# Travel Salesman Problem - Gabriel Augusto - 18/02/2019                                                      #
# gabriel301@gmail.com                                                                                        #
# Approach: Guided Local Search + Fast Local Search + 2-opt + Manhatan Distance Relaxation                    #
# Reference: http://www.bracil.net/CSP/papers/VouTsa-Gls-MetaHeuristic2003.pdf                                #
#                                                                                                             #
###############################################################################################################

import math
from collections import OrderedDict
import sys
import gc
import random 
import time
from enum import Enum
import datetime

###################################
# Data Structures Definitions     #
###################################

#   This is structure is an attemp to avoid calculating all possible edges to the problem in one shot, ie, precompute the distance matrix and thus, save memory (be memory efficient)
#   The idea is store only the edges that are part of the current solution or edges that have been a part of one solution.
#   This is necessary due the penalties that the Guided Local Search attributes to edges.
#   Thus, edges (moves) that not improve the current solution are calculated (for evaluation), but discarted since no penalty will be attributed to them.
#   Altough it can save memory, it might increase the computation time, since creating one edge is more expensive than only querying a value in a matrix
class Edge:
    def __init__(self,p1,p2):
        self.length = -1 #  Distance between node 1 and node 2
        self.penalty = 0 #  Guided local search penalty
        
        #   node1.id < node2.id for symmetry breaking. This reduces the number of edges in half
        #   Eg: Edge 1->2 is the same as Edge 2->1 in this problem. Thus, we only store the edge
        #   1->2 and reference this edge in the both nodes
        if p1.id < p2.id:
            self.node1 = p1 #   Node 1
            self.node2 = p2 #   node 2 
        else:
            self.node1 = p2 #   Node 1
            self.node2 = p1 #   node 2 

        self.id = str(self.node1.id)+"-"+str(self.node2.id)
        self.util = -1 #    Guided Local Search utility function value

    #   Calculate the length in case it was not calculated before and store it in the local variable. Otherwise, just return the stored value
    def GetLength(self):
        if self.length == -1:
            self.length = math.sqrt((self.node1.x - self.node2.x)**2 + (self.node1.y - self.node2.y)**2)
        return self.length

    #   Activate the points (nodes) that are in the both ends os the edge
    #   In this case, the nodes represent sub-neighbourhoods for the problem
    def ActivateNodes(self):
        self.node1.active = True
        self.node2.active = True

class Node:
    def __init__(self,id = -1,x=0.0,y=0.0):
        self.x = x #    Euclidean X coordinate
        self.y = y #    Euclidean Y coordinate
        self.id = id #  Node ID
        self.adjacentList = {} #    Edges that are adjacent to this node - Store the edge because once it is calculated, we do not need to computate it again
        self.active = True #    Active flag for the Fast Local Search procedure
        self.tourPos = -1 # the position of the node in the Tour List
    
    #   Return the adjacent Nodes of a node
    #   List[0] = Previous Node
    #   List[1] = Next Node
    def GetAdjacentNodes(self,tourSize):
        adjacentNodes = [None,None]
        aux = []
        for key in self.adjacentList:
            node = self.adjacentList[key].node1 if self.adjacentList[key].node1.id != self.id else self.adjacentList[key].node2
            aux.append(node)

        #   In case the node is at the ends of the Tour List, the calculation is reversed than when the node is not at the ends
        if(self.tourPos == 0 or self.tourPos == tourSize-1):
            if self.tourPos - aux[0].tourPos < self.tourPos - aux[1].tourPos:
                adjacentNodes[0] = aux[0]
                adjacentNodes[1] = aux[1]
            else:
                adjacentNodes[0] = aux[1]
                adjacentNodes[1] = aux[0]
        else:
            if self.tourPos - aux[0].tourPos > self.tourPos - aux[1].tourPos:
                adjacentNodes[0] = aux[0]
                adjacentNodes[1] = aux[1]
            else:
                adjacentNodes[0] = aux[1]
                adjacentNodes[1] = aux[0]

        return adjacentNodes
    
    #   Get the Foward edge of the node
    #   Eg. If the node is 2, and the edges are 1<->2<->3, return the 2<->3 edge 
    def GetNextEdge(self,tourSize):

        nexNode = self.GetAdjacentNodes(tourSize)[1]
        for key in self.adjacentList:
            if (self.adjacentList[key].node1.id == nexNode.id or self.adjacentList[key].node2.id == nexNode.id):
                return self.adjacentList[key]
        return None        

    #   Get the previous edge of the node
    #   Eg. If the node is 2, and the edges are 1<->2<->3, return the 1<->2 edge 
    def GetPreviousEdge(self,tourSize):
        prevNode = self.GetAdjacentNodes(tourSize)[0]
        for key in self.adjacentList:
            if (self.adjacentList[key].node1.id == prevNode.id or self.adjacentList[key].node2.id == prevNode.id):
                return self.adjacentList[key]
        return None

class Graph:
    def __init__ (self):
        self.nodes = [] #   All nodes of the graph
        self.tourEdges = {} #   Edges of the current solution
        self.tourNodes = [] #   List that stores the visiting sequence of the nodes in the tour
        self.length = 0 #   Number of nodes of the graph
        self.tourLength = 0 #   Length tour path
        self.edgesPool ={} #    Stores all edges that have been checked by the local search procedure. 
                           #Thus, it is not necessary to compute them again if they are evaluated more than onde, saving processing time

    #   Adds a Node in the graph
    def addNode (self,node):
        self.nodes.append(node)
        self.length = self.length+1

    #   Adds and edge in the current tour
    def addEgdeinTour(self,edge): 
        self.tourEdges[edge.id] = edge
        self.nodes[edge.node1.id].adjacentList[edge.id] = edge
        self.nodes[edge.node2.id].adjacentList[edge.id] = edge
        self.tourLength = self.tourLength + edge.GetLength()
        self.addEgdeinPool(edge)
        
    #   Adds an edge in the Edge's Pool
    def addEgdeinPool(self,edge):
        self.edgesPool[edge.id] = edge

    #   Adds a node in the tour
    def addNodeinTour(self,node):
         self.tourNodes.append(node)
         node.tourPos = len(self.tourNodes)-1

    #   Delete an edge from the tour and from the adjacent list of the reffered nodes
    def deleteEdgeinTour(self,edge):      
        distance = edge.GetLength()
        self.tourLength = self.tourLength - distance
        id = edge.id
        del edge.node1.adjacentList[id]
        del edge.node2.adjacentList[id]  
        del self.tourEdges[id]
        gc.collect()

    #   Get and edge from the Edges' Pool, or return None if the edge is not found.
    #   All edges Ids are in the for node1.id-node2.id where node1.id<node2.id
    #   Eg. If the query is by node1.id = 2, and node 2.id = 1, the Edge queried will be 1<->2
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

    #   Swap 2 nodes in the tour.
    #   Used by the Swap Heuristic Function
    def SwapNodesInTour(self,node1,node2):
        a, b = self.tourNodes.index(node1), self.tourNodes.index(node2)
        self.tourNodes[b].tourPos, self.tourNodes[a].tourPos = self.tourNodes[a].tourPos, self.tourNodes[b].tourPos
        self.tourNodes[b], self.tourNodes[a] = self.tourNodes[a], self.tourNodes[b]

    #   Rearrange the tour sequence to reflect an edge exchange. Used by the 2-Opt Heuristic Function
    #   How it Works: In the 2-Opt Iteration Loop, one node is select to be the "Base" node, and then we loop over all edges of the tour 
    #   from this base node. Eg. Supose the tour is 1-6-4-2-3-5. If the Base Node is 4, the we fix the forward edge (4,2) to be removed 
    #   and iterate over the edges (3,5),(5,1), and (1,6), removing them (together with the base edge (4,2)) and evaluating the cost of adding new edges.
    #   For iterating over the edges, we actually iterate over the nodes in the tour (in the sequence they appear in the tour), starting 2 positions ahead from the base node position.
    #   In the code, this iterated node is called swapNode.
    #   In this example, we will iterate over nodes 3,5,1. We stop when the swapNode node is adjacent to the current node,ie node 6.
    #   (In this case, we only remove the forward edges, then, iterating over the previous adjacent node of the base node would eliminate the previous base node edge).
    
    #   Supose that the best move is to remove the edges (4,2) and (3,5) and to add the edges (3,4) and (2,5) (ie, our swap node is 3).
    #   Note that the new edges are built by linking the Base node (4) to the swap node (3) and the foward adjacent node of the base node (2) and the foward adjacent node
    #   of the swap node (5).
    #   
    #   So, the 2-opt works as follows:
    #       1) Remove edges (4,2) and (3,5) :
    #           Previous: 1-6-4-2-3-5
    #           After: 1-6-4   2-3   5
    #
    #       2) Link the Base node (4) to the swap Node (3):
    #           Previous: 1-6-4   2-3   5
    #           After: 1-6-4-3-2   5
    #
    #       3) Link the forward adjacent node of Base Node (2) to the forward adjacent node of the swap node (5)
    #           Previous: 1-6-4-3-2   5
    #           After: 1-6-4-3-2-5
    #
    #       Thus, the new tour is  1-6-4-3-2-5.
    #   Note that the difference between the previous tour (1-6-4-2-3-5) and the new tour (1-6-4-3-2-5) is that the nodes between the base node (4) and the forward adjacent node of the swap node (5)
    #   are in the reverse order.
    #   
    #   After including the new edges in the tour and removing the old ones, we need to rearrange the sequence of the nodes in the tour. The method above does the job.
    #   It works as follows (Using the same example above):
    #   1) Copy to a new array the some nodes in the current order:
    #       1.1) Set the inicial position as the position of the adjacent node of the swap node (5). The position is 5 (0 based index array)
    #       1.2) Set the Final Position for the base node (4) (we must copy it as well). The position is 2.
    #       1.3) Copy into a new list elements from the inicial position (5) to the final position (2). For getting the circular reference working, we use the modulo opeartor.
    #            Copy Result: 5-1-6-4
    #   2) Append to this new array the remaining nodes in reverse order
    #      2.1) Set the initial position as the position of the swap node (3). This position is 4. We add the length of the graph (total number of nodes) 
    #           in order to avoid to get negative numbers in the modulo operation
    #      2.2) Set the Final Position for the forward adjacent node of base node (2) (we must copy it as well). The position is 3
    #      2.3) Appent to the new route elements from the inicial position (4) to the final position (3).
    #            Copy Result: 5-1-6-4-3-2
    #   Once the list is circular, the tour 5-1-6-4-3-2 is the same as 1-6-4-3-2-5 (they are symmetric). We can take leverage of this to make this position exchange
    #   easier to implement.
    #   The final step is attribute the right position for each node in the list

    def SwapEdgesInTour(self,node1,node2):    
        swapNextPos = node2.GetAdjacentNodes(len(self.tourNodes))[1]
        newRoute = []

        i = (swapNextPos.tourPos)%self.length
        end = (node1.tourPos+1)%self.length

        #   Copy the first part
        while i != end:
            newRoute.append(self.tourNodes[i])
            i = (i+1)%self.length


        #   Copy reverse
        i = (node2.tourPos + self.length)%self.length
        end = (node1.tourPos)%self.length
        while i != end:
            newRoute.append(self.tourNodes[i])
            i = (i-1)%self.length

        #   Attribute the right positions
        for i in range(0,len(self.tourNodes)):
            newRoute[i].tourPos = i

        self.tourNodes = newRoute

    #   Return a list with the Ids of the node in the tour order
    def GetTourIds(self):
        nodeIds = []
        for node in self.tourNodes:
            nodeIds.append(node.id)
        return nodeIds

#   Class used to set different strategies to different instances os the problem.
#   One strategy sets different parameters (Maximun Runtime, Local Search Procedure, etc)
class Strategy(Enum):
    Default = "Default"
    Alpha = "Alpha"
    Beta = "Beta"
    Gamma = "Gamma"
    Delta = "Delta"
    Epsilon = "Epsilon"

#   Enum to change the behaviour of the local search method to work with either first improment approach or last improvement approach
class ImprovementType(Enum):
    Best = "Best Improvement"
    First = "First Improvement"

#   Class to help to monitor the runtimes of the algorithm
class Clock():
    def __init__ (self):
        self.start = None

    def isTimeOver(self,end,duration):
        return end-self.start >= duration

    def setStart(self,start):
        self.start = start

    def getStart(self):
        return self.start

##Global Variable to monitor execution time
clock = Clock()

#######################
#    Main Method      #
#######################

def solve_it(input_data):
    # Modify this code to run your optimization algorithm
    start = time.time()
    print("Start DateTime: {}".format(datetime.datetime.now()))
    graph = Graph()
    # parse the input
    lines = input_data.split('\n')

    nodeCount = int(lines[0])

    for i in range(1, nodeCount+1):
        line = lines[i]
        parts = line.split()

        #Build the graph (Without the edges)
        graph.addNode(Node(i-1,float(parts[0]),float(parts[1])))

    #Get The params for the problem instance
    if(graph.length < 200): 
        params = GetInstanceParameters(Strategy.Beta,graph.length)
    elif(graph.length < 500): 
        params = GetInstanceParameters(Strategy.Gamma,graph.length)
    elif(graph.length < 1000): 
        params = GetInstanceParameters(Strategy.Alpha,graph.length)
    elif(graph.length <10000): 
        params = GetInstanceParameters(Strategy.Delta,graph.length)
    else:
        params = GetInstanceParameters(Strategy.Epsilon,graph.length)

    #Guided Fast Local Search (GFLS)
    solutionSequence,objValue = GuidedLocalSearch(graph,params)

    # prepare the solution in the specified output format
    output_data = '%.2f' % objValue + ' ' + str(0) + '\n'
    output_data += ' '.join(map(str, solutionSequence))

    del graph
    gc.collect()
    end = time.time()
    hours, minutes, seconds = getIntervalDuration(start,end)
    print("End DateTime: {}".format(datetime.datetime.now()))
    print("Execution Time: {:0>2}:{:0>2}:{:05.2f}s".format(int(hours),int(minutes),seconds))
    return output_data

################################
#       Utility Methods        #
################################

# Return the time from hour, second and secods to seconds
def getTimeInSeconds(hours,minutes,seconds):
    return (((hours*3600)+(minutes*60)+seconds))

# Return the time interval between start and end (both in seconds) in hour, minute and second
def getIntervalDuration(start,end):
     hours, rem = divmod(end-start, 3600)
     minutes, seconds = divmod(rem, 60)
     return int(hours),int(minutes),seconds

#   Set up parameters for different strategies
def GetInstanceParameters(strategy,instanceSize):
    if strategy == Strategy.Alpha:
        return AlphaSetup(instanceSize)
    elif strategy == Strategy.Beta:
        return BetaSetup(instanceSize)
    elif strategy == Strategy.Gamma:
        return GammaSetup(instanceSize)
    elif strategy == Strategy.Delta:
        return DeltaSetup(instanceSize)
    elif strategy == Strategy.Epsilon:
        return EpsilonSetup(instanceSize)
    else: 
        return DefaultSetup(instanceSize)

###############################################
#             Strategy Setups                 #
###############################################

def AlphaSetup(instanceSize):
    params = DefaultSetup(instanceSize)
    params["strategy"] = Strategy.Alpha
    params["executionTimeLimit"] = getTimeInSeconds(2,0,0)
    params["noImprovementTimeLimit"] = getTimeInSeconds(2,0,0)
    params["localSearchProcedure"] = TwoOpt
    params["improvementType"] = ImprovementType.Best
    params["initialSolutionFunction"] = GetNearestNeighbourSolution
    params["randomRestartsLimit"] = 3
    params["restartLimitIncrement"] = 1.1
    params["randomRestarts"] = False
    params["restartLimitTime"] = getTimeInSeconds(0,5,0)
    
    return params

def BetaSetup(instanceSize):
    params = DefaultSetup(instanceSize)
    params["executionTimeLimit"] = getTimeInSeconds(0,2,0)
    params["noImprovementTimeLimit"] = getTimeInSeconds(0,0,15)
    params["localSearchProcedure"] = TwoOpt
    params["improvementType"] = ImprovementType.Best
    params["initialSolutionFunction"] = GetNearestNeighbourSolution
    params["strategy"] = Strategy.Beta
    return params

def GammaSetup(instanceSize):
    params = DefaultSetup(instanceSize)
    params["strategy"] = Strategy.Gamma
    params["executionTimeLimit"] = getTimeInSeconds(0,3,0)
    params["noImprovementTimeLimit"] = getTimeInSeconds(0,3,0)
    params["localSearchProcedure"] = TwoOpt
    params["improvementType"] = ImprovementType.Best
    params["initialSolutionFunction"] = GetNearestNeighbourSolution
    return params

def DeltaSetup(instanceSize):
    params = DefaultSetup(instanceSize)
    params["strategy"] = Strategy.Delta
    params["executionTimeLimit"] = getTimeInSeconds(4,0,0)
    params["noImprovementTimeLimit"] = getTimeInSeconds(4,0,0)
    params["improvementType"] = ImprovementType.Best
    params["localSearchProcedure"] = TwoOpt
    params["initialSolutionFunction"] = GetNearestNeighbourSolution
    return params

def EpsilonSetup(instanceSize):
    params = DefaultSetup(instanceSize)
    params["executionTimeLimit"] = getTimeInSeconds(4,58,0)
    params["noImprovementTimeLimit"] = getTimeInSeconds(4,58,0)
    params["localSearchProcedure"] = TwoOpt
    params["strategy"] = Strategy.Epsilon
    params["initialSolutionFunction"] = GetNearestNeighbourSolution
    params["improvementType"] = ImprovementType.Best
    params["initialSolutionFunction"] = GetNearestNeighbourSolution
    return params

def DefaultSetup(instanceSize):
    params = {}
    params["improvementType"] = ImprovementType.First
    params["executionTimeLimit"] = getTimeInSeconds(4,30,0) #4 hours and 30 minutes of time limit
    params["beta"] = 0.5 #1/8 <= beta <= 1/2
    params["noImprovementTimeLimit"] = getTimeInSeconds(0,20,0)
    params["swapsLimit"] = 5 if 0.01*instanceSize < 5 else int(0.01*instanceSize)
    params["randomRestarts"] = False
    params["randomRestartsLimit"] = 2
    params["restartLimitIncrement"] = 2
    params["restartLimitTime"] = getTimeInSeconds(0,10,0)
    params["strategy"] = Strategy.Default
    params["earlyStopping"] = True
    params["initialSolutionFunction"] = GetInitialSolution
    params["localSearchProcedure"] = Swap
    

    return params

###############################
#     Search Methods          #
###############################

#   Get the Initial Solution
#   For symmetry breaking, only the egdes a -> b, where a < b, are created.
#   However, the edge is referenced by both nodes
#   This method just create a contiguous path from the first to the last node
def GetInitialSolution(graph):
    global clock
    clock.setStart(time.time())
    print("=========================================================")
    print("Instance: {} - Initial Solution Start".format(graph.length))
    for index in range(0, graph.length-1):
        edge = Edge(graph.nodes[index],graph.nodes[index+1]) 
        graph.addEgdeinTour(edge)
        graph.addNodeinTour(graph.nodes[index])

    edge = Edge(graph.nodes[0],graph.nodes[-1])
    graph.addEgdeinTour(edge)
    graph.addNodeinTour(graph.nodes[-1])

    print("Tour Length: {}".format(graph.tourLength))
    print("Instance: {} - Initial Solution End".format(graph.length))
    print("=========================================================")
    return graph.GetTourIds(),graph.tourLength

#   Get the Initial Solution using the Nearest Neighbour Heuristic
#   For symmetry breaking, only the egdes a -> b, where a < b, are created.
#   However, the edge is referenced by both nodes
#   For better performance (both time and memory), the manhatan distance heuristic is used in order to evaluate the distances. 
#   Thus, it is an approximation of the Nearest Neighbour Search

def GetNearestNeighbourSolution(graph):
    global clock
    clock.setStart(time.time())
    start = time.time()
    print("=========================================================")
    print("Instance: {} - Nearest Neighbour Solution Start".format(graph.length))
    activeNodes = graph.length
    currentNode = graph.nodes[0]
    bestManhatanEdgeDistance = None
    bestNode = None
    while activeNodes > 0:
        bestManhatanEdgeDistance = None
        currentNode.active = False
        bestNode = None
        for j in range(0, graph.length):
            
            if(graph.nodes[j].active == False):
                continue

            if(currentNode.id == graph.nodes[j].id):
                continue

            #Manhatan Distance Checking
            newEdgeManhatenDistance = math.fabs(currentNode.x-graph.nodes[j].x) + math.fabs(currentNode.y-graph.nodes[j].y)

            if bestManhatanEdgeDistance is None:
                bestManhatanEdgeDistance = newEdgeManhatenDistance
                bestNode = graph.nodes[j]
            else:
                if(bestManhatanEdgeDistance > newEdgeManhatenDistance):
                    bestManhatanEdgeDistance = newEdgeManhatenDistance
                    bestNode = graph.nodes[j]

        if(bestManhatanEdgeDistance is None):
            bestNode = graph.tourNodes[0]
            bestManhatanEdgeDistance = math.fabs(currentNode.x-graph.nodes[0].x) + math.fabs(currentNode.y-graph.nodes[0].y)
  
        bestEdge = Edge(currentNode,bestNode)
        graph.addEgdeinTour(bestEdge)
        graph.addNodeinTour(currentNode)
        graph.addEgdeinPool(bestEdge)       
        activeNodes-=1
        currentNode = bestEdge.node1 if bestEdge.node1.id != currentNode.id else bestEdge.node2

    print("Tour Length: {}".format(graph.tourLength))

    for j in range(0, graph.length):
        graph.nodes[j].active = True
    end = time.time()
    h,m,s = getIntervalDuration(start,end)
    print("Execution Time: {:0>2}:{:0>2}:{:05.2f}s".format(h,m,s))
    print("Instance: {} - Nearest Neighbour Solution End".format(graph.length))
    print("=========================================================")
    return graph.GetTourIds(),graph.tourLength


#  Guided Local Search Main Method
def GuidedLocalSearch(graph,params):
    global clock
    hour,minute,second = getIntervalDuration(0,params["executionTimeLimit"])
    nHour,nMinute,nSecond = getIntervalDuration(0,params["noImprovementTimeLimit"])
    print("==================================================================================================================================================================================")
    print("Instance: {} | Strategy: {} | Beta: {} | Improvement Type: {} | Local Search Procedure: {} | Time Limit: {:0>2}:{:0>2}:{:05.2f}s | No Improvement Limit: {:0>2}:{:0>2}:{:05.2f}s".format(graph.length,params["strategy"].value,params["beta"],params["improvementType"].value,params["localSearchProcedure"].__name__,hour,minute,second,nHour,nMinute,nSecond))
    if(params["randomRestarts"]):
        hour,minute,second = getIntervalDuration(0,params["restartLimitTime"])
        print("Random Restarts ENABLED | Perturbation Initial Size: {} | Multiplicative Factor: {} | Number of Restarts: {} | No Improvement Time Limit before restart: {:0>2}:{:0>2}:{:05.2f}s".format(params["swapsLimit"],params["restartLimitIncrement"],params["randomRestartsLimit"],hour,minute,second))
    else:
        print("Random Restarts DISABELD")
    print("===================================================================================================================================================================================")    
    print("=========================================================")
    print("Start Guided Local Search")
    currentSolutionSequence, currentObjFunction = params["initialSolutionFunction"](graph)
    print("Current Objective Value: {}".format(currentObjFunction))
    alpha = 0
    randomRestartsCount =  0
    lastImprovemntClock = Clock()
    messageClock = Clock()
    messageClock.setStart(time.time())
    lastImprovemntClock.setStart(time.time())
    egdesUsedforSolution = len(graph.edgesPool)
    lastRandomRestartClock = Clock()
    lastRandomRestartClock.setStart(time.time())
    # Run until the set up execution time is over
    while not clock.isTimeOver(time.time(),params["executionTimeLimit"]):
        
        # Get the solution of the Fast Local Search Procedure
        solutionSequence, objFunction = FastLocalSearch(graph,alpha,params["executionTimeLimit"],params["improvementType"],params["localSearchProcedure"])
       
        if(messageClock.isTimeOver(time.time(),30)):
            print("CANDIDATE Value: {}".format(objFunction))
            print("CURRENT Value: {}".format(currentObjFunction))
            messageClock.setStart(time.time())

        # Check if a better solution has been found
        if currentObjFunction > objFunction:
            currentObjFunction = objFunction
            currentSolutionSequence = solutionSequence
            print("NEW Objective Value: {}".format(currentObjFunction))
            start = lastImprovemntClock.getStart()
            end = time.time()
            hour,m,sec = getIntervalDuration(start,end)
            print("Time Elapsed since last improvement: {:0>2}:{:0>2}:{:05.2f}s".format(hour,m,sec))
            lastImprovemntClock.setStart(time.time())
            lastRandomRestartClock.setStart(time.time())
            egdesUsedforSolution = len(graph.edgesPool)
            print("Edges Explored to find this solution: {}".format(len(graph.edgesPool)))
            messageClock.setStart(time.time())

        
        
        
        #Random Pertubation Restart
        if  params["randomRestarts"]:
            if(lastRandomRestartClock.isTimeOver(time.time(),params["restartLimitTime"]) and randomRestartsCount < params["randomRestartsLimit"] ):
                randomRestartsCount +=1
                print("Random Restart {}/{}".format(randomRestartsCount,params["randomRestartsLimit"] ))
                RandomSwaps(graph,params["swapsLimit"])        
                lastImprovemntClock.setStart(time.time())
                params["restartLimitTime"] = int(params["restartLimitTime"] * params["restartLimitIncrement"])
                params["swapsLimit"] = int(params["swapsLimit"] * params["restartLimitIncrement"]) 
                #alpha = 0
                messageClock.setStart(time.time())
                lastRandomRestartClock.setStart(time.time())
                continue 

        # If the maximum improvement time is over, terminate the execution
        if(lastImprovemntClock.isTimeOver(time.time(),params["noImprovementTimeLimit"])):
            if  params["earlyStopping"]:
                    hour,minute,second = getIntervalDuration(lastImprovemntClock.getStart(),time.time())
                    print("No improvement after {:0>2}:{:0>2}:{:05.2f}s. Stopping execution.".format(hour,minute,second))
                    break

        #   Update alpha parameter 
        alpha = params["beta"] * (currentObjFunction/len(graph.tourEdges))

        maxUtilValue = 0
        
        # Get the util value for edges (features) in the current solution
        for key in graph.tourEdges.keys():
            aux = GetUtilValue(graph.tourEdges[key])
            if aux > maxUtilValue:
                maxUtilValue = aux

        #   Penalize the features in the solution with the highest util value
        PenalizeFeatures(graph,maxUtilValue)

    print("Instance: {} - End Guided Local Search".format(graph.length))
    print("=========================================================")
    hour,min,sec = getIntervalDuration(clock.getStart(),lastImprovemntClock.getStart())
    print("Time to find the best solution {:0>2}:{:0>2}:{:05.2f}s.".format(hour,min,sec))
    print("Number of Edges exlpored to find the best solution: {}".format(egdesUsedforSolution))
    return currentSolutionSequence, currentObjFunction


#Swap nodes randomly
def RandomSwaps(graph,swapsLimit):
    print("=========================================================")
    print("Instance: {} - Start Random Swaps".format(graph.length))
    print("Maximum Swaps: {}".format(swapsLimit))
    
    
    random.seed(0)
    i=0
    positions = list(range(0,graph.length))
    activeNodes = dict((el,True) for el in positions)

    while i < swapsLimit: 
        pos1=-1
        pos2=-1

        while pos1 == pos2:
            pos1,val1 =  random.choice(list(activeNodes.items()))
            pos2,val2 =  random.choice(list(activeNodes.items()))

        removedEdges, addedEdges = GetSwapMove(graph,graph.tourNodes[pos1],graph.tourNodes[pos2])
        for oldEdge in removedEdges:
            graph.deleteEdgeinTour(oldEdge)
            oldEdge.ActivateNodes()

        for newEdge in addedEdges:
            graph.addEgdeinTour(newEdge)
            newEdge.ActivateNodes()
        graph.SwapNodesInTour(graph.tourNodes[pos1],graph.tourNodes[pos2])

        i+=1


    for key in graph.edgesPool:
        graph.edgesPool[key].penalty = 0

    print("Current Objective Value: {}".format(graph.tourLength))
    print("Instance: {} - End Random Swaps".format(graph.length))
    print("=========================================================")


#   Swap- heuristic using Best Improvement or First Improvement Strategy
#   How it Works: In the 2-Opt Iteration Loop, one node is select to be the "Base" node, and then we loop over all edges of the tour 
#   from this base node. Eg. Supose the tour is 1-6-4-2-3-5. If the Base Node is 4, the we fix the forward edge (4,2) to be removed 
#   and iterate over the edges (3,5),(5,1), and (1,6), removing them (together with the base edge (4,2)) and evaluating the cost of adding new edges.
#   For iterating over the edges, we actually iterate over the nodes in the tour (in the sequence they appear in the tour), starting 2 positions ahead from the base node position.
#   In the code, this iterated node is called swapNode.
#   In this example, we will iterate over nodes 3,5,1. We stop when the swapNode node is adjacent to the current node,ie node 6.
#   (In this case, we only remove the forward edges, then, iterating over the previous adjacent node of the base node would eliminate the previous base node edge).

#   Supose that the best move is to remove the edges (4,2) and (3,5) and to add the edges (3,4) and (2,5) (ie, our swap node is 3).
#   Note that the new edges are built by linking the Base node (4) to the swap node (3) and the foward adjacent node of the base node (2) and the foward adjacent node
#   of the swap node (5).
#   
#   So, the 2-opt works as follows:
#       1) Remove edges (4,2) and (3,5) :
#           Previous: 1-6-4-2-3-5
#           After: 1-6-4   2-3   5
#
#       2) Link the Base node (4) to the swap Node (3):
#           Previous: 1-6-4   2-3   5
#           After: 1-6-4-3-2   5
#
#       3) Link the forward adjacent node of Base Node (2) to the forward adjacent node of the swap node (5)
#           Previous: 1-6-4-3-2   5
#           After: 1-6-4-3-2-5
#
#       Thus, the new tour is  1-6-4-3-2-5.
#   Note that the difference between the previous tour (1-6-4-2-3-5) and the new tour (1-6-4-3-2-5) is that the nodes between the base node (4) and the forward adjacent node of the swap node (5)
#   are in the reverse order.
#   The method returns what edges must be added/removed and which nodes must be place in the active list in the Fast Local Search Procedure.

def TwoOpt(graph,node,alpha=1,improvementType = ImprovementType.First):
    global clock
    currentNode = graph.tourNodes.index(node)
    swapNodes = []
    currentRemovedEdges = [] 
    currentAddedEdges = []
    deltaCost = 0
    currentDeltaCost = 0
    i = (currentNode+2)%graph.length
    end = ((currentNode-1)%graph.length)

    while i!= end and not clock.isTimeOver(time.time(),clock.getStart()):
        
        removedEdges, addedEdges = GetTwoOptMove(graph,graph.tourNodes[currentNode],graph.tourNodes[i],alpha)
        deltaCost = EvaluateMovePenalized(removedEdges,addedEdges,alpha)

        if(deltaCost < currentDeltaCost):
            currentDeltaCost = deltaCost
            swapNodes = []
            swapNodes.append(graph.tourNodes[currentNode])
            swapNodes.append(graph.tourNodes[i])
            currentRemovedEdges = list(removedEdges) 
            currentAddedEdges = list(addedEdges)
            if improvementType == ImprovementType.First:
                break
                
        i = (i+1)%graph.length

    for newEdge in currentAddedEdges:
        newEdge.ActivateNodes()

    for oldEdge in currentRemovedEdges:
        oldEdge.ActivateNodes()

    return currentDeltaCost,currentRemovedEdges,currentAddedEdges,swapNodes

#   This method returns what edges must be added/removed in order to perform the 2-opt movement.
#   It does not change the tour. The tour is change only if an improvement is made by the edge exchange
#   Check whether the edge exists in graph.edgesPool before creation to get efficiency in the memory usage
#   It also uses the Manhatan distance (aka Taxicab distance) to get time efficient. It works due the triangule inequality. If the condition tests true, the method 
#   do not generate a candidate move because the move is cleary worse than the current solution. Thus, we get time efficiency by pruning the search space.
#   The move is obtained by the procedure describe in the 2-opt method.

def GetTwoOptMove(graph,currentNode,swapNode,alpha):
    removedEdges = []
    addedEdges = []
    currentNodeAdjacency = currentNode.GetAdjacentNodes(len(graph.tourNodes))
    swapNodeAdjacency = swapNode.GetAdjacentNodes(len(graph.tourNodes))
    currentNodeEdge = currentNode.GetNextEdge(graph.length)
    swapNodeEdge = swapNode.GetNextEdge(graph.length)
    #Manhatan Distance Checking
    #For better performance (both time and memory), the manhatam distance heuristic is used
    currentManhatamAddedDistance = math.fabs(currentNode.x-swapNode.x) + math.fabs(currentNode.y-swapNode.y)
    swapManhatamAddedDistance = math.fabs(currentNodeAdjacency[1].x-swapNodeAdjacency[1].x) + math.fabs(currentNodeAdjacency[1].y-swapNodeAdjacency[1].y)
    
    #Check if the ground truth value of the edges to be removed plus penalties are less than the Manhatan distances calculated for the edges to be added
    #Checking the ground truth value is actually checking the triagle inequality. The penalty is added in order to let the algortihm to incrementally increases its 
    #search space
    if((currentNodeEdge.GetLength() + alpha*currentNodeEdge.penalty) < currentManhatamAddedDistance and (swapNodeEdge.GetLength()+alpha*swapNodeEdge.penalty) < swapManhatamAddedDistance):    
        return removedEdges,addedEdges

    #Remove the forward edges from both nodes
    removedEdges.append(currentNodeEdge)
    removedEdges.append(swapNodeEdge)
    
    
    #Swap edges
    #Edge linking the current Node to the swap node
    newCurrentEdge = graph.getEdgeFromPool(currentNode.id,swapNode.id)
    if(newCurrentEdge is None):
        newCurrentEdge = Edge(currentNode,swapNode)
        graph.addEgdeinPool(newCurrentEdge)

    #Edge linking the Foward Adjacent Node from Current node and the Foward Adjacent Node from swap node
    newSwapEdge = graph.getEdgeFromPool(currentNodeAdjacency[1].id,swapNodeAdjacency[1].id)
    if(newSwapEdge is None):
        newSwapEdge = Edge(currentNodeAdjacency[1],swapNodeAdjacency[1])
        graph.addEgdeinPool(newSwapEdge)

    addedEdges.append(newCurrentEdge)
    addedEdges.append(newSwapEdge)

    return removedEdges,addedEdges

#   Swap two nodes in the solution
#   The method returns what edges must be added/removed and which nodes must be place in the active list in the Fast Local Search Procedure.
def Swap(graph,node,alpha=1,improvementType = ImprovementType.First):
    global clock
    currentNode = graph.tourNodes.index(node)
    swapNodes = []
    currentRemovedEdges = [] 
    currentAddedEdges = []
    deltaCost = 0
    currentDeltaCost = 0
    i = 0
    while i < graph.length and not clock.isTimeOver(time.time(),clock.getStart()):
       
        if currentNode == i:
            i+=1
            continue
        removedEdges, addedEdges = GetSwapMove(graph,graph.tourNodes[currentNode],graph.tourNodes[i])
        deltaCost = EvaluateMovePenalized(removedEdges,addedEdges,alpha)

        if(deltaCost < currentDeltaCost):
            currentDeltaCost = deltaCost
            swapNodes = []
            swapNodes.append(graph.tourNodes[currentNode])
            swapNodes.append(graph.tourNodes[i])
            currentRemovedEdges = list(removedEdges) 
            currentAddedEdges = list(addedEdges)
            if improvementType == ImprovementType.First:
                break
        i+=1

    for newEdge in currentAddedEdges:
        newEdge.ActivateNodes()

    for oldEdge in currentRemovedEdges:
        oldEdge.ActivateNodes()

    
    return currentDeltaCost,currentRemovedEdges,currentAddedEdges,swapNodes

#This method returns what edges must be added/removed in order to perform the swap movement.
#It does not change the tour. The tour is change only if an improvement is made by the swap
#Check whether the edge exists in graph.edgesPool before creation.
def GetSwapMove(graph,currentNode,swapNode):
    removedEdges = []
    addedEdges = []
    #Get Adjacent nodes in order to create the new edges
    currentNodeAdjacency = currentNode.GetAdjacentNodes(len(graph.tourNodes))
    swapNodeAdjacency = swapNode.GetAdjacentNodes(len(graph.tourNodes))
    
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
                graph.addEgdeinPool(newEdge)
            addedEdges.append(newEdge)
            # print("Edge to be Added: {} ".format(newEdge.id))
    
    for node in swapNodeAdjacency:
        #It only creates the edge if current node and swap node are not adjacents
        if(node.id != currentNode.id):
            newEdge = graph.getEdgeFromPool(currentNode.id,node.id)
            if(newEdge is None):
                newEdge = Edge(currentNode,node)
                graph.addEgdeinPool(newEdge)
            addedEdges.append(newEdge)

    return removedEdges,addedEdges

#   Fast Local Search main Method
def FastLocalSearch(graph,alpha,excutionTimeLimit,improvementType = ImprovementType.First,localSearchProcudure = None):
    global clock
    currentSolutionSequence = graph.GetTourIds()
    currentObjValue = graph.tourLength

   
    i=0
     #   Here there is a slight change of implementation regarginf to the paper.
     #   In the paper, the fast local search runs while there are active nodes (sub-neighbourhoods) 
     #   to be searched and maximum execution time is not over.
     #   However, in the same paper is stated that, the Guided Local Search does not need that the local procedure
     #   generates a high quality local optimal. Thus, beacause the original loop actually produces a high quality local
     #   optima in this case (and consume too much time to get it), I changed the implementation to simple itereate over the
     #   tour and return the best possible move in each iteration. 
     #   After that, it returns to the Guided Local Search Procedure
    while i < graph.length and not clock.isTimeOver(time.time(),excutionTimeLimit):
        node = graph.tourNodes[i]
        i+=1
        if(not node.active):
            continue

        node.active = False
        
        deltaCost,removedEdges,addedEdges,swapNodes = localSearchProcudure(graph,node,alpha,improvementType)
        
        if(deltaCost < 0):
            if (localSearchProcudure.__name__ == "Swap"):
                graph.SwapNodesInTour(swapNodes[0],swapNodes[1])
            else:
                graph.SwapEdgesInTour(swapNodes[0],swapNodes[1])

            for oldEdge in removedEdges:
                graph.deleteEdgeinTour(oldEdge)

            for newEdge in addedEdges:
                graph.addEgdeinTour(newEdge)
                    
            currentSolutionSequence = graph.GetTourIds()
            currentObjValue = graph.tourLength
            # for key in activatedNodes.keys():
            #     activeNeighbourhoods[key] = activatedNodes[key]
            #print("Fast Local Search: Current Value: {}".format(currentObjValue))
    return currentSolutionSequence, currentObjValue

#   Penalizes the edges in the solution with the maximum utility value and activated the nodes (sub-neighbourhoods) at their ends
def PenalizeFeatures(graph, maxUtil):
    for key in graph.tourEdges.keys():
        if graph.tourEdges[key].util == maxUtil:
            graph.tourEdges[key].penalty += 1
            graph.tourEdges[key].ActivateNodes()


#   Calculate the utility value for each edge presented in the local optima solution
def GetUtilValue(edge):
    edge.util = edge.GetLength()/(1+edge.penalty)
    return edge.util


#   Evaluation of the move using Augmented Objective Function
#   This return the variation (delta) of the move. If it is negative, means that the move improve the solution

def EvaluateMovePenalized(removedEdges,addedEdges,alpha=1,EvaluateManhatan = False):

    removed = 0
    added = 0

    for edge in removedEdges:
        removed = removed + edge.GetLength() + (alpha*edge.penalty)

    for edge in addedEdges:
        added = added + edge.GetLength() + (alpha*edge.penalty)

    delta = added - removed
 
    return delta

#Main method
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        file_location = sys.argv[1].strip()
        with open(file_location, 'r') as input_data_file:
            input_data = input_data_file.read()
        print(solve_it(input_data))
    else:
        print('This test requires an input file.  Please select one from the data directory. (i.e. python solver.py ./data/tsp_51_1)')

