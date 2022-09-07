"""
Main module for the import plugin handle necessary code for its registration
in blender and the UI.
"""
# coding=utf-8
from bpy.types import Operator
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper
import bpy

from .operator_import_file import read_bwm_data

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
        options={"HIDDEN"},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        return read_bwm_data(context, self.filepath)


# Only needed if you want to add into a dynamic menu
def menu_func_import(self, context):
    self.layout.operator(
        ImportBWMData.bl_idname, text="Black & White Model (.bwm)"
    )


def register():
    bpy.utils.register_class(ImportBWMData)


def unregister():
    bpy.utils.unregister_class(ImportBWMData)
