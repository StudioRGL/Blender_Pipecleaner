import bpy
from .solver_utils import *

# -------------------------------------------------------------------------------------------------------
# USER INTERFACE FUNCTIONS
# link between the operators and the contour solver


# UI prettifying functions -------------------------
def uiDropDown(layout, propertyLocation, propertyString, property, name):
    """a dropdown section, returns a ui box within itself.
    layout: a UILayout object
    propertyLocation: data from which to take property
    propertyString: identifier of property in data
    property: the bool value of the property (if it's expanded or not)
    name: just a label string
    """
    box = layout.box()
    row = box.row()

    # make this a function so we can reuse, returns box and expanded I guess?
    row.prop(propertyLocation, propertyString,
             icon="TRIA_DOWN" if property else "TRIA_RIGHT",
             icon_only=True, emboss=False
             )
    row.label(text=name)
    return box


def uiChecklist(layout, text, check):
    """simple checklist generator"""
    row = layout.row()
    if check:
        icon = "CHECKBOX_HLT"
    else:
        icon = "CHECKBOX_DEHLT"
    row.label(text=text, icon=icon)


# Polling Helper Functions -----------------------------------
def objectHasMaterialsAssigned():
    """check if the active object has all the required materials assigned"""
    # TODO: write, connect


def cameraChosen():
    """Helper function called by the Poll function of an operator"""
    c = bpy.context.scene.pipecleaner_properties.camera  # TODO: check if the camera exists?
    return c is not ""


def readyToSetActiveMaterial(materialEnum):
    """Helper function called by the Poll function of an operator"""
    if materialsAssigned():
        if bpy.context.mode == 'PAINT_GPENCIL':
            gp = getActiveGreasePencilObject()  # don't need to check that cos materials assigned implies we have a gp
            if gp.active_material.name == materialEnum:
                return False  # can't set it if it's already set
            else:
                return True
        elif bpy.context.mode == 'EDIT_GPENCIL':
            return True  # as long as the material's assigned, we good
    else:
        return False


def materialsExist():
    """check if the materials exist in the scene"""
    # TODO: check that these are GREASE PENCIL materials
    materialsInScene = bpy.data.materials.keys()
    for materialName in materialNames().allMaterialNames:
        if materialName not in materialsInScene:
            return False
    return True


def materialsAssigned():
    """Check if these materials are assigned to the current GP stroke"""

    gp = getActiveGreasePencilObject()
    if gp is None:
        return False

    # sanity check, this should have already been tested before we get here
    # if gp is None:
    #     # raise(Exception("can't check materials, this isn't an object"))
    #     return False
    # if gp.type != "GREASE_PENCIL":
    #     # raise(Exception("can't check materials, this isn't a grease pencil object"))
    #     return False

    if materialsExist() is False:
        return False

    for mat in materialNames().allMaterialNames:
        if mat not in gp.data.materials.keys():  # TODO: doesn't check if mat is IN .materials,
            # it should be if we called this in the right place though
            return False

    return True


def readyToSolve():
    """Checks for the whole load of conditions that need to be true before we can solve"""
    gpFound = getActiveGreasePencilObject() is not None
    materialsFound = materialsExist()  # TODO: name functions/variables more consistently
    materialsAreAssigned = materialsAssigned()
    cameraIsChosen = cameraChosen()
    readyToSolve = gpFound and materialsFound and materialsAreAssigned and cameraIsChosen
    return readyToSolve


def readyToViewCamera():
    """Returns true if we could press the button to view the camera"""
    if cameraChosen() is False:
        return False
    if bpy.context.space_data.type != 'VIEW_3D':
        return False
    # don't bother if we're already viewing it
    if bpy.context.space_data.region_3d.view_perspective == 'CAMERA':
        if bpy.context.space_data.use_local_camera and bpy.context.space_data.camera == getCameraObject():
            return False
    return True


# Operator Helper Sub-functions-------------------------------
def createMaterial(materialName, color):
    """Creates a grease pencil material if it doesn't already exist"""
    if materialName in bpy.data.materials:
        return  # if we already got this one, don't bother
    mat = bpy.data.materials.new(name=materialName)
    mat.use_fake_user = True
    bpy.data.materials.create_gpencil_data(mat)
    mat.grease_pencil.show_stroke = True
    mat.grease_pencil.stroke_style = 'SOLID'
    mat.grease_pencil.color = color  # RGBA
    mat.grease_pencil.show_fill   = False


# Operator Helper Functions ----------------------------------
def createAndSpecifyCamera():
    """create a new camera, add it to the scene, set it as the specified camera"""
    # create the camera
    newCam = bpy.data.cameras.new(name='Pipecleaner_CameraShape')
    newCamObject = bpy.data.objects.new('Pipecleaner_Camera', newCam)  # make a new camera object

    # get current view
    space = bpy.context.space_data
    if space.type == 'VIEW_3D':
        # we can set the camera to this!
        # region = space.region_3d
        # m = region.view_matrix
        # newCamObject.matrix_world = m # set the new camera to that matrix...
        # newCamObject.rotation_mode = 'QUATERNION'
        # newCamObject.rotation_quaternion = region.view_rotation
        # newCamObject.rotation_euler = region.view_rotation.to_euler()
        # distanceVector = newCamObject.matrix_world.to_quaternion() @ Vector((-1.0, 0.0, 0.0))
        # distanceVector.normalize()
        # distance = region.view_distance
        # newCamObject.location = region.view_location + distanceVector * distance

        # cam.matrix_world.to_quaternion() @ Vector((0.0, 0.0, -1.0))
        # doesn't work

        # v = bpy.data.screens['Scripting'].areas[5].spaces[0].region_3d
        # get the v.regions[4].type=='WINDOW'
        # a = bpy.data.screens['Scripting'].areas
        # gotta get https://docs.blender.org/api/current/bpy.types.RegionView3D.html

        # previousSelection = bpy.context.selected_objects
        # bpy.ops.object.select_all(action='DESELECT')
        # newCamObject.select_set(True)
        bpy.context.space_data.use_local_camera = True  # wanna use the specified camera
        bpy.context.space_data.camera = newCamObject  # set the local camera to be this one!
        bpy.ops.view3d.camera_to_view()
    else:
        # hmm probably shoulda been, but we can just make up camera coordinates
        newCamObject.location = Vector((10.0, -10.0, 5.0))
        newCamObject.rotation_euler = Euler((1.3089969158172607, 0.0, 0.7853981852531433), 'XYZ')

    # setup new camera
    newCam.passepartout_alpha = 0.1
    bpy.context.scene.collection.objects.link(newCamObject)  # add it to the scene
    bpy.context.scene.pipecleaner_properties.camera = newCam.name  # store the cam's name
    toggleSpecifiedCamera()
    return


def toggleSpecifiedCamera():
    """sets the view to the specified camera, and the mode to 'draw'"""
    bpy.context.space_data.use_local_camera = True  # wanna use the specified camera
    bpy.context.space_data.lock_camera = False  # don't lock the camera to the view, don't wanna move it accidentally
    bpy.context.space_data.camera = getCameraObject()  # set the local camera to be this one!
    if bpy.context.space_data.region_3d.view_perspective == 'CAMERA':
        return  # if we're already viewing the camera, don't bother
    bpy.ops.view3d.view_camera()
    return


def setActiveMaterial(materialEnum):
    """set the active material"""
    gp = getActiveGreasePencilObject()
    materialsAreAssigned = materialsAssigned()

    if gp is None or materialsAreAssigned is False:
        return None

    materialIndex = gp.material_slots.keys().index(materialEnum)
    bpy.context.object.active_material_index = materialIndex

    # if we're in edit mode, also change the selected stroke(s) to this material
    if bpy.context.mode == 'EDIT_GPENCIL':
        # get all the active strokes
        strokes = getActiveGreasePencilStrokes()
        for stroke in strokes:
            selected = False
            if stroke.select:  # if it's selected
                selected = True
            else:
                for point in stroke.points:
                    if point.select:
                        selected = True
                        break
            if selected:
                stroke.material_index = materialIndex  # set the material index


def createMaterials():
    """if the materials don't exist, create 'em"""
    createMaterial(materialNames().x, [1, 0, 0, 1])
    createMaterial(materialNames().y, [0, 1, 0, 1])
    createMaterial(materialNames().z, [0, 0, 1, 1])
    createMaterial(materialNames().arbitrary, [1, 0, 1, 1])
    createMaterial(materialNames().intersection, [0, 1, 1, 1])
    createMaterial(materialNames().rough, [0, 0, 0, 0.5])


def assignMaterials():
    """assign materials to the active object"""
    gp = bpy.context.active_object

    # sanity check, this should have already been tested before we get here
    if gp is None:
        # raise(Exception("can't check materials, this isn't an object"))
        return False
    if gp.type != "GPENCIL":
        # raise(Exception("can't check materials, this isn't a grease pencil object"))
        return False

    for mat in materialNames().allMaterialNames:
        matData = bpy.data.materials[mat]  # TODO: check it's in there!
        if matData is None:
            return False
        if mat not in gp.data.materials.keys():
            gp.data.materials.append(matData)
            # return False
        # gp.data.materials.append(matData)
    return True
