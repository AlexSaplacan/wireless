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
        def pool(cls,context):
            context.object is not None

        self.layout.prop(context.active_object.wrls, "enable", text="")

    def draw(self, context):

        scene_wrls = bpy.context.window_manager.wrls
        layout = self.layout
        # setting layout to Active , but I see this still allows me to change previews, 
        # therefore, I could make strange choiches
        a_object = context.active_object
        if a_object.wrls.enable == False:
            layout.label (text="Plese select a curve")
        else:
            # layout.active = False
            row = layout.row()
            col = row.column()
            col.scale_y =  6
            col.operator("wrls.cable_prev", icon="TRIA_LEFT", text="")
            col = row.column()
            col.template_icon_view(scene_wrls,"cables_types", show_labels=True, scale = 4)

            col = row.column()
            col.scale_y = 6
            col.operator("wrls.cable_next", icon="TRIA_RIGHT", text="")

        # the head endcap area
        row = layout.row()
        row.prop(context.active_object.wrls, "use_head", text="")
        row.label(text="Use head end cap")

        if a_object.wrls.use_head == False:
            layout.label(text="")
        else:
            # layout.active = False
            row = layout.row()
            col = row.column()
            col.scale_y = 6
            col.operator("wrls.cable_prev", icon="TRIA_LEFT", text="")
            col = row.column()
            col.template_icon_view(scene_wrls, "head_types", show_labels=True, scale=4)
            col = row.column()
            col.scale_y = 6
            col.operator("wrls.cable_next", icon="TRIA_RIGHT", text="")


        # the tail endcap area
        row = layout.row()
        row.prop(context.active_object.wrls, "use_tail", text="")
        row.label(text="Use tail end cap")



def register():

    "register"

def unregister():
    "unregister"