import subprocess
from typing import Tuple, Union


class FfmpegProcess:
    def __init__(self, video_source: str, audio_source: Union[str, None], streaming_server: str, 
                 resolution: Tuple[int, int], fps: float, sample_rate: int, show_log=True):
        self.video_source = video_source
        self.audio_source = audio_source
        
        self.streaming_server = streaming_server
        self.resolution = resolution
        self.fps = fps
        self.sample_rate = sample_rate
        self.show_log = show_log
        
        self.ffmpeg_process = None
        
    def _get_command(self):
        width, height = self.resolution
        
        cmd_begin = [
            'ffmpeg',
            '-y', '-re',
        ]
        cmd_video_input = [
            '-probesize', '16k',
            '-f', 'rawvideo',
            '-vcodec','rawvideo',
            '-pix_fmt', 'bgr24',
            '-s', "{}x{}".format(width, height),
            '-r', str(self.fps),
            '-i', str(self.video_source),
        ]
        cmd_audio_input = [
            '-probesize', '16k',
            '-f', 'f32le',
            '-ar', str(self.sample_rate),
            '-i', str(self.audio_source),
        ]
        cmd_output = [
            '-g', '10',
            '-tune', 'zerolatency',
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-pix_fmt', 'yuv420p',
            '-preset', 'veryfast', 
            '-f', 'flv',
            # '-fflags', 'flush_packets',
            self.streaming_server,
        ]
        cmd = []
        if self.audio_source is None:
            cmd = cmd_begin + cmd_video_input + cmd_output
        else:
            cmd = cmd_begin + cmd_video_input + cmd_audio_input + cmd_output

        return cmd
    
    def run(self):
        cmd = self._get_command()    
        
        if self.show_log:
            print("FFmpeg command:", cmd)

        stdout, stderr = subprocess.DEVNULL, subprocess.DEVNULL
        if self.show_log:
            stdout, stderr = None, None
        self.ffmpeg_process = subprocess.Popen(cmd, stdout=stdout, stderr=stderr)

    def wait(self, timeout: Union[float, None]=None):
        self.ffmpeg_process.wait(timeout)
