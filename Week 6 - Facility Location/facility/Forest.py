from Tree import Tree

class Forest:
    #Trees = None
    #TotalCost = 0
    #TreesCount = 0
    #TotalNodes = 0

    def __init__(self):
        self.Trees = {}

    def addTree(self,tree):
        if tree.getRoot().index in self.Trees.keys():
            self.removeTree(tree)

        self.Trees[tree.getRoot().index] = tree
        self.TotalCost = self.TotalCost + tree.getCost()
        self.TreesCount = self.TreesCount + 1
        self.TotalNodes = self.TotalNodes + len(tree.getNodes())

    def removeTree(self,tree):
        if tree.getRoot().index in self.Trees.keys():
            self.TotalCost = self.TotalCost  - self.Trees[tree.getRoot().index].getCost()
            self.TotalNodes = self.TotalNodes - len(self.Trees[tree.getRoot().index].getNodes())
            self.Trees.pop(tree.getRoot().index,None)
            self.TreesCount = self.TreesCount - 1

    def buildForestFromArray(self,assignments,facilities,customers):
        print("Building Forest from Assignment Array...")
        size = len(assignments)
        self.reset()
        for index in range(0,size):
            if(assignments[index] not in self.Trees.keys()):
                self.Trees[assignments[index]] = Tree(facilities[assignments[index]])

            self.Trees.get(assignments[index]).addNode(customers[index])

        for tree in self.Trees.values():  
            self.TotalCost = self.TotalCost + tree.getCost()
            self.TotalNodes = self.TotalNodes + len(tree.getNodes())
            self.TreesCount = self.TreesCount + 1  

    def getAssignmentsArray(self):
        assignments = [-1]*self.TotalNodes
        for tree in self.Trees.values():
            for node in tree.getNodes().values():
                assignments[node.index] = tree.getRoot().index

        return assignments

    def getTrees(self):
        return self.Trees
    
    def getTotalCost(self):
        return self.TotalCost

    def getTotalNodes(self):
        return self.TotalNodes
    
    def getTreesCount(self):
        return self.TreesCount
    
    def reset(self):
        self.Trees.clear()
        self.TotalCost = 0
        self.TotalNodes = 0
        self.TreesCount = 0