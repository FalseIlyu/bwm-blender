# <pep8-80 compliant>
from bpy.types import Operator
from bpy.props import (
    EnumProperty,
    BoolProperty,
    StringProperty
)

from bpy_extras.io_utils import ExportHelper
from typing import Any, Dict
from bpy.types import Panel
import bpy

from .operator_export_file import organize_bwm_data


def write_bwm_data(
    context: bpy.types.Context,
    filepath: str,
    settings: Dict[str, Any]
):
    print("running write_bwm_data...")

    file = organize_bwm_data(settings, settings["selected_collection"])
    file.write(filepath)

    return {'FINISHED'}


# ExportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.

def validate(collection: bpy.types.Collection):
    inv_collection = []
    mesh = collection.children.get('mesh')
    lod = ["lod1", "lod2", "lod3", "lod4"]
    if not mesh:
        return ('OPT_INVALID', [])
    for _, col in mesh.children.items():
        if col.name not in lod:
            inv_collection.append(col.name)

    valid_col = ["mesh", "bones", "entities", "unknowns", "collision"]
    for _, col in collection.children.items():
        if col.name not in valid_col:
            inv_collection.append(col.name)

    if inv_collection:
        return ('OPT_WARNING', inv_collection)
    return ('OPT_VALID', [])


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
            ('OPT_FIVE', "5.0", "Version 5.0"),
            ('OPT_SIX', "6.0", "Version 6.0"),
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

    selected_name: StringProperty(
        name="Selected collection",
        description="Name of the collection to convert to .bwm",
        maxlen=255,
    )

    experimental: BoolProperty(
        name="experimental",
        description="""Allow add any entities (bone, entities, etc) regardless
         of file type""",
        default=False,
    )

    '''
    def check(self, context: bpy.types.Context) -> bool:
        if self.selected_name != context.collection.name:
            self.selected_name = context.collection.name
            return True
        else:
            return super().check(context)
    '''

    def execute(self, context):
        selected_collection = bpy.data.collections.get(self.selected_name)
        if not selected_collection:
            raise ValueError("This collection don't exist")
        validity_state, _ = validate(selected_collection)
        if validity_state == 'OPT_INVALID':
            raise ValueError(
                f"Collection : {self.selected_name} is unsuitable for export"
            )

        settings = {
            "version": self.version,
            "type": self.type,
            "selected_collection": selected_collection,
            "experimental": self.experimental
        }
        return write_bwm_data(context, self.filepath, settings)

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.prop(self, 'version')
        layout.prop(self, 'type', expand=True)

        layout.prop(self, 'experimental')


class BwmGenericPanel(Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_idname = "EXPORTBWM_PT_BwmGenericPanel"

    @classmethod
    def poll(cls, context: bpy.types.Context):
        operator = context.space_data.active_operator
        return operator.bl_idname == 'EXPORT_TEST_OT_bwm_data'


class BwmDataPanel(BwmGenericPanel):
    bl_idname = "EXPORTBWM_PT_BwmDataPanel"
    bl_label = "Root collection to convert to .bwm"

    def draw(self, context: bpy.types.Context):
        operator = context.space_data.active_operator
        layout = self.layout

        selected = context.collection
        selected_name = selected.name
        operator.selected_name = selected_name
        valid, inv_col = validate(selected)

        selected_icon = selected.color_tag
        if selected_icon != 'NONE':
            selected_icon = 'COLLECTION_' + selected_icon
        else:
            selected_icon = 'OUTLINER_COLLECTION'

        layout.label(
            text=selected_name,
            translate=False,
            icon=selected_icon
        )
        if valid == 'OPT_VALID':
            layout.label(
                text="Collection is ok to export",
                translate=False,
                icon='CHECKMARK'
            )
        if valid == 'OPT_INVALID':
            layout.label(
                text="No export possible",
                translate=False,
                icon='PANEL_CLOSE'
            )
        if valid == 'OPT_WARNING':
            column = layout.column()
            column.label(
                text="Export is possible, excluding the following collections",
                translate=False,
                icon='ERROR'
            )
            for col_name in inv_col:
                column.label(
                    text=col_name,
                    translate=False,
                    icon='OUTLINER_COLLECTION'
                )


def menu_func_export(self, context):
    self.layout.operator(
        ExportBWMData.bl_idname,
        text="Black & White Model (.bwm)"
    )


classes = (
    ExportBWMData,
    BwmDataPanel
)
