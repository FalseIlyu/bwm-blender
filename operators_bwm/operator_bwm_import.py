from os import path
from typing import List, Tuple
import bpy
from operators_bwm.file_definition_bwm import BWMFile

def correct_axis (vector: Tuple[int, int, int]) -> Tuple[int, int, int]:
    return (-vector[2], vector[0], vector[1])


def tuple_sum (tuple1: Tuple, tuple2 : Tuple) -> Tuple:
    ret = [sum(x) for x in zip(tuple1, tuple2)]
    return tuple(ret)


def correct_uv (vector: Tuple[float, float]) -> Tuple[float, float]:
    return (vector[0], 1 - vector[1])


def import_materials(bwm_data : BWMFile, texture_path: str, uvs_count : int) -> Tuple[List[bpy.types.Material], List[List[bpy.types.NodeInputs]]]:
    materials = ([], [[] for i in range(uvs_count)])

    for material in bwm_data.materialDefinitions:
        diffuse_map = material.diffuseMap.replace('\0','')
        light_map = material.lightMap.replace('\0','')
        specular_map = material.specularMap.replace('\0','')
        type = material.type.replace('\0','')
        normal_map = material.normalMap.replace('\0','')
        # unknown1 = material.unknown1.replace('\0','')
        # unknown2 = material.unknown2.replace('\0','')

        material = bpy.data.materials.new(name=type)
        material.use_nodes = True
        materials[0].append(material)

        material_nodes = material.node_tree.nodes
        material_link = material.node_tree.links

        BSDF = material_nodes["Principled BSDF"]
        BSDF.inputs[5].default_value = 0
        BSDF.inputs[6].default_value = 0
        BSDF.inputs[7].default_value = 0
        BSDF.inputs[11].default_value = 0
        BSDF.inputs[13].default_value = 0
        BSDF.inputs[14].default_value = 0
        BSDF.inputs[18].default_value = 0

        base_color_node = material_nodes.new("ShaderNodeMixRGB")
        base_color_node.blend_type = "MULTIPLY"
        material_link.new(BSDF.inputs[0], base_color_node.outputs[0])

        try:
            if diffuse_map != "":
                image = bpy.data.images.load(filepath=path.join(texture_path, diffuse_map), check_existing=True)
                texture = material_nodes.new('ShaderNodeTexImage')
                texture.image = image
                material_link.new(base_color_node.inputs[1], texture.outputs[0])
                material_link.new(base_color_node.inputs[0], texture.outputs[1])
                material_link.new(BSDF.inputs[19], texture.outputs[1])
                materials[1][0].append(texture.inputs[0])
        except:
            pass
        
        try:
            if specular_map != "":
                image = bpy.data.images.load(filepath=path.join(texture_path, specular_map), check_existing=True)
                texture = material_nodes.new('ShaderNodeTexImage')
                texture.image = image
                material_link.new(BSDF.inputs[5], texture.outputs[0])
                material_link.new(BSDF.inputs[6], texture.outputs[1])
                materials[1][0].append(texture.inputs[0])
        except:
            pass

        try:
            if light_map != "":
                image = bpy.data.images.load(filepath=path.join(texture_path, light_map), check_existing=True)
                texture = material_nodes.new('ShaderNodeTexImage')
                texture.image = image
                material_link.new(base_color_node.inputs[2], texture.outputs[0])
                material_link.new(base_color_node.inputs[0], texture.outputs[1])
                if uvs_count > 1:
                    materials[1][1].append(texture.inputs[0])
                else:
                    materials[1][0].append(texture.inputs[0])
        except:
            pass

        try:
            if normal_map != "":
                image = bpy.data.images.load(filepath=path.join(normal_map, light_map), check_existing=True)
                normal = material_nodes.new('ShaderNodeNormalMap')
                texture = material_nodes.new('ShaderNodeTexImage')
                texture.image = image
                material_link.new(BSDF.inputs[20], normal.outputs[0])
                material_link.new(normal.inputs[1], texture.outputs[0])
        except:
            pass

        """if unknown2:
            image = bpy.ops.image.open(path.join(texturepath, unknown2))
            node = bpy.ops.node.add_and_link_node("Image Texture")
            node.image = image
        if unknown1:
            image = bpy.ops.image.open(path.join(texturepath, unknown1))
            node = bpy.ops.node.add_and_link_node("Image Texture")
            node.image = image"""

    return materials


def read_bwm_data(context, filepath, use_bwm_setting):
    print("Reading data from Black & White Model file")
    with open(filepath, 'rb') as file:
        bwm = BWMFile(file)
        vertices = [correct_axis(vertex.position) for vertex in bwm.vertices]
        # normals = [correct_axis(vertex.normal) for vertex in bwm.vertices]
        mesh_uvs = [ [
            (vertex.uvs[i][0], vertex.uvs[i][1]) 
            for i in range(len(vertex.uvs)) ]
            for vertex in bwm.vertices ]
        uvs_count = len(mesh_uvs[0])

        type = bwm.modelHeader.type
        name = path.basename(filepath[:-4])        

        col = bpy.data.collections.new(name)

        if type == 2:
            step = 3
        elif type == 3:
            step = 1
        else:
            raise ValueError("Not a supported type")

        materials = import_materials(bwm, path.join(path.dirname(filepath), "..\\textures"), len(mesh_uvs[0]))

        for mesh_description in bwm.meshDescriptions:
            mesh = bpy.data.meshes.new(str(mesh_description.id))
            obj = bpy.data.objects.new(
                mesh_description.name, mesh
            )

            indicies_offset = mesh_description.indiciesOffset
            vertex_offset = mesh_description.vertexOffset
            dict_vertices = {
                i : i - vertex_offset 
                for i in range(vertex_offset,
                mesh_description.vertexSize + vertex_offset)
            }
            mesh_indexes = bwm.indexes[indicies_offset:mesh_description.indiciesSize+indicies_offset]
            mesh_vertices = vertices[vertex_offset:mesh_description.vertexSize+vertex_offset]
            mesh_faces = [ (
                dict_vertices[mesh_indexes[(i * step) + 0]],
                dict_vertices[mesh_indexes[(i * step) + 1]],
                dict_vertices[mesh_indexes[(i * step) + 2]]
                ) for i in range(mesh_description.facesCount) ]
            

            mesh.from_pydata(mesh_vertices, [], mesh_faces)

            uv_layers = []
            texture_uv_layer = mesh.uv_layers.new(name=mesh.name + "_texture")
            uv_layers.append(texture_uv_layer)
            if uvs_count > 1:
                lightmap_uv_layer = mesh.uv_layers.new(name=mesh.name + "_lightmap")
                uv_layers.append(lightmap_uv_layer)
            for i in range(len(mesh_indexes)):
                texture_uv_layer.data[i].uv = correct_uv(mesh_uvs[mesh_indexes[i]][0])
                if uvs_count > 1:
                    lightmap_uv_layer.data[i].uv = correct_uv(mesh_uvs[mesh_indexes[i]][1])

            for material_reference in mesh_description.materialRefs:
                current_material = materials[0][material_reference.materialDefinition]
                obj.data.materials.append(current_material)
                material_nodes = current_material.node_tree.nodes
                material_links = current_material.node_tree.links

                for i in range(len(uv_layers)):
                    uv_node = material_nodes.new("ShaderNodeUVMap")
                    uv_node.uv_map = uv_layers[i].name
                    for j in materials[1][i]:
                        material_links.new(j, uv_node.outputs[0])

                face_number = min(
                    material_reference.facesSize,
                    mesh_description.facesCount - material_reference.facesOffset
                )
                for face in range(face_number):
                    mesh.polygons[material_reference.facesOffset + face].material_index = len(obj.data.materials) - 1

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
