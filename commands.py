import os
import tempfile

FFMPEG_COMMAND = "ffmpeg -y -v 8"
TEMP_DIR = tempfile.mkdtemp(dir='./')
print(f"Temporary directory {TEMP_DIR} created.")


class Command:
    def makeCommand(self):
        return " ".join(self.outputs) + ": " + " ".join(self.sources) + "\n"


class SplitFile(Command):
    def __init__(self, input, splits):
        super().__init__()
        self.input = input
        self.splits = splits

        self.numParts = len(splits) + 1
        self.sources = [self.input]
        self.outputs = [os.path.join(TEMP_DIR, "split", f"{i:05}.mkv")
                        for i in range(self.numParts)]

    def makeCommand(self):
        r = "# SplitFile\n"
        r += super().makeCommand()
        r += f"\tmkdir -p {os.path.join(TEMP_DIR, 'split')}\n"
        r += (f"\t{FFMPEG_COMMAND} "
              f"-i {self.input} "
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
    def __init__(self, input):
        super().__init__()
        self.input = input

        self.sources = [self.input]
        self.outputs = [os.path.join(TEMP_DIR, "audio.mkv")]

    def makeCommand(self):
        r = "# GetAudio\n"
        r += super().makeCommand()
        r += f"\tmkdir -p {TEMP_DIR}\n"
        r += (f"\t{FFMPEG_COMMAND} "
              f"-i {self.input} -vn -c:a copy " +
              self.outputs[0] + "\n")
        r += f"audio: {self.outputs[0]} ;\n"
        return r


class PasteFiles(Command):
    def __init__(self, splits):
        self.numParts = len(splits) + 1
        self.concatFile = "concat.txt"
        self.audioFile = os.path.join(TEMP_DIR, "audio.mkv")

        self.sources = [os.path.join(TEMP_DIR, "split", f"{i:05}.mkv")
                        for i in range(self.numParts)] + [self.audioFile]
        self.sources += [os.path.join(TEMP_DIR, "check", f"{i:05}.match")
                         for i in range(self.numParts)]
        self.outputs = ["output.mkv"]

    def makeCommand(self):
        r = "# PasteFiles\n"
        r += super().makeCommand()
        r += (f"\tseq -f '%05g' 0 {self.numParts - 1} | "
              r"""awk '{print "file '\''""" +
              os.path.join(TEMP_DIR, 'split') + r"""/" $$1 ".mkv'\''"}' > """
              f"{self.concatFile}\n")
        r += (f"\t{FFMPEG_COMMAND} -f concat -safe 0 -i {self.concatFile} "
              f"-i {self.audioFile} -c:a copy -c copy "
              f"{self.outputs[0]}\n")
        r += f"\trm -f {self.concatFile}\n"
        return r


class All(Command):
    def makeCommand(self):
        return "all: verifyOutputFrames ;\n"


class Prepare(Command):
    def __init__(self, splits):
        numParts = len(splits) + 1
        audioFile = os.path.join(TEMP_DIR, "audio.mkv")
        self.sources = [os.path.join(TEMP_DIR, "split", f"{i:05}.mkv")
                        for i in range(numParts)]
        self.sources += [os.path.join(TEMP_DIR, "split", f"{i:05}.fc")
                         for i in range(numParts)] + [audioFile]

    def makeCommand(self):
        return "prepare: " + ' '.join(self.sources) + " ;\n"


class FrameCount(Command):
    def __init__(self, input, output):
        self.sources = [input]
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
        r += "\tif ! cmp -s $^\n"
        r += "\tthen\n"
        r += '\t\techo "Error while verifying frame counts: $^."\n'
        r += '\t\techo "You should try removing the encoded video."\n'
        r += "\t\texit 2\n"
        r += "\tfi\n"
        r += "\ttouch $@\n"
        return r


class Clean(Command):
    def makeCommand(self):
        return f"clean:\n\trm -rf {TEMP_DIR}\n"
