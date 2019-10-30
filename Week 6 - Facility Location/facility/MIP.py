from pyscipopt import Model, quicksum
import math
from Preprocessing import Preprocessing
from EnumSettings import MipSolver
import docplex.mp.model as cpx
from docplex.util.status import JobSolveStatus


class MIP:
    DEBUG_MESSAGES = True

    def __init__(self, f, c, instanceName,mipSolver): 
        self.initialize(f,c,instanceName,mipSolver)

    def clear(self):
        self.facilities = [] 
        self.customers = [] 
        self.instanceName = None
        self.varFacilityAssignment = {}
        self.varCustomerAssignment = {}

    def initialize(self, f, c, instanceName,mipSolver):
        self.clear()
        self.facilities = f 
        self.customers = c 
        self.instanceName = instanceName
        self.varFacilityAssignment = {}
        self.varCustomerAssignment = {}
        self.solver = mipSolver

    def optimize(self,timeLimit):       
        if(self.solver == MipSolver.SCIP):
            self.__createModelSCIP()
            return self.__optimizeSCIP(timeLimit)
            
        elif (self.solver == MipSolver.CPLEX):
            self.__createModelCPLEX()
            return self.__optimizeCPLEX(timeLimit)

    def __createModelSCIP(self):
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
        self.model.setObjective(quicksum(self.varFacilityAssignment[facility.index]*facility.setup_cost for facility in self.facilities) + quicksum(Preprocessing.getEuclideanDistance(facility.location,customer.location)*self.varCustomerAssignment[facility.index,customer.index] for facility in self.facilities for customer in self.customers),"minimize")
        self.model.data = self.varFacilityAssignment, self.varCustomerAssignment

    def __createModelCPLEX(self):
        self.model = cpx.Model(self.instanceName)
        print("Creating Variables...")
        #Variables
        for f in self.facilities:
            self.varFacilityAssignment[f.index] = self.model.binary_var(name="facility-%s" % f.index)
            for c in self.customers:
                #Demand is binary because each customer must be served by exaclty one facility
                self.varCustomerAssignment[f.index,c.index] = self.model.binary_var(name="demand-(%s,%s)" % (f.index,c.index))

        print("Creating Constraints...")
        #Constraints
        #Ensure all customers are assigned to one facility
        for customer in self.customers:
            self.model.add_constraint(ct=self.model.sum(self.varCustomerAssignment[facility.index,customer.index] for facility in self.facilities) == 1,ctname="Demand(%s)"% customer.index)
        
        #Ensure the demand carried by the facility is at most its capacity
        for facility in self.facilities:
              self.model.add_constraint(ct=self.model.sum(self.varCustomerAssignment[facility.index,customer.index]*customer.demand for customer in self.customers) <= facility.capacity*self.varFacilityAssignment[facility.index],ctname="Capacity(%s)" % facility.index)
        
        #Strong Formulation
        for facility in self.facilities:
            for customer in self.customers:
                self.model.add_constraint(ct=self.varCustomerAssignment[facility.index,customer.index] <=  facility.capacity*self.varFacilityAssignment[facility.index],ctname="Strong(%s,%s)"%(facility.index,customer.index))
                self.model.add_constraint(self.varCustomerAssignment[facility.index,customer.index] >= 0,ctname="Strong2(%s,%s)"%(facility.index,customer.index))
    
        print("Creating Objective Function...")
        #Objective Function
        objective = self.model.sum(self.varFacilityAssignment[facility.index]*facility.setup_cost for facility in self.facilities) + self.model.sum(Preprocessing.getEuclideanDistance(facility.location,customer.location)*self.varCustomerAssignment[facility.index,customer.index] for facility in self.facilities for customer in self.customers)
        self.model.minimize(objective)


    def __optimizeCPLEX(self,timeLimit):
        print("Instace: %s" % self.instanceName)
        if not self.DEBUG_MESSAGES:
            self.model.print_information()
        
        self.model.parameters.timelimit = timeLimit
        self.model.parameters.threads = 8

        print("MIP - Optimizing...")
        solution = self.model.solve(log_output=self.DEBUG_MESSAGES)

        if solution is not None:
            print("Instace: %s solved." % self.instanceName)
        else:
            print("Instace: %s is infeasible" % self.instanceName)
            return None
       

        assignments = []

        for f in self.facilities:
            for c in self.customers:
                if(self.varCustomerAssignment[f.index,c.index].solution_value == 1):
                    assignments.append((f.index,c.index))
       
        obj = self.model.objective_value
        status = "No optimal"
        if self.model.get_solve_status() == JobSolveStatus.OPTIMAL_SOLUTION:
            status = "optimal"
        return  obj,assignments,status

    def __optimizeSCIP(self,timeLimit):
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
    
   

        