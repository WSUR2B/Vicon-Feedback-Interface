"""
Kinematics Calculation Module

This module provides fundamental geometric and mathematical functions for
biomechanical kinematics calculations.

Functions:
    - transform_using_transformation_matrix(): Apply 4x4 transformation to points
    - compute_segment_vector(): Calculate vector between two markers
    - calculate_2d_angle(): Compute angle between two 2D vectors
    - calculate_distance(): Compute Euclidean distance between two points

These functions are used by the MarkerKinematics module to compute joint angles
and positions from marker data.

Author: Daniil Grubich
Institution: Wayne State University - R2B Lab
"""

# ============================================================================
# IMPORTS
# ============================================================================

import numpy as np

# ============================================================================
# TRANSFORMATION FUNCTIONS
# ============================================================================

def transform_using_transformation_matrix(transformation_matrix, points):
    """
    Transforms a set of points using a transformation matrix.

    Args:
        transformation_matrix (numpy.ndarray): The transformation matrix to apply to the points.
        points (numpy.ndarray): The points to be transformed.

    Returns:
        numpy.ndarray: The transformed points.

    """
    # Ensure points are in homogeneous coordinates
    points_homogeneous = np.hstack([points, np.ones((points.shape[0], 1))])
    # Apply the transformation matrix to the points
    transformed_points_homogeneous = points_homogeneous @ transformation_matrix.T
    # Convert back from homogeneous coordinates
    transformed_points = transformed_points_homogeneous[:, :3]
    return transformed_points


def compute_segment_vector(start_marker, end_marker):
    """
    Compute the vector of a segment defined by two markers.

    Parameters:
        start_marker (list): The coordinates of the start marker.
        end_marker (list): The coordinates of the end marker.

    Returns:
        numpy.ndarray: The vector representing the segment.
    """
    return np.array(end_marker) - np.array(start_marker)


def calculate_2d_angle(vector1, vector2):
    """
    Calculates the angle between two 2D vectors.

    Args:
        vector1 (list): The first vector in the form [x1, y1].
        vector2 (list): The second vector in the form [x2, y2].

    Returns:
        float: The angle between the two vectors in degrees.
    """
    angle = np.arctan2(vector2[1], vector2[0]) - np.arctan2(vector1[1], vector1[0])
    angle_degrees = np.degrees(angle)
    return angle_degrees

def calculate_distance(marker1, marker2):
    """
    Calculate the distance between two markers.

    Parameters:
    marker1 (tuple): The coordinates of the first marker.
    marker2 (tuple): The coordinates of the second marker.

    Returns:
    float: The distance between the two markers.
    """
    return np.linalg.norm(np.array(marker2) - np.array(marker1))

