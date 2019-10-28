from pyscipopt import Model, quicksum
import math
from Preprocessing import Preprocessing

class MIP:
    DEBUG_MESSAGES = True

    def __init__(self, f, c, instanceName): 
        self.initialize(f,c,instanceName)

    def clear(self):
        self.facilities = [] 
        self.customers = [] 
        self.instanceName = None
        self.varFacilityAssignment = {}
        self.varCustomerAssignment = {}

    def initialize(self, f, c, instanceName):
        self.clear()
        self.facilities = f 
        self.customers = c 
        self.instanceName = instanceName
        self.varFacilityAssignment = {}
        self.varCustomerAssignment = {}

    def createModel(self):
        self.model = Model(self.instanceName)
        print("Creating Variables...")
        #Variables
        for f in self.facilities:
            self.varFacilityAssignment[f.index] = self.model.addVar(vtype="B",name="facility-%s" % f.index)
            for c in self.customers:
                #Demand is binary because each customer must be served by exaclty one facility
                self.varCustomerAssignment[f.index,c.index] = self.model.addVar(vtype="B",name="demand-(%s,%s)" % (f.index,c.index))

        print("Creating Constraints...")
        #Constraints
        #Ensure all customers are assigned to one facility
        for customer in self.customers:
            self.model.addCons(quicksum(self.varCustomerAssignment[facility.index,customer.index] for facility in self.facilities) == 1,"Demand(%s)"% customer.index)
        
        #Ensure the demand carried by the facility is at most its capacity
        for facility in self.facilities:
              self.model.addCons(quicksum(self.varCustomerAssignment[facility.index,customer.index]*customer.demand for customer in self.customers) <= facility.capacity*self.varFacilityAssignment[facility.index],"Capacity(%s)" % facility.index)
        
        #Strong Formulation
        for facility in self.facilities:
            for customer in self.customers:
                self.model.addCons(self.varCustomerAssignment[facility.index,customer.index] <=  facility.capacity*self.varFacilityAssignment[facility.index],"Strong(%s,%s)"%(facility.index,customer.index))
                self.model.addCons(self.varCustomerAssignment[facility.index,customer.index] >= 0 )
        
        print("Creating Objective Function...")
        #Objective Function
        self.model.setObjective(quicksum(self.varFacilityAssignment[facility.index]*facility.setup_cost for facility in self.facilities) + quicksum(Preprocessing.length(facility.location,customer.location)*self.varCustomerAssignment[facility.index,customer.index] for facility in self.facilities for customer in self.customers),"minimize")
        self.model.data = self.varFacilityAssignment, self.varCustomerAssignment

    def optimize(self,timeLimit):
        print("Instace: %s" % self.instanceName)

        if not self.DEBUG_MESSAGES:
            self.model.hideOutput()
        
        self.model.setRealParam('limits/time', timeLimit)

        print("MIP - Optimizing...")
        self.model.optimize()
        print("Instace: %s solved." % self.instanceName)
        EPS = 1.e-6
        _,cAssigned = self.model.data

        assignments = [(facility,customer) for (facility,customer) in cAssigned if self.model.getVal(cAssigned[facility,customer]) > EPS]
       
        obj = self.model.getObjVal()
        return  obj,assignments,self.model.getStatus()
    
   

        