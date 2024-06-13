import tkinter as tk
import pygame
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.widgets import SpanSelector
import matplotlib.ticker as ticker
import time

from core import get_audio_array


class Plot:
    def __init__(self, root):
        self.root = root

       # Plot
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # Connect the callback function to the 'button_press_event'
        cid = self.fig.canvas.mpl_connect('button_press_event', self.on_click)

        # Navigation toolbar
        # self.toolbar = NavigationToolbar2Tk(self.canvas, root)
        # self.toolbar.update()

        # Span selector for interactive selection
        self.span = SpanSelector(self.ax, self.on_select, 'horizontal', useblit=True)

        # Reference to the core
        self.core = None

        # Plot variables

        self.plot_data = None
        self.plot_line = None
        self.playback_line = None
        self.loop_start_line = None
        self.loop_end_line = None

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

    def display_waveform(self, core):
        self.core = core
        self.plot_data = self.core.original_data
        self.ax.clear()
        self.plot_line, = self.ax.plot(self.plot_data)
        # self.plot_window = len(self.plot_data)
        self.playback_line = self.ax.axvline(x=0, color='r')  # Vertical line for playback position

        self.loop_start_line = self.ax.axvline(x=0, color='r', linestyle='--', linewidth=0.5)  # Red dashed line for loop start
        self.loop_end_line = self.ax.axvline(x=0, color='g', linestyle='--', linewidth=0.5)

        self.update_xaxis_labels()
        self.canvas.draw()
        # self.update_plot()

    def on_select(self, xmin, xmax):
        self.core.on_select(xmin, xmax)

    # Define a callback function to handle click events
    def on_click(self, event):
        self.core.on_click(event)

    def update_plot(self):
        if self.plot_data is not None:
            # get the current time
            current_time = pygame.time.get_ticks() - self.core.start_play_time + self.core.loop_start
            # the current time should not exceed the loop end. It should loop back to the loop start
            if self.core.loop_end is not None and current_time >= self.core.loop_end:
                current_time = self.core.loop_start + (current_time - self.core.loop_end)
                self.core.start_play_time = pygame.time.get_ticks()

            # convert the time to sample index
            self.current_plot_pos = int(current_time / 1000 * self.core.sample_rate)

            # self.current_plot_pos = self.current_plot_pos + self.loop_start
            self.draw_plot()

            if self.core.playing:
                self.root.after(100, self.update_plot)


    def draw_plot(self):
        start = max(0, self.current_plot_pos - int(self.plot_line_index * self.plot_window / self.plot_line_divisions))
        end = min(len(self.plot_data), self.current_plot_pos + int((self.plot_line_divisions - self.plot_line_index)*self.plot_window/self.plot_line_divisions))

        self.plot_line.set_data(np.arange(start, end), self.plot_data[start:end])
        self.ax.set_xlim(start, end)

        self.playback_line.set_xdata([self.current_plot_pos])  # Update playback position line


        # # Draw vertical lines for loop start and end
        # if self.loop_start is not None:
        #     loop_start_index = int(self.loop_start / 1000 * self.core.sample_rate)
        #     self.ax.axvline(x=loop_start_index, color='r', linestyle='--', linewidth=0.5)  # Red dashed line for loop start
        # if self.loop_end is not None:
        #     loop_end_index = int(self.loop_end / 1000 * self.core.sample_rate)
        #     self.ax.axvline(x=loop_end_index, color='g', linestyle='--', linewidth=0.5)  # Green dashed line for loop end

        if self.core.loop_start is not None:
            loop_start_index = int(self.core.loop_start / 1000 * self.core.sample_rate)
            self.loop_start_line.set_xdata([loop_start_index])
        if self.core.loop_end is not None:
            loop_end_index = int(self.core.loop_end / 1000 * self.core.sample_rate)
            self.loop_end_line.set_xdata([loop_end_index])

        self.canvas.draw()

    def update_xaxis_labels(self):
        # Format the x-axis ticks to show minutes and seconds
        formatter = ticker.FuncFormatter(lambda x, pos: time.strftime('%M:%S', time.gmtime(x / self.core.sample_rate)))
        self.ax.xaxis.set_major_formatter(formatter)

        # Set the x-axis label to 'Time (min:sec)'
        self.ax.set_xlabel('Time (min:sec)')

    
