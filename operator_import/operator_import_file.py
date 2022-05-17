# <pep8-80 compliant>
from os import path
import bpy

from ..operator_utilities.file_definition_bwm import (
    BWMFile,
    FileType,
)
from .operator_import_material import bpy_material_from_definition
from .operator_import_mesh import bpy_obj_from_defintion
from ..operator_utilities.vector_utils import (
    zxy_to_xyz,
    construct_transformation_matrix
)


def read_bwm_data(context, filepath: str):
    print("Reading data from Black & White Model file")
    with open(filepath, 'rb') as file:
        bwm = BWMFile(file)
        uvs_count = len(bwm.vertices[0].uvs)

        type = bwm.modelHeader.type
        bwm_name = path.basename(filepath[:-4])

        col = bpy.data.collections.new(bwm_name)

        if not (type == FileType.SKIN or type == FileType.MODEL):
            raise ValueError("Not a supported type")

        list_materials, list_uv_nodes = zip(*[
            bpy_material_from_definition(
                material_definition,
                path.join(path.dirname(filepath), "..\\textures"),
                uvs_count
            ) for material_definition in bwm.materialDefinitions
        ])

        mesh_col = bpy.data.collections.new("mesh")
        col.children.link(mesh_col)
        lods = [[] for i in range(4)]

        for mesh_description in bwm.meshDescriptions:
            obj = bpy_obj_from_defintion(
                mesh_description,
                bwm,
                list_materials,
                list_uv_nodes,
                bwm_name
            )

            # mesh.validate()
            lods[mesh_description.lod_level - 1].append(obj)

        for lod_level, meshses in enumerate(lods):
            if meshses:
                n_col = bpy.data.collections.new(f"lod{lod_level + 1}")
                for mesh in meshses:
                    n_col.objects.link(mesh)
                mesh_col.children.link(n_col)

        if bwm.bones:
            n_col = bpy.data.collections.new("bones")
            draw_size = bwm.modelHeader.height / 20
            for i_bone, bone in enumerate(bwm.bones):
                empty = bpy.data.objects.new(str(i_bone), None)
                empty.matrix_world = construct_transformation_matrix(
                    bone, zxy_to_xyz)

                empty.empty_display_size = draw_size
                empty.empty_display_type = "ARROWS"

                n_col.objects.link(empty)

            col.children.link(n_col)

        if bwm.entities:
            n_col = bpy.data.collections.new("entities")
            draw_size = bwm.modelHeader.height / 20
            for entity in bwm.entities:
                empty = bpy.data.objects.new(entity.name, None)
                empty.matrix_world = construct_transformation_matrix(
                    entity, zxy_to_xyz)

                empty. empty_display_size = draw_size
                empty.empty_display_type = "ARROWS"

                n_col.objects.link(empty)

            col.children.link(n_col)

        unknowns = [
            zxy_to_xyz(unknown.unknown) for unknown in bwm.unknowns1
            ]
        if unknowns:
            mesh = bpy.data.meshes.new("Unknowns")
            obj = bpy.data.objects.new(
                mesh.name, mesh
            )
            mesh.from_pydata(unknowns, [], [])
            n_col = bpy.data.collections.new("unknowns")
            n_col.objects.link(obj)
            col.children.link(n_col)

        collision = [
            zxy_to_xyz(collisionPoint.position)
            for collisionPoint in bwm.collisionPoints
        ]
        if collision:
            mesh = bpy.data.meshes.new("Collision")
            obj = bpy.data.objects.new(
                mesh.name, mesh
            )
            mesh.from_pydata(collision, [], [])
            n_col = bpy.data.collections.new("collision")
            n_col.objects.link(obj)
            col.children.link(n_col)

        bpy.context.scene.collection.children.link(col)

    return {'FINISHED'}
