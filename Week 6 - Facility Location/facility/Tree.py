from Preprocessing import Preprocessing

class Tree:
    #Root = None
    #Nodes = None
    #Cost = 0

    def __init__(self,treeRoot):
        self.Root = None
        self.Nodes = {}
        self.Cost = 0
        self.setRoot(treeRoot)

    def setRoot(self,newRoot):
        if self.Root is not None:
            self.Cost = self.Cost - self.Root.setup_cost
        self.Root = newRoot
        self.Cost = self.Cost + self.Root.setup_cost

    def addNode(self,node):
        self.Nodes[node.index] = node
        self.Cost = self.Cost + Preprocessing.length(self.Root.location,node.location)

    def removeNode(self,node):
        if node.index in self.Nodes.keys():
            self.Cost = self.Cost - Preprocessing.length(self.Root.location,node.location)
            self.Nodes.pop(node.index, None)

    def clearNodes(self):
        self.Nodes.clear()
        self.cost = self.Cost = self.Cost + self.Root.setup_cost

    def getRoot(self):
        return self.Root
    
    def getCost(self):
        return self.Cost
    
    def getNodes(self):
        return self.Nodes