# gui.py

import tkinter as tk
from tkinter import filedialog, messagebox, font
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation
import numpy as np

from gcode_parser import parse_gcode, extract_movements
from time_calculator import calculate_time, DEFAULT_SETTINGS


class GCodeAnalyzer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Parsa's GcodeSim")
        self.geometry("1400x800")
        self.settings = DEFAULT_SETTINGS.copy()

        self.create_widgets()

    def create_widgets(self):
        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(size=12)

        self.open_button = tk.Button(self, text="Open G-Code File", command=self.open_file, font=default_font)
        self.open_button.pack(pady=5)

        self.settings_button = tk.Button(self, text="Settings", command=self.open_settings, font=default_font)
        self.settings_button.pack(pady=5)

        self.result_label = tk.Label(self, text="", font=default_font)
        self.result_label.pack(pady=5)

        # Time breakdown frame
        self.time_frame = tk.LabelFrame(self, text="Time Breakdown", font=default_font)
        self.time_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.time_scroll = tk.Scrollbar(self.time_frame)
        self.time_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.time_breakdown_text = tk.Text(self.time_frame, height=10, wrap=tk.WORD,
                                           yscrollcommand=self.time_scroll.set, font=default_font)
        self.time_breakdown_text.pack(fill=tk.BOTH, expand=True)

        self.time_scroll.config(command=self.time_breakdown_text.yview)

        # Plot frame
        self.plot_frame = tk.LabelFrame(self, text="Tool Path", font=default_font)
        self.plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.canvas_frame = tk.Frame(self.plot_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

        # Animation frame
        self.animation_frame = tk.LabelFrame(self, text="Animation", font=default_font)
        self.animation_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.animation_canvas_frame = tk.Frame(self.animation_frame)
        self.animation_canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.control_frame = tk.Frame(self.animation_frame)
        self.control_frame.pack(pady=5)

        self.play_button = tk.Button(self.control_frame, text="Play", command=self.play_animation, font=default_font)
        self.play_button.pack(side=tk.LEFT, padx=5)

        self.pause_button = tk.Button(self.control_frame, text="Pause", command=self.pause_animation, font=default_font)
        self.pause_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = tk.Button(self.control_frame, text="Stop", command=self.stop_animation, font=default_font)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.speed_label = tk.Label(self.control_frame, text="Speed:", font=default_font)
        self.speed_label.pack(side=tk.LEFT, padx=5)

        self.speed_var = tk.DoubleVar(value=1.0)
        self.speed_scale = tk.Scale(self.control_frame, from_=0.1, to=3.0, orient=tk.HORIZONTAL, resolution=0.1,
                                    variable=self.speed_var, font=default_font)
        self.speed_scale.pack(side=tk.LEFT, padx=5)

        self.animation_running = False

    def open_file(self):
        try:
            file_path = filedialog.askopenfilename(filetypes=[("G-Code files", "*.txt"), ("All files", "*.*")])
            if file_path:
                with open(file_path, 'r') as file:
                    gcode = file.read()

                lines = parse_gcode(gcode)
                total_time, time_breakdown = calculate_time(lines, self.settings)
                self.display_time(total_time, time_breakdown)

                movements = extract_movements(lines)
                self.plot_movements(movements, total_time)
                self.movements = movements
                self.total_time = total_time

                self.result_label.config(
                    text=f"File loaded successfully! Total Time: {int(total_time // 60)} minutes and {total_time % 60:.2f} seconds")
                self.prepare_animation(movements)
        except Exception as e:
            self.result_label.config(text=f"Error loading file: {e}")

    def display_time(self, total_time, time_breakdown):
        breakdown_text = "\n".join([f"{key}: {value:.2f} seconds" for key, value in time_breakdown.items()])
        self.time_breakdown_text.delete(1.0, tk.END)
        self.time_breakdown_text.insert(tk.END, breakdown_text)

    def plot_movements(self, movements, total_time):
        fig = plt.figure()

        # 2D plot
        ax1 = fig.add_subplot(131)
        for move in movements:
            start, end = move
            ax1.plot([start[0], end[0]], [start[1], end[1]], 'b-')

        ax1.set_xlabel("X")
        ax1.set_ylabel("Y")
        ax1.set_title("2D Tool Path")
        ax1.axis('equal')

        # 3D plot with constant Z strategy
        ax2 = fig.add_subplot(132, projection='3d')
        z_levels = sorted(set(pos[1][2] for pos in movements))
        colors = {'G0': 'r', 'G1': 'g', 'G2': 'b'}

        for z in z_levels:
            for move in movements:
                start, end = move
                if start[2] == z and end[2] == z:
                    g_code = 'G0'  # Default to G0
                    if abs(start[2] - end[2]) > 0:
                        g_code = 'G1'
                    elif abs(start[0] - end[0]) > 0 or abs(start[1] - end[1]) > 0:
                        g_code = 'G2'
                    ax2.plot([start[0], end[0]], [start[1], end[1]], [start[2], end[2]], colors[g_code])
            # Add horizontal lines at each Z level to visualize slicing
            ax2.plot([min(start[0] for start, end in movements), max(end[0] for start, end in movements)],
                     [min(start[1] for start, end in movements), max(end[1] for start, end in movements)],
                     [z, z], 'k--')

        ax2.set_xlabel("X")
        ax2.set_ylabel("Y")
        ax2.set_zlabel("Z")
        ax2.set_title("3D Tool Path (Constant Z Slicing)")

        for widget in self.canvas_frame.winfo_children():
            widget.destroy()

        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def prepare_animation(self, movements):
        self.fig, self.ax = plt.subplots()

        self.ax.set_xlim([min(move[0][0] for move in movements), max(move[1][0] for move in movements)])
        self.ax.set_ylim([min(move[0][1] for move in movements), max(move[1][1] for move in movements)])

        self.line, = self.ax.plot([], [], 'bo-')
        self.animation_data = self.get_animation_data(movements)
        self.ani = FuncAnimation(self.fig, self.update_animation, frames=len(self.animation_data), interval=1000,
                                 blit=True)

        for widget in self.animation_canvas_frame.winfo_children():
            widget.destroy()

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.animation_canvas_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def get_animation_data(self, movements):
        data = []
        for move in movements:
            start, end = move
            data.append((start[0], start[1]))
            data.append((end[0], end[1]))
        return data

    def update_animation(self, frame):
        self.line.set_data([self.animation_data[frame][0]], [self.animation_data[frame][1]])
        return self.line,

    def play_animation(self):
        if not self.animation_running:
            self.ani.event_source.start()
            self.animation_running = True

    def pause_animation(self):
        if self.animation_running:
            self.ani.event_source.stop()
            self.animation_running = False

    def stop_animation(self):
        self.pause_animation()
        self.prepare_animation(self.movements)

    def open_settings(self):
        settings_window = tk.Toplevel(self)
        settings_window.title("Settings")

        labels = {
            "RAPID_SPEED": "Rapid Speed (mm/min):",
            "MAX_FEED_RATE": "Max Feed Rate (mm/min):",
            "ACCELERATION": "Acceleration (mm/s²):",
            "PALLET_CHANGE_TIME": "Pallet Change Time (seconds):",
            "M143_TIME": "M143 Time (seconds):",
            "M142_TIME": "M142 Time (seconds):",
            "M9_TIME": "M9 Time (seconds):",
            "M05_TIME": "M05 Time (seconds):"
        }

        for idx, (key, label) in enumerate(labels.items()):
            tk.Label(settings_window, text=label).grid(row=idx, column=0, padx=10, pady=5)
            entry = tk.Entry(settings_window)
            entry.insert(0, str(self.settings[key]))
            entry.grid(row=idx, column=1, padx=10, pady=5)
            entry.bind("<FocusOut>", lambda e, k=key, e2=entry: self.update_setting(k, e2))

    def update_setting(self, key, entry):
        try:
            self.settings[key] = float(entry.get())
        except ValueError:
            messagebox.showerror("Invalid input", f"Please enter a valid number for {key}.")
