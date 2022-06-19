# -*- coding: utf-8 -*-
#
#      DVR-Scan: Video Motion Event Detection & Extraction Tool
#   --------------------------------------------------------------
#       [  Site: https://github.com/Breakthrough/DVR-Scan/   ]
#       [  Documentation: http://dvr-scan.readthedocs.org/   ]
#
# Copyright (C) 2014-2022 Brandon Castellano <http://www.bcastell.com>.
# PySceneDetect is licensed under the BSD 2-Clause License; see the
# included LICENSE file, or visit one of the above pages for details.
#
""" ``dvr_scan.cli.controller`` Module

This file contains the implementation of the DVR-Scan command-line logic.
"""

import os
import os.path
import sys

from scenedetect import VideoOpenFailure

from dvr_scan.cli import get_cli_parser
from dvr_scan.scanner import DetectorType, ScanContext
from dvr_scan.platform import init_logger


def validate_cli_args(args, logger):
    """ Validates command line options, returning a boolean indicating if the validation succeeded,
    and a set of validated options. """
    for file in args.input:
        if not os.path.exists(file):
            logger.error("Error: Input file does not exist:\n  %s", file)
            return False, None
    if args.output and not '.' in args.output:
        args.output += '.avi'
    if args.kernel_size < 0:
        args.kernel_size = None
    try:
        args.bg_subtractor = DetectorType[args.bg_subtractor.upper()]
    except KeyError:
        logger.error('Error: Unknown background subtraction type: %s', args.bg_subtractor)
        return False, None
    return True, args


def run_dvr_scan():
    """Entry point for running DVR-Scan.

    Handles high-level interfacing of video IO and motion event detection.

    Returns:
        0 on successful termination, non-zero otherwise.
    """
    # Parse the user-supplied CLI arguments and init the logger.
    args = get_cli_parser().parse_args()
    logger = init_logger(args.quiet_mode)
    # Validate arguments and then continue.
    validated, args = validate_cli_args(args, logger)
    if not validated:
        return 1
    try:

        if not args.bg_subtractor.value.is_available():
            logger.error(
                'Method %s is not available. To enable it, install a version of'
                ' the OpenCV package `cv2` that includes it.', args.bg_subtractor.name)
            sys.exit(1)

        sctx = ScanContext(
            input_videos=args.input,
            frame_skip=args.frame_skip,
            show_progress=not args.quiet_mode,
        )

        # Set context properties based on CLI arguments.

        sctx.set_output(
            scan_only=args.scan_only_mode,
            comp_file=args.output,
            codec=args.fourcc_str,
        )

        sctx.set_overlays(
            draw_timecode=args.draw_timecode,
            bounding_box_smoothing=args.bounding_box,
        )

        sctx.set_detection_params(
            threshold=args.threshold,
            kernel_size=args.kernel_size,
            downscale_factor=args.downscale_factor,
            roi=args.roi,
        )

        sctx.set_event_params(
            min_event_len=args.min_event_len,
            time_pre_event=args.time_pre_event,
            time_post_event=args.time_post_event,
        )

        sctx.set_video_time(
            start_time=args.start_time,
            end_time=args.end_time,
            duration=args.duration,
        )

        sctx.scan_motion(detector_type=args.bg_subtractor)

    except VideoOpenFailure as ex:
        # Error information is logged in ScanContext when this exception is raised.
        logger.error('Failed to load input: %s', ex)
        return 1

    except ValueError as ex:
        logger.error(ex)
        return 1

    return 0