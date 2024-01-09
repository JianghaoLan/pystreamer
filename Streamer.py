from typing import Tuple, Union
from queue import Queue, Full

import numpy as np
from .FfmpegProcess import FfmpegProcess

from .TcpDataServer import TcpDataServer


class Streamer:
    def __init__(self, server_url: str, resolution: Tuple[int, int], fps: float, 
                 sample_rate: Union[int, None], max_queue_size: int=25, no_audio: bool=False,
                 show_log: bool=True, disable_warning: bool=False):
        """
        Contruct a Streamer object.

        Args:
            server_url (str): Streaming server address.
            resolution (Tuple[int, int]): Video resolution (width, height).
            fps (float): Video frames per second.
            sample_rate (Union[int, None]): Audio sample rate. This cannot be None unless `no_audio=false`
            max_queue_size (int): The maximum number of buffered frames before send to ffmpeg.
            no_audio (bool): Do not streaming audio.
            show_log (bool): Print log.
            disable_warning (bool): Disable "Sample rate is not divisible by fps" warning. Defaults to False.
        """
        self.server_url = server_url
        self.resolution = resolution
        self.fps = fps
        self.sample_rate = sample_rate
        self.pcm_dtype = np.float32
        self.max_queue_size = max_queue_size
        self.no_audio = no_audio
        self.audio_buffer_size = self.max_queue_size
        self.show_log = show_log
        
        if not no_audio and sample_rate % fps != 0 and not disable_warning:
            import warnings
            warnings.warn(f'Sample rate ({sample_rate}) is not divisible by fps ({fps}).'
                          ' This will cause the video and audio to be out of sync after a long time running.'
                          ' You\'d better use a more appropriate video fps and audio sample rate.'
                          '\nIf you want to ensure video and audio to be sync by yourself, set disable_warning=True'
                          'to disable this warning and passing check_duration=False when using push() method.'
                          ' Please know that this may cause unexpected blocking issues.')
        
        self.start_flag = False
        self.v_queue = None
        self.a_queue = None
        self.v_server = None
        self.a_server = None
        self.ffmpeg_process = None
        
    @staticmethod
    def _pad_or_truncate(audio_frames, target_length):
        return np.pad(audio_frames, 
                      (0, max(0, target_length - audio_frames.shape[0])),
                      'constant', constant_values='0')[:target_length]
    
    def start(self):
        """
        Start Streaming. 
        """
        if self.start_flag:
            return
        self.start_flag = True
        
        self.v_queue = Queue(self.max_queue_size)   
        # We use TCP protocol to transfer data to ffmpeg.
        self.v_server = TcpDataServer(self.v_queue, thread_name='VideoStreamSender')
        self.v_server.start()
        video_source = f'tcp://localhost:{self.v_server.get_port()}'
        
        audio_source = None
        if not self.no_audio:
            self.a_queue = Queue(self.audio_buffer_size)
            self.a_server = TcpDataServer(self.a_queue, thread_name='AudioStreamSender')
            self.a_server.start()
            audio_source = f'tcp://localhost:{self.a_server.get_port()}'

        self.ffmpeg_process = FfmpegProcess(video_source, audio_source, self.server_url, 
                                            self.resolution, self.fps, self.sample_rate,
                                            show_log=self.show_log)
        self.ffmpeg_process.run()

    def push(self, video_frames: np.ndarray, audio_frames: Union[np.ndarray, None]=None, timeout: float=15, check_duration: bool=True):
        """
        Push video and audio frames to streaming server.

        Args:
            video_frames (Union[np.ndarray, None]): A 3d numpy array (height, width, 3) representing one video frame or \
            4d numpy array (n, height, width, 3) representing n video frame.
            audio_frames (Union[np.ndarray, None], optional): A 1d numpy array representating corrsponding audio frames. \
            If not provided, empty (zeros) will be used. By default, this method will enforce the video and audio are of the \
            same duration by truncating or padding the audio if necessary.
            timeout (float, optinoal): Enquene timeout. It blocks at most 'timeout' seconds and raises exception if no free slot \
            was available within that time.
            check_duration (bool): If False, the duration of the video and audio will not be checked, nor will it be truncated \
            or padded. Defaults to True.
        """
        assert self.start_flag == True, 'You should start() this streamer first!'
        
        video_frame_list = []
        audio_frame_list = []
        
        if video_frames is not None:
            assert len(video_frames.shape) in [3, 4] and (video_frames.shape[-2], video_frames.shape[-3]) == self.resolution, \
                'Video_frame must be shape of ({}, {}, 3) or (n, {}, {}, 3).'.format(self.resolution[1], self.resolution[0], 
                                                                                    self.resolution[1], self.resolution[0])
            assert video_frames.dtype == np.uint8, 'Video_frame must be type of uint8.'
            if len(video_frames.shape) == 3:
                video_frame_list = [video_frames]
            else:
                video_frame_list = [frame for frame in video_frames]
        
        if not self.no_audio:
            expected_audio_length = int(self.sample_rate * (len(video_frame_list) / self.fps))
            if audio_frames is not None:
                assert len(audio_frames.shape) == 1 and audio_frames.dtype == self.pcm_dtype, \
                    f'Audio frames must be a 1d np.{self.pcm_dtype} array.'
            else:
                audio_frames = np.zeros((expected_audio_length, ), dtype=self.pcm_dtype)
            if check_duration:
                audio_frames = self._pad_or_truncate(audio_frames, expected_audio_length)
            audio_frame_list = np.array_split(audio_frames, len(video_frame_list))
        
        try:
            
            if self.no_audio:
                for video_frame in video_frame_list:
                    self.v_queue.put(video_frame.tobytes(), timeout=timeout)
                    
            else:
                for video_frame, audio_frame in zip(video_frame_list, audio_frame_list):
                    self.v_queue.put(video_frame.tobytes(), timeout=timeout)
                    self.a_queue.put(audio_frame.tobytes(), timeout=timeout)

        except Full:
            raise Exception("Data enqueuing timeout. Try increasing `max_queue_size` and try again."
                            " If this still happen, it might be some unknown problem with PyStreamer.")

    def stop(self):
        """
        Stop Streaming.
        """
        self.start_flag = False
        if self.v_server is not None:
            self.v_server.stop()
        if self.a_server is not None:
            self.a_server.stop()
        if self.ffmpeg_process is not None:
            self.ffmpeg_process.wait(60)
        
        self.v_queue = None
        self.a_queue = None
        self.v_server = None
        self.a_server = None
        self.ffmpeg_process = None
