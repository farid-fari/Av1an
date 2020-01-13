
<h1 align="center">
    <br>
    Av1an
    </br>
</h1>

<h2 align="center">All-in-one tool for streamlining av1 encoding</h2>

![alt text](https://cdn.discordapp.com/attachments/665440744567472169/665760393498460196/banner.jpg)

<h2 align="center">Easy And Efficient </h2>

Start using AV1 encoding. At the moment only Aomenc and Rav1e are supported

Example with default parameters:

    ./avian.py -i input

With your own parameters:

    ./avian.py -i input -enc aomenc -e '--cpu-used=3 --end-usage=q --cq-level=30' -a '-c:a libopus -b:a 24k'

<h2 align="center">Usage</h2>

    -i --file_path          Input file (relative or absolute path)
    -enc --encoder          Encoder to use (aomenc or rav1e. Default: aomenc. Example: -enc rav1e)
    -e --encoding_params    Encoder settings flags 
    -a --audio_params       FFmpeg audio settings flags (Default: -c:a copy (copy audio from source to output)
    -t --workers            Maximum number of workers (overrides automatically set number of workers.
                            Aomenc recommended value is YOUR_THREADS - 2 (Single thread per worker)
                            Rav1e can use tiles that uses multiple threads, example:  
                            '--tile-rows 2 --tile-cols 2' load 2.5 to 3.5 threads, 4 is optimal for 6/12 cpu 
    -tr --threshold         PySceneDetect threshold (Optimal values in range 15 - 50.
     Bigger value = less sensitive )


<h2 align="center">Main Features</h2>

**Spliting video by scenes for parallel encoding** because AV1 encoders currently not good at multithreading encoding is limited to single threads or couple of cores at the same time.

[PySceneDetect](https://pyscenedetect.readthedocs.io/en/latest/) used for spliting video by scenes and running multiple encoders.

Simple and clean console look

Automatic determination of how many workers the host can handle

Building encoding queue with bigger files first, minimizing waiting for last scene to encode

Both video and audio encoding option with FFmpeg

And many more to go..

## Dependencies

* [FFmpeg](https://ffmpeg.org/download.html)
* [AOMENC](https://aomedia.googlesource.com/aom/) For Aomenc encoder
* [Rav1e](https://github.com/xiph/rav1e) For Rav1e encoder
* [PyScenedetect](https://pyscenedetect.readthedocs.io/en/latest/) 
* [mkvmerge/python-pymkv](https://pypi.org/project/pymkv/)
