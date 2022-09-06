from typing import Dict, Union
import bpy

from ..operator_utilities.file_definition_bwm import (
    MaterialDefinition
)


def get_texture_name(
    texture_node: bpy.types.TextureNode
) -> str:
    if texture_node.bl_idname == 'ShaderNodeTexImage':
        if texture_node.image:
            return texture_node.image.name
    return ""


def get_next_node(
    node: bpy.types.Node,
    input: int,
    link: int
) -> Union[bpy.types.Node, None]:
    if input + 1 > len(node.inputs):
        return None
    node_link = node.inputs[input].links
    if link + 1 > len(node_link):
        return None
    return node_link[link].from_socket.node


def description_from_material(
    material: bpy.types.Material
) -> Dict[bpy.types.Material, MaterialDefinition]:
    mat_desc = MaterialDefinition()
    mat_desc.type = material.name.split('.')[0]
    if not material.node_tree:
        return mat_desc
    mat_node = material.node_tree.nodes[0]

    diffuse_node = get_next_node(mat_node, 0, 0)
    if diffuse_node:
        if diffuse_node.bl_idname == 'ShaderNodeMixRGB':
            diffuse_node = get_next_node(diffuse_node, 1, 0)
            if diffuse_node:
                mat_desc.diffuseMap = get_texture_name(diffuse_node)
        else:
            mat_desc.diffuseMap = get_texture_name(diffuse_node)

    lightmap_node = get_next_node(mat_node, 0, 0)
    if lightmap_node:
        if lightmap_node.bl_idname == 'ShaderNodeMixRGB':
            lightmap_node = get_next_node(lightmap_node, 2, 0)
            if lightmap_node:
                mat_desc.lightMap = get_texture_name(lightmap_node)

    return mat_desc
