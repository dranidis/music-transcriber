"""
This module contains functions and a class for handling audio data. 

It includes functions to read an audio file, get a specific segment of an audio array, 
and stretch the audio array. It also contains the Core class (definition not fully shown here).
"""

import pygame
from pydub import AudioSegment
import numpy as np
import librosa


def read_audio_file(file_path):
    """
    Reads an audio file and returns the audio array, sample rate, and number of channels.

    Args:
        file_path (str): The path to the audio file.

    Returns:
        tuple: A tuple containing the audio array, sample rate, and number of channels.
    """
    audio_segment = AudioSegment.from_file(file_path)
    sample_rate = audio_segment.frame_rate
    num_channels = audio_segment.channels
    raw_data = audio_segment.raw_data
    audio_array = np.frombuffer(raw_data, dtype=np.int16)
    if num_channels == 2:
        audio_array = audio_array.reshape((-1, 2))

    return audio_array, sample_rate, num_channels


def get_audio_array(audio_array, start_time, duration, sample_rate):
    """
    Returns the audio array starting from start_time and lasting duration seconds.

    Args:
        audio_array (np.array): The audio array.
        start_time (float): The start time in seconds.
        duration (float): The duration in seconds.
        sample_rate (int): The sample rate.

    Returns:
        np.array: The segment of the audio array.
    """
    return audio_array[int(start_time * sample_rate):int((start_time + duration) * sample_rate)]


def stretch_audio(audio_array, slow_down_rate):
    """
    Stretches the audio array by a given rate.

    Args:
        audio_array (np.array): The audio array.
        slow_down_rate (float): The rate to slow down the audio.

    Returns:
        np.array: The stretched audio array.
    """
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
    """
    The Core class handles the audio data and the interaction with the Pygame mixer.

    Attributes:
        root: The root widget of the application.
        plot: The plot widget of the application.
        beats (list): A list to store the beats.
        measures (list): A list to store the measures.
        original_data (np.array): The original audio data.
        playing_data (np.array): The audio data currently being played.
        sample_rate (int): The sample rate of the audio data.
        num_channels (int): The number of channels in the audio data.
    """

    def __init__(self, root, plot):
        """
        Initializes the Core class with the root and plot widgets, initializes the Pygame mixer,
        and initializes the beats, measures, and audio data attributes.

        Args:
            root: The root widget of the application.
            plot: The plot widget of the application.
        """
        self.root = root
        self.plot = plot

        # Initialize Pygame mixer
        pygame.mixer.init()

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
        """
        Stops the music playback and quits Pygame when the application is closed.
        """
        pygame.mixer.stop()  # Stop music playback
        pygame.quit()  # pyLint: disable=no-member

    def load_mp3_from_file_path(self, file_path):
        """
        Loads an MP3 file from the given file path and displays the waveform.
        """

        self.original_data, self.sample_rate, self.num_channels = read_audio_file(
            file_path)
        self.playing_data = self.original_data
        # Display waveform
        self.plot.display_waveform(self)

    def toggle_play_pause(self, _):
        print("Toggling play/pause")
        if self.playing:
            self.stop_mp3()  # Pause the music
        else:
            self.play_mp3()  # Unpause the music

    def play_mp3(self):
        pygame.mixer.quit()
        self.playing = False
        print("Stopped")

        pygame.mixer.init()
        pygame.init()
        self.paused_at = None

        if self.playing_data.any():
            if self.num_channels == 1:
                audio = np.stack(
                    (self.playing_data, self.playing_data), axis=-1)
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
        self.loop_start = int((xmin / self.sample_rate) * 1000)
        self.loop_end = int((xmax / self.sample_rate) * 1000)
        print(f"Selected region from {
              self.loop_start} ms to {self.loop_end} ms")

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

    def on_plot_click(self, start_at):
        self.playing_data = get_audio_array(self.original_data, start_at/1000,
                                            self.original_data.shape[0] /
                                            self.sample_rate - start_at/1000,
                                            self.sample_rate)
        self.loop_start = start_at
        self.loop_end = None

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
        """
        Slows down the audio by a factor of 0.8.
        """
        slow_down_rate = 0.8
        stretched_audio_int16 = stretch_audio(
            self.original_data, slow_down_rate)

        self.original_data = stretched_audio_int16
        self.plot.display_waveform(self)

        self.playing_data = stretched_audio_int16

        print(f"Slow down rate: {slow_down_rate}")

    def mark_beat(self, event):
        """
        Marks the current time as a beat.
        """
        current_time = self.get_current_time()
        self.beats.append(current_time)
        # self.plot.update_beat_axis()
        # print(self.beats)

    def mark_measure(self, event):
        """
        Marks the current time as a measure.
        """
        self.measures.append(self.get_current_time())
        print(self.measures)
