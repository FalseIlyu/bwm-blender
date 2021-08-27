from os import path
from typing import List, Tuple
import bpy
from operators_bwm.file_definition_bwm import BWMFile

def correct_axis (vector: Tuple[int, int, int]) -> Tuple[int, int, int]:
    return (-vector[2], vector[0], vector[1])

def tuple_sum (tuple1: Tuple, tuple2 : Tuple) -> Tuple:
    ret = [sum(x) for x in zip(tuple1, tuple2)]
    return tuple(ret)

def import_materials(bwm_data : BWMFile, texturepath: str) -> List[bpy.types.Material]:
    mats = []

    for material in bwm_data.materialDefinitions:
        diffuseMap = material.diffuseMap.decode('utf-8').replace('\0','')
        lightMap = material.lightMap.decode('utf-8').replace('\0','')
        specularMap = material.specularMap.decode('utf-8').replace('\0','')
        type = material.type.decode('utf-8').replace('\0','')
        normalMap = material.normalMap.decode('utf-8').replace('\0','')
        unknown1 = material.unknown1.decode('utf-8').replace('\0','')
        unknown2 = material.unknown2.decode('utf-8').replace('\0','')

        mat = bpy.data.materials.new(name=type)
        mat.use_nodes = True
        mat_nodes = mat.node_tree.nodes
        BSDF = mat_nodes["Principled BSDF"]
        mat_link = mat.node_tree.links

        try:
            if diffuseMap != "":
                image = bpy.data.images.load(filepath=path.join(texturepath, diffuseMap), check_existing=True)
                tex = mat_nodes.new('ShaderNodeTexImage')
                tex.image = image
                mat_link.new(BSDF.inputs[0], tex.outputs[0])
        except:
            pass
        
        try:
            if specularMap != "":
                image = bpy.data.images.load(filepath=path.join(texturepath, specularMap), check_existing=True)
                tex = mat_nodes.new('ShaderNodeTexImage')
                tex.image = image
                mat_link.new(BSDF.inputs[5], tex.outputs[0])
        except:
            pass

        try:
            if lightMap != "":
                image = bpy.data.images.load(filepath=path.join(texturepath, lightMap), check_existing=True)
                tex = mat_nodes.new('ShaderNodeTexImage')
                tex.image = image
                mat_link.new(BSDF.inputs[17], tex.outputs[0])
        except:
            pass

        try:
            if normalMap != "":
                image = bpy.data.images.load(filepath=path.join(normalMap, lightMap), check_existing=True)
                norm = mat_nodes.new('ShaderNodeNormalMap')
                tex = mat_nodes.new('ShaderNodeTexImage')
                tex.image = image
                mat_link.new(BSDF.inputs["Normal Map"], norm.outputs[0])
                mat_link.new(norm.inputs[1], tex.outputs[0])
        except:
            pass
        
        """if type:
            image = bpy.ops.image.open(path.join(texturepath, type))
            node = bpy.ops.node.add_and_link_node("Image Texture")
            node.image = image
        if unknown2:
            image = bpy.ops.image.open(path.join(texturepath, unknown2))
            node = bpy.ops.node.add_and_link_node("Image Texture")
            node.image = image
        if unknown1:
            image = bpy.ops.image.open(path.join(texturepath, unknown1))
            node = bpy.ops.node.add_and_link_node("Image Texture")
            node.image = image"""

        mats.append(mat)

    return mats


def read_bwm_data(context, filepath, use_bwm_setting):
    print("Reading data from Black & White Model file")
    with open(filepath, 'rb') as file:
        bwm = BWMFile(file)
        vertices = [correct_axis(vertex.position) for vertex in bwm.vertices]
        normals = [correct_axis(vertex.normal) for vertex in bwm.vertices]
        uv = [(vertex.uvs[0][0], 1 - vertex.uvs[0][1]) for vertex in bwm.vertices]
        type = bwm.modelHeader.type
        name = path.basename(filepath[:-4])        

        col = bpy.data.collections.new(name)
        

        materials = import_materials(bwm, path.join(path.dirname(filepath), "..\\textures"))
        if type == 2:
            step = 3
        elif type == 3:
            step = 1
        else:
            raise ValueError("Not a supported type")

        for meshDesc in bwm.meshDescriptions:
            mesh = bpy.data.meshes.new(str(meshDesc.id))
            obj = bpy.data.objects.new(
                meshDesc.name.decode('utf-8'), mesh
            )
            faces = []

            for matRef in meshDesc.materialRefs:
                cMat = materials[matRef.materialDefinition]
                mesh.materials.append(cMat)
                BSDF = cMat.node_tree.nodes["Principled BSDF"]
                BSDF.inputs[18].default_value = matRef.unknown
                
                off = matRef.indiciesOffset
                faces.extend( [
                    (
                        bwm.indexes[ off + (face * step) + 0 ],
                        bwm.indexes[ off + (face * step) + 1 ],
                        bwm.indexes[ off + (face * step) + 2 ]
                    )
                    for face in range (matRef.facesSize) 
                ] )
                mindexes = [ item for subset in faces for item in subset ]
                
            col.objects.link(obj)

            mesh.from_pydata(vertices, [], faces)
            new_uv = mesh.uv_layers.new(name='UV')
            i = 0
            for loop in mindexes:
                new_uv.data[i].uv = uv[loop]
                i += 1

        """mesh = bpy.data.meshes.new("Unknown1")
        obj = bpy.data.objects.new("Unknown1", mesh)
        vert = [ (
            -vec.unknown[1],
            vec.unknown[0],
            vec.unknown[2],
         ) for vec in bwm.unknowns1]
        mesh.from_pydata(vert, [], [])
        col.objects.link(obj)

        mesh = bpy.data.meshes.new("Unknown2")
        obj = bpy.data.objects.new("Unknown2", mesh)
        vert = [correct_axis(vec.unknown) for vec in bwm.unknowns2]
        mesh.from_pydata(vert, [], [])

        col.objects.link(obj)"""
        """vert3 = []
        for bone in bwm.bones:
            mesh = bpy.data.meshes.new("Bones")
            obj = bpy.data.objects.new("Bones", mesh)
            vert = [
                correct_axis(tuple_sum(bone.unknownv0, bone.position)),
                correct_axis(tuple_sum(bone.unknownv1, bone.position)),
                correct_axis(tuple_sum(bone.unknownv2, bone.position)),
                correct_axis(bone.position)
            ]
            mesh.from_pydata(vert, [], [])
            col.objects.link(obj)"""

    bpy.context.scene.collection.children.link(col)

    return {'FINISHED'}


# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Material, Operator


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
