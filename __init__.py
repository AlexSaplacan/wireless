# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Wireless",
    "author": "A_S",
    "version": (0, 4, 9),
    "blender": (2, 78, 3),
    "location": "3D View > Toolbar > Wireless",
    "description": "Transform quickly a curve into a cable",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "3D View"
}
import logging
logger = logging.getLogger("wrls")
if not logger.handlers:
    handler = logging.StreamHandler()
    logger.addHandler(handler) 

# set logging level here
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
handler.setFormatter(formatter)

if "bpy" in locals():

    import imp

    imp.reload(configs)
    imp.reload(wireless)
    imp.reload(wireless_ui)
    imp.reload(wireless_props)

    configs.init()

else:
    # import logging
    # logger = logging.getLogger("wrls")
    # handler = logging.StreamHandler()

    # # set logging level here
    # logger.addHandler(handler) 
    # handler.setLevel(logging.DEBUG)
    # formatter = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
    # handler.setFormatter(formatter)


    import bpy   
    from . import (
        configs,
        wireless,
        wireless_ui,
        wireless_props,
        )

    configs.init()

def register():
    print("Start register")
    bpy.utils.register_module(__name__)
    wireless.register()
    wireless_props.register()
    wireless_ui.register()
    print("Register done")

def unregister():
    bpy.utils.unregister_module(__name__)
    wireless.unregister()
    wireless_props.unregister()
    wireless_ui.unregister()



if __name__ == "__main__":
    register()