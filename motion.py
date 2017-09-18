import logging

import cv2
import numpy as np

from transcode import open_transcoder
from utils import first


logger = logging.getLogger(__name__)


def has_motion(fpath):
    """
    Returns True if motion is detected on video at fpath. Tries to find
    contours of movin objects and assumes there is motion if a large enough
    contour exitsts long enough without interruption.
    """
    fgbg = cv2.createBackgroundSubtractorKNN(dist2Threshold=1024,
                                             detectShadows=False)
    frame_size = 640 * 480 * 3
    with raw_transcoder(fpath, '-') as xcoder:
        frames_det = 0
        buf = xcoder.read(frame_size)
        while len(buf) == frame_size:
            frame = np.frombuffer(buf, dtype=np.uint8).reshape((480, 640, 3))
            fgmask = fgbg.apply(frame)
            fgmask = cv2.medianBlur(fgmask, 5)
            _, contours, _ = cv2.findContours(fgmask, cv2.RETR_TREE,
                                              cv2.CHAIN_APPROX_SIMPLE)
            hulls = (cv2.convexHull(cnt) for cnt in contours)
            has_big_hull = bool(first(
                True for hull in hulls if cv2.contourArea(hull, True) > 700))
            frames_det = (frames_det + has_big_hull) * has_big_hull
            if frames_det > 50:
                return True
            buf = xcoder.read(frame_size)
    return False


def raw_transcoder(input, output):
    """Transcode to width 640 grayscale (8 bpp)."""
    xcoder_args = '''
        -v error
        -f rawvideo
        -r 25
        -pix_fmt +rgb24
        -vf scale=640:480
    '''.split()
    xcoder = open_transcoder(input, output, additional_flags=xcoder_args,
                             terminate=True)
    return xcoder
