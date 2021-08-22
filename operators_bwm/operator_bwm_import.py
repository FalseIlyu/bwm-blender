from typing import Set
import bpy
import bmesh
from operators_bwm.file_definition_bwm import BWMFile

def read_bwm_data(context, filepath, use_bwm_setting):
    print("Reading data from Black & White Model file")
    with open(filepath, 'rb') as file:
        bwm = BWMFile(file)
        vertices = [vertex.position for vertex in bwm.vertices]
        type = bwm.modelHeader.unknown3
        
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
                off = matRef.indiciesOffset
                faces.extend( [
                    [
                        bwm.indexes[ off + (face * step) + 0 ],
                        bwm.indexes[ off + (face * step) + 1 ],
                        bwm.indexes[ off + (face * step) + 2 ]
                    ]
                    for face in range (
                        matRef.facesOffset, matRef.facesSize
                    ) 
                ] )
                #mvert = set([vertices[item] for sublist in faces for item in sublist])

            col = bpy.data.collections.get("Collection")
            col.objects.link(obj)

            mesh.from_pydata(vertices, [], faces)




    return {'FINISHED'}


# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator


class ImportBWMData(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "import_test.bwm_data"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import data from a .bwm file"

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
