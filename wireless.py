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
log.setLevel(logging.DEBUG)


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
    log.debug("My new imported model is %s" % my_model)

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
            clean_obsolete_materials(extrem)
            bpy.data.objects.remove(extrem, do_unlink=True)

    for child in children:
        if child is not None:
            clean_obsolete_materials(child)
            bpy.data.objects.remove(child, do_unlink=True)



def get_list_and_position(context, list_name):
    """search for the list_name list in the configs.json
    and also find the position on the list of the corrispective context value
    for example: if I want to look for the head_types I will get the head_types list and 
    the position of the wrls.heads_types in that list

    Args:
        context - the bpy.context
        list_name (str (never None)) - the name of the list to look in
    Return:
        list containing the list_name list and the position of the list_name attribute in it
        example [list_name, 2] 
    """
    wrls = context.window_manager.wrls
    current = getattr(wrls, list_name)
    cables_list = configs.data["model_types"][list_name]
    current_pos = [i for i, x in enumerate(cables_list) if x == current]
    log.debug("get_list_and_position current_pos: %s" %current_pos)

    return [cables_list, current_pos]

def get_prev_item(context, list_name):
    """Read the list_name list and set the wrls.list_name attribute to the previous value

    Args:
        context - the bpy.caontext
        list_name (str(never None)) -the name of the list to look in

    Return:
        None
    """
    list_pos = get_list_and_position(context, list_name)

    items_list = list_pos[0]
    current_pos = list_pos[1]
    wrls = bpy.context.window_manager.wrls

    if current_pos == [0]:
        new_pos = len(items_list) - 1
        setattr(wrls, list_name, items_list[new_pos])

    else:
        new_pos = current_pos[0] - 1
        setattr(wrls, list_name, items_list[new_pos])

def get_next_item(context, list_name):
    """Read the list_name list and set the wrls.list_name attribute to the next value

    Args:
        context - the bpy.caontext
        list_name (str(never None)) -the name of the list to look in

    Return:
        None
    """

    list_pos = get_list_and_position(context, list_name)

    items_list = list_pos[0]
    current_pos = list_pos[1]
    wrls = context.window_manager.wrls

    if current_pos == [len(items_list) - 1]:
        new_pos = 0
        setattr(wrls, list_name, items_list[new_pos])

    else:
        new_pos = current_pos[0] + 1
        setattr(wrls, list_name, items_list[new_pos])


def find_part(a_object, part='CABLE'):
    """Find the part object within the wireless "group" of the selected object
    The active object but the active object might be the curve.

    Args:
        a_object - (bpy.Object(never None)) - the serched object
        part (str(never None)) (default 'CABLE') - part that we need to look for

    Return
        bpyObject - the part object declared in the part argument
     """

    data_obj = bpy.data.objects
    if a_object.wrls.wrls_status == 'CABLE':
        cable = a_object

    else:
        # this is the curve, we have to get to the cable
        for child in a_object.children:
            if child.wrls.wrls_status == 'CABLE':
                cable = child
                break

    log.debug("found_part child: %s" %cable)
    cable = bpy.data.objects[cable.name]
    try:
        head_name = cable.modifiers["WRLS_Array"].end_cap.name
        head = data_obj[head_name]
        log.debug("find_part head is: %s" %head)
    except:
        log.debug("head not found POOOOOOOOOOOOOOOP")
        head = None
    try:
        tail_name = cable.modifiers["WRLS_Array"].start_cap.name
        tail = data_obj[tail_name]
    except:
        log.debug("TAIL not found AAAAAAAAAAAAAAAAARRRRRRGH!")
        tail = None

    curve = cable.parent

    if part == 'HEAD':
        if head:
            log.debug("find_part has found a head: %s" %head)
            return head
        else:
            return None
    elif part == 'TAIL':
        if tail:
            log.debug("find_part has found a tail: %s" %tail.name)
            return tail
        else:
            return None

    elif part == 'CURVE':
        log.debug("find_part has found a curve %s" %curve.name)
        return curve

    else:
        log.debug("find_part has found a cable")
        return cable


def clean_obsolete_materials(obj):
    """Look trough the materials used by the obj object and if they have only one user
    get rid of them

    Args:
        obj (bpy Object(never None)) - the target object where to look for materials

    Return:
        None
    """
    count = 0
    for slot in obj.material_slots:
        material = slot.material
        if bpy.data.materials[material.name].users == 1:
            count += 1
            bpy.data.materials.remove(material, do_unlink=True)

    log.info("Removed %s obsolete material(s) used by %s" % (count, obj.name))
    node_count = 0
    for node_tree in bpy.data.node_groups:
        if node_tree.users == 0:
            node_count += 1
            bpy.data.node_groups.remove(node_tree, do_unlink=True)
    log.info("Removed %s obsolete node group(s)" %node_count)

def connect_head(cable, head):
    """Import and connect the head object to the cable object,
    set it as end cap to the array modifier
    and link it to the scene, set to hidden and hide_render

    Args:
        cable (bpy Object (never None) -the mesh object to which the heada is attached
        head (bpy Object (never None)) the mesh object to be set as head
    """
    head_model = import_model(head)

    cable.modifiers["WRLS_Array"].end_cap = head_model

    bpy.context.scene.objects.link(head_model)
    # mirror to orient the head in the right direction
    mirror_head(head_model.name)

    head_model.hide = True
    head_model.hide_render = True
    head_model.wrls.wrls_status = 'HEAD'
    head_model.parent = cable.parent

def connect_tail(cable, tail):
    """Import and connect the tail object to the cable object,
    set it as end cap to the array modifier
    and link it to the scene, set to hidden and hide_render

    Args:
        cable (bpy Object (never None) -the mesh object to which the heada is attached
        tail (bpy Object (never None)) the mesh object to be set as tail
    """
    tail_model = import_model(tail)

    cable.modifiers["WRLS_Array"].start_cap = tail_model

    bpy.context.scene.objects.link(tail_model)
    # mirror to orient the tail in the right direction

    tail_model.hide = True
    tail_model.hide_render = True
    tail_model.wrls.wrls_status = 'TAIL'
    tail_model.parent = cable.parent

############## OPERATORS ###############################

class OBJECT_OT_Cable_Previous(bpy.types.Operator):

    """Load the previous cable type.

    """

    bl_idname = "wrls.cable_prev"
    bl_label = "Previous Cable type"

    def execute(self, context):


        get_prev_item(context, "cables_types")
        # list_pos = get_list_and_position(context, "cable_types")

        # cables_list = list_pos[0]
        # current_pos = list_pos[1]

        # if current_pos == [0]:
        #     new_pos = len(cables_list) - 1
        #     bpy.context.window_manager.wrls.cables_types = cables_list[new_pos]

        # else:
        #     new_pos = current_pos[0] - 1
        #     bpy.context.window_manager.wrls.cables_types = cables_list[new_pos]


        return {'FINISHED'}

class OBJECT_OT_Cable_Next(bpy.types.Operator):

    """Load the next cable type.

    """

    bl_idname = "wrls.cable_next"
    bl_label = "Next Cable type"

    def execute(self, context):

        get_next_item(context, "cables_types")

        # list_pos = get_list_and_position(context, 'cable_types')

        # cables_list = list_pos[0]
        # current_pos = list_pos[1]

        # if current_pos == [len(cables_list) - 1]:
        #     new_pos = 0
        #     bpy.context.window_manager.wrls.cables_types = cables_list[new_pos]

        # else:
        #     new_pos = current_pos[0] + 1
        #     bpy.context.window_manager.wrls.cables_types = cables_list[new_pos]

        return {'FINISHED'}

class OBJECT_OT_Head_Next(bpy.types.Operator):

    """Load the next head type.
    """
    bl_idname = "wrls.head_next"
    bl_label = "Next head type"

    def execute(self, context):
        get_next_item(context, "head_types")
        # list_pos = get_list_and_position(context, 'head_types')

        # cables_list = list_pos[0]
        # current_pos = list_pos[1]

        # if current_pos == [len(cables_list) - 1]:
        #     new_pos = 0
        #     bpy.context.window_manager.wrls.cables_types = cables_list[new_pos]

        # else:
        #     new_pos = current_pos[0] + 1
        #     bpy.context.window_manager.wrls.cables_types = cables_list[new_pos]

        return {'FINISHED'}

class OBJECT_OT_Head_Prev(bpy.types.Operator):

    """Load the prevoius head type.
    """
    bl_idname = "wrls.head_prev"
    bl_label = "Previous head type"

    def execute(self, context):
        get_prev_item(context, "head_types")

        return {'FINISHED'} 

def register():
    "register"
   

def unregister():
   "unregister"