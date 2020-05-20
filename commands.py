import os
import subprocess
# from subprocess import PIPE, STDOUT

FFMPEG_COMMAND = ["ffmpeg", "-hide_banner", "-y"]
TEMP_DIR = './temp'


class Command:
    def __init__(self):
        self.done = False
        self.output = (None, None)

    def verifyDone(self):
        return self.done

    def execute(self):
        self.done = True

    def stdout(self):
        return self.output[0]

    def stdin(self):
        return self.output[1]


class SplitFile(Command):
    def __init__(self, path, splits):
        super().__init__()
        self.path = path
        self.splits = splits

    def command(self):
        r = FFMPEG_COMMAND + [
            '-i', self.path,
            '-map', "0:v:0",
            '-an',
            '-c', 'copy',
            '-avoid_negative_ts', '1']
        if self.splits:
            r += [
                '-f', 'segment',
                '-segment_frames', self.splits,
                os.path.join(TEMP_DIR, "split", "%05d.mkv")]
        return r

    def execute(self):
        result = subprocess.run(self.command(), capture_output=True)
        self.output[0] = result.stdout.decode('utf-8')
        self.output[1] = result.stderr.decode('utf-8')
        super().execute()

    def verifyDone(self):
        if not super().verifyDone():
            return False
        return all(os.path.isfile(
            os.path.join(TEMP_DIR, "split", f"{i:05}.mkv"))
                   for i in range(len(self.splits) + 1))
