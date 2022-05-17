import bpy
from types import List

from ..operator_utilities.file_definition_bwm import (
    MaterialDefinition
)


def extract_material_list(
    collection: bpy.types.Collection
) -> List[bpy.types.Material]:
    materials = []
    empty_mat = MaterialDefinition()
    return (materials, empty_mat)
