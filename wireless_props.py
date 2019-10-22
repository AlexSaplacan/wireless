import os
import logging
import bpy
import bmesh
import math
import mathutils
import numpy as np

from . import configs
from . import wireless

from bpy.types import PropertyGroup
from bpy.props import BoolProperty
from bpy.props import PointerProperty
from bpy.props import EnumProperty
from bpy.props import FloatProperty
from bpy.props import StringProperty

from bpy.utils import previews

log = logging.getLogger('wrls.props')
log.setLevel(logging.INFO)

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
    wireless.set_wrls_collection()
    if curve.wrls.enable:
        if context.object.type == 'CURVE':
            """Create the cable for the firs time
            """

            # If the curve is already not set as undefined get this message
            if wireless.get_is_undefined_curve(context) is False:
                log.debug("This curve is already cable.")

            else:
                log.debug("This is an undefined curve, doing something.")
                obj_name = curve.name
                wireless.set_wrls_status(context, obj_name, 'CURVE')
                curve.wrls.curve = curve.name

                # we use the config.data to load the first thumb
                first_cable = bpy.context.window_manager.wrls.cables_types

                log.debug("OBJECT_OT_InitCable- cable_name is: %s" %first_cable)
                cable_shape = wireless.import_model(first_cable)
                wireless.set_wrls_status(context, cable_shape.name, 'CABLE')
                curve.wrls.cable = cable_shape.name
                cable_shape.wrls.cable_original_x = cable_shape.dimensions[0]
                configs.switch = True
                cable_shape.wrls.enable = True
                curve.wrls.cable = cable_shape.name
                configs.switch = False
                context.scene.collection.children['WrlS'].objects.link(cable_shape)

                log.debug("Curve location is %s" % curve.location)

                # put the cable shape at the desired location and parent it
                cable_shape.location = curve.location
                cable_shape.rotation_euler = curve.rotation_euler
                cable_shape.select_set(True)
                bpy.ops.object.parent_set()
                cable_shape.select_set(False)

                # put 2 modifiers on the shape object ARRAY and CURVE
                wireless.add_cable_modifiers(cable_shape, curve)
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
                wireless.wrls_off_and_delete_children(cable)
            elif wrls_status == 'CABLE':
                cable = cable.parent
                cable.select_set(True)
                # make active the curve so doesn't return error on wireless_ui
                # bpy.context.scene.objects.active = bpy.data.objects[cable.name]
                context.view_layer.objects.active = bpy.data.objects[cable.name]
                # update the scene to avoid error
                bpy.context.scene.update()
                wireless.wrls_off_and_delete_children(cable)
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
    In other words, if the item is in the list declared as category in the "model types", add it's
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


def create_items_from_category_list(category):
    """
    EnumProperty callback

    return a list of tuples for each element in the category.
    The tuple item looks like ('name', 'name, '', count, count)
    """
    enum_categories = []
    for pos, item in enumerate(configs.data[category]):
        enum_categories.append((item, item, '', item, pos))

    return enum_categories


def cable_preview_items(self, context):
    """Create an Enum Property for the cables"""

    return create_preview_by_category(self.cable_categories)


def cable_preview_update(self, context):
    """This runs when you  choose a different cable type"""

    # find the new choice of cable
    log.debug('Running cable preview update')
    new_cable = context.window_manager.wrls.cables_types

    active_obj = bpy.context.active_object

    curve, cable, head, tail = wireless.find_parts(active_obj)

    # Rich edit----------
    thickness = curve.wrls.cable_thickness
    stretch = curve.wrls.cable_stretch

    # if reset, the cable thickness will go back to one when
    #   switching cable shapes
    reset = False
    if reset:
        # overwrite the current thickness when switching cables
        curve.wrls['cable_thickness'] = 1
        cable.wrls['cable_thickness'] = 1
        curve.wrls['old_c_thickness'] = 1
        cable.wrls['old_c_thickness'] = 1
        # overwrite the current stretch when switching cables
        curve.wrls['cable_thickness'] = 1
        cable.wrls['cable_thickness'] = 1
        curve.wrls['old_c_thickness'] = 1
        cable.wrls['old_c_thickness'] = 1

    # Keep record of the active object
    reverse = False
    if active_obj is cable:
        reverse = True

    curve.select_set(True)
    cable.select_set(False)
    context.view_layer.objects.active = bpy.data.objects[curve.name]
    context.evaluated_depsgraph_get()

    #  import new cable and set wrls status
    cable_shape = wireless.import_model(new_cable)
    cable_shape.wrls.cable_x = cable_shape.dimensions[0]
    wireless.set_wrls_status(context, cable_shape.name, 'CABLE')
    configs.switch = True
    cable_shape.wrls.enable = True
    configs.switch = False
    # context.scene.objects.link(cable_shape)
    context.scene.collection.children['WrlS'].objects.link(cable_shape)

    # put the cable shape at the desired location and parent it
    cable_shape.location = active_obj.location
    cable_shape.rotation_euler = active_obj.rotation_euler
    cable_shape.select_set(True)
    bpy.ops.object.parent_set()
    cable_shape.select_set(False)

    # put 2 modifiers on the shape object ARRAY and CURVE
    wrls_array = cable_shape.modifiers.new(type='ARRAY', name="WRLS_Array")
    wrls_array.curve = curve
    wrls_array.fit_type = 'FIT_CURVE'
    wrls_array.use_merge_vertices = True
    wrls_array.merge_threshold = 0.0001
    wrls_array.relative_offset_displace[0] = cable_shape.wrls.array_offset

    # check for tail and head, and if there were, put them back, set up materials
    if head is not None:
        configs.switch = True
        cable_shape.wrls.use_head = True
        configs.switch = False
        wrls_array.end_cap = head
        wireless.setup_materials(cable_shape, head)
    if tail is not None:
        configs.switch = True
        cable_shape.wrls.use_tail = True
        configs.switch = False
        wrls_array.start_cap = tail
        wireless.setup_materials(cable_shape, tail, False)

    wrls_curve = cable_shape.modifiers.new(name='WRLS_Curve', type='CURVE')
    wrls_curve.object = curve
    wireless.clean_obsolete_materials(cable)
    bpy.data.objects.remove(cable, do_unlink=True)

    if reverse:
        context.scene.objects.active = cable_shape
        cable_shape.select_set(True)

    # Rich edit-------------------
    # New cable shape will keep thickness setting
    if not reset:
        # update mesh:
        mesh = cable_shape.data
        v_count = len(mesh.vertices)
        co = np.zeros(v_count * 3)
        mesh.vertices.foreach_get('co', co)
        co.shape = (v_count, 3)
        co[:, 1:] *= thickness
        co[:, 0] *= stretch
        mesh.vertices.foreach_set('co', co.ravel())
        mesh.update()

        # update properties
        curve.wrls['cable_thickness'] = thickness
        cable_shape.wrls['cable_thickness'] = thickness
        curve.wrls['old_c_thickness'] = thickness
        cable_shape.wrls['old_c_thickness'] = thickness

        curve.wrls['cable_stretch'] = stretch
        cable_shape.wrls['cable_stretch'] = stretch
        curve.wrls['old_cable_stretch'] = stretch
        cable_shape.wrls['old_cable_stretch'] = stretch

    if curve.wrls.use_tail:
        offset_tail(cable_shape, tail, cable_co=None)



def get_co(mesh):
    v_count = len(mesh.vertices)
    co = np.zeros(v_count * 3, dtype=np.float32)
    mesh.vertices.foreach_get('co', co)
    co.shape = (v_count, 3)
    return co


def get_proxy_co(ob, mod=None):
    """Returns vertex coords with modifier effects as N x 3"""
    # set mod status
    if mod is not None:
        ob.modifiers[mod].show_render = False
    me = ob.to_mesh()
    if mod is not None:
        ob.modifiers[mod].show_render = True
    v_count = len(me.vertices)
    arr = np.zeros(v_count * 3, dtype=np.float32)
    me.vertices.foreach_get('co', arr)
    arr.shape = (v_count, 3)
    ob.to_mesh_clear()
    return arr


def toggle_head_end_cap(self, context):
    """Runs when turning on/off the use head option"""

    active_obj = context.active_object
    curve, cable, head, tail = wireless.find_parts(active_obj)
    # Do nothing when switch is True
    if configs.switch is True:
        log.debug("toggle head endcap -- Now I should do something else")
    else:
        # Do something when is On
        if active_obj.wrls.use_head is True:
            first_head = context.window_manager.wrls.head_types
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
            wireless.clean_obsolete_materials(head)
            bpy.data.objects.remove(head, do_unlink=True)
            configs.switch = True
            cable.wrls.use_head = False
            curve.wrls.use_head = False
            configs.switch = False


def offset_tail(cable, tail, cable_co=None):
    """Moves the tail object so that it lines up
    during cable stretch adjustments"""
    if cable_co is None:
        cable_co = get_co(cable.data)

    tail_co = get_co(tail.data)
    tail_x_max = np.max(tail_co[:,0])

    cable_x = cable_co[:,0]
    move = np.max(cable_x) - np.min(cable_x)

    tail_co[:, 0] += (move - tail_x_max)

    tail.data.vertices.foreach_set('co', tail_co.ravel())
    tail.data.update()


def toggle_tail_end_cap(self, context):
    """Runs when turning on/off the use tail option"""

    active_obj = context.active_object
    curve, cable, head, tail = wireless.find_parts(active_obj)
    # Do nothing when switch is True
    if configs.switch is True:
        log.debug("toggle tail endcap -- Now I should do something else")
    else:
        # Do something when is On
        if active_obj.wrls.use_tail is True:
            first_tail = context.window_manager.wrls.tail_types
            curve = cable.parent
            active_status = active_obj.wrls.wrls_status
            # let's make sure both curve and cable have "use_tail" = True
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

            curve, cable, head, tail = wireless.find_parts(active_obj)
            offset_tail(cable, tail, cable_co=None)

        # Do something else when turned off
        else:
            wireless.clean_obsolete_materials(tail)
            bpy.data.objects.remove(tail, do_unlink=True)
            configs.switch = True
            cable.wrls.use_tail = False
            curve.wrls.use_tail = False
            configs.switch = False


def head_preview_items(self, context):
    """Create an EnumProperty for the head endcaps"""

    return create_preview_by_category(self.head_categories)


def head_preview_update(self, context):
    """Update the head object to the new model"""

    active_obj = context.active_object
    curve, cable, head, tail = wireless.find_parts(active_obj)

    # find the selected head type
    new_head_name = context.window_manager.wrls.head_types

    #now import and connect the head with the relative name
    wireless.connect_head(cable, new_head_name)
    wireless.clean_obsolete_materials(head)
    bpy.data.objects.remove(head, do_unlink=True)


def tail_preview_items(self, context):
    """Create an EnumProperty for the tail endcaps"""

    return create_preview_by_category(self.tail_categories)


def tail_preview_update(self, context):
    """Update the tail object to the new model"""

    active_obj = context.active_object
    curve, cable, head, tail = wireless.find_parts(active_obj)

    # find the selected tail type
    new_tail_name = context.window_manager.wrls.tail_types

    #now import and connect the tail with the relative name
    wireless.connect_tail(cable, new_tail_name)
    wireless.clean_obsolete_materials(tail)
    bpy.data.objects.remove(tail, do_unlink=True)

    curve, cable, head, tail = wireless.find_parts(active_obj)
    if curve.wrls.use_tail:
        offset_tail(cable, tail, cable_co=None)


def cable_categories_items(self, context):
    """Create an EnumProperty for the Cable categories"""


    return create_items_from_category_list('cable_categories')

def cable_categories_update(self, context):
    pass

def head_categories_items(self, context):
    """Create an EnumProperty for the Cable categories"""
    return create_items_from_category_list('head_categories')

def head_categories_update(self, context):
    pass

def tail_categories_items(self, context):
    """Create an EnumProperty for the Cable categories"""
    return create_items_from_category_list('tail_categories')

def tail_categories_update(self, context):
    pass

def tail_update(self, context):
    pass

def new_part_update(self, context):
    pass

def new_part_preview_items(self, context):
    """Create an EnumProperty for the Cable categories"""
    return create_preview_by_category(self.new_item_categories)

def new_item_categories_items(self, context):
    """Create an EnumProperty for the Cable categories"""
    return create_items_from_category_list('new_parts')

def custom_part_preview_items(self, context):
    """Create an EnumProperty for the Cable categories"""
    return create_preview_by_category('Custom Parts')

def custom_parts_items(self, context):
    """Create an EnumProperty for the Cable categories"""
    return create_items_from_category_list('custom_parts')

def type_of_new_part(self, context):
    pass


def set_old_thickness(self, value):
    self["old_c_thickness"] = value

def update_cable_thickness(self,context):
    """go on editmode and scale the vets on y and z by value
    """
    if configs.switch is False:
        active_obj = bpy.context.active_object
        curve, cable, head, tail = wireless.find_parts(active_obj)

        old_value = curve.wrls.old_c_thickness
        if active_obj == cable:
            value = cable.wrls.cable_thickness
            curve.wrls['cable_thickness'] = value
        else:
            value = curve.wrls.cable_thickness
            cable.wrls['cable_thickness'] = value

        factor = value / old_value

        # debug info:
        log.debug("Found cable thickness on cable: %s" % cable.wrls.cable_thickness)
        log.debug("Found cable thickness on active object: %s" % active_obj.wrls.cable_thickness)
        log.debug("Old cable thickness on : %s" % old_value)
        log.debug("Factor is : %s" % factor)

        # update mesh:
        mesh = cable.data

        co = get_co(mesh)

        co[:, 1:] *= factor
        mesh.vertices.foreach_set('co', co.ravel())
        mesh.update()

        configs.switch = True #?? what does this do ??

        curve.wrls.old_c_thickness = value
        cable.wrls.old_c_thickness = value

        configs.switch = False

def head_use_cable_mat_toggle(self, context):
    """Make the head use the first material the same one used by the cable
    if swithched True, or use it's default material if switched False.
    By default materials for heads and tails are on material slots 2, 3 and 4
     This function is copying the cable material from slot 1 to slot 2
    """
    active_obj = context.active_object
    curve, cable, head, tail = wireless.find_parts(active_obj)

    context.view_layer.objects.active = cable
    wireless.setup_materials(cable, head)


def tail_use_cable_mat_toggle(self, context):
    """Make the tail use the first material the same one used by the cable
    if swithched True, or use it's default material.
    By default materials for heads and tails are on material slots 2, 3 and 4
    For tails they are moved on 5, 6 and 7. This function is copying the cable material
    from slot 1 to slot 4
    """
    active_obj = context.active_object
    curve, cable, head, tail = wireless.find_parts(active_obj)

    context.view_layer.objects.active = cable
    wireless.setup_materials(cable, tail, False)


def adjust_for_head(mesh, curve, co):
    """Adjust mesh scale slightly so it always fits
    the curve exactly... that is, within 1e-5"""
    # get total length of curve:
    cco = get_proxy_co(curve)
    vecs = cco[1:] - cco[:-1]
    total_len = np.sum(np.sqrt(np.einsum("ij,ij->i", vecs, vecs)))

    # if we need to use fit length
    #mesh.modifiers['WRLS_Array'].fit_length = total_len

    # get length of mesh on x axis
    mco = co
    mesh_len = np.max(mco[:,0]) - np.min(mco[:,0])

    # get closest ceiling for nearest repeat count
    div = total_len / mesh_len
    ceceil = math.ceil(div)

    # get scale so it duplicates just barely past the end
    scaly = total_len / (mesh_len * ceceil) + 1e-5

    # apply scale to mesh
    mco[:,0] *= scaly
    return scaly


def update_cable_stretch(self, context):
    """go on editmode and scale the vets on x by value
    """
    if configs.switch is False:
        active_obj = bpy.context.active_object
        curve, cable, head, tail = wireless.find_parts(active_obj)

        old_value = cable.wrls.old_cable_stretch
        if active_obj == cable:
            value = cable.wrls.cable_stretch
            curve.wrls['cable_stretch'] = value
        else:
            value = curve.wrls.cable_stretch
            cable.wrls['cable_stretch'] = value

        factor = value / old_value

        # debug info:
        log.debug("Found cable stretch on cable: %s" % cable.wrls.cable_stretch)
        log.debug("Found cable stretch on curve: %s" % curve.wrls.cable_stretch)
        log.debug("Old cable stretch on cable : %s" % old_value)
        log.debug("Factor is : %s" % factor)

        # update mesh:
        mesh = cable.data

        co = get_co(mesh)

        co[:, 0] *= factor

        scaly = adjust_for_head(cable, curve, co)

        mesh.vertices.foreach_set('co', co.ravel())
        mesh.update()

        if curve.wrls.use_tail:
            offset_tail(cable, tail, cable_co=None)

        #if head:
        if False:
            head.hide = False
            head.select_set(True)
            wireless.mirror_and_translate_head()
            head.hide = False

        configs.switch = True

        curve.wrls['cable_stretch'] = value * scaly
        cable.wrls['cable_stretch'] = value * scaly

        curve.wrls.old_cable_stretch = value * scaly
        cable.wrls.old_cable_stretch = value * scaly

        configs.switch = False


def set_old_head_slide(self, value):
    self["old_head_slide"] = value


def update_head_slide(self, context):
    """in editmode move the vertices on x  by certain ammount
    """
    if configs.switch is False:
        active_obj = bpy.context.active_object
        curve, cable, head, tail = wireless.find_parts(active_obj)

        old_value = cable.wrls.old_head_slide
        value = cable.wrls.head_slide
        wireless.update_wrls_data(cable, 'head_slide', value)
        factor = value - old_value

        head.hide = False
        # bpy.context.scene.objects.active = head
        context.view_layer.objects.active = head

        data = head.data
        if not data.is_editmode:
            bpy.ops.object.editmode_toggle()
        me = bpy.context.object.data
        mesh = bmesh.from_edit_mesh(me)

        for vert in mesh.verts:

            vert.co.x += factor
        bpy.ops.object.editmode_toggle()
        set_old_head_slide(self, value)
        wireless.update_wrls_data(cable, 'head_slide', value)
        wireless.update_wrls_data(cable, 'old_head_slide', value)
        head.hide = True


def curve_set(self, value):
    self['curve'] = value
    return None


def curve_get(self):
    return self['curve']


def curve_update(self, context):
    pass


def cable_set(self, value):
    self['cable'] = value
    return None


def cable_get(self):
    return self['cable']


def cable_update(self, context):
    configs.switch = True


    pass


def head_set(self, value):
    self['head'] = value
    return None


def head_get(self):

    return self['head']


def head_update(self, context):
    pass


def tail_set(self, value):
    self['tail'] = value
    return None


def tail_get(self):
    return self['tail']


############### Property Group ########################

class WirelessPropertyGroup(PropertyGroup):

    """These are the properties hold by objects.

    """
    wrls_status: EnumProperty(
        name='Status',
        default='UNDEFINED',
        items=status_items
        )
    enable: BoolProperty(
        default=False,
        description="Enable Wireless",
        update=toggle_wireless
        )

    curve: StringProperty(
        name='Curve',
        description='The curve object',
        default='None',
        update=curve_update,
        set=curve_set,
        get=curve_get
        )

    cable: StringProperty(
        name='Cable',
        description='The cable object',
        default='None',
        update=cable_update,
        set=cable_set,
        get=cable_get
        )
    head: StringProperty(
        name='Head',
        description='The head object',
        default='None',
        update=head_update,
        set=head_set,
        get=head_get
        )

    tail: StringProperty(
        name='Tail',
        description='The tail object',
        default='None',
        update=tail_update,
        set=tail_set,
        get=tail_get
        )
    use_head: BoolProperty(
        default=False,
        description="Use head end cap",
        update=toggle_head_end_cap
        )
    use_tail: BoolProperty(
        default=False,
        description="Use tail end cap",
        update=toggle_tail_end_cap
        )
    cable_thickness: FloatProperty(
        name="Cable thickness",
        description="Set the Cable thickness",
        default=1.0,
        min=0.001,
        max=100.0,
        soft_min=0.01,
        soft_max=10.0,
        update=update_cable_thickness
        )
    old_c_thickness: FloatProperty(
        name="Old thickness",
        description="",
        default=1.0
        )
    # cable_x stores the x size of the cable without modifiers (used for the head translation)
    cable_x: FloatProperty(
        name="cable_x",
        description="",
        default=0.01
        )
    head_use_cable_mat: BoolProperty(
        name="hea use cable material",
        description="",
        default=False,
        update=head_use_cable_mat_toggle
        )
    tail_use_cable_mat: BoolProperty(
        name="tail use cable material",
        description="",
        default=False,
        update=tail_use_cable_mat_toggle
        )
    old_cable_stretch: FloatProperty(
        name="Cable Stretch",
        description="",
        default=1.0
        )
    cable_stretch: FloatProperty(
        name="Cable Stretch",
        description="",
        default=1.0,
        min=0.1,
        max=20.0,
        soft_min=0.1,
        soft_max=10.0,
        update=update_cable_stretch
        )
    cable_original_x: FloatProperty(
        name="Cable Original X",
        description=""
        )
    head_updated: BoolProperty(
        name="head is updated",
        description="",
        default=False
        )
    old_head_slide: FloatProperty(
        name="Cable Stretch",
        description="",
        default=0
        )
    head_slide: FloatProperty(
        name="Head Slide",
        description="",
        default=0,
        min=-2,
        max=2,
        soft_min=-1.0,
        soft_max=1.0,
        update=update_head_slide
        )
    has_thumb: BoolProperty(
        name='part has thumbnail',
        description='',
        default=False)
    array_offset: FloatProperty(
        name="Offset",
        description="",
        default=1,
        min=0,
        max=100,
        soft_min=-0,
        soft_max=1
        )


class WirelessSettingsPropertyGroup(PropertyGroup):

    """These are settings properties, hold by window_manager

    """

    cables_types: bpy.props.EnumProperty(
        name="Cable types",
        description="Choose your cable",
        items=cable_preview_items,
        update=cable_preview_update
        )
    head_types: bpy.props.EnumProperty(
        name="Head types",
        description="Choose the head endcap",
        items=head_preview_items,
        update=head_preview_update
        )
    tail_types: bpy.props.EnumProperty(
        name="Tail types",
        description="Choose the tail endcap",
        items=tail_preview_items,
        update=tail_preview_update
        )
    cable_categories: bpy.props.EnumProperty(
        name='Cable Categories',
        description='Select category for the cable',
        items=cable_categories_items,
        update=cable_categories_update
        )

    head_categories: bpy.props.EnumProperty(
        name='Head Categories',
        description='Select category for the head',
        items=head_categories_items,
        update=head_categories_update
        )
    tail_categories: bpy.props.EnumProperty(
        name='Tail Categories',
        description='Select category for the tail',
        items=tail_categories_items,
        update=tail_categories_update
        )
    type_of_part: bpy.props.EnumProperty(
        name='Type of new element',
        description='What type of elemnt it is? Cable or Head/Tail?',
        items=[('Cable', 'Cable', 'Cable'),
               ('Head / Tail', 'Head / Tail', 'Head / Tail')],
        update=type_of_new_part
        )
    new_cable_category: bpy.props.EnumProperty(
        name="New Cable Category",
        description="What category this cable is part of?",
        items=cable_categories_items,
        update=cable_categories_update
        )
    new_items: bpy.props.EnumProperty(
        name="New Parts",
        description="Do you like it?",
        items=new_part_preview_items,
        update=new_part_update
        )
    new_item_categories: bpy.props.EnumProperty(
        name='New_item Categories',
        description='Select category for new items',
        items=new_item_categories_items,
        update=tail_categories_update
        )
    new_item_offset: FloatProperty(
        name="Offset",
        description="",
        default=1,
        min=0,
        max=100,
        soft_min=-0,
        soft_max=1
        # update=update_head_slide
        )
    custom_parts: bpy.props.EnumProperty(
        name='Custom parts',
        description='Select custom part to edit',
        items=custom_part_preview_items,
        update=new_part_update
        )

def register():
    """Register here"""

    load_thumbs()

    bpy.utils.register_class(WirelessPropertyGroup)
    bpy.types.Object.wrls =  PointerProperty(type=WirelessPropertyGroup)

    bpy.utils.register_class(WirelessSettingsPropertyGroup)
    bpy.types.WindowManager.wrls = PointerProperty(
        type=WirelessSettingsPropertyGroup)



def unregister():
    """Unregister here:"""
    classes = (WirelessPropertyGroup,
            WirelessSettingsPropertyGroup,
            )

    for clss in reversed(classes):
        bpy.utils.unregister_class(clss)

    del bpy.types.Object.wrls
    del bpy.types.WindowManager.wrls

    for pcoll in configs.thumbs.values():
        bpy.utils.previews.remove(pcoll)
    configs.thumbs.clear()
