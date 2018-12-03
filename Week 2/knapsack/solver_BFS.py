#!/usr/bin/python
# -*- coding: utf-8 -*-
#Branch and Bound using Best First Search Approach

#Todo Fix Memoization
from collections import namedtuple
try:
    import Queue as Q  # ver. < 3.0
except ImportError:
    import queue as Q

import gc

Item = namedtuple("Item", ['index', 'value', 'weight','value_per_weight'])


class Node:
    def __init__(self, current_value, current_estimative,remaining_capacity,parent,level,item):
        self.current_value = current_value
        self.current_estimative = current_estimative
        self.remaining_capacity = remaining_capacity
        self.parent = parent
        self.level = level
        self.item = item

    def __lt__(self, other):
        selfPriority = (self.current_estimative,self.level)
        otherPriority = (other.current_estimative,other.level)
        return selfPriority < otherPriority

class MemoizationTable:
    def __init__(self):
        self.size = 0
    def GetValue(self,position):
        if(position >= self.size):
            return None
        return self.table[position]
    def SetValue(self,value,position):
        if(position < self.size):
            self.table[position] = value
    def CreateTable(self,size):
        self.table = [None]*size
        self.size = size
    def Clear(self):
        del self.table
        self.size = 0
        gc.collect()

memoTable = MemoizationTable()

def solve_it(input_data):
    # Modify this code to run your optimization algorithm

    # parse the input
    lines = input_data.split('\n')

    firstLine = lines[0].split()
    item_count = int(firstLine[0])
    capacity = int(firstLine[1])

    items = []

    for i in range(1, item_count+1):
        line = lines[i]
        parts = line.split()
        items.append(Item(i-1, int(parts[0]), int(parts[1]),float(float(parts[0])/float(parts[1]))))
        #Sort Items by value per weight in decreasing order
        #Must sort to calcualte the upper bound solution
        items.sort(key=lambda x: x.value_per_weight, reverse=True)
    global memoTable
    memoTable.CreateTable(len(items))
    initialEstimative = get_bound(items,capacity)
    best_solution = Branch_and_Bound(initialEstimative,capacity,items)
    solutionItems = returnSolutionItems(best_solution)
    taken = [1 if i in solutionItems else 0 for i in range(len(items)) ]
    value = best_solution.current_value
    
    # prepare the solution in the specified output format
    output_data = str(value) + ' ' + str(0) + '\n'
    output_data += ' '.join(map(str, taken))
    memoTable.Clear()
    gc.collect()
    return output_data

def returnSolutionItems(solution):
    items=[]
    node = solution
    while(node.parent is not None):
        if node.item is not None:
            items.append(node.item.index)
        node = node.parent
    return items
    
#Get the bound for the relaxed problem
def get_bound(items,capacity,level=0):
    global memoTable
    value = memoTable.GetValue(level)
    if(value is not None):
        print("Returning from Memo")
        return value
    print("Returning from Function")
    weight = 0
    value = 0
    i = level
    while i < len(items) and weight + items[i].weight <= capacity:      
        value += items[i].value
        weight += items[i].weight
        i+=1

    if weight < capacity and i < len(items):
        diff = capacity - weight
        ratio = float(diff)/float(items[i].weight)
        value += (ratio * items[i].value)

    memoTable.SetValue(value,level)
    return value



def heuristic(capacity,cost,items,level):
    #If the item is not placed in the bag, the estimative cannot take in account its value
    bound =  get_bound(items,capacity,level)
    return bound + cost


#Evaluate wheter the node can be expanded (put on the frontier)
def evaluate(candidate,best_solution):
    if candidate.remaining_capacity < 0:
        return False
    if candidate.current_estimative < 0:
        return False
    if best_solution.current_value > candidate.current_estimative:
        return False
    
    return True

def create_node(parent,items,include):
    if parent.level+1 >= len(items):
        return None
    if include:
        newLevel = parent.level+1
        newCapacity = parent.remaining_capacity - items[newLevel].weight
        if(newCapacity < 0):
            return None

        new_item = items[newLevel]
        newValue = parent.current_value+items[newLevel].value
        newEstimative = heuristic(newCapacity,newValue,items,newLevel+1)
        if(newEstimative < 0):
            return None
    else:
        newLevel = parent.level+1
        newValue = parent.current_value
        newEstimative = heuristic(parent.remaining_capacity,newValue,items,newLevel+1)
        newCapacity = parent.remaining_capacity
        if(newCapacity < 0 or newEstimative < 0):
            return None
        new_item = None

    return Node(newValue,newEstimative,newCapacity,parent,newLevel,new_item)

def returnBestSolution(currentState,CurrentBest):
    if currentState.current_value  > CurrentBest.current_value:
        return currentState

    return CurrentBest

def Branch_and_Bound(initialEstimative,initialCapacity,items):
    frontier = Q.PriorityQueue()
    node = Node(0,initialEstimative,initialCapacity,None,-1,None)
    best_solution = node
    frontier.put((-node.current_value,node))
    explored = 0
    expanded = 0
    while not frontier.empty():
        currentNode = frontier.get()[1]
        best_solution = returnBestSolution(currentNode,best_solution)
        explored+=1
        if(evaluate(currentNode,best_solution)):
            right = create_node(currentNode,items,False)
            if(right is not None):
                frontier.put((-right.current_value,right))
                expanded+=1
            left = create_node(currentNode,items,True)
            if(left is not None):
                frontier.put((-left.current_value,left))
                expanded+=1

    #print("Nodes Explored {}, Nodes Expanded {}".format(explored,expanded))
    return best_solution

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        file_location = sys.argv[1].strip()
        with open(file_location, 'r') as input_data_file:
            input_data = input_data_file.read()
        print(solve_it(input_data))
    else:
        print('This test requires an input file.  Please select one from the data directory. (i.e. python solver.py ./data/ks_4_0)')
    del memoTable
    gc.collect()

