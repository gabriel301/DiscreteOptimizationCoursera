#!/usr/bin/python
# -*- coding: utf-8 -*-

    ##################################################
    # Graph Coloring - Gabriel Augusto - 21/01/2019  #
    # gabriel301@gmail.com                           #
    # Approach: Tabu Search + Random Restarts        #
    # This solution can get the full score           #
    ##################################################

import gc
import random
import math
from collections import defaultdict
import copy

#Definition of class Node
class Node:
    def __init__(self,id = -1,colors = None):
        self.degree = 0
        self.color = -1
        self.adjacentList = []
        self.adjacentColors = {}
        self.ColorsDomain = colors
        self.id = id #Node ID
        
#Definition of Graph Class
class Graph:
    def __init__ (self,num_nodes):
        self.idx = 0
        self.nodes = []

        for i in range(0,num_nodes):
            self.nodes.append(Node(i,set(range(0,num_nodes))))

        self.length = num_nodes
        self.colorsUsed =  set()
        self.violatedConstraints = 0
        self.edge_count = 0

    def GetDensity(self):
        return 2*self.edge_count/self.length*(self.length-1)

#Definition of TabuList Class
class TabuList:
    def __init__(self): 
        self.elements = defaultdict(list) 

    #Decrease penalties and remove from Tabu elements that has no restriction penalty
    def decreasePenalties(self):
        toBeDeleted = []
        for key in self.elements.keys():
            self.elements[key][0] -=1
            if self.elements[key][0] == 0:
                toBeDeleted.append(key)

        for i in range(0,len(toBeDeleted)):
            self.elements.pop(toBeDeleted[i],None)
            
    #Add one element to Tabu
    def add(self,element,violations,threshold):
        self.elements[element] = [threshold,violations]

    #Remove an element in case the current violations are less than the violations recorded
    def Update(self,element,violations):
        if(element in self.elements.keys()):
            if(self.elements[element][1] > violations):
                self.elements.pop(element,None)
                return True
            else:
                return False
        else:
            return False

    def Length(self):
        return len(self.elements)

    def Clear(self):
        self.elements.clear()

def solve_it(input_data):
    # Modify this code to run your optimization algorithm

    # parse the input
    lines = input_data.split('\n')

    first_line = lines[0].split()
    node_count = int(first_line[0])
    edge_count = int(first_line[1])
    graph = Graph(node_count)

    #Build the graph
    for i in range(1, edge_count + 1):
        line = lines[i]
        parts = line.split()
        graph.nodes[int(parts[0])].adjacentList.append(graph.nodes[int(parts[1])])
        graph.nodes[int(parts[1])].adjacentList.append(graph.nodes[int(parts[0])])
        graph.nodes[int(parts[0])].degree = graph.nodes[int(parts[0])].degree + 1
        graph.nodes[int(parts[1])].degree = graph.nodes[int(parts[1])].degree + 1

    graph.edge_count = edge_count
    
    #Set the Upper Bound
    colors = set(range(0, node_count))

    #Use Tabu Search to find the solution
    solutionColors, solution = TabuSearch(graph,colors)

    # prepare the solution in the specified output format
    output_data = str(solutionColors) + ' ' + str(0) + '\n'
    output_data += ' '.join(map(str, solution))

    del graph.nodes
    del graph
    gc.collect()

    return output_data


def TabuSearch(graph,colors,iterations=100000):
    print("Instance: {}".format(graph.length))

    #Get an initial Greedy Solution
    colorsUsed = GetInitialSolution(graph,colors)
    graph.colorsUsed = copy.deepcopy(colorsUsed)

    #Save the solution as the current solution
    currentsolutionColors = len(graph.colorsUsed)   
    currentSolution = []
    for i in range(0,graph.length):
        currentSolution.append(graph.nodes[i].color)
    currentObjectiveFunction = Evaluate(graph)

    #Parameter to penalize assignments to be inserted into the tabu list
    alpha = int(1.25*math.sqrt(graph.length))

    #Remove one color from the colors domain (reduce the upper bound) and try to reallocate the colors of the nodes
    while True:    
        graph = RemoveColor(graph)
        newSolution = GetSolution(graph,iterations,alpha)
        #In case the solution found is better than current solution, make the better solution as current
        #Otherwise, terminate the execution
        if (currentObjectiveFunction > Evaluate(newSolution)):
            currentsolutionColors = len(newSolution.colorsUsed)
            currentSolution = []
            for i in range(0,newSolution.length):
                currentSolution.append(newSolution.nodes[i].color)
            currentObjectiveFunction = Evaluate(newSolution)
        else:
            break

    return currentsolutionColors,currentSolution


def GetSolution (graph,iterations,alpha):
    tabuList = TabuList()

    #Stores the frequency of each value of the objective function
    frequencyValues = {}

    #Paramter that that compound the frequency Threshold. It represents the percentage of iterations
    epsilon = 0.175

    restartsLimit = 10
    restartsCount = 0
    i = 0
    while i < iterations:

        if restartsLimit < restartsCount:
            break
        #Try to find the assigment that violates the least number of contraints
        nodeId,color,violations = GetNextBetterAssigment(graph,tabuList)
        #In case of no assignment is found (infeasible solution), restart
        if(color == -1):
            print("=========================================================")
            print("Instance: {}".format(graph.length))
            print("Minimum objective function value: {}".format(min(frequencyValues.keys())))
            print("Current Color Domain: {}".format(len(graph.colorsUsed)))
            print("Violated Constraints: {} - Current Objective Function: {} ".format(graph.violatedConstraints,Evaluate(graph)))
            print("Restarting...")
            AssignRandomColors(graph)
            frequencyValues.clear()
            tabuList.Clear()
            restartsCount +=1
            i = 0
            print("Violated Constraints: {} - Current Objective Function: {} ".format(graph.violatedConstraints,Evaluate(graph)))
            print("Current Color Domain: {}".format(len(graph.colorsUsed)))
            print("=========================================================")
        else:   
            #Make the new color assigmnet
            AssingColor(graph,nodeId, color,False)
            #In case the solution does not violate any constraint, terminate the execution (feasible solution found)
            if(graph.violatedConstraints == 0):
                break

            #Remove assignments from the tabu and updates the penalty count (decrease one in each iteration)
            tabuList.decreasePenalties()
            
            #Dynamic penalty for each assigment
            #Assignments that violates more constraints have a higher penalty in tabu list
            #The penalty also counts the graph density and the number of colors available to be assigned
            penalty = alpha*int(graph.violatedConstraints + math.sqrt(graph.GetDensity())/len(graph.colorsUsed))
            
            #Add the new assignment on Tabu
            tabuList.add((nodeId,color),violations,penalty)

            objectiveFunctionValue = Evaluate(graph)
            #Updates the frequency of the value of the objective function
            if objectiveFunctionValue in frequencyValues.keys():
                frequencyValues[objectiveFunctionValue] += 1
            else:
                frequencyValues[objectiveFunctionValue] = 1
            #In case the frequency of this objective is greater or equal than the threshold
            #Make a perturbation - try to escape the local optima and restart
            if(frequencyValues[objectiveFunctionValue] >= int(round(epsilon*iterations))):
                print("=========================================================")
                print("Instance: {}".format(graph.length))
                print("Minimum objective function value: {}".format(min(frequencyValues.keys())))
                print("Current Color Domain: {}".format(len(graph.colorsUsed)))
                print("Violated Constraints: {} - Current Objective Function: {} ".format(graph.violatedConstraints,Evaluate(graph)))
                print("Restarting...")
                AssignRandomColors(graph)
                frequencyValues.clear()
                tabuList.Clear()
                restartsCount +=1
                i = 0         
                print("Current Color Domain: {}".format(len(graph.colorsUsed)))
                print("Violated Constraints: {} - Current Objective Function: {} ".format(graph.violatedConstraints,Evaluate(graph)))
                print("=========================================================")
            else:
                i+=1
    print("END - Instance: {} - Objective Function: {}".format(graph.length,Evaluate(graph)))
    return graph

#Assign random colors for random nodes
def AssignRandomColors(graph):
    #Get a random number of nodes to be change
    nodesCount = random.randint(int(0.5*graph.length),int(graph.length))
    if nodesCount == 0:
        nodesCount = 1

    #Get the number of colors to use
    colorsCount = random.randint(1,len(graph.colorsUsed))
    nodesChanged = set()
    print("Perturbation: {} nodes - Colors: {}".format(nodesCount,colorsCount))
    graph.colorsUsed.clear()
    for i in range(0,nodesCount):    
        while True:
            nodeId = random.randint(0,graph.length-1)
            newColor = random.randint(0,colorsCount-1)
            if(nodeId not in nodesChanged):
                nodesChanged.add(nodeId)     
                break

        AssingColor(graph,nodeId,newColor,False)
        graph.colorsUsed.add(newColor)


#Get the assigment that violates less constraints in the graph
def GetNextBetterAssigment(graph,tabuList):
    violationsCount = sys.maxsize
    currentColor = -1
    currentNodeId = -1

    for i in range(0,graph.length):

        #Get tne constraint Violation violationsCount for the current assigment
        violationsCountBefore = GetConstraintViolationsCount(graph.nodes[i],graph.nodes[i].color)
        
        #In case of no violation, the best assingnment possible is found, the try another node
        if violationsCountBefore == 0:
           continue

        #Get the best assignment for the current node
        nodeId, color = GetNextAssignment(graph.nodes[i],None,tabuList)

        #In case the assignment is the current color or no color, go to the next node
        if(color == graph.nodes[nodeId].color or color == -1):
            continue

        #Get the violations count for the new candidate color
        violationsCountAfter = GetConstraintViolationsCount(graph.nodes[nodeId],color)
        
        #Update the assignment if the new solution is better
        if violationsCount > (violationsCountAfter - violationsCountBefore):
            currentColor = color
            currentNodeId = nodeId
            violationsCount = (violationsCountAfter - violationsCountBefore)

    return currentNodeId,currentColor,violationsCount

#Get the assignment that violates the less number of constraints for a node
def GetNextAssignment(node,currentViolations = None,tabuList = None):
    
    if currentViolations is None:
        currentViolations = sys.maxsize

    colorToBeAssigned = -1

    if tabuList is None:
        tabuList = TabuList()

    for color in node.ColorsDomain:
        violationCount = GetConstraintViolationsCount(node,color)

        #Check whether an assignment is in the Tabu. Case it is, try to update in order to remove it if
        #the new assigment is better (violates less constraints) than the recorded violations
        if((node.id,color) in tabuList.elements):
            if tabuList.Update((node.id,color),violationCount) == False:
                continue

        #If other color has the same violation count, try to assign it
        #It allows more exploration from the algorithm
        if currentViolations >= violationCount and color != node.color:
                currentViolations = violationCount
                colorToBeAssigned = color

    return node.id,colorToBeAssigned
    
#Return a the objective function value for a solution
#If the solution break any constraint, it is penalized with 1.01 for each violated constraint
def Evaluate(graph):
    #return len(graph.colorsUsed) + graph.violatedConstraints * 1.01
    return len(graph.colorsUsed) + pow(graph.violatedConstraints,2) + graph.violatedConstraints

#Remove the color with the last color from the list and assign new colors for the 
#nodes with missing color assignment
def RemoveColor(graph):

    colorToBeRemoved = len(graph.colorsUsed)-1

    #Remove the color from the domain
    graph.colorsUsed.remove(colorToBeRemoved)
    #Remove the color from nodes,domains and adjacent color list
    for i in range(0,graph.length):
        if graph.nodes[i].color == colorToBeRemoved:
            graph.nodes[i].color = -1
        if colorToBeRemoved in graph.nodes[i].adjacentColors.keys():
            graph.nodes[i].adjacentColors.pop(colorToBeRemoved,None)
        graph.nodes[i].ColorsDomain = copy.deepcopy(graph.colorsUsed)
        
    
    #Assign new colors for the nodes without colors
    nodes = GetUnassignedNodes(graph)
    for i in range(0,len(nodes)):
        nodeId,color = GetNextAssignment(nodes[i])
        AssingColor(graph,nodeId,color,False)

    return graph

#Assign a color to a node and update the graph constraint violations
def AssingColor(graph,nodeId,color,removeFromDomain = True):   
    constraintsBeforeAssign = GetConstraintViolationsCount(graph.nodes[nodeId],graph.nodes[nodeId].color)
    
    RemoveColorFromNeighbors(graph.nodes[nodeId],graph.nodes[nodeId].color)
    
    graph.nodes[nodeId].color = color
    graph.colorsUsed.add(color)
    
    PropagateConstraint(graph.nodes[nodeId],color,removeFromDomain)
    
    constraintsAfterAssign = GetConstraintViolationsCount(graph.nodes[nodeId],color)
    
    graph.violatedConstraints += (constraintsAfterAssign - constraintsBeforeAssign)


def RemoveColorFromNeighbors(node,color):
    for i in range(0,len(node.adjacentList)):
        if(color in node.adjacentList[i].adjacentColors.keys()):
            node.adjacentList[i].adjacentColors[color] -= 1
            if node.adjacentList[i].adjacentColors[color] == 0:
                node.adjacentList[i].adjacentColors.pop(color,None)

#Get the list of the nodes to be explored
def GetExplorationList(graph):
    return graph.nodes

#Get the node with no colors assigned
def GetUnassignedNodes(graph):
    nodes = []
    for i in range(0,graph.length):
            if graph.nodes[i].color == -1:
                nodes.append(graph.nodes[i])
    return nodes

#Get an initial greedy solution
#Try to assign the first color available for each node
def GetInitialSolution(graph,colors): 
    colorsUsed = set()
    nodes = GetUnassignedNodes(graph)
    for i in range(0,len(nodes)):
        color = GetNodeColor(nodes[i],colors)
        PropagateConstraint(nodes[i],color)
        colorsUsed.add(color)

    return colorsUsed
        

#Get the first color available for each node
def GetNodeColor (node,colors):
    if node.color != -1:
        return node.color
    availableColors = colors - node.adjacentColors.keys()
    node.color = min(availableColors)
    return node.color

#Assing a color for a node and remove the color from the other nodes domain
def PropagateConstraint (node,color,removeFromDomain = True):
    for i in range(0,len(node.adjacentList)):
        if color in node.adjacentList[i].adjacentColors:
            node.adjacentList[i].adjacentColors[color] += 1
        else:
            node.adjacentList[i].adjacentColors[color] = 1
        if removeFromDomain:
            if color in node.adjacentList[i].ColorsDomain:
                node.adjacentList[i].ColorsDomain.remove(color)

#Get the number of constraints violated by an assignment
def GetConstraintViolationsCount(node,color):
    if(color in node.adjacentColors.keys()):
        return node.adjacentColors[color]
    return 0


import sys

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        file_location = sys.argv[1].strip()
        with open(file_location, 'r') as input_data_file:
            input_data = input_data_file.read()
        print(solve_it(input_data))
    else:
        print('This test requires an input file.  Please select one from the data directory. (i.e. python solver.py ./data/gc_4_1)')

