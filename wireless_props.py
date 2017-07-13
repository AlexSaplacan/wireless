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
    """create a collection of thumbs and stores it in the configs.thumbs

        make one collection for cables and one collection for heads/tails
    """


    pcoll_thumbs = bpy.utils.previews.new()
    pcoll_thumbs_dir = os.path.join(
                    os.path.dirname(__file__),"thumbs")

    thumbs_list = configs.data["Thumbs"]
    cables_list = configs.data["model_types"]["Cable"]
    log.debug("Model_types Cable is: %s" %cables_list)

    # find a way to load only certain thumbs
    # this function runs when registering, can I register again somewhere else to update the lists?
    for item in thumbs_list:
        # if item["id"] in cables_list:
        name = item["id"]
        img = item["img"]
        filepath = os.path.join(pcoll_thumbs_dir, img)
        pcoll_thumbs.load(name, filepath, 'IMAGE') 


    configs.thumbs["cables"] = pcoll_thumbs
    log.debug("Thumbs collection is %s" %configs.thumbs["cables"])
    log.debug("Thumbs collection  USB Type C is %s" %configs.thumbs["cables"]["USB Type C"])
    
def cable_preview_items(self, context):
    """EnumProperty callback"""
    
    enum_thumbs = []
    count = 0
    thumbs = configs.thumbs["cables"]
    thumbs_data = configs.data["Thumbs"]

    log.debug(thumbs)

    if not thumbs:
        return []


    for data in thumbs_data:
        log.debug("This thunb is: %s" %data["id"])
        name = data["id"]
        icon = thumbs[name]
        log.debug("This icon is %s" %icon )
        enum_thumbs.append((name, name, "", icon.icon_id, count))
        count += 1
    
    log.debug(enum_thumbs)
    return enum_thumbs



def cable_preview_update(self, context):
    """This should run when you  choose a different cables group"""

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
                    subtype = 'DIR_PATH',
                    default = "",
                    update=cable_preview_update
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
