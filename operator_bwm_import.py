# <pep8-80 compliant>
import logging
from bpy.types import Operator
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper
from os import path
from typing import List, Tuple, Union
import numpy as np
import bpy

from .file_definition_bwm import (
    Bone,
    Entity,
    BWMFile,
    MeshDescription,
    MaterialDefinition,
)


def correct_axis(
        vector: Tuple[float, float, float]
) -> Tuple[float, float, float]:
    axis_correction = np.array(
        [
            [0.0, 0.0, 1.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0]
        ]
    )
    position = np.array(vector)
    position = axis_correction.dot(position)
    return tuple(position)


def correct_rotation(rotation: List[List[float]]) -> np.ndarray:
    axis_correction = np.array(
        [
            [0.0, 0.0, 1.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0]
        ]
    )
    rotation = np.array(rotation)
    return axis_correction.dot(rotation)


def correct_uv(vector: Tuple[float, float]) -> Tuple[float, float]:
    return (vector[0], 1.0 - vector[1])


def import_material(
    material_definition: MaterialDefinition, texture_path: str, uvs_count: int
) -> Tuple[bpy.types.Material, List[bpy.types.NodeInputs]]:
    logger = logging.getLogger(__name__)

    images = [
        material_definition.diffuseMap,
        material_definition.specularMap,
        material_definition.lightMap,
        material_definition.normalMap,
        material_definition.growthMap,
        material_definition.animatedTexture,
    ]
    type = material_definition.type

    material = bpy.data.materials.new(name=type)
    material.use_nodes = True
    if type == '_plants_' or type == '_yard_' or type == '_vines_':
        material.blend_method = 'BLEND'
    else:
        material.blend_method = 'HASHED'
    material.alpha_threshold = 1.0

    material_nodes = material.node_tree.nodes
    material_link = material.node_tree.links
    uv_maps = [material_nodes.new("ShaderNodeUVMap") for i in range(uvs_count)]

    BSDF = material_nodes["Principled BSDF"]
    base_color_node = material_nodes.new("ShaderNodeMixRGB")
    base_color_node.blend_type = "MULTIPLY"
    base_color_node.inputs[1].default_value = (1.0, 1.0, 1.0, 1.0)
    base_color_node.inputs[2].default_value = (1.0, 1.0, 1.0, 1.0)
    material_link.new(BSDF.inputs[0], base_color_node.outputs[0])

    l_inputs = [
        [
            ("base_color_node", 1), ("base_color_node", 0),
            ("BSDF", 19), ("texture", 0)
        ],
        [("BSDF", 5), ("BSDF", 6), ("texture", 0)],
        [("base_color_node", 2), ("base_color_node", 0), ("texture", 0)],
        [("BSDF", 20), ("texture", 0)],
        [("texture", 0)],
        [("texture", 0)]
    ]
    l_outputs = [
        [
            ("texture", 0),
            ("texture", 1),
            ("texture", 1),
            ("uv_maps[0]", 0)
        ],
        [("texture", 0), ("texture", 1), ("uv_maps[0]", 0)],
        [("texture", 0), ("texture", 1), ("uv_maps[1]", 0)],
        [("texture", 0), ("uv_maps[0]", 0)],
        [("uv_maps[0]", 0)],
        [("uv_maps[0]", 0)]
    ]
    node_dict = {
        "base_color_node": base_color_node,
        "BSDF": BSDF,
        "texture": None
    }
    for i in range(uvs_count):
        node_dict["uv_maps[{}]".format(i)] = uv_maps[i]

    for (file, inputs, outputs) in zip(images, l_inputs, l_outputs):
        try:
            if file != "":
                image = bpy.data.images.load(filepath=path.join(
                    texture_path, file), check_existing=True)
                texture = material_nodes.new('ShaderNodeTexImage')
                texture.image = image
                node_dict["texture"] = texture
                for (input, output) in zip(inputs, outputs):
                    n_input = node_dict[input[0]]
                    n_output = node_dict[output[0]]
                    material_link.new(
                        n_input.inputs[input[1]],
                        n_output.outputs[output[1]]
                    )
        except Exception:
            logger.error(
                "Error while importing " + file,
                exc_info=True
            )

    return (material, uv_maps)


def build_transformation_matrix(
    bwm_entity: Union[Bone, Entity, MeshDescription]
):
    rotation = correct_rotation(
        [
            bwm_entity.axis1,
            bwm_entity.axis2,
            bwm_entity.axis3
        ]
    )
    x = [rotation[i][0] if i < 3 else 0.0 for i in range(4)]
    y = [rotation[i][1] if i < 3 else 0.0 for i in range(4)]
    z = [rotation[i][2] if i < 3 else 0.0 for i in range(4)]
    point = correct_axis(bwm_entity.position)
    point = [point[i] if i < 3 else 1.0 for i in range(4)]
    return [x, y, z, point]


def mesh_material_setup(
    mesh_description: MeshDescription,
    list_materials: List[bpy.types.Material],
    mesh_uvs: List[Tuple[float, float]],
    list_uv_nodes: List[bpy.types.NodeInputs],
    bwm_name: str,
    obj: bpy.types.Object,
    mesh: bpy.types.Mesh,
    uvs_count: int
) -> None:
    # Set up uv maps
    uvs_names = [
        "_uv_texture",
        "_uv_ligthmap",
        "_uv_unknown"
    ]

    uv_layers = []
    for i in range(uvs_count):
        uv_layer = mesh.uv_layers.new(name=bwm_name + uvs_names[i])
        for faces in obj.data.polygons:
            for vert_index, loop_index in zip(
                    faces.vertices, faces.loop_indices
            ):
                uv_layer.data[loop_index].uv = mesh_uvs[i][vert_index]
        uv_layers.append(uv_layer)

    # Set up materials
    for material_reference in mesh_description.materialRefs:
        material_definiton = material_reference.materialDefinition
        current_material = list_materials[material_definiton]
        obj.data.materials.append(current_material)

        face_offset = material_reference.facesOffset
        # Apply the uv maps
        for i in range(len(uv_layers)):
            uv_node = list_uv_nodes[material_definiton][i]
            uv_node.uv_map = uv_layers[i].name
        face_number = min(
            material_reference.facesSize,
            mesh_description.facesCount - face_offset
        )

        # Apply the materials
        for face in range(face_number):
            polygon = mesh.polygons[face_offset + face]
            polygon.material_index = len(obj.data.materials) - 1

    return


def read_bwm_data(context, filepath: str):
    print("Reading data from Black & White Model file")
    with open(filepath, 'rb') as file:
        bwm = BWMFile(file)
        uvs_count = len(bwm.vertices[0].uvs)
        vertices = [correct_axis(vertex.position) for vertex in bwm.vertices]
        normals = [correct_axis(vertex.normal) for vertex in bwm.vertices]
        meshes_uvs = [
            [correct_uv(vertex.uvs[i]) for vertex in bwm.vertices]
            for i in range(uvs_count)
        ]

        type = bwm.modelHeader.type
        bwm_name = path.basename(filepath[:-4])

        col = bpy.data.collections.new(bwm_name)

        if not (type == 2 or type == 3):
            raise ValueError("Not a supported type")

        list_materials, list_uv_nodes = zip(*[
            import_material(
                material_definition,
                path.join(path.dirname(filepath), "..\\textures"),
                uvs_count
            ) for material_definition in bwm.materialDefinitions
        ])

        n_mesh = 0
        mesh_col = bpy.data.collections.new("mesh")
        col.children.link(mesh_col)
        lods = [bpy.data.collections.new("lod" + str(i + 1)) for i in range(4)]
        for n_col in lods:
            mesh_col.children.link(n_col)

        for mesh_description in bwm.meshDescriptions:
            # Reading mesh information from the mesh description
            mesh_name = mesh_description.name.replace('\0', '')
            indicies_offset = mesh_description.indiciesOffset
            indicies_size = mesh_description.indiciesSize
            vertex_offset = mesh_description.vertexOffset
            vertex_size = mesh_description.vertexSize
            # Skins work differently from models
            if type > 2 and n_mesh > 0:
                indicies_offset += 2

            # Set up mesh geometry
            mesh_indexes = bwm.indexes[
                indicies_offset:indicies_size + indicies_offset
            ]
            mesh_vertices = vertices[vertex_offset:vertex_size + vertex_offset]
            mesh_normals = normals[vertex_offset:vertex_size + vertex_offset]
            mesh_uvs = [
                uvs[vertex_offset:vertex_size + vertex_offset]
                for uvs in meshes_uvs
            ]
            if type == 2:
                mesh_faces = [
                    [index -
                        vertex_offset for index in mesh_indexes[(i*3):(i*3)+3]]
                    for i in range(mesh_description.facesCount)
                ]
            if type == 3:
                mesh_faces = [
                    [
                        index - vertex_offset for index in mesh_indexes[i:i+3]
                    ] if (i % 2 == 0)
                    else [
                        mesh_indexes[i+1] - vertex_offset,
                        mesh_indexes[i] - vertex_offset,
                        mesh_indexes[i+2] - vertex_offset
                    ]
                    for i in range(mesh_description.facesCount)
                ]

            mesh = bpy.data.meshes.new(mesh_name)
            obj = bpy.data.objects.new(mesh_name, mesh)
            mesh.transform(
                np.transpose(build_transformation_matrix(mesh_description))
            )
            mesh.from_pydata(mesh_vertices, [], mesh_faces)

            # Set up normals
            for index in range(vertex_size):
                mesh.vertices[index].normal = mesh_normals[index]
            mesh.create_normals_split()

            mesh_material_setup(
                mesh_description,
                list_materials,
                mesh_uvs,
                list_uv_nodes,
                bwm_name,
                obj,
                mesh,
                uvs_count
            )

            # mesh.validate()
            lods[mesh_description.lod_level - 1].objects.link(obj)
            n_mesh += 1

    if bwm.bones:
        n_col = bpy.data.collections.new("bones")
        bone_number = 0
        draw_size = bwm.modelHeader.height / 20
        for bone in bwm.bones:
            empty = bpy.data.objects.new(str(bone_number), None)
            empty.matrix_world = build_transformation_matrix(bone)

            empty.empty_display_size = draw_size
            empty.empty_display_type = "ARROWS"

            n_col.objects.link(empty)
            bone_number += 1

        col.children.link(n_col)

    if bwm.entities:
        n_col = bpy.data.collections.new("entities")
        draw_size = bwm.modelHeader.height / 20
        for entity in bwm.entities:
            empty = bpy.data.objects.new(entity.name, None)
            empty.matrix_world = build_transformation_matrix(entity)

            empty. empty_display_size = draw_size
            empty.empty_display_type = "ARROWS"

            n_col.objects.link(empty)

        col.children.link(n_col)

    unknowns = [correct_axis(unknown.unknown) for unknown in bwm.unknowns1]
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
        correct_axis(collisionPoint.position)
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


# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.


class ImportBWMData(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "import_test.bwm_data"
    # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import .bwm file"

    # ImportHelper mixin class uses this
    filename_ext = ".bwm"

    filter_glob: StringProperty(
        default="*.bwm",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        return read_bwm_data(context, self.filepath)


# Only needed if you want to add into a dynamic menu
def menu_func_import(self, context):
    self.layout.operator(ImportBWMData.bl_idname,
                         text="Black & White Model (.bwm)")


def register():
    bpy.utils.register_class(ImportBWMData)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportBWMData)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.import_test.bwm_data('INVOKE_DEFAULT')
