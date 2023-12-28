"""
This module handle the processing of skin rigging information from blender
into the .bwm format
"""
from typing import List, Union
from ..operator_utilities.file_definition_bwm import BWMFile


def create_bone_weigth_table(
    bwm_data: BWMFile,
) -> List[List[Union[float, int]]]:
    """
    Create the bone/weight table of the skin for the .bwm file
    """
    bone_table = [[[0] for _ in bwm_data.vertices] for _ in range(4)]
    weigth_table = [
        [[0.0 if i > 0 else 1.0] for _ in bwm_data.vertices] for i in range(4)
    ]

    bone_table.extend(weigth_table)
    return bone_table
