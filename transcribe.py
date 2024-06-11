import tkinter as tk
from tkinter import filedialog
import pygame
from pydub import AudioSegment
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.widgets import SpanSelector
import matplotlib.ticker as ticker
import librosa
import time

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
    if stretched_audio.ndim == 1:
        stretched_audio_int16 = np.stack((stretched_audio_int16, stretched_audio_int16), axis=-1)
    return stretched_audio_int16



class MusicTranscriberApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Music Transcriber")

        # Initialize Pygame mixer
        pygame.mixer.init()
        pygame.init()

        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Create a frame for the buttons
        button_frame = tk.Frame(root)
        button_frame.pack(side=tk.TOP, fill=tk.X)

        # Load button
        self.load_button = tk.Button(button_frame, text="Load MP3", command=self.load_mp3)
        self.load_button.pack(side=tk.LEFT)

        # Play button
        self.play_button = tk.Button(button_frame, text="Play", command=self.play_mp3)
        self.play_button.pack(side=tk.LEFT)

        # Pause button
        self.pause_button = tk.Button(button_frame, text="Pause", command=self.pause_mp3)
        self.pause_button.pack(side=tk.LEFT)

        # Slow down button
        self.slow_down_button = tk.Button(button_frame, text="Slow Down", command=self.slow_down)
        self.slow_down_button.pack(side=tk.LEFT)

        # Mark beats and measures
        self.mark_beat_button = tk.Button(button_frame, text="Mark Beat", command=self.mark_beat)
        self.mark_beat_button.pack(side=tk.LEFT)

        self.mark_measure_button = tk.Button(button_frame, text="Mark Measure", command=self.mark_measure)
        self.mark_measure_button.pack(side=tk.LEFT)

        self.reset_loop_button = tk.Button(button_frame, text="Reset Loop", command=self.reset_loop)
        self.reset_loop_button.pack(side=tk.LEFT)        

        self.inc_plot_window_button = tk.Button(button_frame, text="-", command=self.increase_loop_window)
        self.inc_plot_window_button.pack(side=tk.LEFT)   

        self.dec_plot_window_button = tk.Button(button_frame, text="+", command=self.decrease_loop_window)
        self.dec_plot_window_button.pack(side=tk.LEFT)          

        self.dec_plot_line_button = tk.Button(button_frame, text="<", command=self.decrease_loop_line)
        self.dec_plot_line_button.pack(side=tk.LEFT)     

        self.inc_plot_line_button = tk.Button(button_frame, text=">", command=self.increase_loop_line)
        self.inc_plot_line_button.pack(side=tk.LEFT)   
        

        # Currently loaded MP3
        self.current_mp3 = None

        self.beats = []
        self.measures = []

        # Audio data
        self.original_data = None
        self.playing_data = None
        self.sample_rate = None
        self.num_channels = None

        # Playback and loop state
        self.playing = False
        self.loop_start = 0
        self.loop_end = None
        self.start_play_time = None

        # # Set up matplotlib figure and axis
        # self.fig, self.ax = plt.subplots()
        # self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        # self.canvas.get_tk_widget().pack()

        # Plot
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # Connect the callback function to the 'button_press_event'
        cid = self.fig.canvas.mpl_connect('button_press_event', self.on_click)



        # Navigation toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, root)
        self.toolbar.update()

        # Span selector for interactive selection
        self.span = SpanSelector(self.ax, self.on_select, 'horizontal', useblit=True)

        # Plot variables
        self.plot_data = None
        self.plot_line = None
        self.playback_line = None
        self.loop_start_line = None
        self.loop_end_line = None
        self.paused_at = 0

        self.plot_window = 500000  # Plot window size in samples
        self.plot_line_divisions = 8
        self.plot_line_index = 2

        self.current_plot_pos = 0

    def increase_loop_line(self):
        self.plot_line_index = self.plot_line_index + 1
        if self.plot_line_index == self.plot_line_divisions:
            self.plot_line_index = self.plot_line_divisions - 1
        print(f"Plot line: {self.plot_line_index}")
        self.draw_plot()

    def decrease_loop_line(self):
        self.plot_line_index = self.plot_line_index - 1
        if self.plot_line_index < 1:
            self.plot_line_index = 1
        print(f"Plot line: {self.plot_line_index}")
        self.draw_plot()    

    def increase_loop_window(self):
        self.plot_window = 2*self.plot_window
        if self.plot_window > len(self.plot_data):
            self.plot_window = len(self.plot_data)
        print(f"Plot window: {self.plot_window}")
        self.draw_plot()

    def decrease_loop_window(self):
        self.plot_window = int(self.plot_window/2)
        print(f"Plot window: {self.plot_window}")      
        self.draw_plot()

    def on_closing(self):
        print("Closing")
        self.plot_data
        pygame.mixer.stop()  # Stop music playback
        self.root.quit()        # Close the application
        pygame.quit()

    def load_mp3(self):
        file_path = filedialog.askopenfilename(initialdir="~/Documents/", filetypes=[("MP3 files", "*.mp3")])
        if file_path:
            self.original_data, self.sample_rate, self.num_channels = read_audio_file(file_path)

            self.playing_data = self.original_data

            # Display waveform
            self.display_waveform(file_path)

    def display_waveform(self, file_path):
        self.plot_data = self.playing_data
        self.ax.clear()
        self.plot_line, = self.ax.plot(self.plot_data)
        # self.plot_window = len(self.plot_data)
        self.playback_line = self.ax.axvline(x=0, color='r')  # Vertical line for playback position

        self.loop_start_line = self.ax.axvline(x=0, color='r', linestyle='--', linewidth=0.5)  # Red dashed line for loop start
        self.loop_end_line = self.ax.axvline(x=0, color='g', linestyle='--', linewidth=0.5)

        self.update_xaxis_labels()
        self.canvas.draw()

        # self.update_plot()

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
                self.update_plot()  # Start the plot update loop   

                print("Playing")


    def pause_mp3(self):
        if self.playing_data.any():
            if self.playing:
                pygame.mixer.pause()
                # record the time the playback was paused
                self.playing = False
                self.paused_at = pygame.time.get_ticks()

                self.update_plot() 
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
                    self.update_plot()  
                    print("Unpaused")

    def on_select(self, xmin, xmax):
        # Convert sample indices to time in milliseconds
        self.loop_start = int((xmin / self.sample_rate) * 1000)
        self.loop_end = int((xmax / self.sample_rate) * 1000)
        print(f"Selected region from {self.loop_start} ms to {self.loop_end} ms")

        self.playing_data = get_audio_array(self.original_data, self.loop_start/1000, 
                                       self.loop_end/1000 - self.loop_start/1000,
                                       self.sample_rate)
        # self.update_plot()

        if self.playing:
            self.play_mp3()

    # Define a callback function to handle click events
    def on_click(self, event):
        # Check if the event was a mouse button press and if it occurred within the plot area
        if event.inaxes:
            x = event.xdata  # Get the x-coordinate of the click
            y = event.ydata  # Get the y-coordinate of the click (optional, if you need it)
            start_at = int((x / self.sample_rate) * 1000)

            self.playing_data = get_audio_array(self.original_data, start_at/1000, 
                                                self.original_data.shape[0]/self.sample_rate - start_at/1000,
                                                self.sample_rate)
            self.loop_start = start_at
            self.loop_end = None

            print(f"Clicked at x={start_at}")

    def reset_loop(self):
        self.playing_data = self.original_data
        self.loop_start = 0
        self.loop_end = self.playing_data.shape[0]
        if self.playing:
            self.play_mp3()        
        print("Loop reset")

    # def loop_music(self):
    #     if self.looping:
    #         current_pos = pygame.mixer.music.get_pos()
    #         if current_pos == -1 or current_pos >= self.loop_end:
    #             pygame.mixer.music.stop()
    #             pygame.mixer.music.play(start=self.loop_start / 1000.0)
    #         self.root.after(100, self.loop_music)

    def slow_down(self):
        slow_down_rate = 0.7
        stretched_audio_int16 = stretch_audio(self.original_data, slow_down_rate)   
        self.display_waveform(stretched_audio_int16)
        
        self.playing_data = stretched_audio_int16
     
        print(f"Slow down rate: {slow_down_rate}")
        # if self.current_mp3:
            # slowed = self.change_speed(self.current_mp3, 0.5)
            # slowed.export("slowed.mp3", format="mp3")
            # pygame.mixer.music.load("slowed.mp3")
            # pygame.mixer.music.play()
            # self.playing = True
            # self.looping = False
            # print("Slowed down")

    # def change_speed(self, sound, speed=1.0):
    #     # Speed < 1.0 slows down, speed > 1.0 speeds up
    #     sound_with_altered_frame_rate = sound._spawn(sound.raw_data, overrides={
    #          "frame_rate": int(sound.frame_rate * speed)
    #     })

    #     # Convert the sound with altered frame rate back to the original frame rate
    #     return sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)

    def mark_beat(self):
        if pygame.mixer.music.get_busy():
            beat_time = pygame.mixer.music.get_pos()
            self.beats.append(beat_time)
            print(f"Beat marked at: {beat_time} ms")

    def mark_measure(self):
        if pygame.mixer.music.get_busy():
            measure_time = pygame.mixer.music.get_pos()
            self.measures.append(measure_time)
            print(f"Measure marked at: {measure_time} ms")

    def update_plot(self):
        if self.plot_data is not None:
            # get the current time
            current_time = pygame.time.get_ticks() - self.start_play_time + self.loop_start
            # the current time should not exceed the loop end. It should loop back to the loop start
            if self.loop_end is not None and current_time >= self.loop_end:
                current_time = self.loop_start + (current_time - self.loop_end)
                self.start_play_time = pygame.time.get_ticks()

            # convert the time to sample index
            self.current_plot_pos = int(current_time / 1000 * self.sample_rate)

            # self.current_plot_pos = self.current_plot_pos + self.loop_start
            self.draw_plot()

            if self.playing:
                self.root.after(100, self.update_plot)


    def draw_plot(self):
        start = max(0, self.current_plot_pos - int(self.plot_line_index * self.plot_window / self.plot_line_divisions))
        end = min(len(self.plot_data), self.current_plot_pos + int((self.plot_line_divisions - self.plot_line_index)*self.plot_window/self.plot_line_divisions))

        self.plot_line.set_data(np.arange(start, end), self.plot_data[start:end])
        self.ax.set_xlim(start, end)

        self.playback_line.set_xdata([self.current_plot_pos])  # Update playback position line


        # # Draw vertical lines for loop start and end
        # if self.loop_start is not None:
        #     loop_start_index = int(self.loop_start / 1000 * self.sample_rate)
        #     self.ax.axvline(x=loop_start_index, color='r', linestyle='--', linewidth=0.5)  # Red dashed line for loop start
        # if self.loop_end is not None:
        #     loop_end_index = int(self.loop_end / 1000 * self.sample_rate)
        #     self.ax.axvline(x=loop_end_index, color='g', linestyle='--', linewidth=0.5)  # Green dashed line for loop end

        if self.loop_start is not None:
            loop_start_index = int(self.loop_start / 1000 * self.sample_rate)
            self.loop_start_line.set_xdata([loop_start_index])
        if self.loop_end is not None:
            loop_end_index = int(self.loop_end / 1000 * self.sample_rate)
            self.loop_end_line.set_xdata([loop_end_index])

        self.canvas.draw()

    def update_xaxis_labels(self):
        # Format the x-axis ticks to show minutes and seconds
        formatter = ticker.FuncFormatter(lambda x, pos: time.strftime('%M:%S', time.gmtime(x / self.sample_rate)))
        self.ax.xaxis.set_major_formatter(formatter)

        # Set the x-axis label to 'Time (min:sec)'
        self.ax.set_xlabel('Time (min:sec)')
        #     # Format the x-axis ticks to show minutes, seconds and milliseconds
        # formatter = ticker.FuncFormatter(lambda x, pos: time.strftime('%M:%S', time.gmtime(x / self.sample_rate)) + f".{int((x / self.sample_rate % 1) * 10):01}")
        # self.ax.xaxis.set_major_formatter(formatter)

        # # Set the x-axis label to 'Time (min:sec.msec)'
        # self.ax.set_xlabel('Time (min:sec.msec)')
    

if __name__ == "__main__":
    root = tk.Tk()
    app = MusicTranscriberApp(root)
    # app.update_plot()  # Start the plot update loop
    root.mainloop()
