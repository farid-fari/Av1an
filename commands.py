import os

FFMPEG_COMMAND = "ffmpeg -hide_banner -y"
TEMP_DIR = '.temp/'


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
        return r


class PasteFiles(Command):
    def __init__(self, splits):
        self.numParts = len(splits) + 1
        self.concatFile = "concat.txt"
        self.audioFile = os.path.join(TEMP_DIR, "audio.mkv")

        self.sources = [os.path.join(TEMP_DIR, "split", f"{i:05}.mkv")
                        for i in range(self.numParts)] + [self.audioFile]
        self.outputs = ["output.mkv"]

    def makeCommand(self):
        r = "# PasteFiles\n"
        r += super().makeCommand()
        r += (f"\tfind {os.path.join(TEMP_DIR, 'split')} -type f | "
              "awk '{print \"file '\\''\" $$1 \"'\\''\"}' > "
              f"{self.concatFile}\n")
        r += (f"\t{FFMPEG_COMMAND} -f concat -safe 0 -i {self.concatFile} "
              f"-i {self.audioFile} -c:a copy -c copy "
              f"{self.outputs[0]}\n")
        r += f"\trm -f {self.concatFile}\n"
        return r


class All(Command):
    def makeCommand(self):
        return "all: output.mkv ;\n"
