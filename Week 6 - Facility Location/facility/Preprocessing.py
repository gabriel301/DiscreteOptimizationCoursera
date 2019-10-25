import math
import numpy as np

class Preprocessing:

    #Calculate the Euclidean distance between two points
    @staticmethod    
    def length(point1, point2):
        return math.sqrt((point1.x - point2.x)**2 + (point1.y - point2.y)**2)

    #Return quantiles for distances between facilities
    @staticmethod   
    def getDistanceQuantiles(facilities,intervals):
        print("Genarating Quantiles...")
        for f1 in facilities:
            distances = []
            for f2 in facilities:
                if f1.index == f2.index:
                    continue
                distances.append(Preprocessing.length(f1.location,f2.location))
            f1.distance_quantiles.extend(np.quantile(a=distances,q=intervals, interpolation='midpoint').tolist())
           