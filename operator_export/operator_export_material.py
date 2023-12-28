"""
Module charged with everything material related
"""
# coding=utf-8
from typing import Dict, Union
import bpy

from ..operator_utilities.file_definition_bwm import MaterialDefinition


def get_texture_name(texture_node: bpy.types.TextureNode) -> str:
    """
    Get the name of an image used inside a Image node
    """
    if texture_node.bl_idname == "ShaderNodeTexImage":
        if texture_node.image:
            return texture_node.image.name
    return ""


def get_next_node(
    node: bpy.types.Node, node_input: str, link: int
) -> Union[bpy.types.Node, None]:
    """
    Get node linked to a specific input
    """
    node_link = node.inputs.get(node_input).links
    if link + 1 > len(node_link):
        return None
    return node_link[link].from_socket.node


def description_from_material(
    material: bpy.types.Material,
) -> Dict[bpy.types.Material, MaterialDefinition]:
    """
    Transform a material from blender into a Black & White 2 material defintion
    """
    mat_desc = MaterialDefinition()
    mat_desc.type = material.name.split(".")[0]
    if not material.node_tree:
        return mat_desc

    material_node = material.node_tree.nodes.get("Principled BSDF")
    diffuse_node = get_next_node(material_node, "Base Color", 0)
    if diffuse_node:
        mat_desc.diffuseMap = get_texture_name(diffuse_node)

    lightmap_node = get_next_node(material_node, "Emission Strength", 0)
    if lightmap_node:
        mat_desc.lightMap = get_texture_name(lightmap_node)

    specular_node = get_next_node(material_node, "Specular", 0)
    if specular_node:
        mat_desc.specularMap = get_texture_name(specular_node)

    normal_node = get_next_node(material_node, "Normal", 0)
    if normal_node:
        mat_desc.normalMap = get_texture_name(normal_node)

    return mat_desc
