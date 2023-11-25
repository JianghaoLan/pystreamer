import subprocess
from typing import Tuple, Union


class FfmpegProcess:
    def __init__(self, video_source: str, audio_source: str, streaming_server: str, 
                 resolution: Tuple[int, int], fps: float, sample_rate: int):
        self.video_source = video_source
        self.audio_source = audio_source
        
        self.streaming_server = streaming_server
        self.resolution = resolution
        self.fps = fps
        self.sample_rate = sample_rate
        
        self.ffmpeg_process = None
    
    def run(self):
        width, height = self.resolution
        
        cmd = [
            'ffmpeg',
            '-y', '-re',
            '-fflags', 'nobuffer',
            '-f', 'rawvideo',
            '-vcodec','rawvideo',
            '-pix_fmt', 'bgr24',
            '-s', "{}x{}".format(width, height),
            '-r', str(self.fps),
            '-i', str(self.video_source),
            '-f', 'f32le',
            '-ar', str(self.sample_rate),
            '-i', str(self.audio_source),
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-pix_fmt', 'yuv420p',
            '-preset', 'veryfast', 
            '-f', 'flv',
            self.streaming_server,
        ]
        print("ffmpeg command:", ' '.join(cmd))

        self.ffmpeg_process = subprocess.Popen(cmd)

    def wait(self, timeout: Union[float, None]=None):
        self.ffmpeg_process.wait(timeout)
