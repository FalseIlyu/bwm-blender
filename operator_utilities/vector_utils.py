# coding=utf-8
"""
Store utility functions to change the coordinate system of vectors and matrixes
(for uv an geometry), build transformation matrix from BWM entities.
"""
from typing import Tuple, Union, Callable
import numpy as np
from ..operator_utilities.file_definition_bwm import (
    Bone,
    Entity,
    MeshDescription,
)


def zxy_to_xyz(matrix_or_vector: np.ndarray) -> np.ndarray:
    """
    Rotate a vector or a rotation matrix defined in zxy
    coordinate to an xyz one.
    """
    if len(matrix_or_vector) != 3:
        raise ValueError("Must be a vector of size 3 or a 3x3 matrix")

    return np.matmul(
        [
            [0.0, 0.0, 1.0],  # Z -> X
            [1.0, 0.0, 0.0],  # X -> Y
            [0.0, 1.0, 0.0],  # Y -> Z
        ],
        matrix_or_vector,
    )


def xyz_to_zxy(matrix_or_vector: np.ndarray) -> np.ndarray:
    """
    Rotate a vector or a rotation matrix defined in xyz
    coordinate to an zxy one.
    """
    if len(matrix_or_vector) != 3:
        raise ValueError("Must be a vector of size 3 or a 3x3 matrix")

    return np.matmul(
        [
            [0.0, 1.0, 0.0],  # X -> Z
            [0.0, 0.0, 1.0],  # Y -> X
            [1.0, 0.0, 0.0],  # Z -> Y
        ],
        matrix_or_vector,
    )


def construct_transformation_matrix(
    bwm_entity: Union[Bone, Entity, MeshDescription],
    coordinate_rotation: Callable[[np.ndarray], np.ndarray],
) -> np.ndarray:
    """
    Build a transformation matrix from any BWM entity with three axis and a
    position vector.
    """
    rotation = coordinate_rotation(
        [bwm_entity.zaxis, bwm_entity.xaxis, bwm_entity.yaxis]
    )
    point = coordinate_rotation(bwm_entity.position)

    return [
        list(rotation[:, 0]) + [0.0],
        list(rotation[:, 1]) + [0.0],
        list(rotation[:, 2]) + [0.0],
        list(point) + [1.0],
    ]


def correct_uv(vector: Tuple[float, float]) -> Tuple[float, float]:
    """
    Switch from Black & White uv coordinate to Blender uv coordinates
    and vice-versa
    """
    return (vector[0], 1.0 - vector[1])
