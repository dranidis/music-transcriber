import pygame
from pydub import AudioSegment
import numpy as np
import librosa

# a function that reads an audio file and returns the audio array, sample rate, and number of channels
def read_audio_file(file_path):
    audio_segment = AudioSegment.from_file(file_path)
    sample_rate = audio_segment.frame_rate
    num_channels = audio_segment.channels
    sample_width = audio_segment.sample_width
    raw_data = audio_segment.raw_data
    audio_array = np.frombuffer(raw_data, dtype=np.int16)
    if num_channels == 2:
        audio_array = audio_array.reshape((-1, 2))

    return audio_array, sample_rate, num_channels

# a function that returns the audio array starting from start_time and lasting duration seconds
def get_audio_array(audio_array, start_time, duration, sample_rate):
    return audio_array[int(start_time * sample_rate):int((start_time + duration) * sample_rate)]

# a function that takes an audio array and a slow_down_rate and returns a stretched audio array
def stretch_audio(audio_array, slow_down_rate):
    # prepare the audio by converting the audio array to float32
    audio = audio_array.astype(np.float32) / 32767.0
    # stretch the audio
    stretched_audio = librosa.effects.time_stretch(audio, rate=slow_down_rate)
    # convert the stretched audio to int16
    stretched_audio_int16 = (stretched_audio * 32767).astype(np.int16)
    # If mono, convert to stereo by duplicating the channel
    # if stretched_audio.ndim == 1:
    #     stretched_audio_int16 = np.stack((stretched_audio_int16, stretched_audio_int16), axis=-1)
    return stretched_audio_int16

class Core:
    def __init__(self, root, plot):
        self.root = root
        self.plot = plot

        # Initialize Pygame mixer
        pygame.mixer.init()
        pygame.init()

        self.beats = []
        self.measures = []

        # Audio data
        self.original_data = None
        self.playing_data = None
        self.sample_rate = None
        self.num_channels = None

        # Playback and loop state
        self.playing = False
        self.stopped = False
        self.loop_start = 0
        self.loop_end = None
        self.start_play_time = None


        self.paused_at = 0

    def on_closing(self):
        pygame.mixer.stop()  # Stop music playback
        pygame.quit()

    def load_mp3_from_file_path(self, file_path):
        self.original_data, self.sample_rate, self.num_channels = read_audio_file(file_path)
        self.playing_data = self.original_data
        # Display waveform
        self.plot.display_waveform(self)

    def toggle_play_pause(self, event):
        print("Toggling play/pause")
        if self.playing:
            self.stop_mp3()  # Pause the music
        else:
            self.play_mp3() # Unpause the music

    def play_mp3(self):
        pygame.mixer.quit()
        self.playing = False
        print("Stopped")

        pygame.mixer.init()
        pygame.init()
        self.paused_at = None

        if self.playing_data.any():
            if self.num_channels == 1:
                audio = np.stack((self.playing_data, self.playing_data), axis=-1)
                sound = pygame.mixer.Sound(buffer=audio)

                # Play the sound in a loop
                sound.play(loops=-1)

                # record the time the playback started
                self.start_play_time = pygame.time.get_ticks()
                print(f"Start time: {self.start_play_time}")

                self.playing = True
                self.plot.update_plot()  # Start the plot update loop   

                print("Playing")


    def get_current_time(self):
        return pygame.time.get_ticks() - self.start_play_time + self.loop_start

    # def play_mp3(self):
    #     pygame.mixer.quit()
    #     self.playing = False
    #     print("Stopped")

    #     if self.stopped:
    #         self.stopped = False
    #         return

    #     pygame.mixer.init()
    #     pygame.init()
    #     self.paused_at = None

    #     if self.playing_data.any():
    #         if self.num_channels == 1:
    #             audio = np.stack((self.playing_data, self.playing_data), axis=-1)
    #             sound = pygame.mixer.Sound(buffer=audio)

    #             # Play the sound
    #             sound.play()

    #             # record the time the playback started
    #             self.start_play_time = pygame.time.get_ticks()
    #             print(f"Start time: {self.start_play_time}")

    #             self.playing = True
    #             self.plot.update_plot()  # Start the plot update loop   

    #             print("Playing")

    #             # Calculate the duration of the sound in seconds
    #             duration = len(self.playing_data) / self.sample_rate

    #             # Start a timer to call play_mp3 again after the sound finishes playing
    #             if not self.stopped:
    #                 threading.Timer(duration, self.play_mp3).start()    

    def on_select(self, xmin, xmax):
        # Convert sample indices to time in milliseconds
        self.loop_start = int((xmin  / self.sample_rate) * 1000)
        self.loop_end = int((xmax  / self.sample_rate) * 1000)
        print(f"Selected region from {self.loop_start} ms to {self.loop_end} ms")

        self.playing_data = get_audio_array(self.original_data, self.loop_start/1000, 
                                       self.loop_end/1000 - self.loop_start/1000,
                                       self.sample_rate)
        # if self.playing:
        #     self.play_mp3()

    # def on_plot_click(self, start_at):

    #     self.playing_data = get_audio_array(self.original_data, start_at/1000,
    #                                         self.original_data.shape[0]/self.sample_rate - start_at/1000,
    #                                         self.sample_rate)
    #     self.loop_start = start_at
    #     self.loop_end = None

    def on_click(self, xdata):
        # # return if the mouse if moving
        # if event.button != 1:
        #     return

        x = xdata  * self.plot.plot_downsample
        start_at = int((x / self.sample_rate) * 1000)

        self.playing_data = get_audio_array(self.original_data, start_at/1000,
                                            self.original_data.shape[0]/self.sample_rate - start_at/1000,
                                            self.sample_rate)
        self.loop_start = start_at
        self.loop_end = None


        self.plot.current_plot_pos = int(start_at / 1000 * self.sample_rate / self.plot.plot_downsample)

        # self.plot.draw_plot()

        print(f"Clicked at x1={start_at}")

    def stop_mp3(self):
        if self.playing:
            pygame.mixer.stop()
            self.playing = False
            self.plot.update_plot()
            print("Stopped")

    def pause_mp3(self):
        if self.playing_data.any():
            if self.playing:
                pygame.mixer.pause()
                # record the time the playback was paused
                self.playing = False
                self.paused_at = pygame.time.get_ticks()

                self.plot.update_plot() 
                print(f"Paused at {self.paused_at}")
                print("Paused")
            else:
                if self.paused_at:
                    pygame.mixer.unpause()
                    # record the time the playback was unpaused
                    unpause_time = pygame.time.get_ticks()
                    self.start_play_time += unpause_time - self.paused_at

                    print(f"paused for {unpause_time - self.paused_at} ms")
                    print(f"Start time: {self.start_play_time}")

                    self.playing = True
                    self.plot.update_plot()  
                    print("Unpaused")

    def reset_loop(self):
        self.playing_data = self.original_data
        self.loop_start = 0
        self.loop_end = self.playing_data.shape[0]
        if self.playing:
            self.play_mp3()        
        print("Loop reset")

    def slow_down(self):
        slow_down_rate = 0.8
        stretched_audio_int16 = stretch_audio(self.original_data, slow_down_rate)  

        self.original_data = stretched_audio_int16 
        self.plot.display_waveform(self)
        
        self.playing_data = stretched_audio_int16
     
        print(f"Slow down rate: {slow_down_rate}")

    def mark_beat(self, event):
        current_time = self.get_current_time()
        self.beats.append(current_time)
        # self.plot.update_beat_axis()
        # print(self.beats)

    def mark_measure(self, event):
        self.measures.append(self.get_current_time())
        print(self.measures)
