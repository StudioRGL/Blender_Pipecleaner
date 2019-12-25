# The main code for this thang
import sys
import bpy
from .util import *

# OPERATORS ---------------
# __reload_order_index__ = 1

print('loading contourDrawing')


class Pipecleaner_CreateMaterialsOperator(bpy.types.Operator):
    """This adds the required special materials to the scene"""
    # TODO: write this!
    bl_idname = "pipecleaner.creatematerials"
    bl_label = "Create Materials"

    @classmethod
    def poll(cls, context):
        return materialsExist()==False

    def execute(self, context):
        createMaterials()
        return {'FINISHED'}


class Pipecleaner_AssignMaterialsOperator(bpy.types.Operator):
    """This assigns the required special materials to the selected Grease Pencil Stroke"""
    # TODO: write this!
    bl_idname = "pipecleaner.assignmaterials"
    bl_label = "Assign Materials to Stroke"

    @classmethod
    def poll(cls, context):
        return (materialsAssigned() is False) and (getActiveGreasePencilObject() is not None)

    def execute(self, context):
        # createMaterials()
        assignMaterials()
        return {'FINISHED'}


class Pipecleaner_DetectIntersectionMarkersOperator(bpy.types.Operator):
    """Labels all small (in bounding box area) strokes as Intersection Markers"""
    bl_idname = "pipecleaner.detectintersectionmarkers"
    bl_label = "Detect Intersection Markers"
    bl_options = {"REGISTER", "UNDO"}
    param_threshold: bpy.props.FloatProperty(name="Threshold") = 1.0
    # param_camera: bpy.props.PointerProperty(name="MaybeCamera")

    def execute(self, context):
        convertSmallStrokesToMarkers(self.param_threshold)
        return {'FINISHED'}

    # def invoke(self, context, event):
    #    wm = context.window_manager
    #    return wm.invoke_props_dialog(self)


class Pipecleaner_SolveContoursOperator(bpy.types.Operator):
    """This solves the contours for the selected greasepencil object"""
    # TODO: add options (like which camera to use, for example)
    bl_idname = "pipecleaner.solvecontours"
    bl_label = "Solve Contours"

    def execute(self, context):
        solveContours()
        return {'FINISHED'}

class PipeCleaner_SetMaterialX(bpy.types.Operator):
    """Sets the active material to X, if it exists and we're in stroke mode"""
    bl_idname = "pipecleaner.setmaterial_x"
    bl_label = 'X'

    def execute(self, context):
        setActiveMaterial(materialNames().x)
        return{'FINISHED'}

    @classmethod
    def poll(cls, context):
        return readyToSetActiveMaterial(materialNames().x)

class PipeCleaner_SetMaterialY(bpy.types.Operator):
    """Sets the active material to Y, if it exists and we're in stroke mode"""
    bl_idname = "pipecleaner.setmaterial_y"
    bl_label = 'Y'

    def execute(self, context):
        setActiveMaterial(materialNames().y)
        return{'FINISHED'}

    @classmethod
    def poll(cls, context):
        return readyToSetActiveMaterial(materialNames().y)


class PipeCleaner_SetMaterialZ(bpy.types.Operator):
    """Sets the active material to Z, if it exists and we're in stroke mode"""
    bl_idname = "pipecleaner.setmaterial_z"
    bl_label = 'Z'

    def execute(self, context):
        setActiveMaterial(materialNames().z)
        return{'FINISHED'}

    @classmethod
    def poll(cls, context):
        return readyToSetActiveMaterial(materialNames().z)


class PipeCleaner_SetMaterialArbitrary(bpy.types.Operator):
    """Sets the active material to Arbitrary, if it exists and we're in stroke mode"""
    bl_idname = "pipecleaner.setmaterial_arbitrary"
    bl_label = 'Arbitrary'

    def execute(self, context):
        setActiveMaterial(materialNames().arbitrary)
        return{'FINISHED'}

    @classmethod
    def poll(cls, context):
        return readyToSetActiveMaterial(materialNames().arbitrary)


class PipeCleaner_SetMaterialIntersection(bpy.types.Operator):
    """Sets the active material to Intersection, if it exists and we're in stroke mode"""
    bl_idname = "pipecleaner.setmaterial_intersection"
    bl_label = 'Intersection'

    def execute(self, context):
        setActiveMaterial(materialNames().intersection)
        return{'FINISHED'}

    @classmethod
    def poll(cls, context):
        return readyToSetActiveMaterial(materialNames().intersection)


class PipeCleaner_SetMaterialRough(bpy.types.Operator):
    """Sets the active material to Rough, if it exists and we're in stroke mode"""
    bl_idname = "pipecleaner.setmaterial_rough"
    bl_label = 'Rough'

    def execute(self, context):
        setActiveMaterial(materialNames().rough)
        return{'FINISHED'}

    @classmethod
    def poll(cls, context):
        return readyToSetActiveMaterial(materialNames().rough)




# Based on blender's ui_panel_simple.py template
class PipecleanerPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Pipecleaner Tools"
    bl_idname = "PIPECLEANER_PT_tool_panel"
    bl_space_type = 'VIEW_3D'  # 'PROPERTIES'
    bl_region_type = 'UI'  # 'WINDOW' #  ('WINDOW', 'HEADER', 'CHANNELS', 'TEMPORARY', 'UI', 'TOOLS', 'TOOL_PROPS', 'PREVIEW', 'HUD', 'NAVIGATION_BAR', 'EXECUTE', 'FOOTER', 'TOOL_HEADER')
    bl_category = 'Edit'  # 'Pipecleaner Tools'
    # bl_context = 'data'

    def draw(self, context):
        # let's check if we have what we need
        gpFound = getActiveGreasePencilObject() is not None
        materialsFound = materialsExist()  # TODO: name functions/variables more consistently
        materialsAreAssigned = materialsAssigned()
        cameraIsChosen = cameraChosen()
        isReadyToSolve = readyToSolve()

        # draw stuff
        scene = context.scene
        properties = scene.pipecleaner_properties

        layout = self.layout



        # SETUP dropdown
        box = uiDropDown(layout, properties, "panelExpanded_setup", properties.panelExpanded_setup, "Setup")

        if properties.panelExpanded_setup:

            # checklist of things
            uiChecklist(box, "Grease Pencil stroke active", gpFound)
            uiChecklist(box, "Materials created", materialsFound)
            uiChecklist(box, "Materials assigned", materialsAreAssigned)
            uiChecklist(box, "Camera specified", cameraIsChosen)
            uiChecklist(box, "Ready!", isReadyToSolve)

            # get the camera
            box.prop_search(properties, "camera", bpy.data, "cameras", icon = 'CAMERA_DATA')  # select camera!

            row = box.row()
            # row.enabled = gpFound is False
            row.operator('object.gpencil_add', icon='OUTLINER_OB_GREASEPENCIL')

            row = box.row()
            row.operator('object.camera_add', icon='OUTLINER_OB_CAMERA')

            row = box.row()
            row.operator('pipecleaner.creatematerials', icon='NODE_MATERIAL')

            row = box.row()
            row.operator('pipecleaner.assignmaterials', icon='MATERIAL')

        # DRAW dropdown
        box = uiDropDown(layout, properties, "panelExpanded_draw", properties.panelExpanded_draw, "Draw")
        if properties.panelExpanded_draw:
            row = box.row()
            row.operator('view3d.view_camera')
            row = box.row()
            row.operator('pipecleaner.setmaterial_x')
            row.operator('pipecleaner.setmaterial_y')
            row.operator('pipecleaner.setmaterial_z')
            row = box.row()
            row.operator('pipecleaner.setmaterial_arbitrary')
            row.operator('pipecleaner.setmaterial_intersection')
            row.operator('pipecleaner.setmaterial_rough')

        # SETUP dropdown
        box = uiDropDown(layout, properties, "panelExpanded_edit", properties.panelExpanded_edit, "Edit")


        # SOLVE dropdown
        box = uiDropDown(layout, properties, "panelExpanded_solve", properties.panelExpanded_solve, "Solve")
        if properties.panelExpanded_solve:

            if gpFound is False or materialsFound is False or materialsAreAssigned is False:
                return  # we can't continue until it's setup properly

            # set intersection markers
            row = box.row()
            row.operator("pipecleaner.detectintersectionmarkers", icon='SNAP_MIDPOINT')

            # solve contours
            row = box.row()
            row.operator("pipecleaner.solvecontours", icon="SPHERE")

            # row = layout.row()
            # row.label(text="Pipecleaner Tools", icon='WORLD_DATA')
            # row = layout.row()
            # row.label(text="Active object is: " + obj.name)
            # row = layout.row()
            # row.prop(obj, "name")


class PipecleanerProperties(bpy.types.PropertyGroup):
    """Scene properties that are used for the addon"""
    camera: bpy.props.StringProperty() = ""
    intersectionMarkerAreaThreshold: bpy.props.FloatProperty() = 1.0
    panelExpanded_setup: bpy.props.BoolProperty() = True
    panelExpanded_draw: bpy.props.BoolProperty() = False
    panelExpanded_edit: bpy.props.BoolProperty() = False
    panelExpanded_solve: bpy.props.BoolProperty() = False


def register():
    """extra registration stuff not included in auto load..."""
    # bpy.types.Scene.my_addon = bpy.props.PointerProperty(type=PipecleanerProperties)
    # print ('registered extra properties')
    bpy.types.Scene.pipecleaner_properties = bpy.props.PointerProperty(type=PipecleanerProperties)
    pass


print('Finished running code.')
