# Pipecleaner for Blender

Experimental addon for Blender, allowing the construction of 3D "pipecleaner" models from 2D grease pencil strokes

## Todo

- [x] add sort function to clusters
- [x] implement cluster-based population
- [x] add arbitrary planes support
- [ ] make sure it works with colinear points (or rather, fails gracefully)
- [ ] make proper averaging for arbitrary planes?
- [ ] deal with locked/hidden layers? what should it do? maybe ignore locked layers, but not hidden layers?
- [ ] doesn't always seem to reliably deal with intersections?
- [ ] deal correctly with cyclic strokes?
- [ ] add materials generation
- [ ] add operator for 'generate materials'
- [ ] add operator for 'set strokes below threshold to intersectionMarkers'
- [ ] add operator for 'generate'
- [ ] add menu/ui
- [ ] add addon stuff
- [ ] position intersection markers in 3D space?
- [ ] finish readme.md!

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

- only works when drawing from a perspective camera
