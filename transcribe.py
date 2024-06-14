import tkinter as tk
from tkinter import filedialog

from core import Core
from plot import Plot


class MusicTranscriberApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Music Transcriber")

        self.plot = Plot(root)

        core = Core(root, self.plot)
        self.core = core

        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Create a frame for the buttons
        button_frame = tk.Frame(root)
        button_frame.pack(side=tk.TOP, fill=tk.X)

        # Load button
        self.load_button = tk.Button(button_frame, text="Load MP3", command=self.load_mp3)
        self.load_button.pack(side=tk.LEFT)

        # Play button
        self.play_button = tk.Button(button_frame, text="Play", command=core.play_mp3)
        self.play_button.pack(side=tk.LEFT)

        # Pause button
        self.pause_button = tk.Button(button_frame, text="Stop", command=core.stop_mp3)
        self.pause_button.pack(side=tk.LEFT)

        # Slow down button
        self.slow_down_button = tk.Button(button_frame, text="Slow Down", command=core.slow_down)
        self.slow_down_button.pack(side=tk.LEFT)

        # Mark beats and measures
        self.mark_beat_button = tk.Button(button_frame, text="Mark Beat", command=core.mark_beat)
        self.mark_beat_button.pack(side=tk.LEFT)

        self.mark_measure_button = tk.Button(button_frame, text="Mark Measure", command=core.mark_measure)
        self.mark_measure_button.pack(side=tk.LEFT)

        self.reset_loop_button = tk.Button(button_frame, text="Reset Loop", command=core.reset_loop)
        self.reset_loop_button.pack(side=tk.LEFT)        

        self.inc_plot_window_button = tk.Button(button_frame, text="-", command=self.plot.increase_loop_window)
        self.inc_plot_window_button.pack(side=tk.LEFT)   

        self.dec_plot_window_button = tk.Button(button_frame, text="+", command=self.plot.decrease_loop_window)
        self.dec_plot_window_button.pack(side=tk.LEFT)          

        self.dec_plot_line_button = tk.Button(button_frame, text="<", command=self.plot.decrease_loop_line)
        self.dec_plot_line_button.pack(side=tk.LEFT)     

        self.inc_plot_line_button = tk.Button(button_frame, text=">", command=self.plot.increase_loop_line)
        self.inc_plot_line_button.pack(side=tk.LEFT)   

        # Bind the space key to the on_space method
        self.root.bind('<space>', core.toggle_play_pause)
        self.root.bind('b', core.mark_beat)
        self.root.bind('m', core.mark_measure)

        self.core.load_mp3_from_file_path("/home/dimitris/Documents/Stepped-Green.mp3")


    def on_closing(self):
        print("Closing")
        self.core.on_closing()
        self.root.quit()        # Close the application

    def load_mp3(self):
        file_path = filedialog.askopenfilename(initialdir="~/Documents/", filetypes=[("MP3 files", "*.mp3")])
        if file_path:
            self.core.load_mp3_from_file_path(file_path)        


if __name__ == "__main__":
    root = tk.Tk()
    app = MusicTranscriberApp(root)
    root.mainloop()
