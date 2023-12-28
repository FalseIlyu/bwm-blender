"""
Main module contains only the function to transform data from a .bwm file into
a Blender collection
"""
# coding=utf-8
import logging
from typing import List, Union
from os import path
import bpy

from ..operator_utilities.file_definition_bwm import (
    BWMFile,
    FileType,
    Bone,
    Entity,
    Unknown1,
    CollisionPoint
)
from .operator_import_material import bpy_material_from_definition
from .operator_import_mesh import bpy_obj_from_defintion
from ..operator_utilities.vector_utils import (
    zxy_to_xyz,
    construct_transformation_matrix,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

def collection_arrows(name: str, collection: List[Union[Bone, Entity]], draw_size: float, col: bpy.types.Collection):
    """
    Add a simple collection of oriented point inside a blender collection
    """
    logger.info("Loading %s from .bwm", name)
    if collection:
        n_col = bpy.data.collections.new(name)
        for object_desc in collection:
            blender_obj = bpy.data.objects.new(object_desc.name, None)
            blender_obj.matrix_world = construct_transformation_matrix(
                object_desc, zxy_to_xyz
            )

            blender_obj.empty_display_size = draw_size
            blender_obj.empty_display_type = "ARROWS"

            n_col.objects.link(blender_obj)

        col.children.link(n_col)

def collection_points(name: str, collection: List[Union[Unknown1, CollisionPoint]], col: bpy.types.Collection):
    """
    Add a simple collection of point inside a blender collection
    """
    data_col = [zxy_to_xyz(data.position) for data in collection]
    if collection:
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(mesh.name, mesh)
        mesh.from_pydata(data_col, [], [])

        n_col = bpy.data.collections.new(name)
        n_col.objects.link(obj)
        col.children.link(n_col)

def read_bwm_data(context, filepath: str):
    """
    Organize data from a .bwm file inside a Blender collection
    """
    logger.info("Reading data from Black & White Model file")
    with open(filepath, "rb") as file:
        bwm = BWMFile(file)
        uvs_count = len(bwm.vertices[0].uvs)

        model_type = bwm.modelHeader.type
        bwm_name = path.basename(filepath[:-4])

        col = bpy.data.collections.new(bwm_name)

        if not (model_type in (FileType.SKIN, FileType.MODEL)):
            raise ValueError("Not a supported type")

        logger.info("Creating material from definition")
        list_materials, list_uv_nodes = zip(
            *[
                bpy_material_from_definition(
                    material_definition,
                    path.join(path.dirname(filepath), "..\\textures"),
                    uvs_count,
                )
                for material_definition in bwm.materialDefinitions
            ]
        )

        mesh_col = bpy.data.collections.new("mesh")
        col.children.link(mesh_col)
        lods = [[] for _ in range(4)]

        logger.info("Creating mesh from definition")
        for mesh_description in bwm.meshDescriptions:
            obj = bpy_obj_from_defintion(
                mesh_description, bwm, list_materials, list_uv_nodes, bwm_name
            )

            lods[mesh_description.lod_level - 1].append(obj)

        logger.info("Put mesh into lods")
        for lod_level, meshses in enumerate(lods):
            if meshses:
                n_col = bpy.data.collections.new(f"lod{lod_level + 1}")
                for mesh in meshses:
                    n_col.objects.link(mesh)
                mesh_col.children.link(n_col)

        logger.info("Loading additional mesh data")
        draw_size = bwm.modelHeader.height / 20
        collection_arrows("bones", bwm.bones, draw_size, col)
        collection_arrows("entities", bwm.entities, draw_size, col)

        collection_points("unknowns", bwm.unknowns1, col)
        collection_points("collision", bwm.collisionPoints, col)

        bpy.context.scene.collection.children.link(col)

    return {"FINISHED"}
