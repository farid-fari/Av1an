# ma1ke

## A simple, barebones tool for parallelized AV1/HEVC encoding

Example with default parameters:

    python ma1ke.py -i input.mp4
    make

Easy, built-in parallelism:

    make -j 4 # Run 4 encodes at a time

Automatic resuming whe interrupted, progress bar for AV1 encodes.

## Requirements

- Python version **3.6 or greater**
- GNU `make` version **4.3 or greater**
- A supported encoder: `libx265` for HEVC and `SVT-AV1` for AV1
- Semi-optional: [PySceneDetect](https://pyscenedetect.readthedocs.io/en/latest/) for automatic splitting on scenes
- Optional: `tqdm` for progress bar in AV1
