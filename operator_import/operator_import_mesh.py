"""
Module charged with creating the meshses from their description and apply to
them the materials defined in the material references
"""
# coding=utf-8
from typing import List, Tuple
import bpy

from ..operator_utilities.file_definition_bwm import (
    FileType,
    UVType,
    MaterialRef,
    MeshDescription,
    BWMFile,
)
from ..operator_utilities.vector_utils import correct_uv, zxy_to_xyz

# Section
def bpy_obj_from_defintion(
    mesh_description: MeshDescription,
    bwm: BWMFile,
    list_materials: List[bpy.types.Material],
    list_uv_nodes: List[bpy.types.NodeInputs],
    bwm_name: str,
):
    """
    From the data in the BWM and a mesh description call all necessary step
    to make a mesh
    """
    obj, mesh = bpy_mesh_from_definition(mesh_description, bwm)

    uv_layers = setup_mesh_uvlayers(
        mesh, mesh_description.vertexOffset, bwm_name, bwm
    )

    apply_material_to_mesh(
        obj,
        mesh,
        uv_layers,
        mesh_description.materialRefs,
        list_materials,
        list_uv_nodes,
    )

    return obj


def setup_mesh_uvlayers(
    mesh: bpy.types.Mesh,
    vertex_offset: int,
    bwm_name: str,
    bwm: BWMFile,
) -> List[bpy.types.MeshUVLoopLayer]:
    """
    Set up the uv of the differents polygons of the mesh.
    """
    uvs_count = len(bwm.vertices[0].uvs)
    mesh_uvs = [
        [correct_uv(vertex.uvs[i]) for vertex in bwm.vertices]
        for i in range(uvs_count)
    ]

    if len(mesh.uv_layers) < uvs_count:
        for i in range(uvs_count):
            mesh.uv_layers.new(name=f"{bwm_name}_{UVType(i).name}")

    for i, uv_layer in enumerate(mesh.uv_layers):
        for loop in mesh.loops.values():
            vertex_index = loop.vertex_index + vertex_offset
            loop_index = loop.index
            uv_layer.data[loop_index].uv = mesh_uvs[i][vertex_index]

    return mesh.uv_layers


def apply_material_to_mesh(
    obj: bpy.types.Object,
    mesh: bpy.types.Mesh,
    uv_layers: List[bpy.types.MeshUVLoopLayer],
    material_references: List[MaterialRef],
    list_materials: List[bpy.types.Material],
    list_uv_nodes: List[bpy.types.NodeInputs],
) -> None:
    """
    Apply the Materials to the mesh
    """
    # Set up materials
    face_offset = 0
    for material_reference in material_references:
        material_definiton = material_reference.materialDefinition
        current_material = list_materials[material_definiton]
        obj.data.materials.append(current_material)

        face_offset = material_reference.facesOffset
        # Apply the uv maps
        for i, uv_layer in enumerate(uv_layers):
            uv_node = list_uv_nodes[material_definiton][i]
            uv_node.uv_map = uv_layer.name

        # Apply the materials
        for polygon in mesh.polygons[face_offset:face_offset + material_reference.facesSize]:
            polygon.material_index = len(obj.data.materials) - 1
        
        face_offset += material_reference.facesSize


def bpy_mesh_from_definition(
    mesh_description: MeshDescription,
    bwm: BWMFile,
) -> Tuple[bpy.types.Object, bpy.types.Material]:
    """
    Extract the geometry of the mesh from the description and build the mesh
    """
    file_type = bwm.modelHeader.type

    # Reading mesh information from the mesh description
    mesh_name = mesh_description.name.replace("\0", "")
    indicies_offset = mesh_description.indiciesOffset
    indicies_size = mesh_description.indiciesSize
    vertex_offset = mesh_description.vertexOffset
    vertex_size = mesh_description.vertexSize

    def create_face(indexes):
        return [index - vertex_offset for index in indexes]

    # Skins work differently from models
    if file_type == FileType.SKIN and indicies_offset > 0:
        indicies_offset += 2

    # Set up mesh geometry
    mesh_indexes = bwm.indexes[
        indicies_offset : indicies_size + indicies_offset
    ]
    mesh_vertices = bwm.vertices[vertex_offset : vertex_size + vertex_offset]
    vertices_positions = [
        zxy_to_xyz(vertex.position) for vertex in mesh_vertices
    ]
    mesh_normals = [zxy_to_xyz(vertex.normal) for vertex in mesh_vertices]

    if file_type == FileType.MODEL:
        mesh_faces = [
            create_face(mesh_indexes[i : i + 3])
            for i in range(0 , mesh_description.indiciesSize, 3)
        ]
    if file_type == FileType.SKIN:
        mesh_faces = [
            create_face(mesh_indexes[i : i + 3])
            if (i % 2 == 0)
            else create_face(
                [mesh_indexes[i + 1], mesh_indexes[i], mesh_indexes[i + 2]]
            )
            for i in range(0 , mesh_description.indiciesSize, 3)
        ]

    mesh = bpy.data.meshes.new(mesh_name)
    mesh.validate(verbose=True)
    obj = bpy.data.objects.new(mesh_name, mesh)
    mesh.from_pydata(vertices_positions, [], mesh_faces)

    # Set up normals
    # for index, vertex in enumerate(mesh.vertices):
    #     vertex.normal = mesh_normals[index]
    mesh.normals_split_custom_set_from_vertices(mesh_normals)

    return obj, mesh
