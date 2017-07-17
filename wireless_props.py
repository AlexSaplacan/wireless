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

props_log = logging.getLogger('wrls.wireless_props')
# props_log.setLevel(logging.DEBUG)


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
        if context.object.type == 'CURVE':
            bpy.ops.wrls.wrls_init()
        else:
            configs.switch = True
            curve.wrls.enable = False
            configs.switch = False
    else:
        if configs.switch:
            pass
        else:

            props_log.debug("Now I'm deleting everything")
            bpy.ops.wrls.cable_unset()

    return None

def load_thumbs():
    """
    Create a collection of thumbs and stores it in the configs.thumbs

    this runs on "register"
    """

    pcoll_thumbs = bpy.utils.previews.new()
    pcoll_thumbs_dir = os.path.join(
        os.path.dirname(__file__), "thumbs")

    thumbs_list = configs.data["Thumbs"]

    # load each thumbnail in the collection
    for item in thumbs_list:
        name = item["id"]
        img = item["img"]
        filepath = os.path.join(pcoll_thumbs_dir, img)
        pcoll_thumbs.load(name, filepath, 'IMAGE')

    # even if is called "cables", hera are all the thumbs cables and heads
    configs.thumbs["cables"] = pcoll_thumbs
    props_log.debug("Thumbs collection is %s" %configs.thumbs["cables"])

def create_preview_by_category(category):

    """
    EnumProperty callback

    returns a list of tuples for each thumbnail image for the corrispective items in the
    configs.data["model_types"]["Cable"]
    In other words, if the item is in the list declared as category  in the "model types", add it's
    thumbnail data to the list

    Args:
        category (str(nevere None)) This is the category in the json wile that
        defines the tupple elements to he added

    Returns:
        list of touples
    """

    enum_thumbs = []
    count = 0
    thumbs = configs.thumbs["cables"]
    thumbs_data = configs.data["Thumbs"]
    types = configs.data["model_types"][category]

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

def cable_preview_items(self, context):
    """Create an Enum Property for the cables"""

    return create_preview_by_category("Cable")



def cable_preview_update(self, context):
    """This runs when you  choose a different cable type"""

    # find the new choice of cable
    new_cable = context.window_manager.wrls.cables_types

    # Add here a record of the tais and heads

    # remove existing cable from context and set the wrls.status to undefined
    active_obj = bpy.context.active_object

    if active_obj.wrls.wrls_status == 'CURVE':
        wireless.wrls_off_and_delete_childs(active_obj)
    elif active_obj.wrls.wrls_status == 'CABLE':
        active_obj = active_obj.parent
        active_obj.select = True
        # make active the curve so doesn't return error on wireless_ui
        context.scene.objects.active = bpy.data.objects[active_obj.name]
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

def toggle_head_end_cap(self, context):
    """Runs when turning on/off the use head option"""

    active_obj = context.active_object
    # Do something when is On
    cable = wireless.find_cable(active_obj)
    if cable.wrls.use_head is True:
        bpy.ops.wrls.use_head()
    # Do something else when is off

def toggle_tail_end_cap(self, context):

    pass

def head_preview_items(self, context):
    """Create an EnumProperty for the head endcaps"""

    return create_preview_by_category("Ends")

def head_preview_update(self, context):

    pass

def tail_preview_items(self, context):
    """Create an EnumProperty for the head endcaps"""

    return create_preview_by_category("Ends")

def tail_preview_update(self, context):
    pass

############### Property Group ########################

class WirelessPropertyGroup(PropertyGroup):

    """These are the properties hold by objects.

    """

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

    use_head = BoolProperty(
        default=False,
        description="Use head end cap",
        update=toggle_head_end_cap
        )

    use_tail = BoolProperty(
        default=False,
        description="Use tail end cap",
        update=toggle_tail_end_cap
        )

class WirelessSettingsPropertyGroup(PropertyGroup):

    """These are settings properties, hold by window_manager

    """

    cables_types = bpy.props.EnumProperty(
        name="Cable types",
        description="Choose your cable",
        items=cable_preview_items,
        update=cable_preview_update
        )
    cables_previews_dir = bpy.props.StringProperty(
        name="Cables Path",
        subtype='DIR_PATH',
        default="",
        update=cable_preview_update
        )
    head_types = bpy.props.EnumProperty(
        name="Head types",
        description="Choose the head endcap",
        items=head_preview_items,
        update=head_preview_update
        )
    tail_types = bpy.props.EnumProperty(
        name="Tail types",
        description="Choose the tail endcap",
        items=tail_preview_items,
        update=tail_preview_update
        )

def register():
    """Register here"""
    bpy.types.Object.wrls = PointerProperty(
        name="Wireless Property",
        type=WirelessPropertyGroup)

    bpy.types.WindowManager.wrls = PointerProperty(
        name="Wireless Settings Property",
        type=WirelessSettingsPropertyGroup)

    load_thumbs()

def unregister():
    """Unregister here:"""
    del bpy.types.Object.wrls
    del bpy.types.WindowManager.wrls

    for pcoll in configs.thumbs.values():
        bpy.utils.previews.remove(pcoll)
    configs.thumbs.clear()
