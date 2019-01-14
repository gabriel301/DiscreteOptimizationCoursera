#!/usr/bin/python
# -*- coding: utf-8 -*-
import gc
from operator import itemgetter

class Node:
    def __init__(self,number = -1,colors = None):
        self.degree = 0
        self.color = -1
        self.adjacendList = []
        self.adjacentColors = set()
        self.ColorsDomain = colors
        self.number = number
        

class Graph:
    def __init__ (self,num_nodes):
        self.idx = 0
        self.nodes = []
        for i in range(0,num_nodes):
            self.nodes.append(Node(i,set(range(0,num_nodes))))
        self.length = num_nodes
        self.colorsUsed = set()
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
        graph.nodes[int(parts[0])].adjacendList.append(graph.nodes[int(parts[1])])
        graph.nodes[int(parts[1])].adjacendList.append(graph.nodes[int(parts[0])])
        graph.nodes[int(parts[0])].degree = graph.nodes[int(parts[0])].degree + 1
        graph.nodes[int(parts[1])].degree = graph.nodes[int(parts[1])].degree + 1


    
    colors = set(range(0, node_count))

    colorsUsed = GetInitialSolution(graph,colors)
    graph.colorsUsed = colorsUsed
    solution = []
    for i in range(0,graph.length):
        solution.append(graph.nodes[i].color)


    # prepare the solution in the specified output format
    output_data = str(len(colorsUsed)) + ' ' + str(0) + '\n'
    output_data += ' '.join(map(str, solution))

    del graph.nodes
    del graph
    gc.collect()

    return output_data


def GetExplorationList(graph):
    return sorted(graph, key=lambda x: x.degree, reverse=True)
    

def GetCurrentNode(graph):
    result = sorted(graph, key=lambda x: x.degree, reverse=True)
    final = sorted(result, key=lambda x: (len(x.adjacentColors)), reverse=True)
    for i in range(0,len(final)):
        if final[i].color == -1:
            return final[i]
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
    availableColors = colors - node.adjacentColors
    node.color = min(availableColors)
    return node.color

def PropagateConstraint (node,color):
    for i in range(0,len(node.adjacendList)):
        node.adjacendList[i].adjacentColors.add(color)
        if color in node.adjacendList[i].ColorsDomain:
            node.adjacendList[i].ColorsDomain.remove(color)

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

