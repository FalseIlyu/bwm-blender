# <pep8-80 compliant>
from bpy.types import Operator
from bpy.props import (
    IntProperty,
    EnumProperty,
    BoolProperty,
    StringProperty,
    CollectionProperty
)
from bpy_extras.io_utils import ExportHelper
from typing import List, Tuple
from bpy.types import Panel, UIList
import bpy

import numpy as np

from operators_bwm.file_definition_bwm import BWMFile, MaterialDefinition


def correct_axis(
    vector: Tuple[float, float, float]
) -> Tuple[float, float, float]:
    axis_correction = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]])
    position = np.array(vector)
    position = axis_correction.dot(position)
    return tuple(position)


def correct_rotation(rotation: List[List[float]]) -> np.ndarray:
    axis_correction = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]])
    rotation = np.array(rotation)
    return axis_correction.dot(rotation)


def export_material() -> List[MaterialDefinition]:
    material_definitions = []
    for material in bpy.data.materials:
        export = MaterialDefinition()
        material_definitions.append(export)
        continue

    return material_definitions


def organize_bwm_data() -> BWMFile:
    file = BWMFile()

    file.materialDefinitions = export_material()
    file.modelHeader.materialDefinitionCount = len(file.materialDefinitions)

    return file


def write_bwm_data(context, filepath, use_bwm_setting):
    print("running write_bwm_data...")

    with open(filepath, 'w', encoding='utf-8') as f:
        file = organize_bwm_data()
        file.write()
        f.close()

    return {'FINISHED'}


# ExportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.


class ExportBWMData(Operator, ExportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "export_test.bwm_data"  # important since its how
    # bpy.ops.import_test.some_data is constructed
    bl_label = "Export .bwm Data"

    # ExportHelper mixin class uses this
    filename_ext = ".bwm"

    filter_glob: StringProperty(
        default="*.bwm",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    # Choose
    version: EnumProperty(
        name="Version",
        description="Version of the .bwm file",
        items=(
            ('OPT_FIVE', "Version 5.0", "Version 5.0"),
            ('OPT_SIX', "Version 6.0", "Version 6.0"),
        ),
        default='OPT_FIVE',
    )

    type: EnumProperty(
        name="Type",
        description="Type of model to export",
        items=(
            ('OPT_MODEL', "Model", "Model"),
            ('OPT_SKIN', "Skin", "Skin"),
        ),
        default='OPT_MODEL',
    )

    empty_texture: BoolProperty(
        name="Generate empty texture",
        description="Boolean to tell to generate an empty texture",
        default=False,
    )

    mesh_list: CollectionProperty(
        type=bpy.types.Mesh,
        name="Mesh List",
        description="List of the mesh inside the file",
    )

    mesh_list_active: IntProperty(
        name="active_mesh",
        description="Active item in the mesh list",
        default=0,
        min=0,
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

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'version', expand=True)
        layout.prop(self, 'type', expand=True)
        layout.prop(self, 'empty_texture')


class MESH_UIList(UIList):
    def draw_item(
        self,
        context: 'Context',
        layout: 'UILayout',
        data: 'AnyType',
        item: 'AnyType',
        icon: int,
        active_data: 'AnyType',
        active_property: str,
        index: int = 0,
        flt_flag: int = 0
    ):

        # We could write some code to decide which icon to use here...
        custom_icon = 'OBJECT_DATAMODE'

        # Make sure your code supports all 3 layout types
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=item.name, icon=custom_icon)

        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon=custom_icon)


class MESH_COLLECTION_panel(Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Meshses"

    @classmethod
    def poll(cls, context):
        operator = context.space_data.active_operator
        return operator.bl_idname == 'EXPORT_TEST_OT_bwm_data'

    def draw(self, context):
        operator = context.space_data.active_operator

        # column = self.layout.column(align=False)
        row = self.layout.row()
        row.template_list(
            "MESH_UIList", "MESH_UIList",
            operator, "mesh_list",
            operator, "mesh_list_active"
        )

        # layout.prop(operator, 'mesh_list')

# Only needed if you want to add into a dynamic menu


def menu_func_export(self, context):
    self.layout.operator(ExportBWMData.bl_idname,
                         text="Black & White Model (.bwm)")


def register():
    bpy.utils.register_class(ExportBWMData)
    bpy.utils.register_class(MESH_UIList)
    bpy.utils.register_class(MESH_COLLECTION_panel)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(ExportBWMData)
    bpy.utils.unregister_class(MESH_UIList)
    bpy.utils.unregister_class(MESH_COLLECTION_panel)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.export_test.bwm_data('INVOKE_DEFAULT')
