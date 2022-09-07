"""
Module charged with creating the description of the different meshes and
associate them with the proper material definition. It also build the
vertices and indexes array.
"""
# coding=utf-8
from typing import Dict, List, Tuple
import math
from statistics import mean

import bpy
import bmesh

from ..operator_utilities.file_definition_bwm import (
    BWMFile,
    FileType,
    MeshDescription,
    MaterialRef,
    Vertex,
    Stride,
    UVType,
)
from ..operator_utilities.vector_utils import correct_uv, xyz_to_zxy


def organise_mesh_data(
    mesh_collections: bpy.types.Collection,
    bwm_data: BWMFile,
) -> BWMFile:
    """
    Create the mesh descriptions and related material references, and organise
    vertices and indexes accordingly.
    """
    bwm_data.meshDescriptions = []
    m_type = bwm_data.modelHeader.type
    l_materials = list(bpy.data.materials)

    for lod in range(1, 5):
        lod_collection = mesh_collections.children.get(f"lod{lod}")
        if lod_collection:
            for _, obj in lod_collection.objects.items():
                if obj.type == "MESH":
                    mesh_desc = create_basic_description(obj, lod)
                    bwm_data.meshDescriptions.append(mesh_desc)

                    mesh_desc.indiciesOffset = len(bwm_data.indexes)
                    mesh_desc.vertexOffset = len(bwm_data.vertices)
                    vertex_offset = mesh_desc.vertexOffset
                    indicies_offset = mesh_desc.indiciesOffset
                    # Group polygons by materials.
                    d_material_polygon = {
                        material: [] for material in range(len(l_materials))
                    }
                    for polygon in obj.data.polygons:
                        polygon_material = polygon.material_index
                        d_material_polygon[polygon_material].append(polygon)

                    face_offset = 0
                    for material_slot in d_material_polygon:
                        l_polygons = d_material_polygon[material_slot]
                        if not l_polygons:
                            continue

                        vertices_add, d_indexes = organise_vertex_data(
                            l_polygons, obj.data.vertices, obj.data.uv_layers
                        )
                        bwm_data.vertices.extend(vertices_add)

                        indexes_add = organise_index_data(
                            l_polygons, vertex_offset, d_indexes, m_type
                        )
                        bwm_data.indexes.extend(indexes_add)

                        # TODO Extract bone weight data

                        # Create material
                        material = obj.material_slots[material_slot].material
                        mat_ref = MaterialRef()
                        mat_ref.materialDefinition = l_materials.index(material)
                        mat_ref.facesOffset = face_offset
                        mat_ref.vertexOffset = vertex_offset
                        mat_ref.indiciesOffset = indicies_offset
                        mat_ref.facesSize = len(l_polygons)
                        mat_ref.indiciesSize = len(indexes_add)
                        mat_ref.vertexSize = len(vertices_add)
                        mesh_desc.materialRefs.append(mat_ref)

                        if m_type == FileType.SKIN:
                            mat_ref.indiciesSize -= 2

                        face_offset += mat_ref.facesSize
                        indicies_offset += mat_ref.indiciesSize
                        vertex_offset += mat_ref.vertexSize
                        mesh_desc.facesCount += mat_ref.facesSize

                    mesh_desc.indiciesSize = indicies_offset
                    mesh_desc.indiciesSize -= mesh_desc.indiciesOffset
                    mesh_desc.vertexSize = vertex_offset
                    mesh_desc.vertexSize -= mesh_desc.vertexOffset

                    mesh_desc.materialRefsCount = len(mesh_desc.materialRefs)
                    create_bounds(mesh_desc, obj.data.vertices)

    return bwm_data


def create_basic_description(
    obj: bpy.types.Object, lod: int
) -> MeshDescription:
    """
    Build the most basic information of the mesh description,
    name, lod, transformation matrix and volume.
    """
    mesh_desc = MeshDescription()

    mesh_desc.unknown_int = 2
    if lod > 1:
        mesh_desc.unknown_int = 1
    mesh_desc.name = obj.name.split(".")[0]
    rotation = xyz_to_zxy([vector[:3] for vector in obj.matrix_world[:3]])
    mesh_desc.zaxis = rotation[0]
    mesh_desc.yaxis = rotation[1]
    mesh_desc.xaxis = rotation[2]
    mesh_desc.position = obj.location

    # Organise mesh description metadata
    obj = obj.to_mesh(preserve_all_data_layers=True)
    b_mesh = bmesh.new()
    b_mesh.from_mesh(obj)
    mesh_desc.lod_level = lod
    mesh_desc.bbox_volume = b_mesh.calc_volume()

    return mesh_desc


def organise_vertex_data(
    polygons: List[bpy.types.MeshPolygon],
    vertices: List[bpy.types.MeshVertex],
    uv_layers: List[bpy.types.MeshUVLoopLayer],
) -> Tuple[List[bpy.types.MeshVertex], Dict[int, int]]:
    """
    Take the vertices of the mesh and make an array of Black & White 2
    vertices out of them.
    """
    poly_vertices = list(
        {vertex for polygon in polygons for vertex in polygon.vertices}
    )
    num_vertex = len(poly_vertices)

    ret_vertices = [Vertex(Stride()) for _ in range(num_vertex)]
    d_index = {}
    vertex = 0
    for face in polygons:
        for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
            if vert_idx in d_index:
                continue

            c_vertex = vertices[vert_idx]
            r_vertex = ret_vertices[vertex]
            r_vertex.position = tuple(xyz_to_zxy(c_vertex.co))
            r_vertex.normal = tuple(xyz_to_zxy(c_vertex.normal))
            ret_vertices[vertex] = r_vertex
            d_index[vert_idx] = vertex

            for uv_layer in uv_layers:
                if UVType(0).name in uv_layer.name:
                    uv_idx = 0
                elif UVType(1).name in uv_layer.name:
                    uv_idx = 1
                elif UVType(2).name in uv_layer.name:
                    uv_idx = 2
                else:
                    continue

                uv_coord = correct_uv(uv_layer.data[loop_idx].uv)
                r_vertex.uvs.insert(uv_idx, uv_coord)

            vertex += 1

    return ret_vertices, d_index


def organise_index_data(
    faces_seq: List[bpy.types.MeshPolygon],
    vertex_offset: int,
    d_indexes: Dict[int, int],
    m_type: int,
) -> List[int]:
    """
    Take the mesh faces and make an array of indexes from them
    """

    if m_type == FileType.SKIN:
        faces = [
            list(faces_seq[i].vertices)
            if i % 2 == 0
            else [
                faces_seq[i].vertices[1],
                faces_seq[i].vertices[0],
                faces_seq[i].vertices[2],
            ]
            for i in range(len(faces_seq))
        ]
        indexes = faces[0][0:2]
        indexes.extend([face[2] for face in faces[:-1]])
        indexes.extend(faces[-1])

    elif m_type == FileType.MODEL:
        faces = [[index for index in face.vertices] for face in faces_seq]
        indexes = [index for i in range(len(faces)) for index in faces[i]]

    indexes = [d_indexes[i] + vertex_offset for i in indexes]
    return indexes


def create_bounds(
    mesh_desc: MeshDescription, vertices: List[bpy.types.MeshVertex]
) -> None:
    """
    Compute the bounding box, sphere and the height of the mesh
    """
    num_vertex = len(vertices)
    mesh_desc.vertexSize = num_vertex
    loc_list = [tuple(xyz_to_zxy(vertex.co)) for vertex in vertices]
    x = [loc[0] for loc in loc_list]
    y = [loc[1] for loc in loc_list]
    z = [loc[2] for loc in loc_list]
    mesh_desc.cent = (mean(x), mean(y), mean(z))
    mesh_desc.box1 = (min(x), min(y), min(z))
    mesh_desc.box2 = (max(x), max(y), max(z))
    mesh_desc.radius = max([math.dist(loc, mesh_desc.cent) for loc in loc_list])
    mesh_desc.unknowns1 = mesh_desc.box2
    mesh_desc.height = mesh_desc.box2[1]
