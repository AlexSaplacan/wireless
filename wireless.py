# ##############################
# wireless.py
# ##############################

import bpy
import os
import logging

import bmesh

from . import configs


# logging setup
log = logging.getLogger('wrls.wireless')
# log.setLevel(logging.DEBUG)


def get_is_undefined_curve(context):
    """
    Check if the selected object is a curve and if has wrls_status UNDEFINED.

    Args:
        context - required by bpy

    Return
        bool - True if the curve has wrls_status "UNDEFINED", else False
    """
    s_obj = context.active_object
    return bool(s_obj.type == 'CURVE' and s_obj.wrls.wrls_status == 'UNDEFINED')

def set_wrls_status(context, obj_name, value):
    """
    Turn the wrls_status of the object with obj_name to the value
    Args:
        context - required by bpy
        obj_name (str(never None)) - the name of the object, never None
        value (str(never None)) - predefined value, enum in
                                ['UNDEFINED', 'CURVE', 'CABLE', 'HEAD', 'TAIL']

    Returns
        None
    """
    bpy.data.objects[obj_name].wrls.wrls_status = value
    log.debug("wrls_status of %s changed to %s" % (obj_name, value))

def import_model(obj_name):
    """
    Look for the obj_name model into the assets an import it into blender data

    Args:
        obj_name (str(never None)) - the name of the blender object to be imported

    Return:
        (bpy object) - the imported object from the local data
    """
    models = configs.data["Models"]

    my_model = models[obj_name]["name"]
    model_file = models[obj_name]["blend"]
    log.debug("My model is %s" % my_model)

    file_path = os.path.join(os.path.dirname(__file__), "assets", model_file)
    if not os.path.exists(file_path):
        raise OSError()
    with bpy.data.libraries.load(file_path, link=False) as (data_from, data_to):
        if my_model in data_from.objects:
            data_to.objects.append(my_model)
        else:
            raise NameError("The object does not exists")

    return data_to.objects[0]


def mirror_head(obj_name):
    """
    Switch to edit mode and mirror all the vertices on x axis o the object
    is facing now the right way

    Args:
        obj_name (str(never None)) - the name of the bpy object that is going to be mirrored

    Return:
        None
    """
    a_object = bpy.context.active_object
    head_obj = bpy.data.objects[obj_name]
    bpy.context.scene.objects.active = head_obj

    bpy.ops.object.editmode_toggle()
    mesh = bmesh.from_edit_mesh(bpy.context.object.data)
    for vert in mesh.verts:
        vert.co.x *= -1
    bpy.ops.object.editmode_toggle()
    bpy.context.scene.objects.active = a_object
def tail_and_head(obj):
    """
    Find the tail and head object names of the array modifier

    Args:
        obj (bpy object(never None)) - the object that is supposed to have a tail and a head

    Returns:
        None if no tail and head foud
        Array of strings containing the names of the head and/or tail objects
    """

    extrems = []
    array = obj.modifiers["WRLS_Array"]
    try:
        head = array.end_cap
        extrems.append(head)
    except:
        pass

    try:
        tail = array.start_cap
        extrems.append(tail)
    except:
        pass

    if len(extrems) > 0:
        return extrems

    else:
        return None

def wrls_off_and_delete_childs(curve):
    """
    Find all the children of the curve tha have wrls_status 'CABLE'
    and remove them from the scene

    Args:
        curve - (bpy object(never None)) - the curve object that is searched for children

    Return:
        None
    """
    children = []

    for child in curve.children:
        if child.wrls.wrls_status == 'CABLE':
            children.append(child)
            extrems = tail_and_head(child)
    log.debug("Extrems are: %s" %extrems)
    log.debug("Childs are: %s" % children)

    for extrem in extrems:
        if extrem is not None:
            bpy.data.objects[extrem.name].remove(extrem, do_unlink=True)

    for child in children:
        if child is not None:
            bpy.data.objects.remove(child, do_unlink=True)
                    
def get_cables_list_and_position(context):

    # get the actual cable type
    # a bodge up but untill I find how to inherit better can do the work
    current = context.window_manager.wrls.cables_types
    log.debug("Cable Previous OP current: %s" %current)
    

    cables_list = configs.data["model_types"]["Cable"]
    current_pos = [i for i, x in enumerate(cables_list) if x == current]
    log.debug("Cable Previous OP current_pos: %s" %current_pos)

    return [cables_list, current_pos]

def find_cable(a_object):
    """Return the cable object within the wireless "group" of the selected object
    The active object but the active object might be the curve.

    Args:
        object - (bpy.Object(never None)) - the serched object object
    
    Return
        bpyObject - the object that has wrls_status 'CABLE'
     """
    if a_object.wrls.wrls_status == 'CABLE':
        cable = a_object

    else:
        # this is the curve, we have to get to the cable
        for child in a_object.children:
            if child.wrls.wrls_status == 'CABLE':
                cable = child
                break

    return cable
############## OPERATORS ###############################

class OBJECT_OT_InitCable(bpy.types.Operator):

    """Put a cable on selected wire.

    """

    bl_idname = "wrls.wrls_init"
    bl_label = "Create Cable"

    @classmethod
    def pool(cls, context):
        """Don't run this unless it's a curve object"""
        return context.active_object.type != 'CURVE'

    def execute(self, context):
        """Create the cable for the firs time"""
        # If the curve is already not set as undefined get this message
        if get_is_undefined_curve(context) is False:
            log.debug("This curve is already cable.")

        else:
            curve = context.active_object
            log.debug("This is an undefined curve, doing something.")
            obj_name = curve.name
            set_wrls_status(context, obj_name, 'CURVE')

            # we use the config.data to load the first thumb
            first_cable = bpy.context.window_manager.wrls.cables_types

            log.debug("OBJECT_OT_InitCable- cable_name is: %s" %first_cable)
            cable_shape = import_model(first_cable)
            set_wrls_status(context, cable_shape.name, 'CABLE')
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


        return {'FINISHED'}

class OBJECT_OT_RemoveCable(bpy.types.Operator):

    """Turn off cable and reset.

    """
    bl_idname = "wrls.cable_unset"
    bl_label = "Remove Cable"

    def execute(self, context):

        cable = context.active_object
        wrls_status = cable.wrls.wrls_status

        if wrls_status == 'CURVE':
            wrls_off_and_delete_childs(cable)
        elif wrls_status == 'CABLE':
            cable = cable.parent
            cable.select = True
            # make active the curve so doesn't return error on wireless_ui
            # context.scene.objects.active =  bpy.data.objects[cable.name]
            wrls_off_and_delete_childs(cable)
            configs.switch = True
            cable.wrls.enable = False
            configs.switch = False
        else:
            log.debug("This should not happen.")
        cable.wrls.wrls_status = 'UNDEFINED'

        return {'FINISHED'}

# class OBJECT_OT_Cable_Arrows(bpy.types.Operator):

#     # get the actual cable type
#     current = bpy.context.window_manager.wrls.cables_types

#     cables_list = configs.data["model_types"]["Cable"]
#     current_pos = [i for i, x in enumerate(cables_list) if x == current]
#     log.debug("Cable Previous OP current_pos: %s" %current_pos)

#     def execute(self, context):

#         return {'FINISHED'}


class OBJECT_OT_Cable_Previous(bpy.types.Operator):

    """Load the previous cable type.

    """

    bl_idname = "wrls.cable_prev"
    bl_label = "Previous Cable type"

    def execute(self, context):

        list_pos = get_cables_list_and_position(context)

        cables_list = list_pos[0]
        current_pos = list_pos[1]

        if current_pos == [0]:
            new_pos = len(cables_list) - 1
            bpy.context.window_manager.wrls.cables_types = cables_list[new_pos]

        else:
            new_pos = current_pos[0] - 1
            bpy.context.window_manager.wrls.cables_types = cables_list[new_pos]


        return {'FINISHED'}

class OBJECT_OT_Cable_Next(bpy.types.Operator):
    """Load the next cable type.

    """

    bl_idname = "wrls.cable_next"
    bl_label = "Next Cable type"

    def execute(self, context):

        list_pos = get_cables_list_and_position(context)

        cables_list = list_pos[0]
        current_pos = list_pos[1]

        if current_pos == [len(cables_list) - 1]:
            new_pos = 0
            bpy.context.window_manager.wrls.cables_types = cables_list[new_pos]

        else:
            new_pos = current_pos[0] + 1
            bpy.context.window_manager.wrls.cables_types = cables_list[new_pos]

        return {'FINISHED'}

class OBJECT_OT_Init_Head(bpy.types.Operator):

    """Use a head endcap.

    """

    bl_idname = "wrls.use_head"
    bl_label = "Use head end"

    def execute(self, context):
        a_object = context.active_object
        first_head = context.window_manager.wrls.head_types
        cable = find_cable(a_object)

        head_model = import_model(first_head)

        cable.modifiers["WRLS_Array"].end_cap = head_model

        context.scene.objects.link(head_model)
        mirror_head(head_model.name)
        bpy.data.objects[head_model.name].hide = True
        bpy.data.objects[head_model.name].hide_render = True

        return {'FINISHED'}

def register():
    "register"
   

def unregister():
   "unregister"