bl_info = {
    "name": "BWM File Format",
    "blender": (2,98,0),
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