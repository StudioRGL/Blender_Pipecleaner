
import bpy
import math
from mathutils import Vector, geometry
from enum import Enum
import sys
# OPERATORS ---------------
# __reload_order_index__ = 2

print('loading util.py...')

def polarToCartesian(r, phi, theta):  # theta = v, phi = u
    """radius r, inclination theta, azimuth phi in DEGREES"""
    # https://en.wikipedia.org/wiki/Spherical_coordinate_system#Cartesian_coordinates
    # theta 0: N pole
    # theta 180: S pole
    # phi: anticlockwise from above
    theta = math.radians(theta)
    phi = math.radians(phi)
    x = r * math.sin(theta) * math.cos(phi)
    y = r * math.sin(theta) * math.sin(phi)
    z = r * math.cos(theta)
    return ((x, y, z))


def cartesianToPolar(x, y, z):
    """returns radius, phi, theta, in DEGREES where:
     +x axis is (0,90)
     -x axis is (180,90)
     +y axis is (90,90)
     -y axis is (-90,90)
     +z axis is (0,0)
     -z axis is (0,180)
    """
    r = math.sqrt(x * x + y * y + z * z)
    theta = math.acos(z / r)
    phi = math.atan2(y, x)
    return ((r, math.degrees(phi), math.degrees(theta)))  # uv IN DEGREES!!!!


def degreesToFirstPositiveDegrees(angle):
    """ puts an angle in the 0->360 range"""
    answer = math.fmod(angle, 360)
    if answer < 0:
        answer += 360
    return answer


def averageVectors(vectorList):
    """Return the (component-wise) average of the input vector list"""
    answer = Vector()
    nVectors = len(vectorList)
    for v in vectorList:
        answer += v / nVectors
    return answer


def colinear(p0, p1, p2):
    """from https://stackoverflow.com/questions/9608148/python-script-to-determine-if-x-y-coordinates-are-colinear-getting-some-e"""
    x1, y1 = p1[0] - p0[0], p1[1] - p0[1]
    x2, y2 = p2[0] - p0[0], p2[1] - p0[1]
    return abs(x1 * y2 - x2 * y1) < 1e-12


class materialNames():
    """Get a dict of the required materials"""
    # TODO: this seems like a sloppy way of doing this, what's the proper way of doing this?
    def __init__(self):
        prefix = 'Pipecleaner_'
        self.x = prefix + 'X'
        self.y = prefix + 'Y'
        self.z = prefix + 'Z'
        self.arbitrary = prefix + 'W'
        self.intersection = prefix + 'intersection'
        self.rough = prefix + 'rough'
        self.allMaterialNames = [self.x, self.y, self.z, self.arbitrary, self.intersection, self.rough]


class StrokeType(Enum):
    marker           = 0
    planar_axial     = 1
    planar_arbitrary = 2
    undefined        = 3


class Camera():
    # simple view class
    def __init__(self, cam):
        print('setting up camera')
        self.camera = cam
        self.origin = cam.location
        # TODO: we're not actually using rotation now we have direction vector, right?
        rotation_euler = cam.rotation_euler
        if rotation_euler.order != 'XYZ':
            raise(Exception('This has only been tested with the default XYZ rotation order on cameras, you probably wanna change that back'))
        self.heading = math.degrees(rotation_euler[0])  # in radians, we actually might not even need this?!
        self.elevation = math.degrees(rotation_euler[2])
        self.direction = cam.matrix_world.to_quaternion() @ Vector((0.0, 0.0, -1.0))  # it's a vector now, what else do ya want https://blender.stackexchange.com/questions/13738/how-to-calculate-the-direction-and-up-vector-of-a-camera
        print('got camera, position', self.origin, ', heading', self.heading, ', elevation', self.elevation)


class PlanarStrokeCluster():
    """Contains a load of AXIAL, PLANAR strokes which are (directly or indirectly)
    connnected to each other as well references to all the Arbitrary planar strokes"""

    def __init__(self, firstStroke):
        """initialise from just Axial Planar Strokes.
        We give it one stroke and it should connect the dots"""
        # self.strokes = [firstStroke] # should it be a set? those can't be mutable, though
        self.strokes = [firstStroke]
        self.strokes += firstStroke.allConnectedPlanarStrokes(strokeTypes=[StrokeType.planar_axial], connectionList=[firstStroke])  # add all connected planar strokes
        # we DON'T need to give it existing clusters because all strokes in
        # that cluster would already be in a cluster and by definition can't
        # be connected to this one
        self.potentialConnections = self.replaneCluster(testOnly=True)  # find all the potential connections

    def __repr__(self):
        """The print statement"""
        return ('PlanarStrokeCluster with ' + str(len(self.strokes)) + ' strokes and ' + str(len(self.potentialConnections)) + ' potential connections')

    def __lt__(self, other):
        """ the one with less connections is less"""
        nSelfConnections = len(self.potentialConnections)
        nOtherConnections = len(other.potentialConnections)
        return nSelfConnections < nOtherConnections

    def mostConnectedStroke(self):
        self.strokes.sort(reverse=True)
        if len(self.strokes) > 0:
            return self.strokes[0]
        else:
            raise(Exception("could not get 'most connected stroke' from empty stroke cluster"))

    def replaneCluster(self, testOnly=False):
        """ ok so this either tries to, or does, propogate from the mostConnectedStroke through the whole network, alternately doing rounds of axial and arbitrary strokes"""
        # set up the first stroke or it ain't gonna work!
        firstStroke = self.mostConnectedStroke()

        if testOnly is False:
            successfullyCalculatedNormalsAndOrigin = firstStroke.calculateNormalAndOrigin()
            firstStroke.rePlane()
            if not successfullyCalculatedNormalsAndOrigin:
                raise(Exception("Could not calculate origin and normals of first stroke "))
        currentlyConnectedStrokes = [firstStroke]

        i = 0
        MAX_ITERATIONS = 9999  # hmmmm not sure this is good coding practise?

        # ok we're gonna keep expanding outwards, alternatley by axial strokes (1 connection required) and arbitrary strokes (3 connections required)
        # we're gonna keep doing this until we stop getting new connections...
        while i < MAX_ITERATIONS:
            i += 1  # iterate the counter, just to be safe :-)

            newlyConnectedStrokes = []  # keep track of what strokes have been added in this iteration - if we don't get any new ones then we got em all
            for strokeType in [StrokeType.planar_axial, StrokeType.planar_arbitrary]:  # alternate between doing axial and arbitrary strokes
                for stroke in currentlyConnectedStrokes:  # this will increase (hopefully) on each iteration
                    for potentialNewConnection in stroke.adjacentPlanarStrokes():  # get all the strokes directly attached to the current one
                        if potentialNewConnection.strokeType == strokeType:
                            if potentialNewConnection not in currentlyConnectedStrokes + newlyConnectedStrokes:  # if they're not already connected (some will have multiple connections, and we don't wanna repeat)
                                # seems to be a new one!

                                # ok, so the simpler version is to just 'try to replane' here, if it works it works
                                successfullyCalculatedNormalsAndOrigin = potentialNewConnection.calculateNormalAndOrigin(connectedStrokes=(currentlyConnectedStrokes + newlyConnectedStrokes), testOnly=testOnly)

                                if successfullyCalculatedNormalsAndOrigin:
                                    if testOnly is False:
                                        potentialNewConnection.rePlane()
                                    newlyConnectedStrokes.append(potentialNewConnection)    # add them to the list

            if len(newlyConnectedStrokes) > 0:
                # if we got any new ones
                currentlyConnectedStrokes += newlyConnectedStrokes  # plop them on there
            else:
                break  # nothing to see here, think we got em all!

        return currentlyConnectedStrokes


# -------------------------------------------------------------------------------------------------------
class Stroke():
    # containts reference to the stroke, methods for getting its screen space data, etc
    # extended for the 2 types of strokes: planar strokes and intersection markers

    def __init__(self, gpStroke, camera):
        # should intitialize it by passing it the grease pencil stroke I guess?
        # whatever internal stuffs it has
        self.gpStroke = gpStroke
        self.polarPoints = []
        self.intersections = {}  # this is going to be in key/value pairs, with key = object and value = polar coordinate
        self.bBox_phiMin = None
        self.bBox_phiMax = None
        self.bBox_thetaMin = None
        self.bBox_thetaMax = None
        self.cameraOrigin = camera.origin
        self.origin = None  # where it is in 3d space (point for a marker, origin for a planar stroke)
        self.normal = None
        self.hasBeenPlaced = False
        self.strokeType = StrokeType.undefined  # override this!

        # calculate polar points
        for point in self.gpStroke.points.values():
            co = point.co
            coFromOrigin = co - self.cameraOrigin
            polarCoordinate = cartesianToPolar(coFromOrigin[0], coFromOrigin[1], coFromOrigin[2])

            # keep track of screen-space bounding box
            if self.bBox_phiMin   is None or polarCoordinate[1] < self.bBox_phiMin:
                self.bBox_phiMin   = polarCoordinate[1]
            if self.bBox_phiMax   is None or polarCoordinate[1] > self.bBox_phiMax:
                self.bBox_phiMax   = polarCoordinate[1]
            if self.bBox_thetaMin is None or polarCoordinate[2] < self.bBox_thetaMin:
                self.bBox_thetaMin = polarCoordinate[2]
            if self.bBox_thetaMax is None or polarCoordinate[2] > self.bBox_thetaMax:
                self.bBox_thetaMax = polarCoordinate[2]

            self.polarPoints.append(polarCoordinate)

        # ok, now we've got all the polar points, we should have a reasonable bounding box?

        # make sure the bbox wraps correctly at 360 degrees
        self.bBox_phiMin   = degreesToFirstPositiveDegrees(self.bBox_phiMin)
        self.bBox_phiMax   = degreesToFirstPositiveDegrees(self.bBox_phiMax)
        self.bBox_thetaMin = degreesToFirstPositiveDegrees(self.bBox_thetaMin)
        self.bBox_thetaMax = degreesToFirstPositiveDegrees(self.bBox_thetaMax)
        if self.bBox_phiMax   < self.bBox_phiMin:
            self.bBox_phiMax   += 360
        if self.bBox_thetaMax < self.bBox_thetaMin:
            self.bBox_thetaMax += 360

    def __repr__(self):
        """the print statement"""
        return ('Stroke: ' + str(len(self.polarPoints))
                + ' points, type: ' + str(self.strokeType.name)
                + ', polarBBox = ' + str(self.bBox_phiMin) + ', ' + str(self.bBox_phiMax)
                + ', ' + str(self.bBox_thetaMin) + ', ' + str(self.bBox_thetaMax) + ', '
                + str(len(self.intersections)) + ' intersections')

    def bBoxArea(self):
        return (self.bBox_phiMax - self.bBox_phiMin) * (self.bBox_thetaMax - self.bBox_thetaMin)

    def addIntersection(self, intersectingObject, polarCoordinate):
        """ used for storing intersectionMarkers on planarStrokes and vice versa"""
        # print ('adding intersection', intersectingObject, polarCoordinate)
        self.intersections[intersectingObject] = polarCoordinate  # that should do it, right?
        # doesn't check if they already intersecting, which might be ok because sometimes we'll want several markers on the same stroke

    # -------------------------------------------------------------------------------------------------------
    # from https://stackoverflow.com/questions/3838329/how-can-i-check-if-two-segments-intersect
    def on_segment(self, p, q, r):
        '''Given three colinear points p, q, r, the function checks if
        point q lies on line segment "pr"
        '''
        if (q[0] <= max(p[0], r[0]) and q[0] >= min(p[0], r[0]) and q[1] <= max(p[1], r[1]) and q[1] >= min(p[1], r[1])):
            return True
        return False

    def orientation(self, p, q, r):
        '''Find orientation of ordered triplet (p, q, r).
        The function returns following values
        0 --> p, q and r are colinear
        1 --> Clockwise
        2 --> Counterclockwise
        '''

        val = ((q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1]))
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

        return False  # Doesn't fall in any of the above cases

    def get_lineIntersectionPoint(self, A, B, C, D):  # expects xy for A, B, C, D
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
            # return (float('inf'), float('inf'))

        # intersect point(x,y)
        x = ((b2 * c1) - (b1 * c2)) / det
        y = ((a1 * c2) - (a2 * c1)) / det
        return ([x, y])

    # -------------------------------------------------------------------------------------------------------
    def intersection(self, b):
        """returns true if this stroke and stroke b intersect in polar space"""
        if self.bBox_phiMax >= b.bBox_phiMin and b.bBox_phiMax >= self.bBox_phiMin:
            if self.bBox_thetaMax >= b.bBox_thetaMin and b.bBox_thetaMax >= self.bBox_thetaMin:
                # ok, the bboxes intersect, let's check the points
                for iSegment in range(len(self.polarPoints) - 1):  # there is 1 less segment than the number of points
                    for jSegment in range(len(b.polarPoints) - 1):
                        lineA_x1 = self.polarPoints[iSegment][1]  # 0 is radius, remember
                        lineA_y1 = self.polarPoints[iSegment][2]
                        lineA_x2 = self.polarPoints[iSegment + 1][1]  # 0 is radius, remember
                        lineA_y2 = self.polarPoints[iSegment + 1][2]
                        lineB_x1 = b.polarPoints[jSegment][1]  # 0 is radius, remember
                        lineB_y1 = b.polarPoints[jSegment][2]
                        lineB_x2 = b.polarPoints[jSegment + 1][1]  # 0 is radius, remember
                        lineB_y2 = b.polarPoints[jSegment + 1][2]

                        if self.do_intersect((lineA_x1, lineA_y1), (lineA_x2, lineA_y2), (lineB_x1, lineB_y1), (lineB_x2, lineB_y2)):
                            # ok and let's find the real intersection:
                            # slopeA = (lineA_x2-lineA_x1)/(lineA_y2-lineA_y1) # doesn't work if y is 0
                            ip = self.get_lineIntersectionPoint([lineA_x1, lineA_y1], [lineA_x2, lineA_y2], [lineB_x1, lineB_y1], [lineB_x2, lineB_y2])
                            return ip  # just the [phi, theta]
        return None

    def rePlane(self):
        """separated this out, it now assumes you've already specified the ORIGIN and the NORMAL"""
        # so, once we know the normal and origin, for every point:
        for point in self.gpStroke.points.values():
            # we know the line it's on (from the camera origin, through the world point (assuming it's different)
            # we know the plane it's on (from the plane origin and normal
            # so we gotta find the intersection
            p0 = self.cameraOrigin  # p0, p1: define the line
            p1 = point.co
            p_co = self.origin  # p_co is a point on the plane (plane coordinate).
            p_no = self.normal  # p_no is a normal vector defining the plane direction (does not need to be normalized).
            # intersectionPoint = isect_line_plane_v3(p0, p1, p_co, p_no) # should not be none!
            intersectionPoint = geometry.intersect_line_plane(p0, p1, p_co, p_no)
            if intersectionPoint is None:
                raise(Exception("A bad thing that shouldn't have happened happened...."))
            # then move it to the new location
            point.co = intersectionPoint


# -------------------------------------------------------------------------------------------------------
class IntersectionMarker(Stroke):
    """subclass of stroke used for intersection markers"""
    def __init__(self, gpStroke, camera):
        super().__init__(gpStroke, camera)
        self.strokeType = StrokeType.marker
        self.normal = camera.direction  # simple enough huh

    def calculateOriginAndRePlane(self):
        """ok we just look at the first placed connected stroke and intersect with that"""
        for intersection in self.intersections.keys():
            if intersection.hasBeenPlaced:
                # get where we intersect
                polarCoordinate = self.intersections[intersection]
                self.origin = intersection.polarToCartesianPositionOfIntesection(polarCoordinate)
                if self.origin:
                    self.rePlane()
                return


# -------------------------------------------------------------------------------------------------------
class PlanarStroke(Stroke):
    """subclass of stroke used for planar strokes, XYZ ('Axial') to start with, adding 'Arbitrary' ones as well"""
    def __init__(self, gpStroke, camera):
        super().__init__(gpStroke, camera)

        # planar stroke attributes
        # self.planeOrigin = None
        # self.hasBeenDefined = False # has it been defined in xyz space or just polar
        # self.cluster = None # used when building clusters I guess?

    def __repr__(self):
        """the print statement"""
        return super().__repr__() + ', normal:' + str(self.normal)

    def __lt__(self, other):
        """used for sorting list"""
        if len(self.intersections) == len(other.intersections):
            return len(self.polarPoints) < len(other.polarPoints)
        else:
            return len(self.intersections) < len(other.intersections)

    def getScreenSpaceIntersections(self, other):
        """return list of screenspace coordinate of intersections if they intersect, otherwise []
        Needs to handle multiple intersections if they exist! """
        screenSpaceIntersections = []

        # TODO: check if multiple marker intersections even work!
        if len(self.intersections) == 0:
            return screenSpaceIntersections
        if len(other.intersections) == 0:
            return screenSpaceIntersections

        for marker in self.intersections.keys():
            for intersectingStroke in marker.intersections.keys():
                if intersectingStroke == other:
                    # ok, so the two strokes intersect at this marker, let's add the screenspace coordinate to the list
                    ssi = self.intersections[marker]  # this should get the intersection position from the dict
                    screenSpaceIntersections.append(ssi)
        return screenSpaceIntersections

    def polarToCartesianPositionOfIntesection(self, polarCoordinate):
        """assuming the plane has been defined (we know its origin and normal), this calculates the cartesian
        position of the polar coordinate (from the camera)"""
        p0 = self.cameraOrigin  # p0, p1: define the line
        p1 = Vector(polarToCartesian(1, polarCoordinate[0], polarCoordinate[1])) + self.cameraOrigin  # eh gotta get the xyz from the polar, dang. MAYBE CHECK - need to compensate for cam origin not being at zero so added it...?
        p_co = self.origin  # p_co is a point on the plane (plane coordinate).
        p_no = self.normal  # p_no is a normal vector defining the plane direction (does not need to be normalized).
        cartesianCoordinate = geometry.intersect_line_plane(p0, p1, p_co, p_no)
        return cartesianCoordinate

    def calculateNormalAndOrigin(self, connectedStrokes=[], testOnly=False):
        """Recalculates all the point coordinates. Uses the strokes in clusterConnections to get the values we need: polar coordinates, cameraOrigin, normal and origin
        If it's an arbitrary plane, no normal has been specified, searches all intersecting planes to try to find 3 that have been placed!
        returns true if it worked, false if it didn't
        """

        # do all the replaning (setting origins, etc) here instead of scattering around

        # sanity checks
        if self.hasBeenPlaced:
            return False  # it's already been done, let's not do it again!
        if self.strokeType not in [StrokeType.planar_arbitrary, StrokeType.planar_axial]:
            raise(Exception("Stroke has unexpected stroke type: " + str(self.strokeType)))

        # special case if this is the first stroke - we just make up the origin
        if connectedStrokes == []:
            if self.strokeType == StrokeType.planar_axial:
                self.origin = Vector()  # if it's the first stroke, and it's axial
            else:
                raise(Exception("initial stroke in rePlane must be of type planar_axial!"))
        else:
            # for all strokes except the first one:

            # figure out how many anchors we're gonna need
            # an anchor is just a *point in cartesian space that we know is on the new plane*
            if self.strokeType == StrokeType.planar_arbitrary:
                minimumRequiredAnchorPoints = 3
            else:
                minimumRequiredAnchorPoints = 1

            # try to find the correct number of anchor points
            anchorPoints = []
            for intersectingStroke in connectedStrokes:
                # we can safely (?) assume that the plane of this one has been defined, otherwise it shouldn't be connected
                intersectionsWithThisStroke = self.getScreenSpaceIntersections(intersectingStroke)
                for intersectionWithThisStroke in intersectionsWithThisStroke:
                    if testOnly:
                        # if we're just testing, we don't need to do the whole shebang
                        anchorPoints.append(Vector())
                        if len(anchorPoints) >= minimumRequiredAnchorPoints:
                            break  # should really break twice, but hey
                    else:
                        # ok, this is the screenspace coordinate, we can get where it is reasonably easily
                        # where the angular line intersects with the replaneStroke's plane
                        cartesianCoordinate = intersectingStroke.polarToCartesianPositionOfIntesection([intersectionWithThisStroke[0], intersectionWithThisStroke[1]])
                        if cartesianCoordinate is None:
                            raise(Exception("Intersection point = None on stroke: ", self))
                        anchorPoints.append(cartesianCoordinate)
                        # might as well keep going, rather than stopping, and get all the markers we can?

            # ok, let's see if we have enough!
            if len(anchorPoints) < minimumRequiredAnchorPoints:
                # we don't have enough information to make this work
                return False
            else:
                if testOnly:
                    return True  # if we're just testing, that's all the info we needed!

            # ok, now we know the worldspace position of the intersections
            # calculate the normal (can skip this for axial strokes)
            if self.strokeType == StrokeType.planar_arbitrary:

                print('replaning arbitrary stroke')
                # ok, so we don't know where this should go!!!! It's an ARBITRARY PLANE

                print('arbitrary plane found with ' + str(anchorPoints) + ' anchor points defined')

                # right, we have at least 3 anchor points, we gotta put a plane through them.
                # we already calculated the origin
                # TODO: do all average normals!
                # then for *every possible group of 3* we're gonna calculate the normal
                # then we're gonna flip the normals that are inverted
                # then we're gonna take the average normal

                # placeholder simple mode, just from the first three:
                testPoints = anchorPoints[:3]  # should work, right!
                v1 = testPoints[1] - testPoints[0]
                v2 = testPoints[2] - testPoints[0]
                # TODO: check if they're different yo!
                v1.normalize()
                v2.normalize()

                cross = v1.cross(v2)

                # check they're not colinear
                if cross.length <= 0.002:  # sure, could use better epsilon, but the result's gonna be rubbish even if they're only *almost* colinear
                    # raise(Exception('Points are colinear, oh no'))  # TODO: do something useful instead of crashing
                    return False  # TODO: temp HACK

                self.normal = cross

            # set the origin (this is the same for both arbitrary and axial planar strokes)
            self.origin = averageVectors(anchorPoints)  # I thiiink that's right?

        # self.rePlane()

        # we can also place all the markers now (not necessary but makes things a bit more legible!)

        self.hasBeenPlaced = True  # whoop
        return True  # done!

    def adjacentPlanarStrokes(self):
        """return the planar strokes intersecting with markers intersecting with this that aren't this"""
        answer = []
        for marker in self.intersections:  # all strokes intersecting with a planar stroke are MARKERS
            # go through all strokes connected to the markers
            for intersectingStroke in marker.intersections:
                if intersectingStroke != self:
                    answer.append(intersectingStroke)
        return answer

    def allConnectedPlanarStrokes(self, strokeTypes=[StrokeType.planar_axial], connectionList=[]):
        """recursively returns connected strokes with the specified types. The ConnectionList parameter contains previously detected connections, otherwise we're gonna
        end up redoing them loads of times! """
        # go through all strokes to this one
        newConnectionList = []
        for intersectingStroke in self.adjacentPlanarStrokes():
            if intersectingStroke not in connectionList:  # ok, if it hasn't already been done
                if intersectingStroke.strokeType in strokeTypes:
                    newConnectionList.append(intersectingStroke)
                    newConnectionList += intersectingStroke.allConnectedPlanarStrokes(strokeTypes=strokeTypes, connectionList=(connectionList + newConnectionList))  # recurse!

                pass
            pass
        return newConnectionList

    def highlight(self, select=True):
        if len(self.adjacentPlanarStrokes()) == 0:  # we got nothin'
            self.gpStroke.select = select
# -------------------------------------------------------------------------------------------------------

# USER INTERFACE FUNCTIONS


def convertSmallStrokesToMarkers():
    """takes any stroke below a certain polar bounding box size and sets its material to be the intersection material"""
    return


def getActiveGreasePencilObject():
    gp = bpy.context.active_object
    if gp.type != 'GPENCIL':
        return None # raise(Exception("NO ACTIVE GPENCIL OBJECT"))
    return gp


def getStrokeData(camera):
    """goes through all the grease pencil layers for the active frame and gp, and sorts into strokes and intersectionMarkers"""
    planarStrokes = []
    intersectionMarkers = []
    INTERSECTION_MARKER_THRESHOLD = 0.1  # this is now in ANGULAR AREA

    gp = getActiveGreasePencilObject()
    if gp is None:
        raise(Exception("NO ACTIVE GPENCIL OBJECT"))

    # layer = gp.data.layers.active # nah let's do all layers
    for layer in gp.data.layers:

        # get all the frames, find the current one
        frames = layer.frames.values()
        currentFrameFound = False
        for frame in frames:
            if frame.frame_number == bpy.context.scene.frame_current:  # only current frame
                currentFrameFound = True
                strokes = frame.strokes.values()
                for stroke in strokes:
                    # nPoints =  len(stroke.points.values())
                    # print ('checking curve with ', nPoints, ' points')
                    # check the material
                    itsAMarker = False
                    # check material
                    materialIndex = stroke.material_index
                    if materialIndex == gp.data.materials.keys().index(materialNames().intersection):  # or nPoints < INTERSECTION_MARKER_THRESHOLD: # TODO: set up separate marker detection based on bbox
                        # it's an intersection marker
                        # set the material (maybe redundant)
                        itsAMarker = True
                    else:
                        # make a temp stroke to check area
                        tempStroke = Stroke(stroke, camera)
                        bBoxArea = tempStroke.bBoxArea()
                        if bBoxArea < INTERSECTION_MARKER_THRESHOLD:
                            itsAMarker = True
                            # set the mat, cos it wasn't set
                            stroke.material_index = gp.data.materials.keys().index(materialNames().intersection)  # by material name

                    if itsAMarker:
                        # create an intersectionLine from it
                        newIntersectionMarker = IntersectionMarker(stroke, camera)
                        intersectionMarkers.append(newIntersectionMarker)
                    else:
                        # it's some kind of planar stroke
                        # get the material index

                        normal = None
                        strokeType = StrokeType.planar_axial
                        if materialIndex == gp.data.materials.keys().index(materialNames().x):
                            normal = Vector((1, 0, 0))
                        elif materialIndex == gp.data.materials.keys().index(materialNames().y):
                            normal = Vector((0, 1, 0))
                        elif materialIndex == gp.data.materials.keys().index(materialNames().z):
                            normal = Vector((0, 0, 1))
                        elif materialIndex == gp.data.materials.keys().index(materialNames().arbitrary):  # arbitrary plane!
                            normal = None
                            strokeType = StrokeType.planar_arbitrary
                        else:
                            print("Stroke has unknown material (", materialIndex, "), ignoring!")
                            continue

                        newPlanarStroke = PlanarStroke(stroke, camera)
                        newPlanarStroke.normal = normal
                        newPlanarStroke.strokeType = strokeType
                        planarStrokes.append(newPlanarStroke)
                        # check it against the custom materials
                break
        if currentFrameFound is False:
            raise(Exception("couldn't find any gpencil data for current frame, doing nothing!"))
    return (planarStrokes, intersectionMarkers)


def getClusters(planarStrokes):
    """This should hopefully get all the clusters of contiguous axial planar strokes, and return them"""
    # create clusters of all directly-connected axial strokes by :
    # pick a stroke

    print('getting clusters....')

    clusters = []
    for planarStroke in planarStrokes:  # then for every planar stroke
        if planarStroke.strokeType == StrokeType.planar_axial:  # only do this for axial ones
            #   is the stroke in any existing cluster?
            strokeInCluster = False
            for cluster in clusters:
                if planarStroke in cluster.strokes:
                    strokeInCluster = True
                    break
            if strokeInCluster is False:  # if not
                newCluster = PlanarStrokeCluster(planarStroke)  # create a cluster, populate it
                clusters.append(newCluster)

    print('done, found', len(clusters), ' clusters')
    return clusters

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
        if bpy.data.materials[mat] not in gp.data.materials.keys():  # TODO: doesn't check if mat is IN .materials, it should be if we called this in the right place though
            return False

    return True


def assignMaterials():
    """assign materials to the active object"""
    gp = bpy.context.active_object

    # sanity check, this should have already been tested before we get here
    if gp is None:
        # raise(Exception("can't check materials, this isn't an object"))
        return False
    if gp.type != "GREASE_PENCIL":
        # raise(Exception("can't check materials, this isn't a grease pencil object"))
        return False

    for mat in materialNames().allMaterialNames:
        matData = bpy.data.materials[mat]
        if matData is None:
            return False
        if matData not in gp.data.materials:  # TODO: doesn't check if mat is IN .materials, it should be if we called this in the right place though
            return False
        gp.data.materials.append(matData)



def createMaterial(materialName, color):
    if materialName in bpy.data.materials:
        return  # if we already got this one, don't bother
    mat = bpy.data.materials.new(name=materialName)
    mat.use_fake_user = True
    bpy.data.materials.create_gpencil_data(mat)
    mat.grease_pencil.show_stroke = True
    mat.grease_pencil.stroke_style = 'SOLID'
    mat.grease_pencil.color = color  # RGBA
    mat.grease_pencil.show_fill   = False


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


def objectHasMaterialsAssigned():
    """check if the active object has all the required materials assigned"""
    # TODO: write, connect


def uiChecklist(layout, text, check):
    """simple checklist generator"""
    row = layout.row()
    if check:
        icon = "CHECKBOX_HLT"
    else:
        icon = "CHECKBOX_DEHLT"
    row.label(text=text, icon=icon)


def solveContours():
    """ok, so I guess this is gonna be the big guy"""
    print('-' * 100 + '\nsolving contours....')

    # get the camera info
    camera = Camera(bpy.context.scene.camera)

    # build a list of what intersections affect what strokes:
    planarStrokes, intersectionMarkers = getStrokeData(camera)    # - build a dict of intersections and a dict of strokes
    print('found ', len(planarStrokes), ' planar strokes, ', len(intersectionMarkers), ' intersection markers')

    # check screen-space intersections and fill in intersection data
    for i in range(len(intersectionMarkers)):
        # print ('checking marker', i)
        for j in range(len(planarStrokes)):
            intersection = intersectionMarkers[i].intersection(planarStrokes[j])
            if intersection is not None:
                # store a REFERENCE to each in the other!
                intersectionMarkers[i].addIntersection(planarStrokes[j], intersection)
                planarStrokes[j].addIntersection(intersectionMarkers[i], intersection)
                # print ('found intersection with stroke ', j)

    # check that we found anything at all
    if (len(planarStrokes) < 2):
        raise(Exception('Not enough planar strokes found: ' + str(len(planarStrokes))))

    # ok, so, refactored version would be:
    clusters = getClusters(planarStrokes)  # create clusters of all directly-connected axial strokes
    print('calculated clusters')

    # then for each cluster:
    #   measure how many nodes we can define if we propogate outwards, for each cluster (I guess a recursive 'potential connections' checker that can be reused?) this alternates between axial and arbitrary?

    clusters.sort(reverse=True)  # sort them by connectedness

    print("Replaning strokes")
    # for each cluster in order
    for cluster in clusters:
        print(cluster)
        #   if it isn't yet connected:
        if cluster.strokes[0].hasBeenPlaced is False:               # there should always be at least one stroke in a cluster, since it's required to init one! and if one has been placed, they've all been placed
            # clusterStartStroke = cluster.mostConnectedStroke()       # pick the most connected stroke of the 'best' cluster from the undefined clusters list
            # clusterStartStroke.origin = Vector((0,0,0))         # TODO: this should only be done for the first stroke in the chain, and this isn't a good way of doing that
            # recursivelyReplane(clusterStartStroke)                   # do the big thing until we run outta strokes
            cluster.replaneCluster()
            # hey, we done!
            #   propogate definitions outwards from that (using potential connection checker alternately on axial and arbitrary planar strokes until we don't get any more)
            #       connect that one
            #       recurse for all it's children
        else:
            print('already replaned, skipping')

        # note: for arbitrary planar strokes, all parents must be from one cluster

    # not required for the maths, but just to tie things together visually lets position the markers
    for marker in intersectionMarkers:
        marker.calculateOriginAndRePlane()

    # select all strokes not joined to the first cluster
    for i in range(len(clusters)):
        select = (i != 0)
        for stroke in clusters[i].strokes:
            stroke.highlight(select=select)

    return
