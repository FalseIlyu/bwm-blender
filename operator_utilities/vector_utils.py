# <pep8-80 compliant>
from typing import Tuple, Union, Callable
import numpy as np
from .file_definition_bwm import (
    Bone,
    Entity,
    MeshDescription,
)


def zxy_to_xyz(matrix_or_vector: np.ndarray) -> np.ndarray:
    return np.array([
            [0.0, 0.0, -1.0],  # Z -> X
            [-1.0, 0.0, 0.0],  # X -> Y
            [0.0, 1.0, 0.0]   # Y -> Z
        ]).dot(matrix_or_vector)


def xyz_to_zxy(matrix_or_vector) -> np.ndarray:
    return np.array([
            [0.0, 1.0, 0.0],  # X -> Z
            [0.0, 0.0, 1.0],  # Y -> Y
            [-1.0, 0.0, 0.0]   # Z -> Z
        ]).dot(matrix_or_vector)


def construct_transformation_matrix(
    bwm_entity: Union[Bone, Entity, MeshDescription],
    coordinate_rotation: Callable[[np.ndarray], np.ndarray]
) -> np.ndarray:
    rotation = coordinate_rotation([
            bwm_entity.axis1,
            bwm_entity.axis2,
            bwm_entity.axis3
        ])
    point = coordinate_rotation(bwm_entity.position)

    return np.array([
        [rotation[i][0] if i < 3 else 0.0 for i in range(4)],
        [rotation[i][1] if i < 3 else 0.0 for i in range(4)],
        [rotation[i][2] if i < 3 else 0.0 for i in range(4)],
        [point[i] if i < 3 else 1.0 for i in range(4)]
        ])


def correct_uv(vector: Tuple[float, float]) -> Tuple[float, float]:
    return (vector[0], 1.0 - vector[1])
