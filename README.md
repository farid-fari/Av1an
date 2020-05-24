# ma1ke

## A simple, barebones tool for parallelized AV1/HEVC encoding

## WARNING: highly WIP, probably only works on Arch Linux

Example with default parameters:

```bash
    ma1ke.py input.mp4
    make
```

Customizable encoding parameters, and easy, built-in parallelism:

```bash
    ma1ke.py -e hevc -m Makefile.input input.mp4		# Write to Makefile.input
    make -f Makefile.input -j 4 				# Run 4 encodes at a time
```

Automatic resuming when interrupted, multithreading, and progress bar for AV1
encodes.

## Requirements

- Python version **3.8 or greater**
- GNU `make` version **4.3 or greater**
- A supported encoder: `libx265` for HEVC and `SVT-AV1` for AV1
- Semi-optional: [PySceneDetect](https://pyscenedetect.readthedocs.io/en/latest/) for automatic splitting on scenes
- Optional: `tqdm` for progress bar in AV1

## Usage

The python script will generate a makefile, which you can use with GNU make to
encode your video. For a simple case, the only argument you will want to
specify is `-e hevc` if you want an HEVC encode or `-e av1` for AV1.


```
usage: ma1ke.py [-h] [--tempdir TEMPDIR] [-o OUTPUT] [-e {av1,hevc}]
		[-m MAKEFILE] [--splits SPLITS] [--splitsfile SPLITSFILE]
		[--nvidia] [--version] input

A simple AV1/HEVC encoding tool.

positional arguments:
  input                 file to encode

optional arguments:
  -h, --help            show this help message and exit
  --tempdir TEMPDIR     directory in which to work (default: randomly generated)
  -o OUTPUT, --output OUTPUT
                        final encode output file (default: output.mkv)
  -e {av1,hevc}, --encoder {av1,hevc}
                        encoder to use (default: av1)
  -m MAKEFILE, --makefile MAKEFILE
                        makefile name to write to (default: Makefile)
  --splits SPLITS       number of even splits to make
  --splitsfile SPLITSFILE
                        file containing the frames on which to split (default: [input].csv)
  --nvidia              use NVIDIA hardware acceleration (nvenc/dec)
  --version             show program's version number and exit
```

Once the command completes, you will have a makefile named `Makefile`. You can
then begin the encode using `make -j n` where `n` is the number of simultaneous
encodes you want to allow.

**NOTE**: if using `make` version lower than `4.3`, you should first run `make
split` **without the `-j` argument**, and only then run the command above.

### Input splitting

The `--splitsfile` indicates where the splitting locations should be saved and
restored. The default is next to your input file, with the `.csv` extension
instead. If the file exists, the splits will be read from there.

If the file doesn't exist, you will need for *PySceneDetect* to be installed
(see requirements). You can either split the file evenly with `--splits`, or
let *PySceneDetect* detect scene changes to split on.

Scene detection can take a while, in which case it is recommended to use the
`--splits` option. For no splits, specify `--splits 0`.
