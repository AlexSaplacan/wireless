# ##############################
# wireless.py
#
# Read a library of images

# Load the object for each image from the blend file
# Head for one side
# Tail for the other
#
# ##############################

import bpy
import os
import logging

import bmesh

from . import configs


log = logging.getLogger('wrls.wireless')
log.setLevel(logging.DEBUG)


def get_is_undefined_curve(context):
    """
    Check if the selected object is a curve and if has wrls_status UNDEFINED.

    Return bool
    """
    s_obj = context.active_object
    return bool(s_obj.type == 'CURVE' and s_obj.wrls.wrls_status == 'UNDEFINED')

def set_wrls_status(context, obj_name, value):
    """Turn the wrls_status of the object with obj_name to the value """
    bpy.data.objects[obj_name].wrls.wrls_status = value
    log.debug("wrls_status of %s changed to %s" % (obj_name, value))

def import_model(obj_name):
    """
    import the model obj_name from the relative assets blend file

    return object - bpyobject
    """
    models = configs.data["Models"]
    log.debug("models are %s" % models)
    
    my_model = models[0]["name"]
    model_file = models[0]["blend"]
    log.debug("My model is %s" % my_model)

    file_path = os.path.join(os.path.dirname(__file__),"assets", model_file)
    if not os.path.exists(file_path):raise OSError()
    with bpy.data.libraries.load(file_path, link = False) as (data_from, data_to):
        if my_model in data_from.objects:
            data_to.objects.append(my_model)
        else:
            raise NameError("The object does not exists")

    return data_to.objects[0]


def mirror_head(obj_name):
    """Mirror all verts on x axis so the head is facing the right direction"""
    head_obj = bpy.data.objects[obj_name]
    bpy.context.scene.objects.active = head_obj
    bpy.ops.object.editmode_toggle()
    mesh = bmesh.from_edit_mesh(bpy.context.object.data)
    for v in mesh.verts:
        v.co.x *= -1
    bpy.ops.object.editmode_toggle()
    bpy.context.scene.objects.active = bpy.context.scene.objects.active

def tail_and_head(obj):
    """Find the tail and head of the array modifier"""

    extrems = []
    array = obj.modifiers["WRLS_Array"]
    try:
        head = obj.modifiers["WRLS_Array"].end_cap
        extrems.append(head)    
    except:
        pass

    try: 
        tail = obj.modifiers["WRLS_Array"].start_cap
        extrems.append(tail)
    except:
        pass

    if len(extrems) > 0:
        return extrems

    else:
        return None

def wrls_off_and_delete_childs(cable):
    children = []

    for child in cable.children:
        if child.wrls.wrls_status == 'CABLE':
            children.append(child)
            log.debug("Childs are: %s" % children)
            extrems = tail_and_head(child)
            log.debug("Extrems are: %s" %extrems)
    for extrem in extrems:
        if extrem is not None:
            bpy.data.objects[extrem.name].remove(extrem, do_unlink=True)

    for child in children:
        if child is not None:
            bpy.data.objects.remove(child, do_unlink=True)
                    



############## OPERATORS ###############################

class OBJECT_OT_InitCable(bpy.types.Operator):
    """Put a cable on selected wire"""
    bl_idname = "wrls.wrls_init"
    bl_label = "Create Cable"

    @classmethod
    def pool(cls, context):
        return context.active_object.type != 'CURVE'

    def execute(self, context):
        if get_is_undefined_curve(context):


            curve = context.active_object
            log.debug("This is an undefined curve, doing something.")
            obj_name = curve.name
            set_wrls_status(context, obj_name, 'CURVE')
            cable_shape = import_model("WRLS_FlexMetallic")
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

            # put 2 modifiers on the shape object
            wrls_array = cable_shape.modifiers.new(type='ARRAY', name="WRLS_Array")
            wrls_array.curve = curve
            wrls_array.fit_type = 'FIT_CURVE'


            wrls_curve = cable_shape.modifiers.new(name='WRLS_Curve', type='CURVE')
            wrls_curve.object = curve

        else:
            log.debug("This curve is already cable.")
            

        return {'FINISHED'}

class OBJECT_OT_RemoveCable(bpy.types.Operator):
    """Turn off cable and reset."""
    bl_idname = "wrls.cable_unset"
    bl_label = "Remove Cable"

    def execute(self, context):

        cable = context.active_object
        wrls_status = cable.wrls.wrls_status

        if wrls_status == 'CURVE':
            wrls_off_and_delete_childs(cable)
        elif wrls_status == 'CABLE':
            cable = cable.parent
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

class OBJECT_OT_Cable_Previous(bpy.types.Operator):

    bl_idname = "wrls.cable_prev"
    bl_label = "Previous Cable type"

    def execute(self, context):

        return {'FINISHED'}

class OBJECT_OT_Cable_Next(bpy.types.Operator):

    bl_idname = "wrls.cable_next"
    bl_label = "Next Cable type"

    def execute(self, context):

        return {'FINISHED'}


def register():
    "register"
   

def unregister():
   "unregister"