import os

FFMPEG_COMMAND = "$(ffmpegcommand)"
INPUT = "$(input)"
OUTPUT = "$(output)"
SVT_COMMAND = "$(svtexec)"
TEMP_DIR = "$(tempdir)"
NAMED_PIPE = "$(namedpipe)"


class Command:
    def makeCommand(self):
        return " ".join(self.outputs) + ": " + " ".join(self.sources) + "\n"


class SplitFile(Command):
    def __init__(self, splits):
        super().__init__()
        self.splits = splits

        self.numParts = len(splits) + 1
        self.sources = [INPUT]
        self.outputs = [os.path.join(TEMP_DIR, "split", f"{i:05}.mkv")
                        for i in range(self.numParts)] + ["split"]

    def makeCommand(self):
        r = "# SplitFile\n"
        r += " ".join(self.outputs) + " &: " + " ".join(self.sources) + "\n"
        r += f"\t@mkdir -p {os.path.join(TEMP_DIR, 'split')}\n"
        r += (f"\t{FFMPEG_COMMAND} "
              "-i $< -an -c:v copy -avoid_negative_ts 1 ")

        if self.splits:
            r += "-f segment -segment_frames " +\
                 ','.join(str(e) for e in self.splits) + " "
            r += os.path.join(TEMP_DIR, "split", "%05d.mkv")
        else:
            r += os.path.join(TEMP_DIR, "split", "00000.mkv")

        return r


class GetAudio(Command):
    def __init__(self):
        super().__init__()

        self.sources = [INPUT]
        self.outputs = [os.path.join(TEMP_DIR, "audio.mkv"), "audio"]

    def makeCommand(self):
        r = "# GetAudio\n"
        r += super().makeCommand()
        r += f"\t@mkdir -p {TEMP_DIR}\n"
        r += f"\t{FFMPEG_COMMAND} -i $< -vn -c:a copy {self.outputs[0]}"
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
        self.outputs = [OUTPUT]

    def makeCommand(self):
        r = "# PasteFiles\n"
        r += super().makeCommand()
        r += ('\techo "$^" | sed -E "s/ /\\n/g" | grep -Ee ".mkv$$" | '
              'grep -Ev "audio.mkv$$" | '
              r"""awk '{print "file '\''" $$1 "'\''"}' > """
              f"{self.concatFile}\n")
        r += (f"\t{FFMPEG_COMMAND} -f concat -safe 0 -i {self.concatFile} "
              f"-i {self.audioFile} -c copy {self.outputs[0]}\n")
        r += f"\trm -f {self.concatFile}"
        return r


class All(Command):
    def makeCommand(self):
        return "all: verifyOutputFrames"


class Prepare(Command):
    def __init__(self, splits):
        numParts = len(splits) + 1
        audioFile = os.path.join(TEMP_DIR, "audio.mkv")
        self.sources = [os.path.join(TEMP_DIR, "split", f"{i:05}.fc")
                        for i in range(numParts)] + [audioFile]

    def makeCommand(self):
        return "prepare: " + ' '.join(self.sources)


class FrameCount(Command):
    def __init__(self, inFile, output):
        self.sources = [inFile]
        self.outputs = [output]

    def makeCommand(self):
        r = f"# FrameCount {self.sources[0]}\n"
        r += super().makeCommand()
        r += (f"\t{FFMPEG_COMMAND} -v 32 -i $< -an "
              r"-c:v copy -f null - 2>&1 >/dev/null | tr '\r' '\n' | "
              "grep -e '^frame=' | "
              "tail -n 1 | "
              r'sed -E "s/frame=\s*([0-9]+)\s.*/\1/" > $@')
        return r


class MatchEncodedFrames(Command):
    def __init__(self):
        self.sources = [os.path.join(TEMP_DIR, "encode", "%.fc"),
                        os.path.join(TEMP_DIR, "split", "%.fc")]
        self.outputs = [os.path.join(TEMP_DIR, "check", "%.match")]

    def makeCommand(self):
        r = "# MatchFrames\n"
        r += super().makeCommand()
        r += f"\t@mkdir -p {os.path.join(TEMP_DIR, 'check')}\n"
        r += "\t@if ! cmp -s $^; then \\\n"

        def echo(s):
            return f'\t\techo "{s}"; \\\n'
        r += echo("Error while verifying frame counts for $*:")
        r += '\t\tcat $^ | tr "\\n" " "; echo; \\\n'
        r += echo("You can try, in the following order:")
        r += echo("\t\t- recounting the encoded frames with "
                  "'make recount-$*'")
        r += echo("\t\t- reencoding this file with "
                  "'make reencode-%'")
        r += echo("\t\t- restarting the split and encode with 'make split'")
        r += echo("\t\t- restarting everything with 'make clean'")
        r += "\t\tfalse; \\\n"
        r += "\tfi\n"
        r += "\tcp $< $@"
        return r


class MatchOutputFrames(Command):
    def __init__(self):
        self.sources = ["$(inframes)", "$(outframes)"]
        self.outputs = ["verifyOutputFrames"]

    def makeCommand(self):
        r = "# MatchOutputFrames\n"
        r += super().makeCommand()
        r += "\t@if ! cmp -s $^; then \\\n"

        def echo(s):
            return f'\t\techo "{s}"; \\\n'
        r += echo("Error while verifying the output frame count.")
        r += '\t\tcat $^ | tr "\\n" " "; echo; \\\n'
        r += echo("You can try, in the following order:")
        r += echo("\t\t- recounting the output frames with "
                  "'make recount-output'")
        r += echo("\t\t- repasting with 'make paste'")
        r += echo("\t\t- restarting everything with 'make clean'")
        r += "\t\tfalse; \\\n"
        r += "\tfi"
        return r


class Clean(Command):
    def makeCommand(self):
        return f"clean:\n\trm -rf {TEMP_DIR}"


class Encoder(Command):
    def __init__(self):
        self.sources = [os.path.join(TEMP_DIR, "split", "%.mkv"),
                        NAMED_PIPE, 'tqdm']
        self.outputs = [os.path.join(TEMP_DIR, "encode", "%.mkv")]


class SVTEncodeFile(Encoder):
    def makeCommand(self):
        r = "# SVTEncodeFile\n"
        r += super().makeCommand()
        r += f"\t@mkdir -p {os.path.join(TEMP_DIR, 'encode')}\n"
        r += ("\theight=$$(ffprobe $< 2>&1 >/dev/null | "
              "grep -Eoe "
              r"'[0-9]+x[0-9]+,' | sed -E 's/([0-9]+)x.*/\1/')" ";\\\n")
        r += ("\twidth=$$(ffprobe $< 2>&1 >/dev/null | "
              "grep -Eoe "
              r"'[0-9]+x[0-9]+,' | sed -E 's/.*x([0-9]+).*/\1/')" ";\\\n")
        r += (f"\t{FFMPEG_COMMAND} -i $< -strict 1 -pix_fmt yuv420p "
              "-f yuv4mpegpipe - | "
              f"{SVT_COMMAND} -i stdin --preset 8 "
              f"-w $$width -h $$height "
              "--tile-rows 2 --tile-columns 3 --output $@")
        r += (" 2>&1 >/dev/null | "
              r"stdbuf -i0 -o0 tr '\b' '\n' | "
              "stdbuf -i0 -o0 grep -Ee '[0-9]+$$' > $(word 2,$^)")

        return r


class Rav1eEncodeFile(Encoder):
    def makeCommand(self):
        r = "# Rav1eEncodeFile\n"
        r += super().makeCommand()
        r += f"\t@mkdir -p {os.path.join(TEMP_DIR, 'encode')}\n"
        r += ("\theight=$$(ffprobe $< 2>&1 >/dev/null | "
              "grep -Eoe "
              r"'[0-9]+x[0-9]+,' | sed -E 's/([0-9]+)x.*/\1/')" ";\\\n")
        r += ("\twidth=$$(ffprobe $< 2>&1 >/dev/null | "
              "grep -Eoe "
              r"'[0-9]+x[0-9]+,' | sed -E 's/.*x([0-9]+).*/\1/')" ";\\\n")
        r += (f"\t{FFMPEG_COMMAND} -i $< -strict 1 -pix_fmt yuv420p "
              "-f yuv4mpegpipe - | "
              f"{SVT_COMMAND} -i stdin --preset 8 "
              f"-w $$width -h $$height "
              "--tile-rows 2 --tile-columns 3 --output $@")
        r += (" 2>&1 >/dev/null | "
              r"stdbuf -i0 -o0 tr '\b' '\n' | "
              "stdbuf -i0 -o0 grep -Ee '[0-9]+$$' > $(word 2,$^)")

        return r


class HEVCEncodeFile(Encoder):
    def __init__(self, nvidia=False):
        super().__init__()
        self.nvidia = nvidia

    def makeCommand(self):
        r = "# HEVCEncodeFile\n"
        r += super().makeCommand()
        r += f"\t@mkdir -p {os.path.join(TEMP_DIR, 'encode')}\n"
        codec = 'hevc_nvenc' if self.nvidia else 'hevc'
        r += f"\t{FFMPEG_COMMAND} -v 32 -i $< -c:v {codec} $@"
        r += (" 2>&1 >/dev/null | "
              r"stdbuf -i0 -o0 tr '\r' '\n' | "
              "stdbuf -i0 -o0 grep -Ee '^frame=' | "
              r"stdbuf -i0 -o0 sed -E 's/frame=\s+([0-9]+)\s.*/\1/' | "
              r"""stdbuf -i0 -o0 awk '{print "$*\t" $$1}' """
              "> $(word 2,$^)\n")
        r += '\t@echo -e "$*\\tdone" > $(word 2,$^)'

        return r


class VMAF(Command):
    def __init__(self):
        self.sources = [OUTPUT, INPUT, "verifyOutputFrames"]
        self.outputs = ["$(vmaf)"]

    def makeCommand(self):
        r = "# VMAF\n"
        r += super().makeCommand()
        r += (f"\t{FFMPEG_COMMAND} -i $(word 2,$^) -r 60 -i $< "
              '-filter_complex "[0:v]scale=-1:1080:flags=spline[scaled1];'
              '[1:v]scale=-1:1080:flags=spline[scaled2];'
              '[scaled2][scaled1]libvmaf=log_path=$@" -f null -')
        return r


class Recount(Command):
    def __init__(self):
        self.sources = []
        self.outputs = ["recount-%"]

    def makeCommand(self):
        r = "# Recount\n"
        r += super().makeCommand()

        targs = ' '.join([
            os.path.join(TEMP_DIR, 'split', '$*.fc'),
            os.path.join(TEMP_DIR, 'encode', '$*.fc')])

        r += f"\trm -f {targs}\n"
        r += f"\t$(MAKE) {targs}"
        return r


class Tqdm(Command):
    def __init__(self, splits):
        self.sources = ["$(inframes)", NAMED_PIPE]
        self.outputs = ['tqdm']
        self.nProc = len(splits) + 1

    def makeCommand(self):
        r = "# Tqdm\n"
        r += super().makeCommand()
        r += f"\t./progress.py $$(cat $<) {self.nProc} < $(word 2,$^) &"
        return r


class NamedPipe(Command):
    def __init__(self):
        self.sources = []
        self.outputs = [NAMED_PIPE]

    def makeCommand(self):
        r = "# NamedPipe\n"
        r += super().makeCommand()
        r += "\tmkfifo $@"
        return r
