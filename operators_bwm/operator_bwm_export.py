from typing import List, Tuple
import bpy
import numpy as np

from operators_bwm.file_definition_bwm import BWMFile

def correct_axis (vector: Tuple[float, float, float]) -> Tuple[float, float, float]:
    axis_correction = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]])
    position = np.array(vector)
    position = axis_correction.dot(position)
    return tuple(position)

def correct_rotation (rotation: List[List[float]]) -> np.ndarray:
    axis_correction = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]])
    rotation = np.array(rotation)
    return axis_correction.dot(rotation)

def organize_bwm_data() -> BWMFile:
    file = BWMFile()
    return file

def write_bwm_data(context, filepath, use_bwm_setting):
    print("running write_bwm_data...")

    with open(filepath, 'w', encoding='utf-8') as f:

        f.close()

    return {'FINISHED'}


# ExportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator


class ExportBWMData(Operator, ExportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "export_test.bwm_data"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Export BWM Data"

    # ExportHelper mixin class uses this
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
        return write_bwm_data(context, self.filepath, self.use_setting)


# Only needed if you want to add into a dynamic menu
def menu_func_export(self, context):
    self.layout.operator(ExportBWMData.bl_idname, text="Text Export Operator")


def register():
    bpy.utils.register_class(ExportBWMData)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(ExportBWMData)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.export_test.bwm_data('INVOKE_DEFAULT')
