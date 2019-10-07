import os
import bpy
from . import configs
from . import wireless
from bpy.props import StringProperty, IntProperty, BoolProperty


# imported function from wireless as could not import

def error_in_material_slots(obj):
    """
    Check if the object has at max 1 material
    assigned to slot [0] if cable
    or if has maximum 3 materials assigned to
    slots [0-2] if head/tail

    Returns False if no error, or errir nessage of first found
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

################## UI #####################

class OBJECT_PT_WireLessPanel(bpy.types.Panel):
    bl_label = "Create some Wires"
    bl_idname = "OBJECT_PT_wireless"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Wireless"

    # @classmethod
    # def pool(cls,context):


    def draw_header(self, context):
        @classmethod
        def poll(cls, context):
            return context.active_object != None
        try:
            self.layout.prop(context.active_object.wrls, "enable", text="")
        except:
            pass

    def draw(self, context):
        """The layout of the UI"""
        @classmethod
        def poll(cls, context):
            return context.object != None

        wm_wrls = bpy.context.window_manager.wrls
        obj_wrls = bpy.context.active_object.wrls
        # curve, cable, head, tail  = wireless.find_parts(bpy.context.active_object)
        layout = self.layout
        box = layout.box()
        # setting layout to Active , but I see this still allows me to change previews,
        # therefore, I could make strange choiches
        a_object = context.object
        if a_object.type != 'CURVE' and a_object.wrls.wrls_status == 'UNDEFINED':
            layout.label(text="Plese select a curve")
        elif a_object.wrls.wrls_status == 'UNDEFINED':
            layout.label(text="Enable wireless")
        elif a_object.wrls.wrls_status != 'UNDEFINED':
            # layout.active = False
            box.label(text='Category:')
            row = box.row()
            row.prop(wm_wrls, 'cable_categories', text='')
            row = box.row()
            row.template_icon_view(wm_wrls, "cables_types", show_labels=True, scale=4)
            row = box.row()
            col = row.column()
            col.scale_x = 4
            col.operator("wrls.cable_prev", icon="TRIA_LEFT", text="")
            col = row.column()
            col = row.column()
            col.scale_x = 4
            col.operator("wrls.cable_next", icon="TRIA_RIGHT", text="")

            # the thicknes slider
            row = box.row()
            row.label(text="Thickness")
            row = box.row()
            row.prop(obj_wrls, "cable_thickness", text="")

            # the stretch slider
            row = box.row()
            row.label(text="Stretch")
            row = box.row()
            row.prop(obj_wrls, "cable_stretch", text="")

        # the head endcap area

        if a_object.wrls.wrls_status == 'UNDEFINED':
            pass
        else:
            box = layout.box()
            row = box.row()
            row.prop(obj_wrls, "use_head", text="Use head end cap")

            if not a_object.wrls.use_head:
                box.label(text="")
            else:
                # box.active = False
                box.label(text='Category:')
                row = box.row()
                row.prop(wm_wrls, 'head_categories', text='')
                row = box.row()
                row.template_icon_view(wm_wrls, "head_types", show_labels=True, scale=4)
                row = box.row()
                col = row.column()
                col.scale_x = 4
                col.operator("wrls.head_prev", icon="TRIA_LEFT", text="")
                col = row.column()
                col = row.column()
                col.scale_x = 4
                col.operator("wrls.head_next", icon="TRIA_RIGHT", text="")
                row = box.row()
                row.prop(obj_wrls, "head_use_cable_mat", text="Use cable material")

        # the tail endcap area
        if a_object.wrls.wrls_status == 'UNDEFINED':
            pass
        else:
            box = layout.box()
            row = box.row()
            row.prop(obj_wrls, "use_tail", text="Use tail end cap")

            if not a_object.wrls.use_tail:
                box.label(text="")
            else:
                # box.active = False
                box.label(text='Category:')
                row = box.row()
                row.prop(wm_wrls, 'tail_categories', text='')
                row = box.row()
                row.template_icon_view(wm_wrls, "tail_types", show_labels=True, scale=4)
                row = box.row()
                col = row.column()
                col.scale_x = 4
                col.operator("wrls.tail_prev", icon="TRIA_LEFT", text="")
                col = row.column()
                col = row.column()
                col.scale_x = 4
                col.operator("wrls.tail_next", icon="TRIA_RIGHT", text="")
                row = box.row()
                row.prop(obj_wrls, "tail_use_cable_mat", text="Use cable material")

        # a box with apply and purge buttons:
        # the tail endcap area
        if a_object.wrls.wrls_status == 'UNDEFINED':
            pass
        else:
            box = layout.box()
            box.label(text="Utilities")
            row = box.row()
            row.operator("wrls.apply_wrls", icon="FILE_TICK", text="Apply Wireless Data")
            row = box.row()
            row.operator("wrls.purge_wrls", icon="PARTICLES", text="Purge Wireless Data")
        # except:
            # print('something Went wrong')
            # pass


class OBJECT_PT_WirelessCreate(bpy.types.Panel):
    bl_label = 'Add to wireless'
    bl_id_name = 'OBJECT_PT_Wirelessadd'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Wireless'

    @classmethod
    def poll(cls, context):
        """ If this is already a wireles part don't do anything."""
        obj = context.object
        return obj is not None

    def draw(self, context):

        obj = bpy.context.object
        wm_wrls = bpy.context.window_manager.wrls
        if obj is not None:
            if obj.wrls.wrls_status == 'UNDEFINED' and obj.type == 'MESH':
                errors = 0
                layout = self.layout
                box = layout.box()
                row = box.row()
                row.prop(obj, 'name')
                if(obj.name in configs.data['Models']):
                    row = box.row()
                    row.label(text='Name already in use',
                              icon='ERROR')
                    errors += 1
                mat_error = error_in_material_slots(obj)
                if mat_error:
                    row = box.row()
                    row.label(text=mat_error,
                              icon='ERROR')
                    errors += 1

                row = box.row()
                row.label(text='Category')
                row = box.row()
                row.prop(wm_wrls, 'type_of_part', expand=True)
                row = box.row()
                if wm_wrls.type_of_part == 'Cable':
                    row.prop(wm_wrls, 'cable_categories', text='')
                else:
                    row.prop(wm_wrls, 'head_categories', text='')
                row = box.row()
                row.template_icon_view(wm_wrls, "new_items", show_labels=False, scale=4)
                row = box.row()
                row.operator("wrls.render_thumbnail", icon='SCENE', text='Prepare Thumbnail')
                if wm_wrls.type_of_part == 'Cable':
                    row = box.row()
                    row.prop(wm_wrls, 'new_item_offset', text='Relative offset')
                row = box.row()
                col = row.column()
                col.operator("wrls.reset_part", icon='FILE_REFRESH', text='Reset')
                col = row.column()
                col.enabled = obj.wrls.has_thumb and errors == 0
                col.operator("wrls.save_part", icon='NEWFOLDER', text='Save Part')



class OBJECT_PT_WirelessEdit(bpy.types.Panel):
    bl_label = 'Edit custom part'
    bl_id_name = 'OBJECT_PT_Wirelessedit'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Wireless'

    @classmethod
    def poll(cls, context):
        """ If this is already a wireles part don't do anything."""
        obj = context.object
        return obj is not None

    def draw(self, context):
        wm_wrls = bpy.context.window_manager.wrls

        layout = self.layout
        if len(configs.data['model_types']['Custom Parts']) == 0:
            layout.label(text='No custom parts yet.')
        else:
            box = layout.box()
            row = box.row()
            row.template_icon_view(wm_wrls, 'custom_parts', show_labels=False)
            row = box.row()
            col = row.column()
            col.scale_x = 4
            col.operator("wrls.custom_prev", icon="TRIA_LEFT", text="")
            col = row.column()
            col = row.column()
            col.scale_x = 4
            col.operator("wrls.custom_next", icon="TRIA_RIGHT", text="")
            row = box.row()
            row.operator('wrls.delete_custom_part', text='Erase part')


class WirelessPreferencePanel(bpy.types.AddonPreferences):
    bl_idname = __package__

    exp_filepath: StringProperty(
                name="Export folder path",
                subtype='FILE_PATH',
                )
    imp_filepath: StringProperty(
                name="Import folder path",
                subtype='FILE_PATH',
                )


    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="Export custom parts")
        box.prop(self, "exp_filepath")
        if self.exp_filepath == "":
            row = box.row()
            row.label(text='Choose a destination folder to export',
                              icon='ERROR')
        row = box.row()
        row.enabled = bool(self.exp_filepath)
        row.operator('wrls.preferences_export', text='Export Custom Collection')

        box = layout.box()
        box.label(text="Import from folder")
        box.prop(self, "imp_filepath")
        row = box.row()
        row.enabled = bool(self.imp_filepath)
        row.operator('wrls.preferences_import', text='Import Custom Collection')


classes = (
    OBJECT_PT_WireLessPanel,
    OBJECT_PT_WirelessCreate,
    OBJECT_PT_WirelessEdit,
    WirelessPreferencePanel,
    )


def register():
    for clss in classes:
        bpy.utils.register_class(clss)

def unregister():
    for clss in reversed(classes):
        bpy.utils.unregister_class(clss)
