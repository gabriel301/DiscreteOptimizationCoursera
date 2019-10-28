import math
import numpy as np
from sklearn.cluster import MiniBatchKMeans

class Preprocessing:

    #Calculate the Euclidean distance between two points
    @staticmethod    
    def getEuclideanDistance(point1, point2):
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
                distances.append(Preprocessing.getEuclideanDistance(f1.location,f2.location))
            f1.distance_quantiles.extend(np.quantile(a=distances,q=intervals, interpolation='midpoint').tolist())

    #Return quantiles for distances between facilities
    @staticmethod   
    def getFacilityClusters(facilities,numberClusters):
        print("Genarating %s Clusters..."%numberClusters)
        clusters = {}
        dataPoints = np.array([[facility.location.x,facility.location.y] for facility in facilities])
        kmeans = MiniBatchKMeans(n_clusters=numberClusters, random_state=0,tol=1.e-6).fit(dataPoints)
        for facility in facilities:
            if kmeans.labels_[facility.index] not in clusters.keys():
                clusters[kmeans.labels_[facility.index]] = []
            clusters.get(kmeans.labels_[facility.index]).append(facility.index)
        
        return clusters

    #Calculate the Manhatan distance between two points
    @staticmethod
    def getManhatanDistance(p1,p2):
       return  math.fabs(p1.x-p2.x) + math.fabs(p1.y-p2.y)


           