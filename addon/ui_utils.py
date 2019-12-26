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
    if (materialsAssigned()) and (bpy.context.mode in ['PAINT_GPENCIL', 'EDIT_GPENCIL']):
        gp = getActiveGreasePencilObject()  # don't need to check that cos materials assigned should already
        if gp.active_material.name == materialEnum:
            return False  # can't set it if it's already set
        else:
            return True
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
    newCam = bpy.data.cameras.new(name='Pipecleaner_CameraShape')
    newCamObject = bpy.data.objects.new('Pipecleaner_Camera', newCam)
    newCamObject.location = Vector((10.0, -10.0, 5.0))
    newCamObject.rotation_euler = Euler((1.3089969158172607, 0.0, 0.7853981852531433), 'XYZ')
    bpy.context.scene.collection.objects.link(newCamObject)
    bpy.context.scene.pipecleaner_properties.camera = newCam.name
    return


def drawFromSpecifiedCamera():
    """sets the view to the specified camera, and the mode to 'draw'"""
    bpy.context.space_data.use_local_camera = True
    bpy.context.space_data.camera = getCameraObject()
    bpy.ops.view3d.view_camera()
    bpy.ops.object.mode_set(mode="PAINT_GPENCIL")
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
        # get all the selected strokes
        # check which ones are selected
        # if they're selected, set their materials
        pass


def createMaterials():
    """if the materials don't exist, create 'em"""
    # mesh = bpy.data.meshes.new(name="New Object Mesh")
    # mesh.from_pydata(verts, edges, faces)
    # object_data_add(context, mesh, operator=self)
    createMaterial(materialNames().x, [1, 0, 0, 1])
    createMaterial(materialNames().y, [0, 1, 0, 1])
    createMaterial(materialNames().z, [0, 0, 1, 1])
    createMaterial(materialNames().arbitrary, [1, 0, 1, 1])
    createMaterial(materialNames().intersection, [0, 1, 1, 1])
    createMaterial(materialNames().rough, [0, 0, 0, 0.5])
    # TODO: write, connect


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
