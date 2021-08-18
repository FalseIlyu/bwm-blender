bl_info = {
    "name": "Black & White Model (.bwm) Format",
    "blender": (2,93,0),
    "category": "Import-Export",
}

import bpy
from operators_bwm import operator_bwm_import

def register():
    print("Registering : " + bl_info["name"])
    operator_bwm_import.register()

def unregister():
    print("Unregistering : " + bl_info["name"])
    operator_bwm_import.unregister()