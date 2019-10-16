from pyscipopt import Model, quicksum
import math

class MIP:
    facilities = []
    customers = []
    model = None
    name = None
    varFacilityAssignment,varCustomerAssignment= {},{}
    
    def __init__(self, f, c, instanceName): 
        self.facilities = f 
        self.customers = c 
        self.instanceName = instanceName

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
        
        print("Creating Objective Function...")
        #Objective Function
        self.model.setObjective(quicksum(self.varFacilityAssignment[facility.index]*facility.setup_cost for facility in self.facilities) + quicksum(self.length(facility.location,customer.location)*self.varCustomerAssignment[facility.index,customer.index] for facility in self.facilities for customer in self.customers),"minimize")
        self.model.data = self.varFacilityAssignment, self.varCustomerAssignment

    def optimize(self):
        print("Instace: %s" % self.instanceName)
        self.model.optimize()
        print("Instace: %s solved." % self.instanceName)
        EPS = 1.e-6
        _,cAssigned = self.model.data
        assignments = [(facility,customer) for (facility,customer) in cAssigned if self.model.getVal(cAssigned[facility,customer]) > EPS]
        obj = self.model.getObjVal()
        return  obj,assignments
    
    def length(self,point1, point2):
        return math.sqrt((point1.x - point2.x)**2 + (point1.y - point2.y)**2)

        