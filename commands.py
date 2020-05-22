import os
import tempfile

FFMPEG_COMMAND = "ffmpeg -y -v 8"
SVT_COMMAND = "SvtAv1EncApp"
TEMP_DIR = tempfile.mkdtemp(dir='./')
print(f"Temporary directory {TEMP_DIR} created.")


class Command:
    def makeCommand(self):
        return " ".join(self.outputs) + ": " + " ".join(self.sources) + "\n"


class SplitFile(Command):
    def __init__(self, inFile, splits):
        super().__init__()
        self.inFile = inFile
        self.splits = splits

        self.numParts = len(splits) + 1
        self.sources = [self.inFile]
        self.outputs = [os.path.join(TEMP_DIR, "split", f"{i:05}.mkv")
                        for i in range(self.numParts)]

    def makeCommand(self):
        r = "# SplitFile\n"
        r += " ".join(self.outputs) + " &: " + " ".join(self.sources) + "\n"
        r += f"\tmkdir -p {os.path.join(TEMP_DIR, 'split')}\n"
        r += (f"\t{FFMPEG_COMMAND} "
              f"-i {self.inFile} "
              "-map 0:v:0 -an -c copy "
              "-avoid_negative_ts 1 ")
        if self.splits:
            r += "-f segment -segment_frames " +\
                 ','.join(str(e) for e in self.splits) + " "
            r += os.path.join(TEMP_DIR, "split", "%05d.mkv") + "\n"
        else:
            r += os.path.join(TEMP_DIR, "split", "00000.mkv") + "\n"

        r += f"split: {' '.join(self.outputs)} ;\n"

        return r


class GetAudio(Command):
    def __init__(self, inFile):
        super().__init__()
        self.inFile = inFile

        self.sources = [self.inFile]
        self.outputs = [os.path.join(TEMP_DIR, "audio.mkv")]

    def makeCommand(self):
        r = "# GetAudio\n"
        r += super().makeCommand()
        r += f"\tmkdir -p {TEMP_DIR}\n"
        r += (f"\t{FFMPEG_COMMAND} "
              f"-i {self.inFile} -vn -c:a copy " +
              self.outputs[0] + "\n")
        r += f"audio: {self.outputs[0]} ;\n"
        return r


class PasteFiles(Command):
    def __init__(self, splits):
        self.numParts = len(splits) + 1
        self.concatFile = "concat.txt"
        self.audioFile = os.path.join(TEMP_DIR, "audio.mkv")

        self.sources = [os.path.join(TEMP_DIR, "encode", f"{i:05}.mkv")
                        for i in range(self.numParts)] + [self.audioFile]
        self.sources += [os.path.join(TEMP_DIR, "check", f"{i:05}.match")
                         for i in range(self.numParts)]
        self.outputs = ["output.mkv"]

    def makeCommand(self):
        r = "# PasteFiles\n"
        r += super().makeCommand()
        r += ('\techo "$^" | sed -E "s/ /\\n/g" | grep -Ee ".mkv$$" | '
              'grep -Ev "audio.mkv$$" | '
              r"""awk '{print "file '\''" $$1 "'\''"}' > """
              f"{self.concatFile}\n")
        r += (f"\t{FFMPEG_COMMAND} -f concat -safe 0 -i {self.concatFile} "
              f"-i {self.audioFile} -c copy {self.outputs[0]}\n")
        r += f"\trm -f {self.concatFile}\n"
        return r


class All(Command):
    def makeCommand(self):
        return "all: verifyOutputFrames ;\n"


class Prepare(Command):
    def __init__(self, splits):
        numParts = len(splits) + 1
        audioFile = os.path.join(TEMP_DIR, "audio.mkv")
        self.sources = [os.path.join(TEMP_DIR, "split", f"{i:05}.fc")
                        for i in range(numParts)] + [audioFile]

    def makeCommand(self):
        return "prepare: " + ' '.join(self.sources) + " ;\n"


class FrameCount(Command):
    def __init__(self, inFile, output):
        self.sources = [inFile]
        self.outputs = [output]

    def makeCommand(self):
        r = f"# FrameCount {self.sources[0]}\n"
        r += super().makeCommand()
        r += (f"\t{FFMPEG_COMMAND} -v 32 -i $< -map 0:v:0 "
              "-c copy -f null - 2>&1 >/dev/null | grep -e '^frame=' | "
              r'sed -E "s/frame=\s*([0-9]+)\s.*/\1/" > $@' '\n')
        return r


class MatchFrames(Command):
    def __init__(self, name, frames1, frames2):
        self.sources = [frames1, frames2]
        self.outputs = [name]

    def makeCommand(self):
        r = f"# MatchFrames {self.sources[0]}\n"
        r += super().makeCommand()
        r += f"\tmkdir -p {os.path.join(TEMP_DIR, 'check')}\n"
        r += "\tif ! cmp -s $^; then \\\n"
        r += '\t\techo "Error while verifying frame counts: $^."; \\\n'
        r += '\t\techo "You should try removing the encoded video."; \\\n'
        r += "\t\tfalse; \\\n"
        r += "\tfi\n"
        r += "\tcp $< $@\n"
        return r


class Clean(Command):
    def __init__(self, inFile):
        self.inFile = inFile

    def makeCommand(self):
        return (f"clean:\n\trm -rf {TEMP_DIR}\n"
                "\trm -f output.fc verifyOutputFrames "
                f"{os.path.splitext(self.inFile)[0]}.fc\n")


class SVTEncodeFile(Command):
    def __init__(self, width, height):
        self.sources = [os.path.join(TEMP_DIR, "split", "%.mkv"),
                        os.path.join(TEMP_DIR, "split", "%.fc")]
        self.outputs = [os.path.join(TEMP_DIR, "encode", "%.mkv")]

        self.width, self.height = width, height

    def makeCommand(self):
        r = "# SVTEncodeFile\n"
        r += super().makeCommand()
        r += f"\tmkdir -p {os.path.join(TEMP_DIR, 'encode')}\n"
        r += (f"\t{FFMPEG_COMMAND} -i $< -strict 1 -pix_fmt yuv420p "
              "-f yuv4mpegpipe - | "
              f"{SVT_COMMAND} -i stdin --preset 8 "
              f"-w {self.width} -h {self.height} "
              "--tile-rows 2 --tile-columns 3 --output $@")

        try:
            import tqdm
            r += (" 2>&1 >/dev/null | "
                  r"stdbuf -i0 -o0 tr '\b' '\n' | "
                  "stdbuf -i0 -o0 grep -Ee '[0-9]+$$' | "
                  "tqdm --total $$(cat $(patsubst %.mkv,%.fc,$<)) > /dev/null")
        except ModuleNotFoundError:
            pass

        return r + "\n"


class HEVCEncodeFile(Command):
    def __init__(self):
        self.sources = [os.path.join(TEMP_DIR, "split", "%.mkv"), ]
                        # os.path.join(TEMP_DIR, "split", "%.fc")]
        self.outputs = [os.path.join(TEMP_DIR, "encode", "%.mkv")]

    def makeCommand(self):
        r = "# HEVCEncodeFile\n"
        r += super().makeCommand()
        r += f"\tmkdir -p {os.path.join(TEMP_DIR, 'encode')}\n"
        r += (f"\t{FFMPEG_COMMAND} -hwaccel nvdec -i $< -c:v hevc_nvenc "
              "-crf 28 $@\n")
        return r
