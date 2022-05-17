import bpy

from ..operator_utilities.file_definition_bwm import BWMFile
from .operator_export_mesh import organise_mesh_data
from .operator_export_stride import create_vertex_stride


def organize_bwm_data(settings, collection: bpy.types.Collection) -> BWMFile:
    # collection = settings["selected_collection"]
    file = BWMFile()

    meshes = collection.children.get('mesh')
    file = organise_mesh_data(meshes, file)
    file.modelHeader.meshDescriptionCount = len(file.meshDescriptions)
    file.modelHeader.indexCount = len(file.indexes)
    file.modelHeader.vertexCount = len(file.vertices)
    file.strides[0] = create_vertex_stride(file.vertices[0])
    file.modelHeader.box1 = file.meshDescriptions[0].box1
    file.modelHeader.box2 = file.meshDescriptions[0].box2
    file.modelHeader.cent = file.meshDescriptions[0].cent
    file.modelHeader.volume = file.meshDescriptions[0].bbox_volume
    file.modelHeader.height = file.meshDescriptions[0].height
    file.modelHeader.radius = file.meshDescriptions[0].radius

    if settings["type"] == 'OPT_MODEL' or settings["experimental"]:
        # collision = collection.children.get("collision")
        # if collision:
        #     for obj in collision.objects.values():
        #         if obj.type == 'MESH':
        #             obj = obj.to_mesh()
        #             for vertex in obj.vertices.values():
        #                 file.collisionPoints.append(collisionPoint())
        #                 file.collisionPoints[-1].position = correct_axis(
        #   vertex.co
        #   )
        #     file.modelHeader.collisionPointCount = len(file.collisionPoints)

        pass

    if settings["type"] == 'OPT_SKIN' or settings["experimental"]:
        pass

    if settings["version"] == 'OPT_SIX':
        pass

    file.fileHeader.size = file.size()
    file.fileHeader.metadataSize = file.metadataSize()

    return file
