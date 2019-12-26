# The main code for this thang
import sys
import bpy
from .ui_utils import *


class Pipecleaner_CreateMaterialsOperator(bpy.types.Operator):
    """Adds the required specially-named Grease Pencil materials to the scene"""
    # TODO: write this!
    bl_idname = "pipecleaner.creatematerials"
    bl_label = "Create Materials"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return materialsExist() is False

    def execute(self, context):
        createMaterials()
        return {'FINISHED'}


class Pipecleaner_AssignMaterialsOperator(bpy.types.Operator):
    """Assigns the required specially-named materials to the selected Grease Pencil object.
Only available when the materials have been created and a Grease Pencil Object is active"""

    # TODO: write this!
    bl_idname = "pipecleaner.assignmaterials"
    bl_label = "Assign Materials to GP"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return materialsAssigned() is False  # This includes a check if there IS an active GP object

    def execute(self, context):
        # createMaterials()
        assignMaterials()
        return {'FINISHED'}


class Pipecleaner_SolveContoursOperator(bpy.types.Operator):
    """This solves the contours for the selected Grease Pencil object.
Only available when all setup steps have been completed"""
    # TODO: add options (like which camera to use, for example)
    bl_idname = "pipecleaner.solvecontours"
    bl_label = "Solve Contours!"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return readyToSolve()

    def execute(self, context):
        solveContours()
        return {'FINISHED'}


class Pipecleaner_SetMaterialX(bpy.types.Operator):
    """Sets the active material to X, if it exists. Only available in Draw/Edit Modes"""
    bl_idname = "pipecleaner.setmaterial_x"
    bl_label = 'X'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        setActiveMaterial(materialNames().x)
        return{'FINISHED'}

    @classmethod
    def poll(cls, context):
        return readyToSetActiveMaterial(materialNames().x)


class Pipecleaner_SetMaterialY(bpy.types.Operator):
    """Sets the active material to Y, if it exists. Only available in Draw/Edit Modes"""
    bl_idname = "pipecleaner.setmaterial_y"
    bl_label = 'Y'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        setActiveMaterial(materialNames().y)
        return{'FINISHED'}

    @classmethod
    def poll(cls, context):
        return readyToSetActiveMaterial(materialNames().y)


class Pipecleaner_SetMaterialZ(bpy.types.Operator):
    """Sets the active material to Z, if it exists. Only available in Draw/Edit Modes"""
    bl_idname = "pipecleaner.setmaterial_z"
    bl_label = 'Z'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        setActiveMaterial(materialNames().z)
        return{'FINISHED'}

    @classmethod
    def poll(cls, context):
        return readyToSetActiveMaterial(materialNames().z)


class Pipecleaner_SetMaterialArbitrary(bpy.types.Operator):
    """Sets the active material to Arbitrary, if it exists. Only available in Draw/Edit Modes"""
    bl_idname = "pipecleaner.setmaterial_arbitrary"
    bl_label = 'Arbitrary'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        setActiveMaterial(materialNames().arbitrary)
        return{'FINISHED'}

    @classmethod
    def poll(cls, context):
        return readyToSetActiveMaterial(materialNames().arbitrary)


class Pipecleaner_SetMaterialIntersection(bpy.types.Operator):
    """Sets the active material to Intersection, if it exists. Only available in Draw/Edit Modes"""
    bl_idname = "pipecleaner.setmaterial_intersection"
    bl_label = 'Intersection'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        setActiveMaterial(materialNames().intersection)
        return{'FINISHED'}

    @classmethod
    def poll(cls, context):
        return readyToSetActiveMaterial(materialNames().intersection)


class Pipecleaner_SetMaterialRough(bpy.types.Operator):
    """Sets the active material to Rough, if it exists. Only available in Draw/Edit Modes"""
    bl_idname = "pipecleaner.setmaterial_rough"
    bl_label = 'Rough'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        setActiveMaterial(materialNames().rough)
        return{'FINISHED'}

    @classmethod
    def poll(cls, context):
        return readyToSetActiveMaterial(materialNames().rough)


class Pipecleaner_toggleSpecifiedCamera(bpy.types.Operator):
    """Sets the active material to Rough, if it exists. Only available in Draw/Edit Modes"""
    bl_idname = "pipecleaner.togglespecifiedcamera"
    bl_label = 'Toggle Camera'

    def execute(self, context):
        toggleSpecifiedCamera()
        return{'FINISHED'}

    @classmethod
    def poll(cls, context):
        c = cameraChosen()
        gp = getActiveGreasePencilObject()
        return c is True and gp is not None


class Pipecleaner_createAndSpecifyCamera(bpy.types.Operator):
    """creates a new camera in a default location, and sets it as the 'specified' camera"""
    bl_idname = "pipecleaner.createandspecifycamera"
    bl_label = 'Create Camera'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        createAndSpecifyCamera()
        return{'FINISHED'}


# Based on blender's ui_panel_simple.py template
class PipecleanerPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Pipecleaner Tools"
    bl_idname = "PIPECLEANER_PT_tool_panel"
    bl_space_type = 'VIEW_3D'  # 'PROPERTIES'
    bl_region_type = 'UI'
    # available regions are:
    # 'WINDOW' #  ('WINDOW', 'HEADER', 'CHANNELS', 'TEMPORARY', 'UI', 'TOOLS', 'TOOL_PROPS', 'PREVIEW', 'HUD',
    # 'NAVIGATION_BAR', 'EXECUTE', 'FOOTER', 'TOOL_HEADER')
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
            uiChecklist(box, "Camera specified", cameraIsChosen)
            uiChecklist(box, "Grease Pencil stroke active", gpFound)
            uiChecklist(box, "Materials created", materialsFound)
            uiChecklist(box, "Materials assigned", materialsAreAssigned)
            uiChecklist(box, "Ready!", isReadyToSolve)

            # get the camera
            box.prop_search(properties, "camera", bpy.data, "cameras", text='Camera', icon='CAMERA_DATA')

            row = box.row()
            row.operator('pipecleaner.createandspecifycamera', icon='OUTLINER_OB_CAMERA')

            row = box.row()
            row.operator('object.gpencil_add', icon='OUTLINER_OB_GREASEPENCIL')

            row = box.row()
            row.operator('pipecleaner.creatematerials', icon='NODE_MATERIAL')

            row = box.row()
            row.operator('pipecleaner.assignmaterials', icon='MATERIAL')

        # DRAW dropdown
        box = uiDropDown(layout, properties, "panelExpanded_draw", properties.panelExpanded_draw, "Draw & Edit")
        if properties.panelExpanded_draw:
            row = box.row()
            row.operator('pipecleaner.togglespecifiedcamera')
            row = box.row()
            row.label(text='Material Quick Select')
            row = box.row()
            row.operator('pipecleaner.setmaterial_x')
            row.operator('pipecleaner.setmaterial_y')
            row.operator('pipecleaner.setmaterial_z')
            row = box.row()
            row.operator('pipecleaner.setmaterial_arbitrary')
            row.operator('pipecleaner.setmaterial_intersection')
            row.operator('pipecleaner.setmaterial_rough')

        # SOLVE dropdown
        box = uiDropDown(layout, properties, "panelExpanded_solve", properties.panelExpanded_solve, "Solve")
        if properties.panelExpanded_solve:

            if gpFound is False or materialsFound is False or materialsAreAssigned is False:
                return  # we can't continue until it's setup properly

            # solve contours
            # options
            box.row().prop(context.scene.pipecleaner_properties, "solve_respectHiddenLayers", text="Respect hidden layers")
            box.row().prop(context.scene.pipecleaner_properties, "solve_respectLockedLayers", text="Respect locked layers")
            
            box.row().operator("pipecleaner.solvecontours", icon="SPHERE")


class PipecleanerProperties(bpy.types.PropertyGroup):
    """Scene properties that are used for the addon"""
    camera: bpy.props.StringProperty() = ""
    panelExpanded_setup: bpy.props.BoolProperty() = True
    panelExpanded_draw: bpy.props.BoolProperty() = False
    panelExpanded_solve: bpy.props.BoolProperty() = False
    solve_respectLockedLayers: bpy.props.BoolProperty() = True
    solve_respectHiddenLayers: bpy.props.BoolProperty() = True
    


def register():
    """extra registration stuff not included in auto load..."""
    # bpy.types.Scene.my_addon = bpy.props.PointerProperty(type=PipecleanerProperties)
    # print ('registered extra properties')
    bpy.types.Scene.pipecleaner_properties = bpy.props.PointerProperty(type=PipecleanerProperties)
    pass


print('Finished running code.')
