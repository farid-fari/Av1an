#!/usr/bin/env python

import argparse
from commands import (
    GetAudio, SplitFile, PasteFiles, All, Prepare, Clean, HEVCEncodeFile,
    FrameCount, MatchEncodedFrames, MatchOutputFrames, SVTEncodeFile, VMAF,
    Recount, NamedPipe, Tqdm)
import os
from pathlib import Path
import tempfile
from util import testMakeVersion
from warnings import warn


def sceneDetect(inFile, scenesFile):
    from scenedetect.video_manager import VideoManager
    from scenedetect.stats_manager import StatsManager
    from scenedetect.scene_manager import SceneManager
    from scenedetect.detectors import ContentDetector

    videoManager = VideoManager([str(inFile)])
    statsManager = StatsManager()
    sceneManager = SceneManager(statsManager)
    sceneManager.add_detector(ContentDetector())
    baseTimecode = videoManager.get_base_timecode()

    videoManager.start()
    sceneManager.detect_scenes(frame_source=videoManager)
    sceneList = sceneManager.get_scene_list(baseTimecode)

    splitList = [str(scene[0].get_frames()) for scene in sceneList][1:]

    return splitList


def main():
    parser = argparse.ArgumentParser(
        description="A simple AV1/HEVC encoding tool.")
    parser.add_argument('input', type=Path, help='file to encode')
    parser.add_argument(
        '--tempdir', type=Path, help='directory in which to work \
(default: randomly generated)')
    parser.add_argument('-o', '--output', type=Path, default="output.mkv",
                        help='final encode output file (default: output.mkv)')
    parser.add_argument(
        '-e', '--encoder', default='av1', choices=['av1', 'hevc'],
        help='encoder to use (default: av1)')
    parser.add_argument('-m', '--makefile', type=Path, default="Makefile",
                        help='makefile name to write to (default: Makefile)')
    parser.add_argument('--splits', default=None, type=int,
                        help='number of even splits to make')
    parser.add_argument('--splitsfile', default=None, type=Path,
                        help='file containing the frames on which to split\
 (default: [input].csv)')
    parser.add_argument('--nvidia', action='store_true',
                        help='use NVIDIA hardware acceleration (nvenc/dec)')
    parser.add_argument('--version', action='version', version='ma1ke v0.1')
    args = parser.parse_args()

    if args.tempdir is None:
        dir = args.input.parent
        dir = dir if os.path.exists(dir) else Path('./')
        args.tempdir = Path(tempfile.mkdtemp(dir=dir))
        args.tempdir.rmdir()

    if not args.input.exists():
        warn("Your input file does not exist, you will have to"
             " create it before you run make.", category=RuntimeWarning)

    # Ridding input of spaces, parenthesis
    if " " in (s := str(args.input)) or '(' in s or ')' in s:
        warn("Input file contains a dangerous character. Creating a safe "
             "symlink here.")
        f, newFile = tempfile.mkstemp(suffix=args.input.suffix,
                                      dir=args.tempdir)
        os.close(f)
        newFile = Path(newFile).relative_to(Path.cwd())
        newFile.unlink()
        newFile.symlink_to(args.input)
        args.input = newFile

    # Ridding output of spaces, parenthesis
    if " " in (s := str(args.output)) or '(' in s or ')' in s:
        warn("Output file contains a dangerous character. Creating a safe "
             "symlink and copy rule.")
        f, newFile = tempfile.mkstemp(suffix=args.output.suffix, dir='./')
        os.close(f)
        newFile = Path(newFile).relative_to(Path.cwd())
        newFile.unlink()
        newFile.symlink_to(args.input)
        args.input = newFile

    if args.input.resolve() == args.output.resolve():
        warn("Output and input filenames refer to the same file.")

    if args.tempdir.exists() and args.tempdir.iterdir():
        warn("Temporary directory not empty: files may be overwritten.")

    if args.splitsfile is None:
        args.splitsfile = args.input.with_suffix('.csv')

    if args.splitsfile.exists():
        with open(args.splitsfile) as f:
            o = f.read().strip()
            if o:
                splits = o.split(',')
            else:
                splits = []
    else:
        if args.splits is not None:
            from scenedetect.video_manager import VideoManager

            videoManager = VideoManager([str(args.input)])
            total = videoManager.get_duration()[0]
            total = total.get_frames()

            splits = [str(i*total//args.splits) for i in range(1, args.splits)]
        else:
            splits = sceneDetect(args.input, args.splits)

        with args.splitsfile.open('w') as f:
            print(','.join(splits), file=f)

    commandList = [
        All(),
        Clean(),
        Prepare(splits),
        NamedPipe(),
        Tqdm(splits),
        VMAF(),
        GetAudio(),
        SplitFile(splits),
        PasteFiles(splits),
        FrameCount("$(input)", "$(inframes)"),
        FrameCount("$(output)", "$(outframes)"),
        FrameCount("%.mkv", "%.fc"),
        Recount(),
        MatchEncodedFrames(),
        MatchOutputFrames(), ]

    if args.encoder == 'hevc':
        commandList.append(HEVCEncodeFile(nvidia=args.nvidia))
    else:
        commandList.append(SVTEncodeFile())

    with open('Makefile', 'w') as fo:
        print("# Generated by ma1ke v0.1\n", file=fo)
        print(".SECONDARY:", file=fo)
        print(".PHONY: all clean audio split verifyOutputFrames tqdm "
              "recount-%", file=fo)

        print(f'tempdir = {args.tempdir}', file=fo)
        print("$(shell mkdir -p $(tempdir))\n", file=fo)

        hardwareDec = ' -hwaccel nvdec' if args.nvidia else ''
        print(f"ffmpegcommand = ffmpeg -y -v 8{hardwareDec}", file=fo)
        print("svtexec = SvtAv1EncApp\n", file=fo)

        print(f'input = {os.path.normpath(args.input)}', file=fo)
        print(f'output = {os.path.normpath(args.output)}\n', file=fo)

        inframes = os.path.join("$(tempdir)",
                                Path(args.input.name).with_suffix(".fc"))
        print(f'inframes = {inframes}', file=fo)
        outframes = os.path.join("$(tempdir)",
                                 Path(args.output.name).with_suffix(".fc"))
        print(f'outframes = {outframes}', file=fo)
        vmaf = os.path.normpath(args.output.with_suffix(".vmaf.xml"))
        print(f'vmaf = {vmaf}\n', file=fo)

        for command in commandList:
            print(command.makeCommand(), end='\n\n', file=fo)

    if (mv := testMakeVersion()) == -1:
        warn("GNU make not found.")
    elif not mv:
        warn("GNU make is a version lower than 4.3\nYou MUST run \
`make split` before running the multi-threaded encode.")


if __name__ == '__main__':
    main()
