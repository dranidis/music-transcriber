import tkinter as tk
import time
import pygame
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.widgets import SpanSelector
import matplotlib.ticker as ticker


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
        self.span = SpanSelector(
            self.ax, self.on_select, 'horizontal', useblit=True)

        # Reference to the core
        self.core = None

        # Plot variables

        self.plot_data = None
        self.plot_line = None
        self.playback_line = None
        self.loop_start_line = None
        self.loop_end_line = None

        self.beat_axis = None

        self.plot_downsample = 20

        self.plot_window = 500000 / self.plot_downsample  # Plot window size in samples
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
        self.plot_data = self.core.original_data[::self.plot_downsample]
        self.ax.clear()
        self.plot_line, = self.ax.plot(self.plot_data)
        # self.plot_window = len(self.plot_data)
        # Vertical line for playback position
        self.playback_line = self.ax.axvline(x=0, color='r')

        self.loop_start_line = self.ax.axvline(
            x=0, color='r', linestyle='--', linewidth=0.5)  # Red dashed line for loop start
        self.loop_end_line = self.ax.axvline(
            x=0, color='g', linestyle='--', linewidth=0.5)

        # Create a twin x-axis for the beats
        self.beat_axis = self.ax.twiny()
        self.beat_axis.xaxis.tick_top()
        self.beat_axis.xaxis.set_label_position('top')

        # Convert beats from milliseconds to samples
        beat_samples = [
            (beat / 1000) * self.core.sample_rate for beat in self.core.beats]

        # Adjust for downsampling
        beat_samples_downsampled = [
            beat / self.plot_downsample for beat in beat_samples]

        # Set the initial tick locations to the beats
        self.beat_axis.set_xticks(beat_samples_downsampled)
        self.beat_axis.set_xticklabels(
            [''] * len(beat_samples_downsampled))  # No labels, just ticks

        self.update_xaxis_labels()
        self.canvas.draw()
        # self.update_plot()

    def on_select(self, xmin, xmax):
        print(f"Selected region from {xmin} to {xmax}")
        self.core.on_select(xmin * self.plot_downsample,
                            xmax * self.plot_downsample)

    def transform_to_ms(self, value, min_ms, max_ms):
        return value * (max_ms - min_ms) + min_ms

    def get_current_x_range(self, ax):
        return ax.get_xlim()

    # Define a callback function to handle click events
    def on_click(self, event):
        # Check if the click was in the primary axes
        if event.inaxes != self.ax and event.inaxes != self.beat_axis:
            return

        # # If the click was in the secondary axis, convert the x-coordinate to the scale of the primary axis
        # if event.inaxes == self.beat_axis:
        #     print('secondary axis')
        #     # xdata = self.ax.transData.inverted().transform((event.xdata, 0))[0]
        #     xmin, xmax = self.get_current_x_range(self.ax)
        #     xdata = self.transform_to_ms(event.xdata, xmin, xmax)
        # else:
        #     print('primary axis')
        #     xdata = event.xdata

        # print(f"Clicked at x={xdata}")
        # self.core.on_click(xdata)

        x = event.xdata * self.plot_downsample
        start_at = int((x / self.core.sample_rate) * 1000)

        self.core.on_plot_click(start_at)

        self.current_plot_pos = int(
            start_at / 1000 * self.core.sample_rate / self.plot_downsample)
        print(f"Clicked at x1={start_at}")

        # self.plot.draw_plot()

    def update_plot(self):
        if self.plot_data is not None:
            # get the current time
            current_time = self.core.get_current_time()
            # the current time should not exceed the loop end. It should loop back to the loop start
            if self.core.loop_end is not None and current_time >= self.core.loop_end:
                current_time = self.core.loop_start + \
                    (current_time - self.core.loop_end)
                self.core.start_play_time = pygame.time.get_ticks()

            # convert the time to sample index
            self.current_plot_pos = int(
                current_time / 1000 * self.core.sample_rate / self.plot_downsample)

            # self.current_plot_pos = self.current_plot_pos + self.loop_start
            self.draw_plot()

            if self.core.playing:
                self.root.after(100, self.update_plot)

    def draw_plot(self):
        start = max(0, self.current_plot_pos - int(self.plot_line_index *
                    self.plot_window / self.plot_line_divisions))
        end = min(len(self.plot_data), self.current_plot_pos + int((self.plot_line_divisions -
                  self.plot_line_index)*self.plot_window/self.plot_line_divisions))

        # start *= self.plot_downsample
        # end *= self.plot_downsample

        self.plot_line.set_data(np.arange(start, end),
                                self.plot_data[start:end])
        self.ax.set_xlim(start, end)

        # Update playback position line
        self.playback_line.set_xdata([self.current_plot_pos])

        if self.core.loop_start is not None:
            loop_start_index = int(
                self.core.loop_start / 1000 * self.core.sample_rate / self.plot_downsample)
            self.loop_start_line.set_xdata([loop_start_index])
        else:
            self.loop_start_line.set_xdata([0])
        if self.core.loop_end is not None:
            loop_end_index = int(self.core.loop_end / 1000 *
                                 self.core.sample_rate / self.plot_downsample)
            self.loop_end_line.set_xdata([loop_end_index])
        else:
            self.loop_end_line.set_xdata([0])

        self.update_beat_axis()

        self.canvas.draw()

    def update_xaxis_labels(self):
        # Format the x-axis ticks to show minutes and seconds
        formatter = ticker.FuncFormatter(lambda x, pos: time.strftime(
            '%M:%S', time.gmtime(x / self.core.sample_rate * self.plot_downsample)))
        self.ax.xaxis.set_major_formatter(formatter)

        # Set the x-axis label to 'Time (min:sec)'
        self.ax.set_xlabel('Time (min:sec)')

        self.update_beat_axis()

    def update_beat_axis(self):
        # print("Updating beat axis")
        # Update the beat axis
        if hasattr(self, 'beat_axis'):
            # print(self.beat_axis.get_xticks())
            # Convert beats from milliseconds to samples and adjust for downsampling
            beat_samples_downsampled = [
                (beat / 1000) * self.core.sample_rate / self.plot_downsample for beat in self.core.beats]
            self.beat_axis.set_xticks(beat_samples_downsampled)
            self.beat_axis.set_xticklabels(
                [''] * len(beat_samples_downsampled))

            # Update the x-axis range of the beat axis to match the main x-axis
            self.beat_axis.set_xlim(self.ax.get_xlim())
