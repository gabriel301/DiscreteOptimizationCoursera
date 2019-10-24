from Tree import Tree

class Forest:
    Trees = {}
    TotalCost = 0
    TreesCount = 0
    TotalNodes = 0

    def addTree(self,tree):
        if tree.getRoot().index in self.Trees.keys():
            self.removeTree(tree)

        self.Trees[tree.getRoot().index] = tree
        self.TotalCost = self.TotalCost + tree.getCost()
        self.TreesCount = self.TreesCount + 1
        self.TotalNodes = self.TotalNodes + len(tree.getNodes())

    def removeTree(self,tree):
        if tree.getRoot().index in self.Trees.keys():
            self.TotalCost = self.TreesCount - self.Trees[tree.getRoot().index].getCost()
            self.TotalNodes = self.TotalNodes - len(self.Trees[tree.getRoot().index].getNodes())
            self.Trees.pop(tree.getRoot().index,None)
            self.TreesCount = self.TreesCount - 1

    def buildForestFromArray(self,assignments,facilities,customers):
        size = len(assignments)
        for index in range(0,size):
            if(assignments[index] not in self.Trees.keys()):
                self.Trees[assignments[index]] = Tree(facilities[assignments[index]])

            self.Trees[assignments[index]].addNode(customers[index])


    def getAssignmentsArray(self):
        assignments = [-1]*self.TotalNodes
        for tree in self.Trees:
            for node in tree.getNodes():
                assignments[node.index] = tree.getRoot().index

        return assignments

