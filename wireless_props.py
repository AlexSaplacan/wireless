import os
import logging
import bpy


from . import configs
from . import wireless

from bpy.types import PropertyGroup
from bpy.props import BoolProperty
from bpy.props import PointerProperty
from bpy.props import EnumProperty

from bpy.utils import previews

log = logging.getLogger('wrls.props')
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
        if context.object.type == 'CURVE':
            """Create the cable for the firs time"""
            # If the curve is already not set as undefined get this message
            if wireless.get_is_undefined_curve(context) is False:
                log.debug("This curve is already cable.")

            else:
                log.debug("This is an undefined curve, doing something.")
                obj_name = curve.name
                wireless.set_wrls_status(context, obj_name, 'CURVE')

                # we use the config.data to load the first thumb
                first_cable = bpy.context.window_manager.wrls.cables_types

                log.debug("OBJECT_OT_InitCable- cable_name is: %s" %first_cable)
                cable_shape = wireless.import_model(first_cable)
                wireless.set_wrls_status(context, cable_shape.name, 'CABLE')
                configs.switch = True
                cable_shape.wrls.enable = True
                configs.switch = False
                context.scene.objects.link(cable_shape)

                log.debug("Curve location is %s" % curve.location)

                # put the cable shape at the desired location and parent it
                cable_shape.location = curve.location
                cable_shape.select = True
                bpy.ops.object.parent_set()
                cable_shape.select = False

                # put 2 modifiers on the shape object ARRAY and CURVE
                wrls_array = cable_shape.modifiers.new(type='ARRAY', name="WRLS_Array")
                wrls_array.curve = curve
                wrls_array.fit_type = 'FIT_CURVE'


                wrls_curve = cable_shape.modifiers.new(name='WRLS_Curve', type='CURVE')
                wrls_curve.object = curve


            # bpy.ops.wrls.wrls_init()
        else:
            configs.switch = True
            curve.wrls.enable = False
            configs.switch = False
    else:
        if configs.switch:
            pass
        else:

            log.debug("Now I'm deleting everything")

            cable = context.active_object
            wrls_status = cable.wrls.wrls_status

            if wrls_status == 'CURVE':
                wireless.wrls_off_and_delete_childs(cable)
            elif wrls_status == 'CABLE':
                cable = cable.parent
                cable.select = True
                # make active the curve so doesn't return error on wireless_ui
                bpy.context.scene.objects.active = bpy.data.objects[cable.name]
                # update the scene to avoid error
                bpy.context.scene.update()
                wireless.wrls_off_and_delete_childs(cable)
                configs.switch = True
                cable.wrls.enable = False
                configs.switch = False
            else:
                log.debug("This should not happen.")
            cable.wrls.wrls_status = 'UNDEFINED'
            # bpy.ops.wrls.cable_unset()

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
    log.debug("Thumbs collection is %s" %configs.thumbs["cables"])

def create_preview_by_category(category):

    """
    EnumProperty callback

    returns a list of tuples for each thumbnail image for the corrispective items in the
    configs.data["model_types"]["Cable"]
    In other words, if the item is in the list declared as category  in the "model types", add it's
    thumbnail data to the list

    Args:
        category (str(nevere None)) This is the category in the json wile that
        defines the tupple elements to be added

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

    return create_preview_by_category("cables_types")



def cable_preview_update(self, context):
    """This runs when you  choose a different cable type"""

    # find the new choice of cable
    new_cable = context.window_manager.wrls.cables_types

    active_obj = bpy.context.active_object
    # Add here a record of the tais and heads
    head = wireless.find_part(active_obj, 'HEAD')
    tail = wireless.find_part(active_obj, 'TAIL')
    cable = wireless.find_part(active_obj, 'CABLE')
    curve = wireless.find_part(active_obj, 'CURVE')
    log.debug("cable_preview_update -- found parts are: %s, %s, %s, %s" %(
        curve, cable, head, tail))

    curve.select = True
    cable.select = False
    context.scene.objects.active = bpy.data.objects[curve.name]
    context.scene.update()

    #  import new cable and set wrls status
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
    wrls_array.curve = curve
    wrls_array.fit_type = 'FIT_CURVE'

    # check for tail and head, and if there were, put them back
    if head is not None:
        configs.switch = True
        cable_shape.wrls.use_head = True
        configs.switch = False
        wrls_array.end_cap = head
    if tail is not None:
        configs.switch = True
        cable_shape.wrls.use_tail = True
        configs.switch = False
        wrls_array.start_cap = tail


    wrls_curve = cable_shape.modifiers.new(name='WRLS_Curve', type='CURVE')
    wrls_curve.object = curve
    wireless.clean_obsolete_materials(cable)
    bpy.data.objects.remove(cable, do_unlink=True)

def toggle_head_end_cap(self, context):
    """Runs when turning on/off the use head option"""

    active_obj = context.active_object
    # Do nothing when switch is True
    if configs.switch is True:
        log.debug("toggle head endcap -- Now I should do something else")
    else:
        # Do something when is On
        if active_obj.wrls.use_head is True:
            first_head = context.window_manager.wrls.head_types
            cable = wireless.find_part(active_obj)
            curve = cable.parent
            active_status = active_obj.wrls.wrls_status
            # let's make sure both curve and cable have "use_head" = True
            if active_status == 'CURVE':
                configs.switch = True
                cable.wrls.use_head = True
                configs.switch = False

            else:
                curve = active_obj.parent
                configs.switch = True
                curve.wrls.use_head = True
                configs.switch = False

            log.debug("toggle_head_end_cap -- cable object is %s" %cable)
            wireless.connect_head(cable, first_head)
            

        # Do something else when turned off
        else:
            # find the head object
            head = wireless.find_part(active_obj, 'HEAD')
            cable = wireless.find_part(active_obj, 'CABLE')
            curve = wireless.find_part(active_obj, 'CURVE')
            log.debug("toggle_head_endcap -- found parts are: %s, %s, %s" %(
                head.name, cable.name, curve.name))
            wireless.clean_obsolete_materials(head)
            bpy.data.objects.remove(head, do_unlink=True)
            configs.switch = True
            cable.wrls.use_head = False
            curve.wrls.use_head = False
            configs.switch = False

def toggle_tail_end_cap(self, context):
    """Runs when turning on/off the use tail option"""

    active_obj = context.active_object
    # Do nothing when switch is True
    if configs.switch is True:
        log.debug("toggle tail endcap -- Now I should do something else")
    else:
        # Do something when is On
        if active_obj.wrls.use_tail is True:
            first_tail = context.window_manager.wrls.tail_types
            cable = wireless.find_part(active_obj)
            curve = cable.parent
            active_status = active_obj.wrls.wrls_status
            # let's make sure both curve and cable have "use_head" = True
            if active_status == 'CURVE':
                configs.switch = True
                cable.wrls.use_tail = True
                configs.switch = False

            else:
                curve = active_obj.parent
                configs.switch = True
                curve.wrls.use_tail = True
                configs.switch = False

            log.debug("toggle_tail_end_cap -- cable object is %s" %cable)
            wireless.connect_tail(cable, first_tail)

        # Do something else when turned off
        else:
            # find the tail object
            tail = wireless.find_part(active_obj, 'TAIL')
            cable = wireless.find_part(active_obj, 'CABLE')
            curve = wireless.find_part(active_obj, 'CURVE')
            log.debug("toggle_tail_endcap -- found parts are: %s, %s, %s" %(
                tail.name, cable.name, curve.name))
            wireless.clean_obsolete_materials(tail)
            bpy.data.objects.remove(tail, do_unlink=True)
            configs.switch = True
            cable.wrls.use_tail = False
            curve.wrls.use_tail = False
            configs.switch = False


def head_preview_items(self, context):
    """Create an EnumProperty for the head endcaps"""

    return create_preview_by_category("head_types")

def head_preview_update(self, context):
    """Update the head object to the new model"""

    active_obj = context.active_object
    head = wireless.find_part(active_obj, 'HEAD')
    cable = wireless.find_part(active_obj, 'CABLE')
    curve = wireless.find_part(active_obj, 'CURVE')

    # find the selected head type
    new_head_name = context.window_manager.wrls.head_types

    #now import and connect the head with the relative name
    wireless.connect_head(cable, new_head_name)
    wireless.clean_obsolete_materials(head)
    bpy.data.objects.remove(head, do_unlink=True)

def tail_preview_items(self, context):
    """Create an EnumProperty for the tail endcaps"""

    return create_preview_by_category("tail_types")

def tail_preview_update(self, context):
    """Update the tail object to the new model"""

    active_obj = context.active_object
    tail = wireless.find_part(active_obj, 'TAIL')
    cable = wireless.find_part(active_obj, 'CABLE')
    curve = wireless.find_part(active_obj, 'CURVE')

    # find the selected tail type
    new_tail_name = context.window_manager.wrls.tail_types

    #now import and connect the tail with the relative name
    wireless.connect_tail(cable, new_tail_name)
    wireless.clean_obsolete_materials(tail)
    bpy.data.objects.remove(tail, do_unlink=True)

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
