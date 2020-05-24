import subprocess
import re


def testMakeVersion():
    try:
        c = subprocess.run(['make', '--version'], capture_output=True)
    except FileNotFoundError:
        return -1

    v = c.stdout.decode('utf-8')
    v = v.split('\n')[0]

    if v.startswith("GNU Make 4.3"):
        return True
    return False
