import bpy
import os
import logging


from . import configs
# from . import wireless

from bpy.types import PropertyGroup
from bpy.props import BoolProperty
from bpy.props import PointerProperty
from bpy.props import EnumProperty

from bpy.utils import previews

log = logging.getLogger('wrls.wireless')
log.setLevel(logging.DEBUG)


############### Property Update Functions ############

status_items = [
    ("UNDEFINED", "Undefined", "", 0),
    ("CURVE", "Curve", "", 1),
    ("CABLE", "Cable", "", 2),
    ("HEAD", "Head", "", 3),
    ("TAIL", "Tail", "", 4)
    ]

def toggle_wireless(self, context):
    """
    First set a state here like on and off -- to prevent recursive calls ?
    If not is True (was off)
        start to use wireless
    If was on:
        do something else
    """
    curve = context.active_object


    configs.switch = False
    if curve.wrls.enable:
        if context.object.type =='CURVE':
            bpy.ops.wrls.wrls_init()
        else:
            configs.switch = True
            curve.wrls.enable = False
            configs.switch = False           
    else:
        if configs.switch:
            pass
        else:

            log.debug("Now I'm deleting everything")
            bpy.ops.wrls.cable_unset()            
    return None

def load_thumbs():

    pcoll_thumbs = bpy.utils.previews.new()
    pcoll_thumbs_dir = os.path.join(
                    os.path.dirname(__file__),"thumbs")

    thumbs_list = configs.data["Thumbs"]
    for item in thumbs_list:
        name = item["id"]
        img = item["img"]
        filepath = os.path.join(pcoll_thumbs_dir, img)
        pcoll_thumbs.load(name, filepath, 'IMAGE') 


    configs.thumbs["cables"] = pcoll_thumbs
    log.debug("Thumbs collection is %s" %configs.thumbs["cables"])
    log.debug("Thumbs collection  USB Type C is %s" %configs.thumbs["cables"]["USB Type C"])
    
def cable_preview_items(self, context):
    """EnumProperty callback"""
    

    thumbs = configs.thumbs["cables"]

    if not thumbs:
        return []



    for thumb in thumbs:
        name = thumb["id"]
        icon = configs.thumbs["cables"][name]
        number = thumb["img"][:-4]
        enum_thumbs.append((str(count), name, "", thumb["img"], number))
        count += 1
    
    log.debug(enum_thumbs)
    return enum_thumbs



def cable_preview_update(self, context):

    pass


############### Property Group ########################

class WirelessPropertyGroup(PropertyGroup):
    # add some properties
    wrls_status = EnumProperty(
                    name='Status', 
                    default='UNDEFINED', 
                    items=status_items
                    )

    enable = BoolProperty(
                    default=False, 
                    description="Enable Wireless", 
                    update=toggle_wireless
                    )

class WirelessSettingsPropertyGroup(PropertyGroup):

    cables_types = bpy.props.EnumProperty(
                    name="Cable types",
                    description="Choose your cable",
                    items=cable_preview_items,
                    update=cable_preview_update
                    )
    cables_previews_dir = bpy.props.StringProperty(
                    name = "Cables Path",
                    subtype = 'DIR_PATH'.
                    default = "",
                    update=preview_cable_dir_update
                    )

def register():
    bpy.types.Object.wrls = PointerProperty(
                    name="Wireless Property",
                    type=WirelessPropertyGroup)

    bpy.types.WindowManager.wrls = PointerProperty(
                        name="Wireless Settings Property",
                        type=WirelessSettingsPropertyGroup)

    load_thumbs()

def unregister():

    del bpy.types.Object.wrls
    del bpy.types.WindowManager.wrls

    for pcoll in configs.thumbs.values():
        bpy.utils.previews.remove(pcoll)
    configs.thumbs.clear()
