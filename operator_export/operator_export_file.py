"""
Main module contains only the function to transform a blender collection into
a .bwm file
"""
# coding=utf-8
import numpy as np
import bpy

from ..operator_utilities.vector_utils import xyz_to_zxy

from .operator_export_material import description_from_material

from ..operator_utilities.file_definition_bwm import (
    BWMFile,
    Bone,
    CollisionPoint,
    Entity,
    FileType,
)
from .operator_export_mesh import organise_mesh_data
from .operator_export_stride import create_vertex_stride


def organize_bwm_data(settings, collection: bpy.types.Collection) -> BWMFile:
    """
    Organize a valid blender collection into a format that can be written
    into a .bwm file
    """
    file = BWMFile()

    file.materialDefinitions = [
        description_from_material(material) for material in bpy.data.materials
    ]
    file.modelHeader.materialDefinitionCount = len(file.materialDefinitions)

    if settings["version"] == "OPT_SIX":
        file.fileHeader.version = 6

    if settings["type"] == "OPT_SKIN" or settings["experimental"]:
        file.modelHeader.type = FileType.SKIN

        bone_collection = collection.children.get("bones")
        if bone_collection:
            for obj in bone_collection.objects.values():
                if obj.type == "EMPTY":
                    index = int(obj.name)
                    rotation = xyz_to_zxy(np.array(obj.matrix_world)[:3, :3])
                    bone = Bone()
                    bone.zaxis = rotation[0]
                    bone.yaxis = rotation[2]
                    bone.xaxis = rotation[1]
                    bone.position = xyz_to_zxy(obj.location)
                    file.bones.insert(index, bone)
            file.modelHeader.boneCount = len(file.bones)

    if settings["type"] == "OPT_MODEL" or settings["experimental"]:
        file.modelHeader.type = FileType.MODEL

        entity_collection = collection.children.get("entities")
        if entity_collection:
            for obj in entity_collection.objects.values():
                if obj.type == "EMPTY":
                    rotation = xyz_to_zxy(np.array(obj.matrix_world)[:3, :3])
                    entity = Entity()
                    entity.zaxis = rotation[0]
                    entity.yaxis = rotation[2]
                    entity.xaxis = rotation[1]
                    entity.position = xyz_to_zxy(obj.location)
                    entity.name = obj.name.split(".")[0]
                    file.entities.append(entity)
            file.modelHeader.entityCount = len(file.entities)

        collision = collection.children.get("collision")
        if collision:
            for obj in collision.objects.values():
                if obj.type == "MESH":
                    obj = obj.to_mesh()
                    for point in obj.vertices.values():
                        col_point = CollisionPoint()
                        col_point.position = xyz_to_zxy(point.co)
                        file.collisionPoints.append(col_point)
        file.modelHeader.collisionPointCount = len(file.collisionPoints)

    meshes = collection.children.get("mesh")
    file = organise_mesh_data(meshes, file)
    file.modelHeader.meshDescriptionCount = len(file.meshDescriptions)
    file.modelHeader.indexCount = len(file.indexes)
    file.modelHeader.vertexCount = len(file.vertices)
    file.strides[0] = create_vertex_stride(file.vertices[0])
    file.modelHeader.box1 = file.meshDescriptions[0].box1
    file.modelHeader.box2 = file.meshDescriptions[0].box2
    file.modelHeader.cent = file.meshDescriptions[0].cent
    file.modelHeader.pnt = file.modelHeader.box2
    file.modelHeader.volume = file.meshDescriptions[0].bbox_volume
    file.modelHeader.height = file.meshDescriptions[0].height
    file.modelHeader.radius = file.meshDescriptions[0].radius

    file.fileHeader.size = file.size()
    file.fileHeader.metadataSize = file.metadataSize()

    return file
