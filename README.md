# PyStreamer

A FFmpeg-based tool that helps you push video and audio to RTMP streaming server in real time. It can be easily integrated into your python DIP workflow to create live streaming applications. 

This repository is currently under development, and the code may be unstable. If you encounter any issues or bugs, please feel free to open an issue.

## Preparation

- Install [FFmpeg](https://ffmpeg.org/).
- Deploy an RTMP server, like [NGINX-based Media Streaming Server](https://github.com/arut/nginx-rtmp-module).

## Usage

First, clone this respository under your workdir:

```shell
$ cd /your/workdir
$ git clone https://github.com/JianghaoLan/pystreamer.git

# /your/workdir
# ├── pystreamer
# │   ├── ...
# ├── your_python_file.py
# └── ...
```

Next, import `Streamer` in your python file:

```shell
from pystreamer import Streamer
```

Then, you can refer to the following example to push your video and audio to RTMP server:

```shell
from pystreamer import Streamer

if __name__ == '__main__':

    # Use opencv to read video frames and librosa to read audio frames. It's not important how you get these data.
    import cv2
    import librosa

    cap = cv2.VideoCapture("test-video.mp4")
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Video info: {width}x{height}, {fps}fps.")

    audio_frames, sr = librosa.load("test_audio.wav")
    print(f"Audio sample rate: {sr}")

    ### 1. create `Streamer` object ###
    rtmp_url = "rtmp://localhost:1935/live/app"
    streamer = Streamer(rtmp_url, (width, height), fps, sr)

    ### 2. invoke `start()` to open ffmpeg process ###
    streamer.start()

    i = 0
    audio_frame_size = sr // fps
    while (cap.isOpened()):
        ret, video_frame = cap.read()
        if not ret:
            break

        audio_frame = audio[i:i+audio_frame_size]

        ### 3. using `push()` to push your media data to RTMP server ###
        # `video_frame`: numpy array (w, h, 3) or (n, w, h, 3), uint8
        # `audio_frame`: 1d numpy array (audio_frame_size, ), float32
        streamer.push(video_frame, audio_frame)

        i += audio_frame_size

    ### 4. `stop()` when you finish your stream ###
    streamer.stop()

    print("Finish.")
```

## Options

`Streamer`'s constructor and `push()` method accept some other parameters you may need. For example, you may want to hide ffmpeg's console output (set `show_log=False`), or don't want to push audio (set `no_audio=True`). You can refer to method's docstring for more detail.

For some other customizations, you may need to modify my code. For example, if you are using other streaming protocols (such as HLS, DASH, etc.) instead of RTMP, check out `FfmpegProcess.py` and modify the FFmpeg command.
