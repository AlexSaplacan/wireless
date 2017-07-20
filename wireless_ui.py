import os
import bpy
from . import configs


################## UI #####################

class OBJECT_PT_WireLessPanel(bpy.types.Panel):
    bl_label = "Create some Wires"
    bl_idname = "OBJECT_PT_wireless"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Misc"

    # @classmethod
    # def pool(cls,context):


    def draw_header(self, context):
        @classmethod
        def pool(cls, context):
            not context.object

        self.layout.prop(context.active_object.wrls, "enable", text="")

    def draw(self, context):
        """The layout of the UI"""
        @classmethod
        def pool(cls, context):
            not context.object

        wm_wrls = bpy.context.window_manager.wrls
        obj_wrls = bpy.context.active_object.wrls
        layout = self.layout
        # setting layout to Active , but I see this still allows me to change previews,
        # therefore, I could make strange choiches
        a_object = context.active_object
        if a_object.type != 'CURVE' and a_object.wrls.wrls_status == 'UNDEFINED':
            layout.label(text="Plese select a curve")
        elif a_object.wrls.wrls_status == 'UNDEFINED':
            layout.label(text="Enable wireless")
        else:
            # layout.active = False
            row = layout.row()
            col = row.column()
            col.scale_y = 6
            col.operator("wrls.cable_prev", icon="TRIA_LEFT", text="")
            col = row.column()
            col.template_icon_view(wm_wrls, "cables_types", show_labels=True, scale=4)

            col = row.column()
            col.scale_y = 6
            col.operator("wrls.cable_next", icon="TRIA_RIGHT", text="")

            # the thicknes slider
            row = layout.row()
            row.label(text="Thickness")
            row.prop(obj_wrls, "cable_thickness", text="")

        # the head endcap area

        if a_object.wrls.wrls_status == 'UNDEFINED':
            pass
        else:
            row = layout.row()
            row.prop(context.active_object.wrls, "use_head", text="")
            row.label(text="Use head end cap")

            if not a_object.wrls.use_head:
                layout.label(text="")
            else:
                # layout.active = False
                row = layout.row()
                col = row.column()
                col.scale_y = 6
                col.operator("wrls.head_prev", icon="TRIA_LEFT", text="")
                col = row.column()
                col.template_icon_view(wm_wrls, "head_types", show_labels=True, scale=4)
                col = row.column()
                col.scale_y = 6
                col.operator("wrls.head_next", icon="TRIA_RIGHT", text="")


        # the tail endcap area
        if a_object.wrls.wrls_status == 'UNDEFINED':
            pass
        else:
            row = layout.row()
            row.prop(context.active_object.wrls, "use_tail", text="")
            row.label(text="Use tail end cap")

            if not a_object.wrls.use_tail:
                layout.label(text="")
            else:
                # layout.active = False
                row = layout.row()
                col = row.column()
                col.scale_y = 6
                col.operator("wrls.tail_prev", icon="TRIA_LEFT", text="")
                col = row.column()
                col.template_icon_view(wm_wrls, "tail_types", show_labels=True, scale=4)
                col = row.column()
                col.scale_y = 6
                col.operator("wrls.tail_next", icon="TRIA_RIGHT", text="")




def register():

    "register"

def unregister():
    "unregister"
