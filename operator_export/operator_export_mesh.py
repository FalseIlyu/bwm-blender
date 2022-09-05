import bpy
import bmesh
import math
from statistics import mean
from typing import List

from ..operator_utilities.file_definition_bwm import (
    BWMFile,
    FileType,
    MeshDescription,
    MaterialRef,
    Vertex,
    Stride,
    UVType
)
from ..operator_utilities.vector_utils import (
    correct_uv,
    xyz_to_zxy
)


def organise_mesh_data(
    mesh_collections: bpy.types.Collection,
    bwm_data: BWMFile
) -> BWMFile:

    bwm_data.meshDescriptions = []
    type = bwm_data.modelHeader.type
    # materials = []

    face_offset = 0
    vertex_offset = 0
    for lod in range(1, 5):
        lod_collection = mesh_collections.children.get(f"lod{lod}")
        if lod_collection:
            for _, obj in lod_collection.objects.items():
                if obj.type == 'MESH':
                    mesh_desc = MeshDescription()
                    mesh_desc.unknown_int = 2
                    mesh_desc.name = obj.name
                    rotation = [vector[:3] for vector in obj.matrix_world[:3]]
                    mesh_desc.zaxis = rotation[0]
                    mesh_desc.xaxis = rotation[1]
                    mesh_desc.yaxis = rotation[2]
                    mesh_desc.position = obj.location

                    # Organise mesh description metadata
                    obj = obj.to_mesh(preserve_all_data_layers=True)
                    b_mesh = bmesh.new()
                    b_mesh.from_mesh(obj)
                    mesh_desc.lod_level = lod
                    mesh_desc.bbox_volume = b_mesh.calc_volume()

                    bwm_data.meshDescriptions.append(mesh_desc)

                    # Extract vertex
                    mesh_desc.vertexOffset = len(bwm_data.vertices)
                    vertices_add = organise_vertex_data(
                        mesh_desc,
                        obj.vertices,
                        obj.uv_layers
                    )
                    bwm_data.vertices.extend(vertices_add)
                    mesh_desc.height = mesh_desc.box2[1]

                    # TODO Extract bone weight data

                    # Create indicies and face data
                    mesh_desc.indiciesOffset = len(bwm_data.indexes)
                    indexes_add = organise_index_data(
                        mesh_desc, obj.polygons, type
                    )
                    indexes_add = [i + vertex_offset for i in indexes_add]
                    bwm_data.indexes.extend(indexes_add)
                    vertex_offset = len(bwm_data.vertices)

                    mat_ref = MaterialRef()
                    mat_ref.indiciesOffset = mesh_desc.indiciesOffset
                    mat_ref.indiciesSize = mesh_desc.indiciesSize
                    mat_ref.facesOffset = face_offset
                    mat_ref.facesSize = mesh_desc.facesCount
                    mat_ref.vertexOffset = mesh_desc.vertexOffset
                    mat_ref.vertexSize = mesh_desc.vertexSize
                    mat_ref.materialDefinition = 0
                    mesh_desc.materialRefs = [mat_ref]

                    face_offset += mat_ref.facesSize

    return bwm_data


def organise_vertex_data(
    mesh_description: MeshDescription,
    vertices: List[bpy.types.MeshVertex],
    uv_layers: List[bpy.types.MeshUVLoopLayer]
) -> List[bpy.types.MeshVertex]:

    num_vertex = len(vertices)
    mesh_description.vertexSize = num_vertex
    loc_list = [vertex.co for vertex in vertices]
    x = [loc[0] for loc in loc_list]
    y = [loc[1] for loc in loc_list]
    z = [loc[2] for loc in loc_list]
    mesh_description.cent = (
        mean(x),
        mean(y),
        mean(z)
    )
    mesh_description.box1 = (
        min(x),
        min(y),
        min(z)
    )
    mesh_description.box2 = (
        max(x),
        max(y),
        max(z)
    )
    mesh_description.radius = max(
        [math.dist(loc, mesh_description.cent) for loc in loc_list]
    )
    ret_vertices = [Vertex(Stride()) for i in range(num_vertex)]

    for vertex in range(num_vertex):
        c_vertex = vertices[vertex]
        r_vertex = ret_vertices[vertex]
        r_vertex.position = c_vertex.co
        r_vertex.normal = c_vertex.normal
        ret_vertices[vertex] = r_vertex

        for uv_layer in uv_layers:
            if UVType(0).name in uv_layer.name:
                uv_idx = 0
            elif UVType(1).name in uv_layer.name:
                uv_idx = 1
            elif UVType(2).name in uv_layer.name:
                uv_idx = 2
            else:
                continue

            uv_coord = correct_uv(uv_layer.data[vertex].uv)
            r_vertex.uvs.insert(uv_idx, uv_coord)

    return ret_vertices


def organise_index_data(
    mesh_description: MeshDescription,
    faces_seq: List[bpy.types.MeshPolygon],
    type: int
) -> List[int]:

    vertex_offset = mesh_description.vertexOffset
    indexes = [
        [index + vertex_offset for index in face.vertices]
        for face in faces_seq
    ]
    mesh_description.facesCount = len(indexes)

    if type == FileType.SKIN:
        indexes = [
            index for i in mesh_description.facesCount for index in indexes[i]
            if i % 4 == 0
        ]
        mesh_description.indiciesSize = len(indexes)

    elif type == FileType.MODEL:
        indexes = [index for face in faces_seq for index in face.vertices]
        mesh_description.indiciesSize = len(indexes)

    return indexes


"""def organise_uv_data(
    vertices: List[Vertex],
    mesh: bpy.types.Mesh,
    uv_layers: List[bpy.types.MeshUVLoopLayer]
) -> None:

    faces_seq = mesh.polygons

    for face in faces_seq:
        for i in face.loop_indices:
            for uv_layer in uv_layers:
                if UVType(0).name in uv_layer.name:
                    uv_idx = 0
                elif UVType(1).name in uv_layer.name:
                    uv_idx = 1
                elif UVType(2).name in uv_layer.name:
                    uv_idx = 2
                else:
                    continue
                lk_idx = mesh.loops[i].vertex_index
                uv_coord = correct_uv(uv_layer.data[i].uv)
                vertices[lk_idx].uvs.insert(uv_idx, uv_coord)"""
