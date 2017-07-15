import bpy
import os
import logging


from . import configs
from . import wireless

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

        this runs on register
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
    types = configs.data["model_types"]["Cable"]

    if not thumbs:
        return []


    for data in thumbs_data:
        # here sort only the thumbs that are for cables
        if data["id"] in types:
            name = data["id"]
            icon = thumbs[name]
            enum_thumbs.append((name, name, "", icon.icon_id, count))
            count += 1
    
    return enum_thumbs



def cable_preview_update(self, context):
    """This should run when you  choose a different cable type"""

    # find the new choice of cable
    new_cable = context.window_manager.wrls.cables_types

    # remove existing cable from context and set the wrls.status to undefined
    active_obj = bpy.context.active_object

    if active_obj.wrls.wrls_status == 'CURVE':
        wireless.wrls_off_and_delete_childs(active_obj)
    elif active_obj.wrls.wrls_status == 'CABLE':
        active_obj = active_obj.parent
        active_obj.select = True
        # make active the curve so doesn't return error on wireless_ui
        context.scene.objects.active =  bpy.data.objects[active_obj.name]
        wireless.wrls_off_and_delete_childs(active_obj)

    #  import ne cable and set wrls status

    cable_shape = wireless.import_model(new_cable)
    wireless.set_wrls_status(context, cable_shape.name, 'CABLE')
    configs.switch = True
    cable_shape.wrls.enable = True
    configs.switch = False
    context.scene.objects.link(cable_shape)

    # put the cable shape at the desired location and parent it
    cable_shape.location = active_obj.location
    cable_shape.select = True
    bpy.ops.object.parent_set()
    cable_shape.select = False

    # put 2 modifiers on the shape object ARRAY and CURVE
    wrls_array = cable_shape.modifiers.new(type='ARRAY', name="WRLS_Array")
    wrls_array.curve = active_obj
    wrls_array.fit_type = 'FIT_CURVE'


    wrls_curve = cable_shape.modifiers.new(name='WRLS_Curve', type='CURVE')
    wrls_curve.object = active_obj

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
