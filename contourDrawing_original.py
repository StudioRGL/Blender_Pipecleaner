# The main code for this thang

import bpy, math
from mathutils import Vector, geometry
from enum import Enum
            
def polarToCartesian(r, phi, theta): # theta = v, phi = u
    """radius r, inclination theta, azimuth phi"""
    # https://en.wikipedia.org/wiki/Spherical_coordinate_system#Cartesian_coordinates
    # theta 0: N pole
    # theta 180: S pole
    # phi: anticlockwise from above
    theta = math.radians(theta)
    phi   = math.radians(phi)
    x = r * math.sin(theta)*math.cos(phi)
    y = r * math.sin(theta)*math.sin(phi)
    z = r * math.cos(theta)
    return ((x,y,z))

   
def cartesianToPolar(x,y,z):
    """returns radius, phi, theta, where:
     +x axis is (0,90)
     -x axis is (180,90)
     +y axis is (90,90)
     -y axis is (-90,90)
     +z axis is (0,0)
     -z axis is (0,180) 
    """
    r = math.sqrt(x*x+y*y+z*z)
    theta = math.acos(z/r)
    phi = math.atan2(y,x)
    return ((r,math.degrees(phi), math.degrees(theta))) #uv IN DEGREES!!!!
   

def degreesToFirstPositiveDegrees(angle):
    """ puts an angle in the 0->360 range"""
    answer = math.fmod(angle, 360)
    if answer <0:
        answer += 360
    return answer

# -------------------------------------------------------------------------------------------------------  
class StrokeType(Enum):
    marker           = 0
    planar_axial     = 1
    planar_arbitrary = 2

# -------------------------------------------------------------------------------------------------------      
class Camera():
    # simple view class
    def __init__(self, cam):
        print ('setting up camera')
        self.camera = cam
        self.origin = cam.location
        rotation_euler = cam.rotation_euler #
        if rotation_euler.order!='XYZ':
            raise(Exception('This has only been tested with the default XYZ rotation order on cameras, you probably wanna change that back'))
        self.heading = math.degrees(rotation_euler[0]) # in radians, we actually might not even need this?!
        self.elevation= math.degrees(rotation_euler[2])
        
        print ('got camera, position', self.origin, ', heading', self.heading, ', elevation', self.elevation)


# -------------------------------------------------------------------------------------------------------
class AxialPlanarStrokeCluster():
    """Contains a load of AXIAL, PLANAR strokes which are (directly or indirectly) connnected to each other
    as well references to all the Arbitrary planar strokes"""
    
    def __init__(self, firstStroke):
        """initialise. We give it one stroke and it should connect the dots"""
        self.strokes = [firstStroke]
        # now go through all connected strokes, and add them to the cluster
        #           get every AXIAL planar stroke attached to it recursively, and add them to the cluster (stop at ARBITRARY planar strokes)
    
    def __repr__(self):
        """The print statement"""
        return ('AxialPlanarStrokeCluster with ' + str(len(self.strokes)) + ' strokes')


# -------------------------------------------------------------------------------------------------------
class Stroke():
    # containts reference to the stroke, methods for getting its screen space data, etc
    # extended for the 2 types of strokes: planar strokes and intersection markers
    
    def __init__(self, gpStroke, camera):
        # should intitialize it by passing it the grease pencil stroke I guess?
        # whatever internal stuffs it has
        self.gpStroke = gpStroke
        self.polarPoints = []
        self.intersections = {} # this is going to be in key/value pairs, with key = object and value = polar coordinate
        self.bBox_phiMin = None
        self.bBox_phiMax = None
        self.bBox_thetaMin = None
        self.bBox_thetaMax = None
        self.cameraOrigin = camera.origin
        
        #calculate polar points
        for point in self.gpStroke.points.values():
            co = point.co
            coFromOrigin = co - self.cameraOrigin
            polarCoordinate = cartesianToPolar(coFromOrigin[0], coFromOrigin[1], coFromOrigin[2])
            
            # keep track of screen-space bounding box
            if self.bBox_phiMin   == None or polarCoordinate[1]<self.bBox_phiMin:   self.bBox_phiMin   = polarCoordinate[1]
            if self.bBox_phiMax   == None or polarCoordinate[1]>self.bBox_phiMax:   self.bBox_phiMax   = polarCoordinate[1]
            if self.bBox_thetaMin == None or polarCoordinate[2]<self.bBox_thetaMin: self.bBox_thetaMin = polarCoordinate[2]
            if self.bBox_thetaMax == None or polarCoordinate[2]>self.bBox_thetaMax: self.bBox_thetaMax = polarCoordinate[2]
                        
            self.polarPoints.append(polarCoordinate)
            
        # ok, now we've got all the polar points, we should have a reasonable bounding box?
        
        # make sure the bbox wraps correctly at 360 degrees
        self.bBox_phiMin   = degreesToFirstPositiveDegrees(self.bBox_phiMin)
        self.bBox_phiMax   = degreesToFirstPositiveDegrees(self.bBox_phiMax)
        self.bBox_thetaMin = degreesToFirstPositiveDegrees(self.bBox_thetaMin)
        self.bBox_thetaMax = degreesToFirstPositiveDegrees(self.bBox_thetaMax)
        if self.bBox_phiMax   < self.bBox_phiMin:   self.bBox_phiMax   += 360
        if self.bBox_thetaMax < self.bBox_thetaMin: self.bBox_thetaMax += 360
        
        
    
    def __repr__(self):
        """the print statement"""
        return ('Stroke: ' +  str(len(self.polarPoints)) + ' points, polarBBox = ' + str(self.bBox_phiMin) +', '+ str(self.bBox_phiMax) +', '+ str(self.bBox_thetaMin) +', '+ str(self.bBox_thetaMax) + ', ' + str(len(self.intersections)) + ' intersections')
    
    def bBoxArea(self):
        return (self.bBox_phiMax-self.bBox_phiMin) * (self.bBox_thetaMax-self.bBox_thetaMin)
    
    def addIntersection(self, intersectingObject, polarCoordinate):
        """ used for storing intersectionMarkers on planarStrokes and vice versa"""
        #print ('adding intersection', intersectingObject, polarCoordinate)
        self.intersections[intersectingObject] = polarCoordinate # that should do it, right?
        # doesn't check if they already intersecting
    
    # -------------------------------------------------------------------------------------------------------
    # from https://stackoverflow.com/questions/3838329/how-can-i-check-if-two-segments-intersect
    def on_segment(self, p, q, r):
        '''Given three colinear points p, q, r, the function checks if 
        point q lies on line segment "pr"
        '''
        if (q[0] <= max(p[0], r[0]) and q[0] >= min(p[0], r[0]) and
            q[1] <= max(p[1], r[1]) and q[1] >= min(p[1], r[1])):
            return True
        return False

    def orientation(self, p, q, r):
        '''Find orientation of ordered triplet (p, q, r).
        The function returns following values
        0 --> p, q and r are colinear
        1 --> Clockwise
        2 --> Counterclockwise
        '''

        val = ((q[1] - p[1]) * (r[0] - q[0]) - 
                (q[0] - p[0]) * (r[1] - q[1]))
        if val == 0:
            return 0  # colinear
        elif val > 0:
            return 1   # clockwise
        else:
            return 2  # counter-clockwise

    
    def do_intersect(self, p1, q1, p2, q2):
        '''Main function to check whether the closed line segments p1 - q1 and p2 
           - q2 intersect'''
        o1 = self.orientation(p1, q1, p2)
        o2 = self.orientation(p1, q1, q2)
        o3 = self.orientation(p2, q2, p1)
        o4 = self.orientation(p2, q2, q1)

        # General case
        if (o1 != o2 and o3 != o4):
            return True

        # Special Cases
        # p1, q1 and p2 are colinear and p2 lies on segment p1q1
        if (o1 == 0 and self.on_segment(p1, p2, q1)):
            return True

        # p1, q1 and p2 are colinear and q2 lies on segment p1q1
        if (o2 == 0 and self.on_segment(p1, q2, q1)):
            return True

        # p2, q2 and p1 are colinear and p1 lies on segment p2q2
        if (o3 == 0 and self.on_segment(p2, p1, q2)):
            return True

        # p2, q2 and q1 are colinear and q1 lies on segment p2q2
        if (o4 == 0 and self.on_segment(p2, q1, q2)):
            return True

        return False # Doesn't fall in any of the above cases
    
    
    def get_lineIntersectionPoint(self, A, B, C, D): # expects xy for A, B, C, D
        # from https://stackoverflow.com/questions/3252194/numpy-and-line-intersections
        # a1x + b1y = c1
        a1 = B[1] - A[1]
        b1 = A[0] - B[0]
        c1 = a1 * (A[0]) + b1 * (A[1])

        # a2x + b2y = c2
        a2 = D[1] - C[1]
        b2 = C[0] - D[0]
        c2 = a2 * (C[0]) + b2 * (C[1])

        # determinant
        det = a1 * b2 - a2 * b1

        # parallel line (hmmm they could be colinear, right?
        if det == 0:
            # we already checked that they DO intersect, so just gonna return a point on the line
            # this shouldn't really ever happen!
            return A
            #return (float('inf'), float('inf'))

        # intersect point(x,y)
        x = ((b2 * c1) - (b1 * c2)) / det
        y = ((a1 * c2) - (a2 * c1)) / det
        return ([x, y])
    # -------------------------------------------------------------------------------------------------------



    
    def intersection(self, b):
        """returns true if this stroke and stroke b intersect in polar space"""
        if self.bBox_phiMax>=b.bBox_phiMin and b.bBox_phiMax>=self.bBox_phiMin:
            if self.bBox_thetaMax>=b.bBox_thetaMin and b.bBox_thetaMax>=self.bBox_thetaMin:
                #ok, the bboxes intersect, let's check the points
                for iSegment in range(len(self.polarPoints)-1): # there is 1 less segment than the number of points
                    for jSegment in range(len(b.polarPoints)-1):
                        lineA_x1 = self.polarPoints[iSegment][1] # 0 is radius, remember
                        lineA_y1 = self.polarPoints[iSegment][2]
                        lineA_x2 = self.polarPoints[iSegment+1][1] # 0 is radius, remember
                        lineA_y2 = self.polarPoints[iSegment+1][2]     
                        lineB_x1 = b.polarPoints[jSegment][1] # 0 is radius, remember
                        lineB_y1 = b.polarPoints[jSegment][2]
                        lineB_x2 = b.polarPoints[jSegment+1][1] # 0 is radius, remember
                        lineB_y2 = b.polarPoints[jSegment+1][2]
                        
                        if self.do_intersect((lineA_x1,lineA_y1), (lineA_x2,lineA_y2), (lineB_x1,lineB_y1), (lineB_x2,lineB_y2)): 
                            #print ('intersection found:',iSegment,jSegment,(lineA_x1,lineA_y1), (lineA_x2,lineA_y2), (lineB_x1,lineB_y1), (lineB_x2,lineB_y2))
                            self.gpStroke.points[iSegment].select=True
                            self.gpStroke.points[iSegment+1].select=True 
                            b.gpStroke.points[jSegment].select=True
                            b.gpStroke.points[jSegment+1].select=True
                            
                            # ok and let's find the real intersection:
                            #slopeA = (lineA_x2-lineA_x1)/(lineA_y2-lineA_y1) # doesn't work if y is 0
                            ip = self.get_lineIntersectionPoint([lineA_x1, lineA_y1], [lineA_x2, lineA_y2], [lineB_x1, lineB_y1], [lineB_x2, lineB_y2])
                            return ip # just the [phi, theta]
        return None
    pass


# -------------------------------------------------------------------------------------------------------
class IntersectionMarker(Stroke):
    """subclass of stroke used for intersection markers"""
    def __init__(self, gpStroke, camera):
        super().__init__(gpStroke, camera)
        #self.intersectingStrokes = [] # store a list of references to all intersecting strokes
        
    def definedIntersectingStrokes(self):
        """returns a list of all DEFINED strokes that intersect this one"""
        answer = []
        for i in self.intersections.keys():
            if i.hasBeenDefined:
                answer.append(i)
        return answer
    
    def hasDefinedIntersectingStrokes(self):
        """returns a bool if any of the intersecting strokes has been defined"""
        for i in self.intersections.keys():
            if i.hasBeenDefined:
                return True
        return False
        

# -------------------------------------------------------------------------------------------------------
class PlanarStroke(Stroke):
    """subclass of stroke used for planar strokes, XYZ ('Axial') to start with, adding 'Arbitrary' ones as well"""
    def __init__(self, gpStroke, camera):
        super().__init__(gpStroke, camera)
        
        # planar stroke attributes
        self.normal = None    
        self.planeOrigin = None
        self.hasBeenDefined = False # has it been defined in xyz space or just polar
        #self.cluster = None # used when building clusters I guess?
        
    def __repr__(self):
        """the print statement"""
        return super().__repr__() + ', normal:' + str(self.normal)    
    
    def __lt__(self, other): 
        """used for sorting list"""
        if len(self.intersections)==len(other.intersections):
            return len(self.polarPoints) < len(other.polarPoints) 
        else:
            return len(self.intersections)<len(other.intersections)
    
    def setNormal(self,normal):
        """The normal to the plane in which this stroke is, give it a vector"""
        self.normal = normal   
    
    def strokeType(self):
        """what kinda stroke are we?"""
        if self.normal==None:
            return StrokeType.planar_arbitrary
        else:
            return StrokeType.planar_axial

    def rePlane(self):
        """Recalculates all the point coordinates based on the polar coordinates, cameraOrigin, normal and planeOrigin
        If no normal has been specified, searches all intersecting planes to try to find 3
        
        NEEDS REFACTORING!
        
        """
        #
        # ok, so this is the main thing innit
        #print('rePlaning')
        
        # check we have all the info we need
        if self.cameraOrigin==None or self.planeOrigin==None:
            raise(Exception("We don't have all the information we need:" + str(self.cameraOrigin) + ',' + str(self.planeOrigin)))
        
        if self.normal==None:
            # ok, so we don't know where this should go!!!! It's an ARBITRARY PLANE
            
            definedIntersectionMarkers = {}
            for item in self.intersections.items():
                print (item)
                if item[0].hasDefinedIntersectingStrokes():
                    definedIntersectionMarkers[item[0]] = item[1] # *think* that's right
                    #print ('yes')
                else:
                    #print('no')
                    pass

            nDefinedIntersections = len(definedIntersectionMarkers)
            print ('arbitrary plane found with ' + str(nDefinedIntersections) + '/' + str(len(self.intersections)) + ' intersections defined')
            
            # ok, so how about this. We're gonna prioritize connections from axial planar strokes, if we have 3 of those then we good.
            # TODO: add axial strokes to the priority list thing
            # if not, and we have any connection to a planar stroke that has already been defined, use the first one
            # if we have many connections to 
            
            if nDefinedIntersections==0:
                # no idea what to do with this....let's just say...Z?
                print ('no defined intersections found on arbitrary stroke, skipping')
                return # we haven't set it to be 'defined' so this will not recurse
            elif nDefinedIntersections<3:
                print ('<3 defined intersections found on arbitrary stroke, guessing')
                # ok, just gonna go thru all of them until we find something that has been defined, that's gonna be the parent!
                foundParent = False
                for intersection in self.intersections:
                    for intersectingPlanarStroke in intersection.intersections:
                        if intersectingPlanarStroke.hasBeenDefined:
                            self.normal = intersectingPlanarStroke.normal
                            foundParent = True
                            break
                    if foundParent:
                        break
                if foundParent==False:
                    return
            else:
                # ok, so we have at least 3 intersections
                pass

    

                            
                     
                
            


            
        # so, once we know the normal, for every point:
        for point in self.gpStroke.points.values():
            # we know the line it's on (from the camera origin, through the world point (assuming it's different)
            # we know the plane it's on (from the plane origin and normal
            # so we gotta find the intersection
            p0 = self.cameraOrigin # p0, p1: define the line
            p1 = point.co 
            p_co = self.planeOrigin # p_co is a point on the plane (plane coordinate).
            p_no = self.normal #p_no is a normal vector defining the plane direction (does not need to be normalized).
            #intersectionPoint = isect_line_plane_v3(p0, p1, p_co, p_no) # should not be none!
            intersectionPoint = geometry.intersect_line_plane(p0, p1, p_co, p_no)
            if intersectionPoint==None:
                raise(Exception("A bad thing happened that shouldn't have happened...."))

            # then move it to the new location
            point.co = intersectionPoint


        self.hasBeenDefined = True #whoop
    
    def connectedPlanarStrokes(self, strokeTypes = [StrokeType.planar_axial], connectionList = []):
        """recursively returns connected strokes with the following types"""
        #connectionList.append(self) # this should work right? right?
        for marker in self.intersections: # all strokes intersecting with a planar stroke are MARKERS
            # go through all strokes connected to the markers
            for intersectingStroke in marker.intersections:
                if intersectingStroke not in connectionList: # ok, it's not us, and it hasn't already been done
                    if intersectingStroke.strokeType() in strokeTypes:
                        connectionList.append(intersectingStroke)
                        # do all connecting strokes? recurse...
                        
                        # how do we avoid doing ones we already have
                    pass
                pass
            pass
        return connectionList

# -------------------------------------------------------------------------------------------------------



def getActiveGreasePencilObject():
    gp = bpy.context.active_object
    if gp.type != 'GPENCIL':
        raise(Exception("make sure you have a gpencil object active"))
    return gp
    

def getStrokeData(camera):
    """goes through all the grease pencil layers for the active frame and gp, and sorts into strokes and intersectionMarkers"""
    planarStrokes = []
    intersectionMarkers = []
    INTERSECTION_MARKER_THRESHOLD = 0.1 # this is now in ANGULAR AREA
      
    gp = getActiveGreasePencilObject()

    # layer = gp.data.layers.active # nah let's do all layers
    
    for layer in gp.data.layers:

        # get all the frames, find the current one
        frames = layer.frames.values()
        currentFrameFound = False
        for frame in frames:
            if frame.frame_number == bpy.context.scene.frame_current: #only current frame
                currentFrameFound = True
                strokes = frame.strokes.values()
                for stroke in strokes:
                    nPoints =  len(stroke.points.values())
                    #print ('checking curve with ', nPoints, ' points') 
                    
                    
                    
                    # check the material
                    itsAMarker = False
                    # check material
                    materialIndex = stroke.material_index
                    if materialIndex == gp.data.materials.keys().index('contour_intersection') or nPoints < INTERSECTION_MARKER_THRESHOLD:
                        # it's an intersection marker
                        # set the material (maybe redundant)
                        itsAMarker = True
                    else:
                        # make a temp stroke to check area
                        tempStroke = Stroke(stroke, camera)
                        bBoxArea = tempStroke.bBoxArea()
                        if bBoxArea<INTERSECTION_MARKER_THRESHOLD:
                            itsAMarker = True
                            # set the mat, cos it wasn't set
                            stroke.material_index = gp.data.materials.keys().index('contour_intersection') # by material name 
                        
                    if itsAMarker:
                        # create an intersectionLine from it
                        newIntersectionMarker = IntersectionMarker(stroke, camera)
                        intersectionMarkers.append(newIntersectionMarker)
                    else:
                        # it's some kind of planar stroke
                        # get the material index
                        
                        
                        normal = None
                        if materialIndex == gp.data.materials.keys().index('contour_X'):
                            normal = Vector((1,0,0))
                        elif materialIndex == gp.data.materials.keys().index('contour_Y'):
                            normal = Vector((0,1,0))
                        elif materialIndex == gp.data.materials.keys().index('contour_Z'):
                            normal = Vector((0,0,1))
                        elif materialIndex == gp.data.materials.keys().index('contour_W'): # arbitrary plane!
                            normal = None
                        else:
                            print("Stroke has unknown material (", materialIndex, "), ignoring!")
                            continue
                        
                        newPlanarStroke = PlanarStroke(stroke, camera)
                        newPlanarStroke.setNormal(normal)
                        planarStrokes.append(newPlanarStroke)
                        # check it against the custom materials
                break
        if currentFrameFound == False:
            raise(Exception("couldn't find any gpencil data for current frame, doing nothing!"))
    return (planarStrokes, intersectionMarkers)

def getClusters(planarStrokes):
    """This should hopefully get all the clusters of contiguous axial planar strokes, and return them"""
    # create clusters of all directly-connected axial strokes by :
    # pick a stroke

    print ('getting clusters....')

    clusters = []
    for planarStroke in planarStrokes: # then for every AXIAL planar stroke
        pass
        #   is the stroke in any existing cluster?
        strokeInCluster = False
        for cluster in clusters:
            if planarStroke in cluster.strokes:
                strokeInCluster = True
                break
        if strokeInCluster == False: #       if not:
            newCluster = AxialPlanarStrokeCluster(planarStroke) #           create a cluster, populate it
            clusters.append(newCluster)

    print ('done.')
    return clusters

def recursivelyReplane(replaneStroke):
    if replaneStroke.hasBeenDefined == False and replaneStroke.planeOrigin==None:
        replaneStroke.planeOrigin = Vector((0,0,0)) # TODO: this should only be done for the first stroke in the chain, and this isn't a good way of doing that
    
    # we have all the info we need, so let's replane it
    replaneStroke.rePlane() 
    
    if replaneStroke.hasBeenDefined==False:
        return # we can't go any further because this one hasn't been defined, maybe because it doesn't have enough connections?
        
    # ok, so otherwise, assuming it did get defined, now we're gonna go thru all the intersections on the replaneStroke, and set their origins
    for intersection in replaneStroke.intersections.keys():
        # ok, so these should only be _markers_, cos we didn't check strokes against strokes
        marker = intersection # get the marker
        polarCoordinate = replaneStroke.intersections[intersection] # get the coordinate from the dict

        # where the angular line intersects with the replaneStroke's plane                
        p0 = replaneStroke.cameraOrigin # p0, p1: define the line
        p1 = Vector(polarToCartesian(1, polarCoordinate[0], polarCoordinate[1])) + replaneStroke.cameraOrigin  # eh gotta get the xyz from the polar, dang. MAYBE CHECK - need to compensate for cam origin not being at zero so added it...?
        p_co = replaneStroke.planeOrigin # p_co is a point on the plane (plane coordinate).
        p_no = replaneStroke.normal #p_no is a normal vector defining the plane direction (does not need to be normalized).
        #cartesianCoordinate = isect_line_plane_v3(p0, p1, p_co, p_no) # should not be none!
        cartesianCoordinate = geometry.intersect_line_plane(p0, p1, p_co, p_no)
        
        # ok, now we know the worldspace position of the intersection
        # need to also store this coordinate on the MARKER?
        if cartesianCoordinate==None:
            raise(Exception("Intersection point = None! on stroke ", replaneStroke))
                  
        for childStroke in marker.intersections: # go through all the children of the marker
            if childStroke.hasBeenDefined: # check if the child has already been replaned
                continue# if it has, skip it (could probably improve this at some point!)
            else: # otherwise, set the grandchild's planeOrigin to be the intersectionPoint 
                childStroke.planeOrigin = cartesianCoordinate # whoop set the plane origin to the interseciton point
                # hmmm, if we're setting plane origin here, maybe we should also do all the normal calculations here. but might make sense the other way round?
                # yeah should probably do this in the child right? urgh except then it ends up being depth-first
    
    # we're doing this in a separate loop so we go breadth-first instead of depth-first
    # for every intersection
    for marker in replaneStroke.intersections.keys():
        for childStroke in marker.intersections: # go through all the children of the marker
            if childStroke.hasBeenDefined == False: # check if the child's depth has already been set
                if childStroke.planeOrigin == None:# (if it hasn't already been set)
                    raise(Exception("Plane origin of child somehow hasn't been set?"))
                
                recursivelyReplane(childStroke)# move onto the child and recursively replane
                
        
    # todo: ok, so if we store the angular positions of all intersections (in pairs, with the intersected object)
    # we can look at where they intersect the plane of the parent, and that's simply the planeOrigin
    
    
    pass

def flattenAll():
    """ just for testing really?"""
    camera = Camera(bpy.context.scene.camera)
    gp = getActiveGreasePencilObject()
    layer = gp.data.layers.active
    frames = layer.frames.values()
    currentFrameFound = False
    for frame in frames:
        for stroke in frame.strokes.values():
            p = PlanarStroke(stroke, camera)
            p.planeOrigin = Vector((0,2,0))
            p.setNormal(Vector((-1,1,0)))
            p.hasBeenDefined=True
            print (p.cameraOrigin)
            print(p)  
            p.rePlane()
    pass


def solveContours():
    """ok, so I guess this is gonna be the big guy"""
    print ('-'*100+'\nsolving contours....')
    
    # get the camera info
    camera = Camera(bpy.context.scene.camera)
    
    # idea 2
    # build a list of what intersections affect what strokes:
    planarStrokes, intersectionMarkers = getStrokeData(camera)    # - build a dict of intersections and a dict of strokes
    print('found ', len(planarStrokes), ' planar strokes, ', len(intersectionMarkers), ' intersection markers')
    
    
    # check intersections and fill in intersection data
    for i in range(len(intersectionMarkers)):
        #print ('checking marker', i)
        for j in range(len(planarStrokes)):
            intersection = intersectionMarkers[i].intersection(planarStrokes[j])
            if intersection != None:
                # store a REFERENCE to each in the other!
                intersectionMarkers[i].addIntersection(planarStrokes[j], intersection)
                planarStrokes[j].addIntersection(intersectionMarkers[i], intersection)
                #print ('found intersection with stroke ', j)
                
    # check that we found anything at all                
    if len(planarStrokes)<2: raise(Exception('Not enough planar strokes found: '+ str(len(planarStrokes))) )
    
    
    # ok, so, refactored version would be:
    clusters = getClusters(planarStrokes)
    # create clusters of all directly-connected axial strokes by :
    # pick a stroke
    # then for every AXIAL planar stroke
    #   is the stroke in any existing group?
    #       if not:
    #           create a cluster
    #           get every AXIAL planar stroke attached to it recursively, and add them to the cluster (stop at ARBITRARY planar strokes)
    
    # then for each cluster:
    #   measure how many nodes we can define if we propogate outwards, for each cluster (I guess a recursive 'potential connections' checker that can be reused?) this alternates between axial and arbitrary?
    
    # sort them by connectedness
    # for each cluster in order
    #   if it isn't yet connected:
    #       pick the most connected stroke of the 'best' cluster from the undefined clusters list
    
    #   propogate definitions outwards from that (using potential connection checker alternately on axial and arbitrary planar strokes until we don't get any more)
    #   for all remaining clusters:
    #       if any are now definied, remove them from the list
    #   loop
    # for arbitrary planar strokes, all parents must be from one cluster
    
    
    connectedStrokes = (planarStrokes[0].connectedPlanarStrokes())
    print (len(connectedStrokes), 'strokes connected')

    # temp hack disable
    return
    
    
    



    
    # prioritize the strokes - the one with the most intersections is the most important I guess? then by number of points? then by index?
    planarStrokes.sort()
    planarStrokes.reverse() # start with the one with most intersections, then recurse through each one

    # go through all the strokes, starting with the most connected one, and replane every child stroke of that stroke
    # in its current form, this means each will only be visited once per chain? So may need multiple loops through  
    for stroke in planarStrokes:
        if stroke.hasBeenDefined == False:
            #print('Recursing stroke: ' + str(stroke))
            recursivelyReplane(stroke) # chain through all strokes that are connected to this one
    
    # ok, let's have a look and see what happened
    for stroke in planarStrokes:
    #    print(stroke, 'has been defined: ', stroke.hasBeenDefined)
        if stroke.hasBeenDefined == False:
            print ('intersections:')
            print (stroke.intersections)
    



#flattenAll()
solveContours()


print('Finished running code.')