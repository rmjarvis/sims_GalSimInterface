import unittest
import os
import numpy as np
import lsst.utils.tests
import lsst.afw.geom as afwGeom
import lsst.geom as LsstGeom
from lsst.utils import getPackageDir
from lsst.sims.utils.CodeUtilities import sims_clean_up
from lsst.sims.utils import ObservationMetaData, haversine, arcsecFromRadians
from lsst.sims.coordUtils.utils import ReturnCamera
from lsst.sims.coordUtils import _raDecFromPixelCoords
from lsst.sims.GalSimInterface.wcsUtils import tanWcsFromDetector, tanSipWcsFromDetector
from lsst.sims.GalSimInterface import GalSimCameraWrapper
from lsst.sims.GalSimInterface import LSSTCameraWrapper
from lsst.sims.coordUtils import lsst_camera

from lsst.sims.coordUtils import chipNameFromPupilCoordsLSST
from lsst.sims.coordUtils import focalPlaneCoordsFromPupilCoordsLSST
from lsst.sims.coordUtils import pupilCoordsFromFocalPlaneCoordsLSST


def setup_module(module):
    lsst.utils.tests.init()


class WcsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.camera_wrapper = LSSTCameraWrapper()
        cls.detector = cls.camera_wrapper.camera['R:1,1 S:2,2']

        cls.obs = ObservationMetaData(pointingRA=25.0, pointingDec=-10.0,
                                      boundType='circle', boundLength=1.0,
                                      mjd=49250.0, rotSkyPos=0.0,
                                      bandpassName='g')
        cls.epoch = 2000.0

    @classmethod
    def tearDownClass(cls):
        sims_clean_up()
        del cls.detector
        del cls.camera_wrapper

        if hasattr(chipNameFromPupilCoordsLSST, '_detector_arr'):
            del chipNameFromPupilCoordsLSST._detector_arr
        if hasattr(focalPlaneCoordsFromPupilCoordsLSST, '_z_fitter'):
            del focalPlaneCoordsFromPupilCoordsLSST._z_fitter
        if hasattr(pupilCoordsFromFocalPlaneCoordsLSST, '_z_fitter'):
            del pupilCoordsFromFocalPlaneCoordsLSST._z_fitter
        if hasattr(lsst_camera, '_lsst_camera'):
            del lsst_camera._lsst_camera

    def testTanSipWcs(self):
        """
        Test that tanSipWcsFromDetector works by fitting a TAN WCS and a TAN-SIP WCS to
        a detector with distortions and verifying that the TAN-SIP WCS better approximates
        the truth.
        """

        tanWcs = tanWcsFromDetector(self.detector.getName(), self.camera_wrapper,
                                    self.obs, self.epoch)
        tanSipWcs = tanSipWcsFromDetector(self.detector.getName(), self.camera_wrapper,
                                          self.obs, self.epoch)

        tanWcsRa = []
        tanWcsDec = []
        tanSipWcsRa = []
        tanSipWcsDec = []

        xPixList = []
        yPixList = []
        for xx in np.arange(0.0, 4001.0, 100.0):
            for yy in np.arange(0.0, 4001.0, 100.0):
                xPixList.append(xx)
                yPixList.append(yy)

                pt = afwGeom.Point2D(xx, yy)
                skyPt = tanWcs.pixelToSky(pt).getPosition(LsstGeom.degrees)
                tanWcsRa.append(skyPt.getX())
                tanWcsDec.append(skyPt.getY())

                skyPt = tanSipWcs.pixelToSky(pt).getPosition(LsstGeom.degrees)
                tanSipWcsRa.append(skyPt.getX())
                tanSipWcsDec.append(skyPt.getY())

        tanWcsRa = np.radians(np.array(tanWcsRa))
        tanWcsDec = np.radians(np.array(tanWcsDec))

        tanSipWcsRa = np.radians(np.array(tanSipWcsRa))
        tanSipWcsDec = np.radians(np.array(tanSipWcsDec))

        xPixList = np.array(xPixList)
        yPixList = np.array(yPixList)

        (raTest,
         decTest) = self.camera_wrapper._raDecFromPixelCoords(xPixList, yPixList,
                                                              [self.detector.getName()]*len(xPixList),
                                                              obs_metadata=self.obs,
                                                              epoch=self.epoch)

        tanDistanceList = arcsecFromRadians(haversine(raTest, decTest, tanWcsRa, tanWcsDec))
        tanSipDistanceList = arcsecFromRadians(haversine(raTest, decTest, tanSipWcsRa, tanSipWcsDec))

        maxDistanceTan = tanDistanceList.max()
        maxDistanceTanSip = tanSipDistanceList.max()

        msg = 'max error in TAN WCS %e arcsec; in TAN-SIP %e arcsec' % (maxDistanceTan, maxDistanceTanSip)
        self.assertLess(maxDistanceTanSip, 0.01, msg=msg)
        self.assertGreater(maxDistanceTan-maxDistanceTanSip, 1.0e-10, msg=msg)


class MemoryTestClass(lsst.utils.tests.MemoryTestCase):
    pass

if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
