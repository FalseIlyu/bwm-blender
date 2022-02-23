# <pep8-80 compliant>
from . import operator_bwm_export, operator_bwm_import

bl_info = {
    "name": "Black & White Model (.bwm) Format",
    "blender": (2, 93, 0),
    "category": "Import-Export",
}


def register():
    print("Registering : " + bl_info["name"])
    operator_bwm_import.register()
    operator_bwm_export.register()


def unregister():
    print("Unregistering : " + bl_info["name"])
    operator_bwm_import.unregister()
    operator_bwm_export.unregister()
