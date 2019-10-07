# ##############################
# wireless.py
# ##############################

import bpy
import os
import shutil
import logging
import json
import numpy as np
import datetime

import bmesh

from . import configs
from . import wireless_props

# logging setup
log = logging.getLogger('wrls.wireless')
log.setLevel(logging.INFO)


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

    Return
        None
    """
    bpy.data.objects[obj_name].wrls.wrls_status = value
    log.debug("wrls_status of %s changed to %s" % (obj_name, value))


def set_wrls_collection():
    if 'WrlS' in bpy.data.collections:
        return bpy.data.collections['WrlS']
    else:
        wrls_coll = bpy.data.collections.new('WrlS')
        master_coll = bpy.context.scene.collection
        master_coll.children.link(wrls_coll)


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
    new_model = data_to.objects[0]
    if 'offset' in models[obj_name]:
        new_model.wrls.array_offset = models[obj_name]['offset']
    return new_model


def setup_studio_scene():
    """
    Append the studio scene.
    """

    studio_path = os.path.join(os.path.dirname(__file__), 'assets', 'Studio.blend')

    with bpy.data.libraries.load(studio_path, link=False) as (data_from, data_to):
        if 'Studio Scene' in data_from.scenes:
            data_to.scenes.append('Studio Scene')
        else:
            raise NameError("Scene does not exist")

    # bpy.context.window.screen.scene = bpy.data.scenes['Studio Scene']
    studio_scene = bpy.data.scenes['Studio Scene']
    bpy.context.window.scene = studio_scene


def get_co(mesh):
    v_count = len(mesh.vertices)
    co = np.zeros(v_count * 3, dtype=np.float32)
    mesh.vertices.foreach_get('co', co)
    co.shape = (v_count, 3)
    return co


def mirror_and_translate_head():
    """
    Scale the head's verts on x and y by -1
    """

    a_object = bpy.context.active_object
    curve, cable, head, tail = find_parts(a_object)

    head_co = get_co(head.data)

    head_co[:, :2] *= -1

    head.data.vertices.foreach_set('co', head_co.ravel())
    head.data.update()


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

def wrls_off_and_delete_children(curve):
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



def get_list_and_position(context, list_name, part_type):
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
    wm_wrls = context.window_manager.wrls
    part_types = {'cables_types': 'cable_categories',
                  'head_types': 'head_categories',
                  'tail_types': 'tail_categories',
                  'custom_parts': 'Custom Parts'

    }
    try:
        category = getattr(wm_wrls, part_types[part_type])
    except:
        category = part_types[part_type]
    cables_list = configs.data["model_types"][category]
    current = list_name
    current_pos = [i for i, x in enumerate(cables_list) if x == current]
    log.debug("get_list_and_position current_pos: %s, list : %s" %(current_pos, cables_list))

    return [cables_list, current_pos]

def get_prev_item(context, list_name, part_type):
    """Read the list_name list and set the wrls.list_name attribute to the previous value

    Args:
        context - the bpy.caontext
        list_name (str(never None)) -the name of the list to look in

    Return:
        None
    """
    list_pos = get_list_and_position(context, list_name, part_type)

    items_list = list_pos[0]
    current_pos = list_pos[1]
    wrls = bpy.context.window_manager.wrls

    if current_pos == [0]:
        new_pos = len(items_list) - 1
        setattr(wrls, part_type, items_list[new_pos])

    else:
        new_pos = current_pos[0] - 1
        setattr(wrls, part_type, items_list[new_pos])

def get_next_item(context, list_name, part_type):
    """Read the list_name list and set the wrls.list_name attribute to the next value

    Args:
        context - the bpy.context
        list_name (bpy Enum Property -the name of the list to look in
        part_type (str) -the string name of the list-name

    Return:
        None
    """

    list_pos = get_list_and_position(context, list_name, part_type)

    items_list = list_pos[0]
    current_pos = list_pos[1]
    wrls = context.window_manager.wrls
    log.debug('list_name is %s' %list_name)

    if current_pos == [len(items_list) - 1]:
        new_pos = 0
        setattr(wrls, part_type, items_list[new_pos])

    else:
        new_pos = current_pos[0] + 1
        # wrls.list_name = items_list[new_pos]
        setattr(wrls, part_type, items_list[new_pos])


def find_parts(a_object):
    """Find all the objects within the wireless "group" of a_object and put them in a list

    Args:
        a_object - (bpy.Object(never None)) - the serched object

    Return
        list of bpy Objects (4) containing [Curve, Cable, Head, Tail].
        if any of this don't exits, it's replaced with 'None'
    """

    data_obj = bpy.data.objects

    if a_object.wrls.wrls_status == 'CURVE':
        # this is the curve
        curve = data_obj[a_object.name]

        # now let's check out if a cable exists
        cable = None
        for child in curve.children:
            if child.wrls.wrls_status == 'CABLE':
                cable = child
                break
    else:
        # this is the cable
        cable = data_obj[a_object.name]
        curve = cable.parent

    # head and tail
    head, tail = None, None

    if cable is not None:
        head = cable.modifiers['WRLS_Array'].end_cap
        tail = cable.modifiers['WRLS_Array'].start_cap

    wrls_group = [curve, cable, head, tail]
    log.debug("Elements found: %s" %wrls_group)

    return wrls_group


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
        if slot.material is not None:
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
    and link it to the scene, set to hidden and hide_render, setup materials

    Args:
        cable (bpy Object (never None) -the mesh object to which the heada is attached
        head (bpy Object (never None)) the mesh object to be set as head
    """
    head_model = import_model(head)
    head_model.wrls.wrls_status = 'HEAD'
    # materials setup for the head
    setup_materials(cable, head_model)
    cable.modifiers["WRLS_Array"].end_cap = head_model
    bpy.context.scene.collection.children['WrlS'].objects.link(head_model)
    # mirror to orient the head in the right direction
    mirror_and_translate_head()

    head_model.hide_viewport = True
    head_model.hide_render = True
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
    tail_model.wrls.wrls_status = 'TAIL'
    bpy.context.scene.collection.children['WrlS'].objects.link(tail_model)
    setup_materials(cable, tail_model, False)
    cable.modifiers["WRLS_Array"].start_cap = tail_model
    # mirror to orient the tail in the right direction

    tail_model.hide_viewport = True
    tail_model.hide_render = True
    tail_model.parent = cable.parent


def setup_materials(cable, cap, is_head=True):
    """Adjust the materials of the cable in such way that the extremity cap has
    the material on it.

    Args:
        cable  bpyObject (notNone) - the cable object
        cap  bpyObject(not None) - the extremity (can be either the tail or the head)
        position (bool) default True -  if True, the function affects the head materials,
        otherwire the tail
    """
    if is_head:
        if not cable.wrls.head_use_cable_mat:
            for idx, slot in enumerate(cap.material_slots):
                if idx >= 1 and idx <= 3:
                    cable.material_slots[idx].material = slot.material

        else:
            cable_mat = cable.material_slots[0].material
            cable.material_slots[1].material = cable_mat
    else:
        # this is a tail
        # we need first to assign diferent material slots to the tail obhect.
        # vertices from slot 1 will be assigned to 4, 2 --> 5 and 3 --> 6

        # first make sure we're not on editmode
        a_object = bpy.context.active_object
        if  a_object.data.is_editmode:
            bpy.ops.object.editmode_toggle()

        # now perform stuff on the tail
        cap.select_set(True)
        cap.hide_viewport = False
        bpy.context.view_layer.objects.active = cap
        bpy.ops.object.editmode_toggle()

        # safty check... how many material slots we have?
        existig_slots_n = len(cap.material_slots)
        log.debug("%s has %s slot materials" % (cap.name, existig_slots_n))
        # add the missing ones
        count = 0
        for i in range(7 - existig_slots_n):
            bpy.ops.object.material_slot_add()
            count += 1
        log.debug("I have added %s slot materials" % count)
        # assign verts 3 slots forward
        for i in range(1, 4):
            bpy.ops.mesh.select_all(action='DESELECT')
            cap.active_material_index = i
            bpy.ops.object.material_slot_select()
            cap.active_material_index = i + 3
            bpy.ops.object.material_slot_assign()
            cable.material_slots[i + 3].material = cap.material_slots[i].material

        bpy.ops.object.editmode_toggle()
        cap.hide_viewport = True
        # now check if to use the cable material
        if cable.wrls.tail_use_cable_mat:
            cable.material_slots[4].material = cable.material_slots[0].material
        a_object.select_set(True)
        bpy.context.view_layer.objects.active = a_object


def add_cable_modifiers(cable, curve):
    """
    Puts on the array and curve modifiers on the cable object

    Args:
        cable - the cable mest
        curve - the curve to follow
    """

    wrls_array = cable.modifiers.new(type='ARRAY', name="WRLS_Array")
    wrls_array.curve = curve
    wrls_array.fit_type = 'FIT_CURVE'
    wrls_array.use_merge_vertices = True
    wrls_array.merge_threshold = 0.0001
    wrls_array.relative_offset_displace[0] = cable.wrls.array_offset

    wrls_curve = cable.modifiers.new(name='WRLS_Curve', type='CURVE')
    wrls_curve.object = curve


def measure_curve():
    """
    Duplicates the curve, convert it to mesh and add all segments lenghts.
    Delete the object at the end.

    Return:
        Float - the Length of the curve

    """
    a_object = bpy.context.active_object
    scene = bpy.context.scene
    curve = find_parts(a_object)[0]

    scene.objects.active = curve
    mesh = curve.to_mesh(scene=scene, apply_modifiers=True, settings='PREVIEW')

    bm = bmesh.new()
    bm.from_mesh(mesh, face_normals=True, use_shape_key=True)

    length = 0
    for edge in bm.edges:
        length += edge.calc_length()

    bpy.data.meshes.remove(mesh, do_unlink=True)
    bm.free()

    bpy.ops.object.modifier_remove(modifier='WRLS_Measure_Subsuf')
    return length


def update_wrls_data(element, property_name, value):
    """
    Update the property on all other members of the cable group

    """
    elements = find_parts(element)
    for part in elements:
        if part is None:
            continue
        setattr(part.wrls, property_name, value)
        log.debug("Property set: %s = %s" %(property_name, value))


def camera_step_back():
    """
    Step back by a certain percentage of the distance
    between camera and dummy
    """

    camera = bpy.data.scenes['Studio Scene'].camera
    dummy = bpy.data.objects['WRLS_dummy_mesh']
    distance = dummy.location[1] - camera.location[1]
    camera.location[1] -= distance * 0.13


def convert_new_model_name(obj_name):
    """
    Add "WRLS_" prefix and replace spases with "_"
    """
    new_name = 'WRLS_' + obj_name.replace(' ', '_')
    return new_name


def add_to_category(obj, data):
    """
    Add the object name to All Cables or head_types
    and All Heads and Tails depending on the type_of_part
    """
    wm_wrls = bpy.context.window_manager.wrls
    is_cable = bool(wm_wrls.type_of_part == 'Cable')


    if is_cable:
        data['model_types']['All Cables'].append(obj.name)
        if wm_wrls.cable_categories != 'All Cables':
            data['model_types'][wm_wrls.cable_categories].append(obj.name)

    else:
        data['model_types']['head_types'].append(obj.name)
        data['model_types']['All Heads and Tails'].append(obj.name)
        if wm_wrls.head_categories != 'All Heads and Tails':
            data['model_types'][wm_wrls.head_categories].append(obj.name)


def add_thumb(obj, data):
    """
    Adds a new element to data['Thumbs']
    """
    img_name = convert_new_model_name(obj.name) + '.jpg'
    new_thumb = {'id': obj.name,
                 'img': img_name
                }
    data['Thumbs'].append(new_thumb)


def add_new_model(obj, data):
    """
    Add object's information to the data,
    so it can be used within the addon
    """
    wm_wrls = bpy.context.window_manager.wrls
    obj_name = obj.name
    new_obj_name = convert_new_model_name(obj_name)
    type_of_part = wm_wrls.type_of_part
    cable = True if type_of_part == 'Cable' else False

    obj_info = {'name': new_obj_name,
                'blend': obj_name + '.blend',
                'cable': cable}
    if cable:
        obj_info['offset'] = wm_wrls.new_item_offset

    data['Models'][obj_name] = obj_info
    add_to_category(obj, data)
    add_thumb(obj, data)

    data['model_types']['Custom Parts'].append(obj_name)

    return new_obj_name


def write_new_part_to_library():
    """
    Export the object to Custom_parts.blend
    """
    sel_objects = bpy.context.selected_objects
    actor_name = sel_objects[0].name
    new_name = convert_new_model_name(actor_name)
    bpy.data.objects[actor_name].name = new_name
    custom_filepath = os.path.join(os.path.dirname(__file__),
                                   'assets', actor_name + '.blend')

    if os.path.exists(custom_filepath):
        os.remove(custom_filepath)

    data_blocks = set(sel_objects)
    bpy.data.libraries.write(custom_filepath, data_blocks, fake_user=True)


def check_name_taken(obj):
    """
    Check if the name of the object already exists in the configs
    and return True or False
    """
    data = configs.data
    return bool(obj.name in data["Models"])

def error_in_material_slots(obj):
    """
    Check if the object has at max 1 matrial
    assigned to slot [0] if cable
    or if has maximum 3 materials assigned to
    slots [0-2] if head/tail

    Returns False if no error, or error message of first found
    """
    error = None
    type_of_part = bpy.context.window_manager.wrls.type_of_part

    if type_of_part == 'Cable':
        if len(obj.material_slots) > 1:
            for slot in obj.material_slots[1:]:
                if slot.material == None:
                    continue
                error = 'Found more than one material on cable {}'.format(obj.name)
                break

    if type_of_part == 'Head / Tail':
        if len(obj.material_slots) > 3:
            error = 'Max 3 materials allowed on Heads/Tails'

    return error

def update_material_slots(obj):
    """
    Setup the material slots to 7 material slots for the
    cable or add new material slots up to 4 and move the assigned
    materials one slot up for each of them
    """
    type_of_part = bpy.context.window_manager.wrls.type_of_part
    if type_of_part == 'Cable':
        n_slots = len(obj.material_slots)
        for i in range(7 - n_slots):
            bpy.ops.object.material_slot_add()

    if type_of_part == 'Head / Tail':
        mats = [obj.material_slots[i].material for i in range(len(obj.material_slots))]
        n_slots = len(obj.material_slots)
        for i in range(4 - n_slots):
            bpy.ops.object.material_slot_add()

        # reassign verts to slots
        if not obj.data.is_editmode:
            bpy.ops.object.editmode_toggle()
        for i in range(2, -1, -1):
            bpy.ops.mesh.select_all(action='DESELECT')
            obj.active_material_index = i
            bpy.ops.object.material_slot_select()
            obj.active_material_index = i + 1
            bpy.ops.object.material_slot_assign()
            obj.material_slots[i + 1].material = obj.material_slots[i].material

        # for i in range(len(mats)):
        #     obj.material_slots[i + 1].material = mats[i]

        bpy.ops.object.editmode_toggle()
        obj.material_slots[0].material = None

def reset_material_slots(obj):

    type_of_part = bpy.context.window_manager.wrls.type_of_part
    if type_of_part == 'Head / Tail':
        mats = [obj.material_slots[i].material for i in range(len(obj.material_slots))]
        if not obj.data.is_editmode:
            bpy.ops.object.editmode_toggle()
        for i in range(1, 4):
            bpy.ops.mesh.select_all(action='DESELECT')
            obj.active_material_index = i
            bpy.ops.object.material_slot_select()
            obj.active_material_index = i - 1
            bpy.ops.object.material_slot_assign()
            obj.material_slots[i - 1].material = obj.material_slots[i].material
        bpy.ops.object.editmode_toggle()
        obj.active_material_index = 4
        bpy.ops.object.material_slot_remove()

def scale_thumb_curve(actor, guide_curve):
    ideal_thick = 0.004
    max_thick = max(actor.dimensions[1], actor.dimensions[2])
    factor = max_thick / ideal_thick
    guide_curve.scale = ((factor, factor, factor))


def delete_custom_part_data():
    data = configs.data
    custom_part = bpy.context.window_manager.wrls.custom_parts

    print (type(data['model_types']))

    for part_type, values in data['model_types'].items():
        data['model_types'][part_type] = [ x for x in values if x != custom_part]

    data['Models'].pop(custom_part)

    data['Thumbs'] = [thumb for thumb in data['Thumbs'] if thumb['id'] != custom_part]

def write_custom_data():
    data = configs.data
    c_data = data.copy()
    c_parts = c_data['model_types']['Custom Parts']
    log.debug(c_parts)
    c_data['Models'] = {k : c_data['Models'][k] for k in c_parts}
    log.debug(c_data['Models'])
    c_data['Thumbs'] = [x for x in c_data['Thumbs'] if x['id'] in c_parts]
    log.debug(c_data['Thumbs'])
    for cat in c_data['cable_categories'] + c_data['tail_categories']:
        if cat in c_data['model_types']:
            if any(v in c_data['model_types'][cat] for v in c_parts):
                c_cat = [v for v in c_data['model_types'][cat] if v in c_parts]
                c_data['model_types'][cat] = c_cat
                continue
            c_data['model_types'].pop(cat, None)

    log.debug(c_data)
    return c_data

def export_custom_parts(custom_data, dst_dir):

    loc_dir = os.path.dirname(__file__)
    dst_thumbs = os.path.join(dst_dir, 'thumbs')
    dst_assets = os.path.join(dst_dir, 'assets')
    os.mkdir(dst_thumbs)
    os.mkdir(dst_assets)

    for thumb in custom_data['Thumbs']:
        img = thumb['img']
        src = os.path.join(loc_dir, 'thumbs', img)
        dst = os.path.join(dst_thumbs, img)
        shutil.copyfile(src, dst)

    models = [v['blend'] for k, v in custom_data['Models'].items()]
    for model in models:
        src = os.path.join(loc_dir, 'assets', model)
        dst = os.path.join(dst_assets, model)
        shutil.copyfile(src, dst)


def get_custom_data_from_path(imp_path):
    """
    return json data for the custom_configs.json within imp_path
    """
    json_path = os.path.join(imp_path, 'custom_configs.json')

    try:
        with open(json_path) as data_file:
            c_data = json.load(data_file)
    except FileNotFoundError:

        err = 'Could not find custom_configs.json in %s. Aborting' % imp_path
        return err
    return c_data


def check_import_directory(imp_path):
    data = configs.data
    c_data = get_custom_data_from_path(imp_path)
    try:
        new_models = c_data['model_types']['Custom Parts']
    except KeyError:
        err = 'Could not find Custom Parts list. Aborting'
        return err
    log.debug(new_models)

    for model in new_models:
        if model in data['Models']:
            err = 'Model %s already in the wireless data. Aborting.' % model
            return err

        for item in c_data['Thumbs']:
            if item['id'] != model:
                continue
            img_name = item['img']
            img_src = os.path.join(imp_path, 'thumbs', img_name)
            log.debug(img_src)
            if os.path.isfile(img_src):
                continue
            err = 'Could not find thumbnail for %s. Aborting' % model
            return err
        blend = c_data['Models'][model]['blend']
        pkg_src = os.path.join(imp_path, 'assets', blend)
        if not os.path.isfile(pkg_src):
            err = 'Could not find package for %s. Aborting' % model
            return err
    return None

def import_parts(imp_path, c_data):

    dst_img = os.path.join(os.path.dirname(__file__), 'thumbs')
    dst_pkg = os.path.join(os.path.dirname(__file__), 'assets')
    new_models = c_data['model_types']['Custom Parts']
    for model in new_models:
        for item in c_data['Thumbs']:
            if item['id'] != model:
                continue
            img_name = item['img']
            src_img = os.path.join(imp_path, 'thumbs', img_name)
            log.info('Copying file from %s ---->>> %s' %(src_img, dst_img))
            shutil.copy(src_img, dst_img)
        src_pkg = os.path.join(imp_path, 'assets', c_data['Models'][model]['blend'])
        log.info('Copying file from %s ---->>> %s' %(src_pkg, dst_pkg))
        shutil.copy(src_pkg, dst_pkg)


def import_parts_data(c_data):

    data = configs.data
    new_models = c_data['model_types']['Custom Parts']
    for model in new_models:
        data['Models'][model] = c_data['Models'][model]
        for item in c_data['Thumbs']:
            if item['id'] != model:
                continue
            data['Thumbs'].append(item)

        for k, f in c_data['model_types'].items():
            if model not in c_data['model_types'][k]:
                continue
            data['model_types'][k].append(model)




############## OPERATORS ###############################

class OBJECT_OT_Cable_Previous(bpy.types.Operator):

    """Load the previous cable type.

    """

    bl_idname = "wrls.cable_prev"
    bl_label = "Previous Cable type"

    def execute(self, context):
        wm_wrls = bpy.context.window_manager.wrls

        get_prev_item(context, wm_wrls.cables_types, 'cables_types')


        return {'FINISHED'}


class OBJECT_OT_Cable_Next(bpy.types.Operator):

    """Load the next cable type.

    """

    bl_idname = "wrls.cable_next"
    bl_label = "Next Cable type"

    def execute(self, context):
        wm_wrls = bpy.context.window_manager.wrls

        get_next_item(context, wm_wrls.cables_types, 'cables_types')
        return {'FINISHED'}


class OBJECT_OT_Head_Next(bpy.types.Operator):

    """Load the next head type.
    """
    bl_idname = "wrls.head_next"
    bl_label = "Next head type"

    def execute(self, context):
        wm_wrls = bpy.context.window_manager.wrls
        get_next_item(context, wm_wrls.head_types, 'head_types')

        return {'FINISHED'}


class OBJECT_OT_Head_Prev(bpy.types.Operator):

    """Load the prevoius head type.
    """
    bl_idname = "wrls.head_prev"
    bl_label = "Previous head type"

    def execute(self, context):
        wm_wrls = bpy.context.window_manager.wrls
        get_prev_item(context, wm_wrls.head_types, 'head_types')

        return {'FINISHED'}


class OBJECT_OT_Tail_Next(bpy.types.Operator):

    """Load the next head type.
    """
    bl_idname = "wrls.tail_next"
    bl_label = "Next tail type"

    def execute(self, context):
        wm_wrls = bpy.context.window_manager.wrls
        get_next_item(context, wm_wrls.tail_types, 'tail_types')

        return {'FINISHED'}


class OBJECT_OT_Tail_Prev(bpy.types.Operator):

    """Load the prevoius head type.
    """
    bl_idname = "wrls.tail_prev"
    bl_label = "Previous tail type"

    def execute(self, context):
        wm_wrls = bpy.context.window_manager.wrls
        get_prev_item(context, wm_wrls.tail_types, 'tail_types')

        return {'FINISHED'}


class OBJECT_OT_Wireless_Apply(bpy.types.Operator):

    """Apply wireless modifiers and make the cable a normal object.
    """
    bl_idname = "wrls.apply_wrls"
    bl_label = "Apply wireless data"

    def execute(self, context):

        active_object = context.active_object

        curve, cable, head, tail = find_parts(active_object)

        context.scene.objects.active = cable

        # find WRLS modifiers and apply them
        for modifier in cable.modifiers:
            if modifier.name.startswith("WRLS"):
                bpy.ops.object.modifier_apply(modifier=modifier.name)

        # delete head and tail if they exist
        if head is not None:
            bpy.data.objects.remove(head, do_unlink=True)
        if tail is not None:
            bpy.data.objects.remove(tail, do_unlink=True)

        # cable now has no parent
        a_object = context.active_object
        a_object.select = True
        log.debug("Before_clear active object is %s" % a_object)
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

        # set WRLS status to UNDEFINED to cable and curve
        configs.switch = True
        bpy.ops.wm.properties_remove(data_path="object", property="wrls")
        context.scene.objects.active = curve
        bpy.ops.wm.properties_remove(data_path="object", property="wrls")
        configs.switch = False

        return {'FINISHED'}


class OBJECT_OT_Purge_Wireless(bpy.types.Operator):

    """Just in case something went wrong.
    """
    bl_idname = "wrls.purge_wrls"
    bl_label = "Purge wireless"

    def execute(self, context):
        active_object = context.active_object

        curve, cable, head, tail = find_parts(active_object)

        # delete head and tail if they exist
        if head is not None:
            bpy.data.objects.remove(head, do_unlink=True)
        if tail is not None:
            bpy.data.objects.remove(tail, do_unlink=True)

        # clear materials data and remove cable
        clean_obsolete_materials(cable)
        bpy.data.objects.remove(cable, do_unlink=True)

         # select the curve and set wrls_status to UNDEFINED
        context.view_layer.objects.active = curve
        curve.select_set(True)
        configs.switch = True
        bpy.ops.wm.properties_remove(data_path="object",
                                     property="wrls")
        configs.switch = False
        log.info("All wrls data cleaned.")

        return {'FINISHED'}


class OBJECT_OT_Prepare_Thumbnail(bpy.types.Operator):
    """
    Create a thumbnail of the object
    """
    bl_idname = "wrls.render_thumbnail"
    bl_label = "Render Thumbnail"

    def execute(self, context):
        curr_scene = bpy.context.scene
        actor_name = bpy.context.object.name
        actor = bpy.data.objects[actor_name]
        wm_wrls = context.window_manager.wrls
        new_part_type = wm_wrls.type_of_part


        # append scene
        setup_studio_scene()
        #link new object
        dummy = bpy.context.scene.objects['WRLS_dummy_mesh']
        guide_curve = bpy.context.scene.objects['WRLS_curve_guide']
        dummy.data = actor.data

        # if actor has subsurf modifier, add it to the dummy too
        for mod in actor.modifiers:
            if mod.type == 'SUBSURF':
                dummy.modifiers.new(type='SUBSURF', name='Subsurf')
                dummy.modifiers['Subsurf'].levels = mod.levels
        if new_part_type == 'Cable':
            # add array and curve modifiers
            scale_thumb_curve(actor, guide_curve)
            dummy.wrls.array_offset = wm_wrls.new_item_offset
            add_cable_modifiers(dummy, guide_curve)

        # scene_setup and render thumbnail
        thumb_name = 'WRLS_' + actor_name
        render_filepath = os.path.join(os.path.dirname(__file__), 'assets', thumb_name+'.jpg')
        bpy.data.scenes['Studio Scene'].render.filepath = render_filepath
        # zoom in and out
        bpy.ops.object.select_all(action='DESELECT')
        dummy.select_set(True)
        bpy.ops.view3d.camera_to_view_selected()
        camera_step_back()
        bpy.ops.render.render(write_still=True, scene='Studio Scene')


        # update the image
        preview_path = os.path.join(os.path.dirname(__file__), "thumbs", 'empty_thumb.jpg')
        shutil.move(render_filepath, preview_path)

        # delete scene (and cleanup)
        for obj in bpy.context.scene.objects:
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.scenes.remove(bpy.context.scene, do_unlink=True)

        configs.thumbs['cables'].clear()
        bpy.utils.previews.remove(configs.thumbs['cables'])
        wireless_props.load_thumbs()
        actor.wrls.has_thumb = True
        return {'FINISHED'}


class OBJECT_OT_Reset_Part(bpy.types.Operator):
    """
    Reset preview to original
    """
    bl_idname = "wrls.reset_part"
    bl_label = "Reset Part"

    def execute(self, context):
        """
        Loads of stuff going in here
        """
        actor_name = bpy.context.object.name
        actor = bpy.data.objects[actor_name]

        # for last put back the image where it was
        backup_thmb = os.path.join(os.path.dirname(__file__), "thumbs", 'empty_thumb_backup.jpg')
        empty_thumb = os.path.join(os.path.dirname(__file__), "thumbs", 'empty_thumb.jpg')
        shutil.copy(backup_thmb, empty_thumb)
        configs.thumbs['cables'].clear()
        bpy.utils.previews.remove(configs.thumbs['cables'])
        wireless_props.load_thumbs()
        actor.wrls.has_thumb = False

        return {'FINISHED'}


class OBJECT_OT_Save_Part(bpy.types.Operator):
    """
    Save the new wireless part
    """
    bl_idname = "wrls.save_part"
    bl_label = "Save Part"

    def execute(self, context):
        """
        Loads of stuff going in here
        """
        log.debug('Aim gonna save this part')
        actor_name = bpy.context.object.name
        actor = bpy.data.objects[actor_name]
        json_path = os.path.join(os.path.dirname(__file__), 'configs.json')
        new_name = add_new_model(actor, configs.data)
        update_material_slots(actor)
        actor.wrls.array_offset = bpy.context.window_manager.wrls.new_item_offset
        with open(json_path, 'w') as outfile:
            json.dump(configs.data, outfile, indent=4)
        write_new_part_to_library()
        reset_material_slots(actor)
        actor.name = actor_name

        # for last put back the image where it was and set the new one
        backup_thmb = os.path.join(os.path.dirname(__file__), "thumbs", 'empty_thumb_backup.jpg')
        empty_thumb = os.path.join(os.path.dirname(__file__), "thumbs", 'empty_thumb.jpg')
        new_thmb = os.path.join(os.path.dirname(__file__), "thumbs", new_name + '.jpg')

        shutil.copy(empty_thumb, new_thmb)
        shutil.copy(backup_thmb, empty_thumb)
        configs.thumbs['cables'].clear()
        bpy.utils.previews.remove(configs.thumbs['cables'])
        wireless_props.load_thumbs()

        return {'FINISHED'}

class OBJECT_OT_Delete_Part(bpy.types.Operator):
    """
    Save the new wireless part
    """
    bl_idname = "wrls.delete_custom_part"
    bl_label = "Delete Custom Part"

    def execute(self, context):
        """
        Clean data and delete custom part
        """
        custom_part = bpy.context.window_manager.wrls.custom_parts
        json_path = os.path.join(os.path.dirname(__file__), 'configs.json')

        delete_custom_part_data()
        with open(json_path, 'w') as outfile:
            json.dump(configs.data, outfile, indent=4)

        thumb_name = convert_new_model_name(custom_part) + '.jpg'
        thumb_path = os.path.join(os.path.dirname(__file__), "thumbs", thumb_name)
        lib_path = os.path.join(os.path.dirname(__file__), "assets", custom_part + '.blend')
        os.remove(thumb_path)
        os.remove(lib_path)

        return {'FINISHED'}

class OBJECT_OT_Custom_Next(bpy.types.Operator):

    """Load the next head type.
    """
    bl_idname = "wrls.custom_next"
    bl_label = "Next custom part."

    def execute(self, context):
        wm_wrls = bpy.context.window_manager.wrls
        get_next_item(context, wm_wrls.custom_parts, 'custom_parts')

        return {'FINISHED'}


class OBJECT_OT_Custom_Prev(bpy.types.Operator):

    """Load the prevoius custom part.
    """
    bl_idname = "wrls.custom_prev"
    bl_label = "Previous custom part."

    def execute(self, context):
        wm_wrls = bpy.context.window_manager.wrls
        get_prev_item(context, wm_wrls.custom_parts, 'custom_parts')

        return {'FINISHED'}

class OBJECT_OT_wireless_preferences_export_path(bpy.types.Operator):
    bl_idname = "wrls.preferences_export"
    bl_label = 'Export custom parts'

    def execute(self, context):
        preferences = context.preferences
        addon_preferences = preferences.addons[__package__].preferences
        exp_path = addon_preferences.exp_filepath
        now = datetime.datetime.now()
        dir_name = now.strftime("%y_%m_%d_wireless_custom_%f%S")
        c_dir_path = os.path.join(exp_path, dir_name)
        log.info('Trying to write custom data to %s' % c_dir_path)
        try:
            os.makedirs(c_dir_path)
        except PermissionError:
            err = 'Permission denied %s' % c_dir_path
            self.report({'ERROR'}, err)
            return {'FINISHED'}
        except NotADirectoryError:
            err = '%s is not a directory path' % exp_path
            self.report({'ERROR'}, err)
            return {'FINISHED'}

        c_data = write_custom_data()
        json_path = os.path.join(c_dir_path, 'custom_configs.json')

        with open(json_path, 'w') as outfile:
            json.dump(c_data, outfile, indent=4)

        export_custom_parts(c_data, c_dir_path)

        info = ("Exported successfuly to : %s" % exp_path)
        self.report({'INFO'}, info)
        print(info)

        return {'FINISHED'}

class OBJECT_OT_wireless_preferences_import(bpy.types.Operator):

    bl_idname = "wrls.preferences_import"
    bl_label = 'Import custom parts'

    def execute(self, context):

        data = configs.data
        preferences = context.preferences
        addon_preferences = preferences.addons[__package__].preferences
        imp_path = addon_preferences.imp_filepath

        log.info('checking directory for wireless data: %s' % imp_path)

        err = check_import_directory(imp_path)
        if err is not None:
            self.report({'ERROR'}, err)
            return {'FINISHED'}

        c_data = get_custom_data_from_path(imp_path)
        import_parts(imp_path, c_data)
        import_parts_data(c_data)

        json_path = os.path.join(os.path.dirname(__file__), 'configs.json')
        with open(json_path, 'w') as outfile:
            json.dump(data, outfile, indent=4)

        wireless_props.load_thumbs()
        self.report({'INFO'}, 'Package OK')

        return {'FINISHED'}

class DUMMY_OT(bpy.types.Operator):
    bl_idname = 'wrls.dummy_op'
    bl_label = 'do nothing'

    def execute(self, context):
        return {'FINISHED'}

classes = (
           OBJECT_OT_Cable_Previous,
           OBJECT_OT_Cable_Next,
           OBJECT_OT_Custom_Next,
           OBJECT_OT_Custom_Prev,
           OBJECT_OT_Delete_Part,
           OBJECT_OT_Head_Next,
           OBJECT_OT_Head_Prev,
           OBJECT_OT_Tail_Next,
           OBJECT_OT_Tail_Prev,
           OBJECT_OT_Prepare_Thumbnail,
           OBJECT_OT_Purge_Wireless,
           OBJECT_OT_Reset_Part,
           OBJECT_OT_Save_Part,
           OBJECT_OT_Wireless_Apply,
           OBJECT_OT_wireless_preferences_import,
           OBJECT_OT_wireless_preferences_export_path,
           DUMMY_OT
           )


def register():
    for clss in classes:
        bpy.utils.register_class(clss)
        'register'

def unregister():
    for clss in reversed(classes):
        bpy.utils.unregister_class(clss)
