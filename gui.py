# gui.py

import tkinter as tk
from tkinter import filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D

from gcode_parser import parse_gcode, extract_movements
from time_calculator import calculate_time, DEFAULT_SETTINGS


class GCodeAnalyzer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("G-Code Analyzer")
        self.geometry("800x600")
        self.settings = DEFAULT_SETTINGS.copy()

        self.create_widgets()

    def create_widgets(self):
        self.open_button = tk.Button(self, text="Open G-Code File", command=self.open_file)
        self.open_button.pack()

        self.settings_button = tk.Button(self, text="Settings", command=self.open_settings)
        self.settings_button.pack()

        self.result_label = tk.Label(self, text="")
        self.result_label.pack()

        self.canvas_frame = tk.Frame(self)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

    def open_file(self):
        try:
            file_path = filedialog.askopenfilename(filetypes=[("G-Code files", "*.txt"), ("All files", "*.*")])
            if file_path:
                with open(file_path, 'r') as file:
                    gcode = file.read()

                lines = parse_gcode(gcode)
                total_time = calculate_time(lines, self.settings)
                self.display_time(total_time)

                movements = extract_movements(lines)
                self.plot_movements(movements, total_time)

                self.result_label.config(text="File loaded successfully!")

        except Exception as e:
            self.result_label.config(text=f"Error loading file: {e}")

    def display_time(self, total_time):
        minutes = int(total_time // 60)
        seconds = total_time % 60
        self.result_label.config(
            text=f"Estimated time to complete the program: {minutes} minutes and {seconds:.2f} seconds")

    def plot_movements(self, movements, total_time):
        fig = plt.figure()

        # 2D plot
        ax1 = fig.add_subplot(121)
        for move in movements:
            start, end = move
            ax1.plot([start[0], end[0]], [start[1], end[1]], 'b-')

        ax1.set_xlabel("X")
        ax1.set_ylabel("Y")
        ax1.set_title("2D Tool Path")
        ax1.axis('equal')

        # Display total time on the plot
        minutes = int(total_time // 60)
        seconds = total_time % 60
        ax1.text(0.5, 0.95, f"Total Time: {minutes} minutes and {seconds:.2f} seconds",
                 transform=ax1.transAxes, ha="center", va="center", fontsize=12, color="red")

        # 3D plot with constant Z strategy
        ax2 = fig.add_subplot(122, projection='3d')
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
