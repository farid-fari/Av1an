#!/usr/bin/env python

from collections import defaultdict
from tqdm import tqdm
import sys

total = int(sys.argv[1])
progress = defaultdict(int)
bar = tqdm(total=total, leave=False, unit='fr')

while True:
    for line in open(sys.argv[2], 'r'):
        proc, numFrames = line.split('\t')

        if 'done' in numFrames:
            del progress[proc]

        addFrames = int(numFrames) - progress[proc]
        bar.update(addFrames)
        progress[proc] = int(numFrames)

        if not len(progress) or sum(progress.values()) >= total:
            exit()
