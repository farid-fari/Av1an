#!/usr/bin/env python

from collections import defaultdict
from tqdm import tqdm
import sys

total, numproc = int(sys.argv[1]), int(sys.argv[2])
progress = defaultdict(int)
done = set()
bar = tqdm(total=total, leave=False, unit='fr')

while True:
    for line in sys.stdin:
        proc, numFrames = line.split('\t')

        if 'done' in numFrames:
            done.add(proc)
        else:
            addFrames = int(numFrames) - progress[proc]
            bar.update(addFrames)
            progress[proc] = int(numFrames)

    if len(done) >= numproc or sum(progress.values()) >= total:
        exit()
