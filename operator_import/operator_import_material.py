"""
Module charged with everything material related
"""
# coding=utf-8
import logging
from os import path
from typing import List, Tuple, Dict
import bpy

from ..operator_utilities.file_definition_bwm import MaterialDefinition


def bpy_material_from_definition(
    material_definition: MaterialDefinition, texture_path: str, uvs_count: int
) -> Tuple[bpy.types.Material, List[bpy.types.NodeInputs]]:
    """
    Translate black & white 2 material defintion into a Blender material
    """
    logger = logging.getLogger(__name__)

    images = [
        material_definition.diffuseMap,
        material_definition.specularMap,
        material_definition.lightMap,
        material_definition.normalMap,
        material_definition.growthMap,
        material_definition.animatedTexture,
    ]
    texture_type = material_definition.type

    material = bpy.data.materials.new(name=texture_type)
    material.use_nodes = True
    if texture_type == "_plants_" or texture_type == "_yard_" or texture_type == "_vines_":
        material.blend_method = "BLEND"
    else:
        material.blend_method = "HASHED"
    material.alpha_threshold = 1.0

    material_nodes = material.node_tree.nodes
    material_link = material.node_tree.links
    uv_maps = [material_nodes.new("ShaderNodeUVMap") for i in range(uvs_count)]

    BSDF = material_nodes["Principled BSDF"]

    l_inputs = [
        [("BSDF", "Base Color"), ("BSDF", "Emission"), ("BSDF", "Alpha"), ("texture", "Vector")],
        [("BSDF", "Specular"), ("BSDF", "Specular Tint"), ("texture", "Vector")],
        [("BSDF", "Emission Strength"), ("texture", "Vector")],
        [("BSDF", "Normal"), ("texture", "Vector")],
        [("texture", "Vector")],
        [("texture", "Vector")],
    ]
    l_outputs = [
        [("texture", "Color"), ("texture", "Color"), ("texture", "Alpha"), ("uv_maps[0]", "UV")],
        [("texture", "Color"), ("texture", "Color"), ("uv_maps[0]", "UV")],
        [("texture", "Color"), ("uv_maps[1]", "UV")],
        [("texture", "Color"), ("uv_maps[0]", "UV")],
        [("uv_maps[0]", "UV")],
        [("uv_maps[0]", "UV")],
    ]
    node_dict : Dict[str, bpy.types.Node]
    node_dict = {
        "BSDF": BSDF,
        "texture": None,
    }
    for i in range(uvs_count):
        node_dict[f"uv_maps[{i}]"] = uv_maps[i]

    for (file, inputs, outputs) in zip(images, l_inputs, l_outputs):
        try:
            if file != "":
                image = bpy.data.images.load(
                    filepath=path.join(texture_path, file), check_existing=True
                )
                texture = material_nodes.new("ShaderNodeTexImage")
                texture.image = image
                node_dict["texture"] = texture
                for (node_input, output) in zip(inputs, outputs):
                    n_input = node_dict[node_input[0]]
                    n_output = node_dict[output[0]]

                    material_link.new(
                        n_input.inputs.get(node_input[1]), n_output.outputs.get(output[1])
                    )
        except RuntimeError:
            logger.error("Could not find %s", file, exc_info=True)

    return (material, uv_maps)
