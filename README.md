# Pipecleaner for Blender

Experimental addon for Blender, allowing the construction of 3D "pipecleaner" models from 2D grease pencil strokes

## Todo

- [x] add sort function to clusters
- [x] implement cluster-based population
- [x] add arbitrary planes support
- [ ] make sure it works with colinear points (or rather, fails gracefully)
- [ ] rename functions for consistency (get, set, etc)
- [ ] make proper averaging for arbitrary planes?
- [ ] deal with locked/hidden layers? what should it do? maybe ignore locked layers, but not hidden layers?
- [ ] doesn't always seem to reliably deal with intersections?
- [ ] deal correctly with cyclic strokes?
- [x] add materials generation
- [x] add operator for 'generate materials'
- [x] add operator for 'solve'
- [x] add operator for 'draw from camera'
- [x] add operator for each material
- [ ] maybe add operator for split/join strokes
- [x] add menu/ui
- [x] add addon stuff
- [x] position intersection markers in 3D space?
- [ ] finish readme.md!
- [ ] clarify hasBeenPlaced vs hasBeenDefined
- [ ] make it work with camera at origin
- [ ] better names for materialsExist etc
- [x] make 'add camera' before GP and fill in box
- [x] make sure 'solve contours' uses the correct camera
- [x] add generic function to get camera OBJECT from camera SHAPE NAME
- [x] separate UI helper functions from solver helper functions
- [x] combine Draw & Edit
- [x] make 'draw from camera' not a toggle, maybe also for edit mode
- [ ] add helpful descriptions to operators
- [ ] write objectHasMaterialAssigned
- [x] add undos to everything!
- [ ] add vertex groups?
- [ ] check if it works when there's not GP layers!
- [x] remove camera passepartout
- [x] create camera from current view!
- [ ] add polling for camera toggle
- [ ] rename camera toggle

## Usage

1. learn to draw
1. install the Pipecleaner addon
1. make a camera in Blender
1. set it as the scene camera
1. we recommend locking the camera - or this is not gonna work
1. from the camera view, roughly draw your object or scene, making sure it's aligned with the perspective grid (you can also put some rough 3D objects if you need a guide, accuracy is important with this)
1. add the required materials
1. draw a series of strokes aligned to either the x, y or z plane using the respective materials
1. connect the strokes into long chains of strokes with the intersection marker material (like making a model out of pipecleaners...). You can also just make tiny strokes using whatever brush you're currently using, then use a function to convert everything

## Limitations

- Only works when drawing from a perspective camera. Workaround: use a perspective camera far away to approximate orthographic behaviour if you need it
- If there's already an existing material with one of the reserved names that is not a Grease Pencil Material, some functions will crash. Workaround: Don't do that...
