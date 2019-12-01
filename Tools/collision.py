# Created on 11 November 2019
# Defines class and functions for handling collisions between polygons

from pygame import Rect
from math import sqrt


# This contains information for a single polygon
class Polygon:
    def __init__(self, points):
        # Store all points
        self.points = points
        # Calculate all edges
        self.edges = [[val2 - val1 for val1, val2 in zip(points[i], points[(i + 1) % len(points)])]
                      for i in range(len(points))]

    def collides_polygon(self, polygon):
        # Convert Rect object to surface object
        if isinstance(polygon, Rect):
            polygon = Polygon([polygon.topleft, polygon.topright,
                               polygon.bottomright, polygon.bottomleft])
        # Store perpendicular unit vectors for each edge
        vectors = []
        for edge in self.edges + polygon.edges:
            # Get perpendicular vector
            v = [-edge[1], edge[0]]
            # Get magnitude and unit vector
            mag = sqrt(sum([pow(val, 2) for val in v]))
            v = [val / mag for val in v]
            # Make sure our vector is not parallel to any other vectors
            if all([not are_parallel(v, v_) for v_ in vectors]):
                vectors.append(v)
        # Go through each vector
        for vector in vectors:
            min_, max_ = [0, 0], [0, 0]
            # Go through each point on each polygon
            for i, points in enumerate([self.points, polygon.points]):
                # Start with the first point
                dot = dot_product(vector, points[0])
                min_[i], max_[i] = dot, dot
                for p in points[1:]:
                    # Calculate the dot product and see if it is a new min or max
                    dot = dot_product(vector, p)
                    if dot < min_[i]:
                        min_[i] = dot
                    elif dot > max_[i]:
                        max_[i] = dot

            # Figure out which projection is smaller
            idx = min_.index(min(min_))
            # Check if the projections don't overlap
            if min_[1 - idx] > max_[idx]:
                return False
        return True


# This performs a dot product
def dot_product(v1, v2):
    return v1[0] * v2[0] + v1[1] * v2[1]


# Checks if two vectors are parallel
def are_parallel(v1, v2):
    cross = v2[1] * v1[0] - v1[1] * v2[0]
    return abs(cross) < .01
