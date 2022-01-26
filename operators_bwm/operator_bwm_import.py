from os import path
from typing import List, Tuple
import bpy
from operators_bwm.file_definition_bwm import BWMFile

def correct_axis (vector: Tuple[int, int, int]) -> Tuple[int, int, int]:
    return (vector[2], vector[0], vector[1])


def tuple_sum (tuple1: Tuple, tuple2 : Tuple) -> Tuple:
    ret = [sum(x) for x in zip(tuple1, tuple2)]
    return tuple(ret)


def correct_uv (vector: Tuple[float, float]) -> Tuple[float, float]:
    return (vector[0], 1 - vector[1])


def import_materials(bwm_data : BWMFile, texture_path: str, uvs_count : int) -> Tuple[List[bpy.types.Material], List[List[bpy.types.NodeInputs]]]:
    materials = ([], [])

    for material in bwm_data.materialDefinitions:
        images = [
            material.diffuseMap,
            material.specularMap,
            material.lightMap,
            material.normalMap,
            material.growthMap,
            material.animatedTexture,
        ]
        type = material.type

        material = bpy.data.materials.new(name=type)
        material.use_nodes = True
        materials[0].append(material)
        
        material_nodes = material.node_tree.nodes
        material_link = material.node_tree.links
        uv_maps = [material_nodes.new("ShaderNodeUVMap") for i in range(uvs_count)]
        materials[1].append(uv_maps)

        BSDF = material_nodes["Principled BSDF"]
        base_color_node = material_nodes.new("ShaderNodeMixRGB")
        base_color_node.blend_type = "MULTIPLY"
        material_link.new(BSDF.inputs[0], base_color_node.outputs[0])

        l_inputs = [
            [ ("base_color_node", 1), ("base_color_node", 0), ("BSDF", 19), ("texture", 0) ],
            [ ("BSDF", 5), ("BSDF", 6), ("texture", 0)],
            [ ("base_color_node", 2), ("base_color_node", 0), ("texture", 0)],
            #[ (BSDF, 20), (BSDF, 0), (None, 0)],
        ]
        l_outputs = [
            [ ("texture", 0), ("texture", 1), ("texture", 1), ("uv_maps[0]", 0) ],
            [ ("texture", 0), ("texture", 1), ("uv_maps[0]", 0) ],
            [ ("texture", 0), ("texture", 1), ("uv_maps[1]", 0) ],
            #[ (None, 0), (None, 1), (None, 1), (uv_maps[0], 0) ],
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
                    image = bpy.data.images.load(filepath=path.join(texture_path, file), check_existing=True)
                    texture = material_nodes.new('ShaderNodeTexImage')
                    texture.image = image
                    node_dict["texture"] = texture
                    for (input, output) in zip(inputs, outputs):
                        n_input = node_dict[input[0]]
                        n_output = node_dict[output[0]]
                        material_link.new(n_input.inputs[input[1]], n_output.outputs[output[1]])
            except:
                pass

    return materials


def read_bwm_data(context, filepath, use_bwm_setting):
    print("Reading data from Black & White Model file")
    with open(filepath, 'rb') as file:
        bwm = BWMFile(file)
        uvs_count = len(bwm.vertices[0].uvs)
        vertices = [correct_axis(vertex.position) for vertex in bwm.vertices]
        # normals = [correct_axis(vertex.normal) for vertex in bwm.vertices]
        mesh_uvs = [ 
            [vertex.uvs[i] for vertex in bwm.vertices]
            for i in range(uvs_count) 
            ]
        
        uvs_names = [
            "_uv_texture",
            "_uv_ligthmap", 
            "_uv_unknown"
            ]

        type = bwm.modelHeader.type
        bwm_name = path.basename(filepath[:-4])        

        col = bpy.data.collections.new(bwm_name)

        if type == 2:
            step = 3
        elif type == 3:
            step = 1
        else:
            raise ValueError("Not a supported type")

        materials = import_materials(bwm, path.join(path.dirname(filepath), "..\\textures"), uvs_count)

        n_mesh = 0
        for mesh_description in bwm.meshDescriptions:
            mesh = bpy.data.meshes.new(str(mesh_description.id))
            mesh_name = mesh_description.name.replace('\0', '')
            obj = bpy.data.objects.new(
                mesh_name, mesh
            )

            # Set up mesh geometry
            indicies_offset = mesh_description.indiciesOffset
            if type > 2 and n_mesh > 0:
                indicies_offset += 2
            indicies_size = mesh_description.indiciesSize
            vertex_offset = mesh_description.vertexOffset
            vertex_size = mesh_description.vertexSize
            mesh_indexes = bwm.indexes[indicies_offset:indicies_size + indicies_offset]
            mesh_vertices = vertices[vertex_offset:vertex_size + vertex_offset]
            mesh_faces = []
            if type == 2:
                mesh_faces = [
                    [index - vertex_offset for index in mesh_indexes[(i*3):(i*3)+3]]
                    for i in range(mesh_description.facesCount)
                    ]
            if type == 3:
                mesh_faces = [
                    [index - vertex_offset for index in mesh_indexes[i:i+3]] if (i%2 == 0)
                    else [
                        mesh_indexes[i+1] - vertex_offset,
                        mesh_indexes[i] - vertex_offset,
                        mesh_indexes[i+2] - vertex_offset
                        ]
                    for i in range(mesh_description.facesCount)
                    ]

            mesh.from_pydata(mesh_vertices, [], mesh_faces)
            n_mesh += 1

            # Set up normals
            for index in range(vertex_offset, vertex_offset + vertex_size):
                mesh.vertices[index-vertex_offset].normal = correct_axis(bwm.vertices[index].normal)
            mesh.create_normals_split()

            # Set up uv maps
            uv_layers = []
            for i in range(uvs_count):
                uv_layer = mesh.uv_layers.new(name=bwm_name + uvs_names[i])
                for faces in obj.data.polygons:
                    for vert_index, loop_index in zip(faces.vertices, faces.loop_indices):
                        uv_layer.data[loop_index].uv = correct_uv(mesh_uvs[i][vert_index+vertex_offset])
                uv_layers.append(uv_layer)

            # Set up materials
            for material_reference in mesh_description.materialRefs:
                current_material = materials[0][material_reference.materialDefinition]
                obj.data.materials.append(current_material)
                
                # Apply the uv maps (should be done elsewhere)
                for i in range(len(uv_layers)):
                    uv_node = materials[1][material_reference.materialDefinition][i]
                    uv_node.uv_map = uv_layers[i].name
                face_number = min(
                    material_reference.facesSize,
                    mesh_description.facesCount - material_reference.facesOffset
                )

                #Apply the materials
                for face in range(face_number):
                    mesh.polygons[material_reference.facesOffset + face].material_index = len(obj.data.materials) - 1

            #mesh.validate()

            col.objects.link(obj)

    bpy.context.scene.collection.children.link(col)

    return {'FINISHED'}


# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty
from bpy.types import Operator


class ImportBWMData(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "import_test.bwm_data"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import .bwm file"

    # ImportHelper mixin class uses this
    filename_ext = ".bwm"

    filter_glob: StringProperty(
        default="*.bwm",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    use_setting: BoolProperty(
        name="Example Boolean",
        description="Example Tooltip",
        default=True,
    )

    '''type: EnumProperty(
        name="Example Enum",
        description="Choose between two items",
        items=(
            ('OPT_A', "First Option", "Description one"),
            ('OPT_B', "Second Option", "Description two"),
        ),
        default='OPT_A',
    )'''

    def execute(self, context):
        return read_bwm_data(context, self.filepath, self.use_setting)


# Only needed if you want to add into a dynamic menu
def menu_func_import(self, context):
    self.layout.operator(ImportBWMData.bl_idname, text="Black & White Model (.bwm)")


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
