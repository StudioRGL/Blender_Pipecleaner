# The main code for this thang
import sys
import bpy
# from 1_util import *
# from util import *

# OPERATORS ---------------
# __reload_order_index__ = 1

print ('loading contourDrawing')

class Pipecleaner_CreateMaterialsOperator(bpy.types.Operator):
    """This adds the required special materials to the scene"""
    # TODO: write this!
    bl_idname = "pipecleaner.creatematerials"
    bl_label = "Create Materials"

    def execute(self, context):
        createMaterials()
        return {'FINISHED'}


class Pipecleaner_AssignMaterialsOperator(bpy.types.Operator):
    """This assigns the required special materials to the selected Grease Pencil Stroke"""
    # TODO: write this!
    bl_idname = "pipecleaner.assignmaterials"
    bl_label = "Assign Materials to Stroke"

    def execute(self, context):
        # createMaterials()
        assignMaterials()
        return {'FINISHED'}


class Pipecleaner_DetectIntersectionMarkersOperator(bpy.types.Operator):
    """Labels all small (in bounding box area) strokes as Intersection Markers"""
    bl_idname = "pipecleaner.detectintersectionmarkers"
    bl_label = "Detect Intersection Markers"

    def execute(self, context):
        convertSmallStrokesToMarkers()
        return {'FINISHED'}


class Pipecleaner_SolveContoursOperator(bpy.types.Operator):
    """This solves the contours for the selected greasepencil object"""
    # TODO: add options (like which camera to use, for example)
    bl_idname = "pipecleaner.solvecontours"
    bl_label = "Solve Contours"

    def execute(self, context):
        return {'FINISHED'}


# Based on blender's ui_panel_simple.py template
class PipecleanerPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Pipecleaner Tools"
    bl_idname = "Pipecleaner_ToolPanel"
    bl_space_type = 'VIEW_3D'  # 'PROPERTIES'
    bl_region_type = 'UI'  # 'WINDOW' #  ('WINDOW', 'HEADER', 'CHANNELS', 'TEMPORARY', 'UI', 'TOOLS', 'TOOL_PROPS', 'PREVIEW', 'HUD', 'NAVIGATION_BAR', 'EXECUTE', 'FOOTER', 'TOOL_HEADER')
    bl_category = 'Edit'  # 'Pipecleaner Tools'
    #bl_context = 'data'

    def draw(self, context):
        # let's check if we have what we need
        gpFound = (bpy.context.active_object is not None) and (bpy.context.active_object.type == 'GPENCIL')
        materialsFound = materialsExist()  # TODO: name functions/variables more consistently
        materialsAreAssigned = materialsAssigned()

        # draw stuff
        layout = self.layout

        # checklist of things
        uiChecklist(layout, "Grease Pencil stroke active", gpFound)
        uiChecklist(layout, "Materials created", materialsFound)
        uiChecklist(layout, "Materials assigned", materialsAreAssigned)

        # create buttons if we need 'em
        if gpFound is False:
            row = layout.row()
            row.operator('object.gpencil_add', icon='OUTLINER_OB_GREASEPENCIL')

        if materialsFound is False:
            row = layout.row()
            row.operator('pipecleaner.creatematerials', icon='NODE_MATERIAL')

        if materialsAreAssigned is False:
            row = layout.row()
            row.operator('pipecleaner.assignmaterials', icon='MATERIAL')

        if gpFound is False or materialsFound is False or materialsAreAssigned is False:
            return  # we can't continue until it's setup properly

        # set intersection markers
        row = layout.row()
        row.operator("pipecleaner.detectintersectionmarkers", icon='SNAP_MIDPOINT')

        # solve contours
        row = layout.row()
        row.operator("pipecleaner.solvecontours", icon="SPHERE")

        # row = layout.row()
        # row.label(text="Pipecleaner Tools", icon='WORLD_DATA')
        # row = layout.row()
        # row.label(text="Active object is: " + obj.name)
        # row = layout.row()
        # row.prop(obj, "name")


# def register():
#     print('Registering Pipecleaner UI Panel & Operators')
#     # bpy.utils.register_class(PipecleanerPanel)
#     for c in [PipecleanerPanel, Pipecleaner_CreateMaterialsOperator, Pipecleaner_AssignMaterialsOperator, Pipecleaner_DetectIntersectionMarkersOperator, Pipecleaner_SolveContoursOperator]:
#         bpy.utils.register_class(c)
#     print('Done.')
# 
# 
# def unregister():
#     # HACK: make sure you've added all the operators to both REGISTER and UNREGISTER
#     for c in [PipecleanerPanel, Pipecleaner_CreateMaterialsOperator, Pipecleaner_AssignMaterialsOperator, Pipecleaner_DetectIntersectionMarkersOperator, Pipecleaner_SolveContoursOperator]:
#         bpy.utils.unregister_class(c)
# 
# 
# if __name__ == "__main__":
#     register()
# 
# 
# register()
# flattenAll()
# solveContours()


print('Finished running code.')
