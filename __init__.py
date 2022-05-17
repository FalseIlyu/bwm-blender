# <pep8-80 compliant>
import bpy

from .operator_export import operator_bwm_export
from .operator_import import operator_bwm_import

bl_info = {
    "name": "Black & White Model (.bwm) Format",
    "blender": (2, 93, 0),
    "category": "Import-Export",
}


def register():
    print(f"Registering : {bl_info['name']}")

    operator_bwm_import.register()
    bpy.types.TOPBAR_MT_file_import.append(
        operator_bwm_import.menu_func_import
    )

    [bpy.utils.register_class(cls) for cls in operator_bwm_export.classes]
    bpy.types.TOPBAR_MT_file_export.append(
        operator_bwm_export.menu_func_export
    )


def unregister():
    print(f"Unregistering : {bl_info['name']}")

    operator_bwm_import.unregister()
    bpy.types.TOPBAR_MT_file_import.remove(
        operator_bwm_import.menu_func_import
    )

    [bpy.utils.unregister_class(cls) for cls in operator_bwm_export.classes]
    bpy.types.TOPBAR_MT_file_export.remove(
        operator_bwm_export.menu_func_export
    )
