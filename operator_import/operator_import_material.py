# <pep8-80 compliant>
import logging
from os import path
from typing import List, Tuple
import bpy

from ..operator_utilities.file_definition_bwm import MaterialDefinition


def bpy_material_from_definition(
    material_definition: MaterialDefinition, texture_path: str, uvs_count: int
) -> Tuple[bpy.types.Material, List[bpy.types.NodeInputs]]:
    logger = logging.getLogger(__name__)

    images = [
        material_definition.diffuseMap,
        material_definition.specularMap,
        material_definition.lightMap,
        material_definition.normalMap,
        material_definition.growthMap,
        material_definition.animatedTexture,
    ]
    type = material_definition.type

    material = bpy.data.materials.new(name=type)
    material.use_nodes = True
    if type == '_plants_' or type == '_yard_' or type == '_vines_':
        material.blend_method = 'BLEND'
    else:
        material.blend_method = 'HASHED'
    material.alpha_threshold = 1.0

    material_nodes = material.node_tree.nodes
    material_link = material.node_tree.links
    uv_maps = [material_nodes.new("ShaderNodeUVMap") for i in range(uvs_count)]

    BSDF = material_nodes["Principled BSDF"]
    base_color_node = material_nodes.new("ShaderNodeMixRGB")
    base_color_node.blend_type = "MULTIPLY"
    base_color_node.inputs[1].default_value = (1.0, 1.0, 1.0, 1.0)
    base_color_node.inputs[2].default_value = (1.0, 1.0, 1.0, 1.0)
    material_link.new(BSDF.inputs[0], base_color_node.outputs[0])

    l_inputs = [
        [
            ("base_color_node", 1), ("base_color_node", 0),
            ("BSDF", 19), ("texture", 0)
        ],
        [("BSDF", 5), ("BSDF", 6), ("texture", 0)],
        [("base_color_node", 2), ("base_color_node", 0), ("texture", 0)],
        [("BSDF", 20), ("texture", 0)],
        [("texture", 0)],
        [("texture", 0)]
    ]
    l_outputs = [
        [
            ("texture", 0),
            ("texture", 1),
            ("texture", 1),
            ("uv_maps[0]", 0)
        ],
        [("texture", 0), ("texture", 1), ("uv_maps[0]", 0)],
        [("texture", 0), ("texture", 1), ("uv_maps[1]", 0)],
        [("texture", 0), ("uv_maps[0]", 0)],
        [("uv_maps[0]", 0)],
        [("uv_maps[0]", 0)]
    ]
    node_dict = {
        "base_color_node": base_color_node,
        "BSDF": BSDF,
        "texture": None
    }
    for i in range(uvs_count):
        node_dict[f"uv_maps[{i}]"] = uv_maps[i]

    for (file, inputs, outputs) in zip(images, l_inputs, l_outputs):
        try:
            if file != "":
                image = bpy.data.images.load(filepath=path.join(
                    texture_path, file), check_existing=True)
                texture = material_nodes.new('ShaderNodeTexImage')
                texture.image = image
                node_dict["texture"] = texture
                for (input, output) in zip(inputs, outputs):
                    n_input = node_dict[input[0]]
                    n_output = node_dict[output[0]]
                    material_link.new(
                        n_input.inputs[input[1]],
                        n_output.outputs[output[1]]
                    )
        except RuntimeError:
            logger.error(f"Could not find {file}", exc_info=True)

    return (material, uv_maps)
