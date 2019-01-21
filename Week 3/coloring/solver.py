#!/usr/bin/python
# -*- coding: utf-8 -*-
import gc
import random
import math

class Node:
    def __init__(self,number = -1,colors = None):
        self.degree = 0
        self.color = -1
        self.adjacentList = []
        self.adjacentColors = {}
        self.ColorsDomain = colors
        self.number = number
        

class Graph:
    def __init__ (self,num_nodes):
        self.idx = 0
        self.nodes = []
        for i in range(0,num_nodes):
            self.nodes.append(Node(i,set(range(0,num_nodes))))
        self.length = num_nodes
        self.colorsUsed =  set()
        self.brokenConstraints = 0
        self.edge_count = 0
    def __iter__(self):
        return self
    def __next__(self):
        self.idx += 1
        try:
            return self.nodes[self.idx-1]
        except IndexError:
            self.idx = 0
            raise StopIteration  # Done iterating.
    next = __next__  # python2.x compatibility.

    def Destroy(self):
        del self.nodes
        del self
        gc.collect()

    def GetDensity(self):
        return 2*self.edge_count/self.length*(self.length-1)

class TabuList:
    def __init__(self): 
        self.elements = []
        self.threshhold = []
        self.violations = []
        self.length = 0

    def clear(self):
        for i in range(0,len(self.threshhold)):
            if(self.threshhold[i] > 0):
                self.threshhold[i] = self.threshhold[i] - 1
                if(self.threshhold[i] == 0):
                    self.elements[i] = None
                    self.violations[i] = -1
                    self.length = self.length - 1

    def add(self,element,violations,threshhold):
        added = False
        for i in range(0,len(self.elements)):
            if( self.elements[i] is None):
                self.elements[i] = element
                self.threshhold[i] = threshhold
                self.violations[i] = violations
                added = True
                break
        if added == False:
            self.elements.append(element)
            self.threshhold.append(threshhold)
            self.violations.append(violations)
        self.length = self.length + 1
    def Update(self,element,violations):
        elementIndex = self.elements.index(element)
        if(self.violations[elementIndex] > violations):
            self.elements[elementIndex] = None
            self.violations[elementIndex] = -1
            self.threshhold[elementIndex] = 0
            self.length = self.length - 1
            return True
        else:
            return False


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
    
    colors = set(range(0, node_count))

    solutionColors, solution = TabuSearch(graph,colors)

    # prepare the solution in the specified output format
    output_data = str(solutionColors) + ' ' + str(0) + '\n'
    output_data += ' '.join(map(str, solution))

    del graph.nodes
    del graph
    gc.collect()

    return output_data


def TabuSearch(graph,colors,iterations=5500,alpha = 1):
    colorsUsed = GetInitialSolution(graph,colors)
    graph.colorsUsed = colorsUsed
    currentsolutionColors = len(graph.colorsUsed)
    
    currentSolution = []
    for i in range(0,graph.length):
        currentSolution.append(graph.nodes[i].color)
    currentSolutionScore = Evaluate(graph)
    alpha = int(1.25*math.sqrt(graph.length))
    while True:    
        graph = RemoveColor(graph)
        newSolution = GetSolution(graph,iterations,alpha)
        if (currentSolutionScore > Evaluate(newSolution)):
            currentsolutionColors = len(newSolution.colorsUsed)
            currentSolution = []
            for i in range(0,newSolution.length):
                currentSolution.append(newSolution.nodes[i].color)
            currentSolutionScore = Evaluate(newSolution)
        else:
            break

    return currentsolutionColors,currentSolution


def GetSolution (graph,iterations,alpha):
    tabuList = TabuList()
    for i in range(0,iterations):
        nodeNumber,color,violations = GetNextBrokenConstraint(graph,tabuList)
        if(color == -1):
            break
        AssingColor(graph,nodeNumber, color,False) 
        if(graph.brokenConstraints == 0):
            break
        tabuList.clear()
        penalty = alpha*int(graph.brokenConstraints + math.sqrt(graph.GetDensity())/len(graph.colorsUsed))
        tabuList.add((nodeNumber,color),violations,penalty)
        # print("Penalty")
        # print(penalty)
        # print("Tabu List/ Violations")
        # print( (tabuList.length,graph.brokenConstraints))
    return graph

def GetNextBrokenConstraint(graph,tabuList):
    count = sys.maxsize
    currentColor = -1
    currentNodeNumber = -1

    for i in range(0,graph.length):
        countBefore = CheckConstraintCount(graph.nodes[i],graph.nodes[i].color)
        if countBefore == 0:
           continue

        nodeNumber, color = GetNextAssignment(graph.nodes[i],None,tabuList)

        if(color == graph.nodes[nodeNumber].color or color == -1):
            continue

        countAfter = CheckConstraintCount(graph.nodes[nodeNumber],color)
        if count > (countAfter - countBefore):
            currentColor = color
            currentNodeNumber = nodeNumber
            count = (countAfter - countBefore)
    #         print("Node/Color/Count")
    #         print((nodeNumber,color,count))
    # print("CurrentNode/CurrentColor")
    # print((currentNodeNumber,currentColor))
    return currentNodeNumber,currentColor,count

#Get the assignment that violates the less number of constraints
def GetNextAssignment(node,currentViolations = None,tabuList = None):
    if currentViolations is None:
        currentViolations = sys.maxsize

    colorToBeAssigned = -1
    if tabuList is None:
        tabuList = TabuList()

    for color in node.ColorsDomain:
        violationCount = CheckConstraintCount(node,color)

        if((node.number,color) in tabuList.elements):
            if tabuList.Update((node.number,color),violationCount) == False:
                continue

        if currentViolations >= violationCount and color != node.color:
                currentViolations = violationCount
                colorToBeAssigned = color

    return node.number,colorToBeAssigned
    
#Return a score for a solution
#If the solution break any constraint, it is penalized with 1.01 for each constraint broken
def Evaluate(graph):
    return len(graph.colorsUsed) + graph.brokenConstraints * 1.01

#Remove the color with the least number of nodes, least degree and greatest color number
def RemoveColor(graph):
    colorToBeRemoved = list(graph.colorsUsed)[len(graph.colorsUsed)-1]

    #Remove the color from colors Used
    graph.colorsUsed.remove(colorToBeRemoved)
    
    #Remove the color from nodes,domains and adjacent color list
    for i in range(0,graph.length):
        if graph.nodes[i].color == colorToBeRemoved:
            graph.nodes[i].color = -1
        if colorToBeRemoved in graph.nodes[i].adjacentColors:
            graph.nodes[i].adjacentColors.pop(colorToBeRemoved,None)
        graph.nodes[i].ColorsDomain = set(graph.colorsUsed)

    #Assign new colors for the nodes without colors
    nodes = GetUnassignedNodes(graph)
    for i in range(0,len(nodes)):
        nodeNumber,color = GetNextAssignment(nodes[i])
        AssingColor(graph,nodeNumber,color,False)
    return graph

def AssingColor(graph,nodeNumber,color,removeFromDomain = True):   
    constraintsBeforeAssign = CheckConstraintCount(graph.nodes[nodeNumber],graph.nodes[nodeNumber].color)
    graph.nodes[nodeNumber].color = color
    graph.colorsUsed.add(color)
    
    PropagateConstraint(graph.nodes[nodeNumber],color,removeFromDomain)
    constraintsAfterAssign = CheckConstraintCount(graph.nodes[nodeNumber],color)
    graph.brokenConstraints += (constraintsAfterAssign - constraintsBeforeAssign)

def GetExplorationList(graph):
    return graph.nodes
    
def GetUnassignedNodes(graph):
    nodes = []
    for i in range(0,graph.length):
            if graph.nodes[i].color == -1:
                nodes.append(graph.nodes[i])
    return nodes

def GetCurrentNode(graph):
    #result = sorted(graph, key=lambda x: x.degree, reverse=True)
    #final = sorted(result, key=lambda x: (len(x.adjacentColors)), reverse=True)
    for i in range(0,graph.length):
        if graph.nodes[i].color == -1:
            return graph.nodes[i]
    return None


def GetInitialSolution(graph,colors): 
    colorsUsed = set()
    while True:
        node = GetCurrentNode(graph)
        if node is None:
            return colorsUsed
        color = GetNodeColor(node,colors)
        PropagateConstraint(node,color)
        colorsUsed.add(color)


def GetNodeColor (node,colors):
    if node.color != -1:
        return node.color
    availableColors = colors - node.adjacentColors.keys()
    node.color = min(availableColors)
    return node.color

def PropagateConstraint (node,color,removeFromDomain = True):
    for i in range(0,len(node.adjacentList)):
        if color in node.adjacentList[i].adjacentColors:
            node.adjacentList[i].adjacentColors[color] += 1
        else:
            node.adjacentList[i].adjacentColors[color] = 1
        if removeFromDomain:
            if color in node.adjacentList[i].ColorsDomain:
                node.adjacentList[i].ColorsDomain.remove(color)

def CheckConstraintCount(node,color):
    brokenConstraints = 0
    for i in range(0,len(node.adjacentList)):
        if color > -1 and color == node.adjacentList[i].color:
            brokenConstraints += 1
    return brokenConstraints


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

