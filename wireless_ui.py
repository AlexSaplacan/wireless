import os
import bpy
from . import configs
from . import wireless


################## UI #####################

class OBJECT_PT_WireLessPanel(bpy.types.Panel):
    bl_label = "Create some Wires"
    bl_idname = "OBJECT_PT_wireless"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Wireless"

    # @classmethod
    # def pool(cls,context):


    def draw_header(self, context):
        @classmethod
        def pool(cls, context):
            context.active_object = None
        try:
            self.layout.prop(context.active_object.wrls, "enable", text="")
        except:
            pass

    def draw(self, context):
        """The layout of the UI"""
        @classmethod
        def pool(cls, context):
            context.active_object = None


        try:

            wm_wrls = bpy.context.window_manager.wrls
            obj_wrls = bpy.context.active_object.wrls
            # cable = wireless.find_part(bpy.context.active_object, 'CABLE')
            layout = self.layout
            box = layout.box()
            # setting layout to Active , but I see this still allows me to change previews,
            # therefore, I could make strange choiches
            a_object = context.active_object
            if a_object.type != 'CURVE' and a_object.wrls.wrls_status == 'UNDEFINED':
                layout.label(text="Plese select a curve")
            elif a_object.wrls.wrls_status == 'UNDEFINED':
                layout.label(text="Enable wireless")
            else:
                # layout.active = False
                row = box.row()
                col = row.column()
                col.scale_y = 6
                col.operator("wrls.cable_prev", icon="TRIA_LEFT", text="")
                col = row.column()
                col.template_icon_view(wm_wrls, "cables_types", show_labels=True, scale=4)

                col = row.column()
                col.scale_y = 6
                col.operator("wrls.cable_next", icon="TRIA_RIGHT", text="")

                # the thicknes slider
                row = box.row()
                row.label(text="Thickness")
                row = box.row()
                row.prop(obj_wrls, "cable_thickness", text="")

                # # the stretch slider
                # row = box.row()
                # row.label(text="Stretch")
                # row = box.row()
                # row.prop(cable.wrls, "cable_stretch", text="")

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
                    row = box.row()
                    col = row.column()
                    col.scale_y = 6
                    col.operator("wrls.head_prev", icon="TRIA_LEFT", text="")
                    col = row.column()
                    col.template_icon_view(wm_wrls, "head_types", show_labels=True, scale=4)
                    col = row.column()
                    col.scale_y = 6
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
                    row = box.row()
                    col = row.column()
                    col.scale_y = 6
                    col.operator("wrls.tail_prev", icon="TRIA_LEFT", text="")
                    col = row.column()
                    col.template_icon_view(wm_wrls, "tail_types", show_labels=True, scale=4)
                    col = row.column()
                    col.scale_y = 6
                    col.operator("wrls.tail_next", icon="TRIA_RIGHT", text="")
                    row = box.row()
                    row.prop(obj_wrls, "tail_use_cable_mat", text="Use cable material")

            # a box with apply and purge buttons:
            # the tail endcap area
            if a_object.wrls.wrls_status == 'UNDEFINED':
                pass
            else:
                box = layout.box()
                box.label(text="Utilityes")
                row = box.row()
                row.operator("wrls.apply_wrls", icon="FILE_TICK", text="Apply Wireless Data")
                row = box.row()
                row.operator("wrls.purge_wrls", icon="PARTICLES", text="Purge Wireless Data")
        except:
            pass




def register():

    "register"

def unregister():
    "unregister"
