# ma1ke

## A simple, barebones tool for parallelized AV1/HEVC encoding

Example with default parameters:

```bash
    python ma1ke.py input.mp4
    make
```

Customizable encoding parameters, and easy, built-in parallelism:

```bash
    python ma1ke.py -e hevc -m Makefile.input input.mp4		# Write to Makefile.input
    make -f Makefile.input -j 4 				# Run 4 encodes at a time
```

Automatic resuming whe interrupted, progress bar for AV1 encodes.

## Requirements

- Python version **3.6 or greater**
- GNU `make` version **4.3 or greater**
- A supported encoder: `libx265` for HEVC and `SVT-AV1` for AV1
- Semi-optional: [PySceneDetect](https://pyscenedetect.readthedocs.io/en/latest/) for automatic splitting on scenes
- Optional: `tqdm` for progress bar in AV1

## Usage

```
usage: ma1ke.py [-h] [--tempdir TEMPDIR] [-o OUTPUT] [-e {av1,hevc}] [-m MAKEFILE] [--splits SPLITS] [--nvidia] [--version] input

A simple AV1/HEVC encoding tool.

positional arguments:
  input                 File to encode.

optional arguments:
  -h, --help            show this help message and exit
  --tempdir TEMPDIR     directory in which to work(default: randomly generated)
  -o OUTPUT, --output OUTPUT
                        final encode output file (default: output.mkv)
  -e {av1,hevc}, --encoder {av1,hevc}
                        encoder to use (default: av1)
  -m MAKEFILE, --makefile MAKEFILE
                        makefile name to write to (default: Makefile)
  --splits SPLITS       file containing the frames on which to split. (default: [input].csv)
  --nvidia              use NVIDIA hardware acceleration (nvenc/dec)
  --version             show program's version number and exit
```
