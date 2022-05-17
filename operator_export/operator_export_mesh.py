import bpy
import bmesh
import math
from statistics import mean
from typing import List

from ..operator_utilities.file_definition_bwm import (
    BWMFile,
    MeshDescription,
    MaterialRef,
    Vertex,
    Stride
)
from ..operator_utilities.vector_utils import (
    correct_uv,
    zxy_to_xyz
)


def organise_mesh_data(
    mesh_collections: bpy.types.Collection,
    bwm_data: BWMFile
) -> BWMFile:
    bwm_data.meshDescriptions = []
    type = bwm_data.modelHeader.type
    materials = []

    for lod in range(1, 5):
        lod_collection = mesh_collections.children.get(f"lod{lod}")
        if lod_collection:
            for _, obj in lod_collection.objects.items():
                if obj.type == 'MESH':
                    mesh_desc = MeshDescription()
                    mesh_desc.unknown_int = 2
                    mesh_desc.name = obj.name
                    rotation = zxy_to_xyz(obj.matrix_world[:3, :3])
                    mesh_desc.axis1 = rotation[0]
                    mesh_desc.axis2 = rotation[1]
                    mesh_desc.axis3 = rotation[2]
                    mesh_desc.position = zxy_to_xyz(obj.location)

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
                    vertices_add = organise_uv_data(
                        vertices_add,
                        obj,
                        obj.uv_layers
                    )
                    bwm_data.vertices.extend(vertices_add)
                    mesh_desc.height = mesh_desc.box2[1]

                    # TODO Extract bone weight data

                    # Create indicies and face data
                    mesh_desc.indiciesOffset = len(bwm_data.indexes)
                    bwm_data.indexes.extend(
                        organise_index_data(mesh_desc, obj.polygons, type)
                    )

                    mat_ref = MaterialRef()
                    mat_ref.indiciesOffset = mesh_desc.indiciesOffset
                    mat_ref.indiciesSize = mesh_desc.indiciesSize
                    mat_ref.facesOffset = 0
                    mat_ref.facesSize = mesh_desc.facesCount
                    mat_ref.vertexOffset = mesh_desc.vertexOffset
                    mat_ref.vertexSize = mesh_desc.vertexSize
                    mat_ref.materialDefinition = 0
                    mesh_desc.materialRefs = [mat_ref]

    return bwm_data


def organise_vertex_data(
    mesh_description: MeshDescription,
    vertices: List[bpy.types.MeshVertex],
    uv_layers: List[bpy.types.MeshUVLoopLayer]
) -> List[bpy.types.MeshVertex]:
    num_vertex = len(vertices)
    mesh_description.vertexSize = num_vertex
    loc_list = [zxy_to_xyz(vertex.co) for vertex in vertices]
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
        r_vertex.position = zxy_to_xyz(c_vertex.co)
        r_vertex.normal = zxy_to_xyz(c_vertex.normal)
        ret_vertices[vertex] = r_vertex
        for uv_layer in uv_layers:
            ret_vertices[vertex].uvs.append((0.0, 0.0))

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

    if type == 3:
        indexes = [
            index for i in mesh_description.facesCount for index in indexes[i]
            if i % 4 == 0
        ]
        mesh_description.indiciesSize = len(indexes)

    elif type == 2:
        indexes = [index for face in faces_seq for index in face.vertices]
        mesh_description.indiciesSize = len(indexes)

    return indexes


def organise_uv_data(
    vertices: List[Vertex],
    mesh: bpy.types.Mesh,
    uv_layers: List[bpy.types.MeshUVLoopLayer]
) -> List[Vertex]:

    faces_seq = mesh.polygons

    for uv_layer in uv_layers:
        if "texture" in uv_layer.name:
            uv_idx = 0
        elif "ligthmap" in uv_layer.name:
            uv_idx = 1
        elif "unknown" in uv_layer.name:
            uv_idx = 2
        else:
            continue

        for face in faces_seq:
            for i in face.loop_indices:
                lk_idx = mesh.loops[i].vertex_index
                uv_coord = correct_uv(uv_layer.data[i].uv)
                vertices[lk_idx].uvs[uv_idx] = uv_coord
        uv_idx += 1

    return vertices
